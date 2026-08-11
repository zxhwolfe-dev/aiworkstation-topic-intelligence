#!/usr/bin/env python3
"""Run Topic Intelligence eval cases in fresh host processes.

The runner is intentionally host-observability tooling, not a semantic judge and
not a Skill installer.  It records what a fresh host process did, preserves the
raw trace, and classifies only behavior that is directly observable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

# Keep the direct `python scripts/run_host_evals.py` entrypoint importable.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.grade_host_eval import PASS_GRADES, grade_report


REPORT_SCHEMA = "ati.host-eval.v1"
SUPPORTED_HOSTS = ("codex",)
SUPPORTED_SUITES = ("trigger", "quality", "v0.2.1")
TOPIC_INTELLIGENCE_SKILLS = (
    "creator-topic-opportunity-research",
    "evidence-backed-content-brief",
)
HANDOFF_SCHEMA = "ati.topic-opportunity-handoff.v1"
DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_MAX_OUTPUT_CHARS = 200_000
LIVE_RADAR_NETWORK_DOMAIN = "aiworkstation.cn"
LIVE_RADAR_NETWORK_DOMAINS = [LIVE_RADAR_NETWORK_DOMAIN]
ORIGIN_OVERRIDE_ENV_VARS = (
    "AIWORKSTATION_TOPIC_RADAR_BASE_URL",
    "AI_WORKSTATION_API_BASE_URL",
    "TOPIC_RADAR_BASE_URL",
)
PASSING_TRACE_INTEGRITY_STATUSES = {
    "complete_clean",
    "complete_after_recovery",
}
TOOL_ITEM_TYPES = {
    "command_execution",
    "file_change",
    "image_generation",
    "mcp_tool_call",
    "web_search",
}
STREAM_DISCONNECT_MARKERS = (
    "responsestreamdisconnected",
    "response_stream_disconnected",
    "response stream disconnected",
    "stream disconnected",
    "stream closed before response.completed",
)
STREAM_DISCONNECT_CODES = {
    "responsestreamdisconnected",
    "responsestreamdisconnect",
    "streamdisconnected",
    "streamdisconnect",
}


class HostEvalError(RuntimeError):
    """Raised when an eval run cannot be prepared safely."""


@dataclass(frozen=True)
class EvalCase:
    suite: str
    case_id: str
    prompt: str
    expected_skill: str | None
    expected_workflow: tuple[str, ...]
    requires_live_network: bool | None
    source: Mapping[str, Any]
    installed_skills: tuple[str, ...] = ()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HostEvalError(f"missing eval file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HostEvalError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HostEvalError(f"expected JSON object in {path}")
    return payload


def load_suite(root: Path, suite: str) -> list[EvalCase]:
    if suite == "trigger":
        path = root / "evals" / "cases.json"
        payload = _load_json(path)
        if payload.get("schema") != "ati.skill-evals.v1":
            raise HostEvalError(f"unexpected trigger eval schema: {payload.get('schema')!r}")
        raw_cases = payload.get("cases")
        if not isinstance(raw_cases, list):
            raise HostEvalError("trigger eval payload is missing cases list")
        cases: list[EvalCase] = []
        for raw in raw_cases:
            if not isinstance(raw, dict):
                raise HostEvalError("trigger eval case must be an object")
            case_id = _required_string(raw, "id", context="trigger case")
            prompt = _required_string(raw, "prompt", context=case_id)
            expected_skill = raw.get("expected_skill")
            if expected_skill is not None and expected_skill not in TOPIC_INTELLIGENCE_SKILLS:
                raise HostEvalError(f"{case_id}: unsupported expected_skill {expected_skill!r}")
            workflow = () if expected_skill is None else (str(expected_skill),)
            cases.append(
                EvalCase(
                    suite=suite,
                    case_id=case_id,
                    prompt=prompt,
                    expected_skill=expected_skill,
                    expected_workflow=workflow,
                    installed_skills=(
                        () if expected_skill is None else (str(expected_skill),)
                    ),
                    requires_live_network=None,
                    source=raw,
                )
            )
        return cases

    if suite in {"quality", "v0.2.1"}:
        path = root / "evals" / ("v0.2.1-skill-quality.json" if suite == "v0.2.1" else "m3-skill-quality.json")
        payload = _load_json(path)
        expected_schema = "ati.v0.2.1-skill-quality.v1" if suite == "v0.2.1" else "ati.m3-skill-quality.v1"
        if payload.get("schema") != expected_schema:
            raise HostEvalError(f"unexpected quality eval schema: {payload.get('schema')!r}")
        raw_cases = payload.get("cases")
        if not isinstance(raw_cases, list):
            raise HostEvalError("quality eval payload is missing cases list")
        cases = []
        for raw in raw_cases:
            if not isinstance(raw, dict):
                raise HostEvalError("quality eval case must be an object")
            case_id = _required_string(raw, "id", context="quality case")
            prompt = _required_string(raw, "prompt", context=case_id)
            workflow_raw = raw.get("expected_workflow", [])
            if not isinstance(workflow_raw, list) or not all(
                isinstance(item, str) and item.strip() for item in workflow_raw
            ):
                raise HostEvalError(f"{case_id}: expected_workflow must be a string list")
            installed_raw = raw.get("installed_skills")
            if (
                not isinstance(installed_raw, list)
                or not installed_raw
                or not all(isinstance(item, str) for item in installed_raw)
                or len(installed_raw) != len(set(installed_raw))
                or any(item not in TOPIC_INTELLIGENCE_SKILLS for item in installed_raw)
            ):
                raise HostEvalError(
                    f"{case_id}: installed_skills must be a non-empty unique list "
                    "of known Topic Intelligence Skills"
                )
            requires_live = raw.get("requires_live_network")
            if requires_live is not None and not isinstance(requires_live, bool):
                raise HostEvalError(f"{case_id}: requires_live_network must be boolean when present")
            cases.append(
                EvalCase(
                    suite=suite,
                    case_id=case_id,
                    prompt=prompt,
                    expected_skill=None,
                    expected_workflow=tuple(workflow_raw),
                    installed_skills=tuple(installed_raw),
                    requires_live_network=requires_live,
                    source=raw,
                )
            )
        return cases

    raise HostEvalError(f"unsupported suite: {suite}")


def _required_string(payload: Mapping[str, Any], key: str, *, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HostEvalError(f"{context}: missing non-empty string {key!r}")
    return value


def select_cases(
    root: Path,
    suites: Sequence[str],
    case_ids: Sequence[str],
) -> list[EvalCase]:
    loaded: list[EvalCase] = []
    for suite in suites:
        loaded.extend(load_suite(root, suite))

    if not case_ids:
        return loaded

    requested = set(case_ids)
    selected = [case for case in loaded if case.case_id in requested]
    found = {case.case_id for case in selected}
    missing = sorted(requested - found)
    if missing:
        raise HostEvalError(f"unknown case id(s): {', '.join(missing)}")
    return selected


def resolve_launcher(explicit: str | None) -> list[str]:
    raw = explicit or os.getenv("ATI_CODEX_LAUNCHER")
    if raw:
        parts = shlex.split(raw)
        if not parts:
            raise HostEvalError("launcher must not be empty")
        return parts

    for candidate in ("codex", "codex_yinhe"):
        path = shutil.which(candidate)
        if path:
            return [path]
    raise HostEvalError(
        "Codex launcher not found; pass --launcher or set ATI_CODEX_LAUNCHER"
    )


def build_codex_command(
    launcher: Sequence[str],
    prompt: str,
    *,
    sandbox: str,
    json_trace: bool,
    live_radar_network: bool = False,
    disabled_skill_paths: Sequence[Path] = (),
    neutral_workspace: bool = False,
) -> list[str]:
    if live_radar_network and sandbox != "workspace-write":
        raise HostEvalError(
            "--live-radar-network requires --sandbox workspace-write"
        )
    command = [*launcher, "exec", "--sandbox", sandbox]
    if neutral_workspace:
        command.append("--skip-git-repo-check")
    if live_radar_network:
        # Network access is deliberately opt-in and scoped to the public Radar
        # origin.  The proxy feature enforces the domain policy for commands
        # executed inside the workspace-write sandbox.
        command.extend(
            [
                "-c",
                "sandbox_workspace_write.network_access=true",
                "-c",
                'network_proxy={enabled=true,allowed_domains=["aiworkstation.cn"]}',
                "-c",
                'approval_policy="never"',
            ]
        )
    if disabled_skill_paths:
        entries = ",".join(
            "{path=" + json.dumps(str(path)) + ",enabled=false}"
            for path in disabled_skill_paths
        )
        command.extend(["-c", f"skills.config=[{entries}]"])
    if json_trace:
        command.append("--json")
    command.append(prompt)
    return command


def _original_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def _potential_duplicate_skill_paths(
    source_root: Path, codex_home: Path, original_home: Path
) -> list[Path]:
    """Find known non-fixture Topic Intelligence Skill locations.

    The case HOME is fresh, so the real user's `~/.agents/skills` is normally
    invisible. The explicit disable list still covers user, evaluated-repository,
    Codex/plugin, and administrator locations so discovery behavior cannot widen
    the declared fixture set.
    """

    roots = (
        source_root / "skills",
        original_home / ".agents" / "skills",
        codex_home / "skills",
        codex_home / "plugins",
        original_home / ".codex" / "plugins",
        Path("/etc/codex/skills"),
        Path("/opt/codex/skills"),
        Path("/usr/local/share/codex/skills"),
    )
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for skill in TOPIC_INTELLIGENCE_SKILLS:
            for candidate in root.glob(f"**/{skill}/SKILL.md"):
                if candidate.is_file():
                    found.append(candidate.resolve())
    return sorted(set(found))


def _skill_file_manifest(skill_root: Path) -> list[dict[str, Any]]:
    """Describe portable fixture files without persisting their absolute root."""

    rows: list[dict[str, Any]] = []
    for path in sorted(item for item in skill_root.rglob("*") if item.is_file()):
        relative = path.relative_to(skill_root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        payload = path.read_bytes()
        rows.append(
            {
                "path": relative.as_posix(),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return rows


def _directory_is_empty(path: Path) -> bool:
    return path.is_dir() and next(path.iterdir(), None) is None


def prepare_case_skill_environment(
    case: EvalCase,
    *,
    source_root: Path,
    source_commit: str,
    home: Path,
    codex_home: Path,
    original_home: Path,
) -> tuple[
    dict[str, str],
    list[Path],
    dict[str, str],
    dict[str, list[dict[str, Any]]],
]:
    """Create the exact declared Skill fixture without copying Codex auth."""

    skills_root = home / ".agents" / "skills"
    skills_root.mkdir(parents=True, exist_ok=False)
    for skill in case.installed_skills:
        source = source_root / "skills" / skill
        if not (source / "SKILL.md").is_file():
            raise HostEvalError(
                f"{case.case_id}: missing Skill at evaluated commit: {skill}"
            )
        destination = skills_root / skill
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    visible = sorted(
        path.parent.name for path in skills_root.glob("*/SKILL.md")
    )
    if visible != sorted(case.installed_skills):
        raise HostEvalError(
            f"{case.case_id}: isolated Skill fixture differs from installed_skills"
        )

    environment = os.environ.copy()
    environment["HOME"] = str(home)
    environment["CODEX_HOME"] = str(codex_home)
    environment["ATI_HOST_EVAL_SKILL_SOURCE_COMMIT"] = source_commit
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    fixture_roots = {
        skill: str((skills_root / skill).resolve()) for skill in case.installed_skills
    }
    fixture_manifest = {
        skill: _skill_file_manifest(skills_root / skill)
        for skill in case.installed_skills
    }
    for skill in case.installed_skills:
        source_manifest = _skill_file_manifest(source_root / "skills" / skill)
        if fixture_manifest[skill] != source_manifest:
            raise HostEvalError(
                f"{case.case_id}: fixture manifest differs from evaluated Skill: {skill}"
            )
    disabled = _potential_duplicate_skill_paths(
        source_root, codex_home, original_home
    )
    fixture_paths = [Path(path) for path in fixture_roots.values()]
    if any(
        disabled_path == fixture_root / "SKILL.md"
        or fixture_root in disabled_path.parents
        for disabled_path in disabled
        for fixture_root in fixture_paths
    ):
        raise HostEvalError(f"{case.case_id}: fixture was included in disabled Skills")
    return environment, disabled, fixture_roots, fixture_manifest


def _git_output(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode != 0:
        raise HostEvalError(f"git {' '.join(args)} failed in {cwd}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def validate_live_worktree(root: Path, cwd: Path, commit: str | None) -> dict[str, Any]:
    """Require an isolated, clean detached worktree for live Host runs."""

    root = root.resolve()
    cwd = cwd.resolve()
    if cwd == root:
        raise HostEvalError("live Host Eval must use a temporary detached worktree, not the repository root")
    if _git_output(cwd, "rev-parse", "--is-inside-work-tree") != "true":
        raise HostEvalError(f"live Host Eval cwd is not a Git worktree: {cwd}")
    top = Path(_git_output(cwd, "rev-parse", "--show-toplevel")).resolve()
    if top != cwd:
        raise HostEvalError(f"live Host Eval cwd must be the worktree root: {cwd}")
    symbolic = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    if symbolic.returncode == 0 and symbolic.stdout.strip():
        raise HostEvalError("live Host Eval worktree must be detached")
    if symbolic.returncode not in {0, 1}:
        raise HostEvalError("could not determine whether live Host Eval worktree is detached")
    actual = _git_output(cwd, "rev-parse", "HEAD")
    if commit and actual != commit:
        raise HostEvalError(f"live Host Eval worktree commit {actual} does not match {commit}")
    status = _git_output(cwd, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise HostEvalError("live Host Eval worktree must be clean before execution")
    return {
        "path": str(cwd),
        "temporary": True,
        "detached": True,
        "clean_before": True,
        "commit": actual,
    }


def _clean_worktree_status(cwd: Path) -> list[str]:
    try:
        output = _git_output(cwd, "status", "--porcelain", "--untracked-files=all")
    except HostEvalError:
        return ["<git status unavailable>"]
    return [line for line in output.splitlines() if line.strip()]


def _collect_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _collect_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _collect_strings(item)


def trace_text(stdout: str, stderr: str) -> str:
    """Return searchable text from raw stdout/stderr, including JSONL values."""

    collected: list[str] = [stdout, stderr]
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        collected.extend(_collect_strings(payload))
    return "\n".join(collected)


def _is_stream_disconnect_event(event: Mapping[str, Any]) -> bool:
    """Recognize Codex response-stream interruptions, not helper/network errors."""

    if event.get("type") != "error":
        return False

    # Codex versions have emitted both a structured ``codexErrorInfo.code``
    # and a human-readable reconnect message. Prefer the structured code when
    # present, while retaining the known message forms for older launchers.
    def codes(value: Any) -> Iterable[str]:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                normalized_key = str(key).lower().replace("-", "_")
                if normalized_key in {"code", "error_code", "codex_error_code"}:
                    if isinstance(nested, str):
                        yield nested
                yield from codes(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from codes(nested)

    for code in codes(event):
        normalized = "".join(char for char in code.lower() if char.isalnum())
        if normalized in STREAM_DISCONNECT_CODES:
            return True

    text = "\n".join(_collect_strings(event)).lower().replace("-", "_")
    return any(marker in text for marker in STREAM_DISCONNECT_MARKERS)


def analyze_jsonl_trace(
    stdout: str,
    *,
    exit_code: int | None,
    runtime_status: str,
    timed_out: bool,
    stdout_truncated: bool,
    stderr_truncated: bool,
    worktree_clean_after: bool,
) -> dict[str, Any]:
    """Classify one Codex JSONL lifecycle from observable process evidence."""

    events: list[Mapping[str, Any]] = []
    invalid_jsonl_line_count = 0
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            invalid_jsonl_line_count += 1
            continue
        if not isinstance(value, Mapping):
            invalid_jsonl_line_count += 1
            continue
        events.append(value)

    turn_started_positions: list[int] = []
    turn_completed_positions: list[int] = []
    turn_failed_count = 0
    error_event_count = 0
    stream_disconnect_event_count = 0
    non_stream_error_event_count = 0
    started_items: dict[str, tuple[int, str]] = {}
    completed_item_ids: set[str] = set()
    tool_activity_positions: list[int] = []
    final_agent_message_position: int | None = None

    for position, event in enumerate(events):
        event_type = str(event.get("type") or "")
        item_value = event.get("item")
        item = item_value if isinstance(item_value, Mapping) else {}
        item_type = str(item.get("type") or "")
        item_id_value = item.get("id")
        item_id = str(item_id_value) if item_id_value not in {None, ""} else ""

        if event_type == "turn.started":
            turn_started_positions.append(position)
        elif event_type == "turn.completed":
            turn_completed_positions.append(position)
        elif event_type == "turn.failed":
            turn_failed_count += 1
        elif event_type == "error":
            error_event_count += 1
            if _is_stream_disconnect_event(event):
                stream_disconnect_event_count += 1
            else:
                non_stream_error_event_count += 1

        if event_type == "item.started":
            key = item_id or f"<missing-id@{position}>"
            started_items[key] = (position, item_type)
        elif event_type == "item.completed" and item_id:
            completed_item_ids.add(item_id)

        if item_type in TOOL_ITEM_TYPES and event_type in {"item.started", "item.completed"}:
            tool_activity_positions.append(position)
        if event_type == "item.completed" and item_type == "agent_message":
            final_agent_message_position = position

    incomplete_item_ids = sorted(
        item_id for item_id in started_items if item_id not in completed_item_ids
    )
    tool_activity_after_final_agent_message = bool(
        final_agent_message_position is not None
        and any(position > final_agent_message_position for position in tool_activity_positions)
    )
    last_event_type = str(events[-1].get("type") or "") if events else None
    lifecycle_complete = bool(
        exit_code == 0
        and runtime_status == "completed"
        and not timed_out
        and not stdout_truncated
        and not stderr_truncated
        and invalid_jsonl_line_count == 0
        and len(turn_started_positions) == 1
        and len(turn_completed_positions) == 1
        and turn_failed_count == 0
        and non_stream_error_event_count == 0
        and not incomplete_item_ids
        and final_agent_message_position is not None
        and not tool_activity_after_final_agent_message
        and turn_completed_positions[0] > final_agent_message_position
        and last_event_type == "turn.completed"
        and worktree_clean_after
    )
    stream_disconnect_observed = stream_disconnect_event_count > 0
    stream_recovered = lifecycle_complete and stream_disconnect_observed
    stream_terminal_failure = stream_disconnect_observed and not stream_recovered
    if lifecycle_complete:
        trace_integrity_status = (
            "complete_after_recovery"
            if stream_disconnect_observed
            else "complete_clean"
        )
    else:
        trace_integrity_status = "incomplete_or_failed"

    return {
        "jsonl_event_count": len(events),
        "invalid_jsonl_line_count": invalid_jsonl_line_count,
        "turn_started_count": len(turn_started_positions),
        "turn_completed_count": len(turn_completed_positions),
        "turn_failed_count": turn_failed_count,
        "error_event_count": error_event_count,
        "stream_disconnect_event_count": stream_disconnect_event_count,
        "non_stream_error_event_count": non_stream_error_event_count,
        "final_agent_message_observed": final_agent_message_position is not None,
        "tool_activity_after_final_agent_message": tool_activity_after_final_agent_message,
        "incomplete_item_ids": incomplete_item_ids,
        "last_event_type": last_event_type,
        "trace_integrity_status": trace_integrity_status,
        "stream_disconnect_observed": stream_disconnect_observed,
        "stream_recovered": stream_recovered,
        "stream_terminal_failure": stream_terminal_failure,
        # Preserve the old diagnostic field as an observation, not a gate.
        "stream_disconnected": stream_disconnect_observed,
    }


def observe_tokens(text: str, expected_workflow: Sequence[str]) -> dict[str, Any]:
    observed_skills = [
        skill for skill in TOPIC_INTELLIGENCE_SKILLS if skill in text
    ]
    tokens = list(dict.fromkeys([*expected_workflow, HANDOFF_SCHEMA]))
    observed_tokens = [token for token in tokens if token and token in text]
    return {
        "skills": observed_skills,
        "workflow_tokens": observed_tokens,
        "handoff_schema_observed": HANDOFF_SCHEMA in text,
    }


def classify_observation(case: EvalCase, observation: Mapping[str, Any]) -> str:
    observed_skills = set(observation.get("skills") or [])
    observed_tokens = set(observation.get("workflow_tokens") or [])

    if case.suite == "trigger":
        if case.expected_skill is None:
            return "fail_unexpected_skill" if observed_skills else "pass_no_skill_observed"
        if case.expected_skill in observed_skills:
            return "pass_expected_skill_observed"
        if observed_skills:
            return "fail_wrong_skill_observed"
        return "unobservable"

    expected = set(case.expected_workflow)
    if not expected:
        return "unobservable"
    matched = expected & observed_tokens
    if expected <= observed_tokens:
        return "pass_expected_workflow_observed"
    if matched:
        return "partial_workflow_observed"
    return "unobservable"


def _result_is_gate_failure(result: Mapping[str, Any], *, strict_observation: bool = False) -> bool:
    del strict_observation  # authoritative grading owns workflow pass/fail
    return bool(
        str(result.get("runtime_status")) != "completed"
        or result.get("trace_integrity_status")
        not in PASSING_TRACE_INTEGRITY_STATUSES
        or result.get("worktree_clean_after") is not True
        or result.get("execution_workspace_clean_after") is not True
        or result.get("source_worktree_used_as_host_cwd") is not False
        or result.get("authoritative_evidence_grade") not in PASS_GRADES
    )


def _truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def run_case(
    case: EvalCase,
    *,
    command: Sequence[str],
    cwd: Path,
    timeout_seconds: float,
    max_output_chars: int,
    dry_run: bool,
    strict_observation: bool = False,
    worktree: Mapping[str, Any] | None = None,
    environment: Mapping[str, str] | None = None,
    skill_environment_isolated: bool = False,
    skill_source_commit: str | None = None,
    codex_home_preserved: bool = False,
    skill_fixture_roots: Mapping[str, str] | None = None,
    skill_fixture_manifest: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    disabled_skill_paths: Sequence[Path] = (),
    source_worktree: Path | None = None,
    execution_workspace_isolated: bool = False,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    source_worktree_resolved = (
        source_worktree.resolve() if source_worktree is not None else cwd.resolve()
    )
    host_cwd = cwd.resolve()
    source_used_as_host_cwd = host_cwd == source_worktree_resolved
    workspace_clean_before = _directory_is_empty(host_cwd)
    workspace_neutral = bool(
        execution_workspace_isolated
        and workspace_clean_before
        and not source_used_as_host_cwd
        and not any(
            (host_cwd / name).exists()
            for name in ("scripts", "skills", "AGENTS.md", ".agents", ".codex", ".git")
        )
    )
    if dry_run:
        return {
            "id": case.case_id,
            "suite": case.suite,
            "prompt": case.prompt,
            "expected_skill": case.expected_skill,
            "expected_workflow": list(case.expected_workflow),
            "installed_skills": list(case.installed_skills),
            "requires_live_network": case.requires_live_network,
            "command": list(command),
            "runtime_status": "dry_run",
            "route_observation": "not_run",
            "exit_code": None,
            "timed_out": False,
            "duration_seconds": 0.0,
            "started_at": started_at,
            "observation": {
                "skills": [],
                "workflow_tokens": [],
                "handoff_schema_observed": False,
            },
            "stdout": "",
            "stderr": "",
            "stdout_truncated": False,
            "stderr_truncated": False,
            "worktree_clean_after": None,
            "trace_integrity_status": "not_run",
            "skill_environment_isolated": False,
            "skill_source_commit": skill_source_commit,
            "codex_home_preserved": codex_home_preserved,
            "authentication_material_copied": False,
            "authentication_content_recorded": False,
            "skill_fixture_roots": dict(skill_fixture_roots or {}),
            "skill_fixture_manifest": {
                key: list(value)
                for key, value in (skill_fixture_manifest or {}).items()
            },
            "disabled_skill_paths": [str(path) for path in disabled_skill_paths],
            "execution_workspace_isolated": False,
            "execution_workspace_root": str(host_cwd),
            "execution_workspace_neutral": False,
            "execution_workspace_clean_before": workspace_clean_before,
            "execution_workspace_clean_after": None,
            "source_worktree_used_as_host_cwd": source_used_as_host_cwd,
        }

    start = time.monotonic()
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    timed_out = False
    runtime_status = "completed"
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
            env=dict(environment) if environment is not None else None,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        exit_code = completed.returncode
        if completed.returncode != 0:
            runtime_status = "nonzero_exit"
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        runtime_status = "timeout"
        stdout = _coerce_subprocess_text(exc.stdout)
        stderr = _coerce_subprocess_text(exc.stderr)
    except OSError as exc:
        runtime_status = "launcher_error"
        stderr = str(exc)

    duration = round(time.monotonic() - start, 3)
    searchable = trace_text(stdout, stderr)
    observation = observe_tokens(searchable, case.expected_workflow)
    route_observation = classify_observation(case, observation)
    if strict_observation and route_observation == "unobservable":
        route_observation = "fail_unobservable"
    stdout, stdout_truncated = _truncate(stdout, max_output_chars)
    stderr, stderr_truncated = _truncate(stderr, max_output_chars)
    source_worktree_clean_after = not _clean_worktree_status(source_worktree_resolved)
    if execution_workspace_isolated:
        execution_workspace_clean_after = _directory_is_empty(host_cwd)
        skill_fixture_clean_after = bool(
            skill_fixture_roots
            and skill_fixture_manifest
            and all(
                Path(root).is_dir()
                and _skill_file_manifest(Path(root))
                == list(skill_fixture_manifest.get(skill) or [])
                for skill, root in skill_fixture_roots.items()
            )
        )
        clean_after = bool(
            execution_workspace_clean_after
            and source_worktree_clean_after
            and skill_fixture_clean_after
        )
    else:
        execution_workspace_clean_after = source_worktree_clean_after
        skill_fixture_clean_after = True
        clean_after = source_worktree_clean_after
    trace_integrity = analyze_jsonl_trace(
        stdout,
        exit_code=exit_code,
        runtime_status=runtime_status,
        timed_out=timed_out,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        worktree_clean_after=clean_after,
    )

    return {
        "id": case.case_id,
        "suite": case.suite,
        "prompt": case.prompt,
        "expected_skill": case.expected_skill,
        "expected_workflow": list(case.expected_workflow),
        "installed_skills": list(case.installed_skills),
        "requires_live_network": case.requires_live_network,
        "command": list(command),
        "runtime_status": runtime_status,
        "route_observation": route_observation,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_seconds": duration,
        "started_at": started_at,
        "observation": observation,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
        "worktree_clean_after": clean_after,
        "skill_environment_isolated": skill_environment_isolated,
        "skill_source_commit": skill_source_commit,
        "codex_home_preserved": codex_home_preserved,
        "authentication_material_copied": False,
        "authentication_content_recorded": False,
        "skill_fixture_roots": dict(skill_fixture_roots or {}),
        "skill_fixture_manifest": {
            key: list(value)
            for key, value in (skill_fixture_manifest or {}).items()
        },
        "disabled_skill_paths": [str(path) for path in disabled_skill_paths],
        "execution_workspace_isolated": execution_workspace_isolated,
        "execution_workspace_root": str(host_cwd),
        "execution_workspace_neutral": workspace_neutral,
        "execution_workspace_clean_before": workspace_clean_before,
        "execution_workspace_clean_after": execution_workspace_clean_after,
        "source_worktree_used_as_host_cwd": source_used_as_host_cwd,
        "source_worktree_clean_after": source_worktree_clean_after,
        "skill_fixture_clean_after": skill_fixture_clean_after,
        **trace_integrity,
    }


def _coerce_subprocess_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def summarize(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    route_counts: dict[str, int] = {}
    runtime_counts: dict[str, int] = {}
    grade_counts: dict[str, int] = {}
    for result in results:
        route = str(result.get("route_observation"))
        runtime = str(result.get("runtime_status"))
        grade = str(result.get("authoritative_evidence_grade"))
        route_counts[route] = route_counts.get(route, 0) + 1
        runtime_counts[runtime] = runtime_counts.get(runtime, 0) + 1
        if grade != "None":
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
    return {
        "total": len(results),
        "route_observations": dict(sorted(route_counts.items())),
        "runtime_statuses": dict(sorted(runtime_counts.items())),
        "authoritative_evidence_grades": dict(sorted(grade_counts.items())),
    }


def build_report(
    *,
    root: Path,
    host: str,
    suites: Sequence[str],
    sandbox: str,
    timeout_seconds: float,
    launcher: Sequence[str],
    results: Sequence[Mapping[str, Any]],
    dry_run: bool,
    strict_observation: bool = False,
    commit: str | None = None,
    live_radar_network: bool = False,
    network_allowed_domains: Sequence[str] | None = None,
    worktree: Mapping[str, Any] | None = None,
    launcher_config: Sequence[str] | None = None,
) -> dict[str, Any]:
    version_path = root / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else None
    return {
        "schema": REPORT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": host,
        "skill_version": version,
        "commit": commit or _repository_commit(root),
        "suites": list(suites),
        "sandbox": sandbox,
        "timeout_seconds": timeout_seconds,
        "launcher": list(launcher),
        "launcher_config": list(launcher_config or []),
        "dry_run": dry_run,
        "strict_observation": strict_observation,
        "live_radar_network": live_radar_network,
        "network_allowed_domains": list(network_allowed_domains or []),
        "worktree": dict(worktree or {}),
        "summary": summarize(results),
        "cases": list(results),
        "grading_note": (
            "route_observation is collector diagnostics only; authoritative_evidence_grade "
            "is regenerated by grade_report and is the workflow gate, while semantic "
            "must_show/must_not grading remains a separate review step"
        ),
    }


def attach_authoritative_grades(report: dict[str, Any]) -> None:
    """Grade the complete raw report and bind each runner result to that grade."""

    if report.get("dry_run") is True:
        for result in report.get("cases") or []:
            if isinstance(result, dict):
                result["authoritative_evidence_grade"] = "not_run"
        report["summary"] = summarize(report.get("cases") or [])
        return
    graded = grade_report(report)
    graded_cases = graded.get("cases") or []
    raw_cases = report.get("cases") or []
    if len(graded_cases) != len(raw_cases):
        raise HostEvalError("authoritative grader returned a different case count")
    for raw_case, graded_case in zip(raw_cases, graded_cases):
        if not isinstance(raw_case, dict) or not isinstance(graded_case, Mapping):
            raise HostEvalError("authoritative grader returned an invalid case record")
        raw_case["authoritative_evidence_grade"] = graded_case.get("evidence_grade")
    report["summary"] = summarize(raw_cases)


def _repository_commit(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Topic Intelligence evals in fresh host processes"
    )
    parser.add_argument("--host", choices=SUPPORTED_HOSTS, default="codex")
    parser.add_argument(
        "--suite",
        choices=SUPPORTED_SUITES,
        action="append",
        dest="suites",
        help="Eval suite to run; repeat to run more than one",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        dest="case_ids",
        help="Run only this case id; repeat for multiple cases",
    )
    parser.add_argument(
        "--launcher",
        help="Codex launcher command, e.g. 'codex' or 'codex_yinhe'",
    )
    parser.add_argument("--sandbox", default="read-only")
    parser.add_argument(
        "--live-radar-network",
        action="store_true",
        help="Explicitly enable restricted live Radar networking (workspace-write only)",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--max-output-chars", type=int, default=DEFAULT_MAX_OUTPUT_CHARS
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the complete ati.host-eval.v1 JSON report to this path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate case selection and commands without invoking the host",
    )
    parser.add_argument(
        "--strict-observation",
        action="store_true",
        help="Treat an unobservable live host trace as a gate failure",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        help="Working directory for fresh host processes; defaults to repository root",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = repository_root()
    suites = args.suites or ["trigger"]
    if args.timeout <= 0:
        print("error: --timeout must be positive", file=sys.stderr)
        return 2
    if args.max_output_chars <= 0:
        print("error: --max-output-chars must be positive", file=sys.stderr)
        return 2

    try:
        cases = select_cases(root, suites, args.case_ids)
        launcher = resolve_launcher(args.launcher) if not args.dry_run else shlex.split(
            args.launcher or os.getenv("ATI_CODEX_LAUNCHER") or "codex"
        )
        if not launcher:
            raise HostEvalError("launcher must not be empty")
        source_worktree = (args.cwd or root).expanduser().resolve()
        if args.live_radar_network and args.dry_run:
            raise HostEvalError("--live-radar-network cannot be combined with --dry-run")
        if args.live_radar_network and args.sandbox != "workspace-write":
            raise HostEvalError("--live-radar-network requires --sandbox workspace-write")
        if args.live_radar_network and args.cwd:
            raise HostEvalError("--live-radar-network always creates its own temporary detached worktree; do not pass --cwd")
        if not source_worktree.is_dir():
            raise HostEvalError(f"working directory does not exist: {source_worktree}")
        if args.live_radar_network:
            overridden = [name for name in ORIGIN_OVERRIDE_ENV_VARS if os.getenv(name)]
            if overridden:
                raise HostEvalError(
                    "live Host Eval refuses custom Radar origin environment: "
                    + ", ".join(overridden)
                )

        # Bind the report to the repository revision that was inspected before
        # any host process starts.  This prevents a concurrent code change from
        # silently changing the meaning of an otherwise valid-looking trace.
        commit = _repository_commit(root)
        original_home = Path.home().resolve()
        codex_home = _original_codex_home()
        if not codex_home.is_dir() and not args.dry_run:
            raise HostEvalError(f"CODEX_HOME does not exist: {codex_home}")
        if args.live_radar_network and not commit:
            raise HostEvalError("live Host Eval requires a resolvable repository commit")
        if args.live_radar_network and _git_output(root, "status", "--porcelain", "--untracked-files=all"):
            raise HostEvalError("live Host Eval requires a clean repository before creating its temporary worktree")

        worktree: dict[str, Any] = {}
        temporary_worktree: tempfile.TemporaryDirectory[str] | None = None
        if args.live_radar_network:
            temporary_worktree = tempfile.TemporaryDirectory(prefix="ati-host-eval-")
            temp_path = Path(temporary_worktree.name) / "worktree"
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(temp_path), str(commit)],
                cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
            )
            source_worktree = temp_path.resolve()
            worktree = validate_live_worktree(root, source_worktree, commit)

        results: list[dict[str, Any]] = []
        try:
            for case in cases:
                environment: Mapping[str, str] | None = None
                disabled_skill_paths: list[Path] = []
                case_home: tempfile.TemporaryDirectory[str] | None = None
                case_workspace: tempfile.TemporaryDirectory[str] | None = None
                fixture_roots: dict[str, str] = {}
                fixture_manifest: dict[str, list[dict[str, Any]]] = {}
                try:
                    if not args.dry_run:
                        case_home = tempfile.TemporaryDirectory(
                            prefix="ati-host-eval-home-"
                        )
                        (
                            environment,
                            disabled_skill_paths,
                            fixture_roots,
                            fixture_manifest,
                        ) = prepare_case_skill_environment(
                            case,
                            source_root=source_worktree,
                            source_commit=str(commit),
                            home=Path(case_home.name),
                            codex_home=codex_home,
                            original_home=original_home,
                        )
                        case_workspace = tempfile.TemporaryDirectory(
                            prefix="ati-host-eval-workspace-"
                        )
                        if not _directory_is_empty(Path(case_workspace.name)):
                            raise HostEvalError(
                                f"{case.case_id}: neutral execution workspace is not empty"
                            )
                    command = build_codex_command(
                        launcher,
                        case.prompt,
                        sandbox=args.sandbox,
                        json_trace=True,
                        live_radar_network=args.live_radar_network,
                        disabled_skill_paths=disabled_skill_paths,
                        neutral_workspace=not args.dry_run,
                    )
                    result = run_case(
                        case,
                        command=command,
                        cwd=(
                            source_worktree
                            if args.dry_run
                            else Path(str(case_workspace.name))
                        ),
                        timeout_seconds=float(args.timeout),
                        max_output_chars=args.max_output_chars,
                        dry_run=args.dry_run,
                        strict_observation=args.strict_observation,
                        worktree=worktree,
                        environment=environment,
                        skill_environment_isolated=not args.dry_run,
                        skill_source_commit=str(commit) if commit else None,
                        codex_home_preserved=not args.dry_run,
                        skill_fixture_roots=fixture_roots,
                        skill_fixture_manifest=fixture_manifest,
                        disabled_skill_paths=disabled_skill_paths,
                        source_worktree=source_worktree,
                        execution_workspace_isolated=not args.dry_run,
                    )
                finally:
                    if case_workspace is not None:
                        case_workspace.cleanup()
                    if case_home is not None:
                        case_home.cleanup()
                results.append(result)
                if args.live_radar_network and result.get("worktree_clean_after") is not True:
                    raise HostEvalError(
                        f"Host modified the temporary worktree during case {case.case_id}; evidence rejected"
                    )
            if args.live_radar_network:
                status_after = _clean_worktree_status(source_worktree)
                worktree["clean_after"] = not status_after
                worktree["status_after"] = status_after
        finally:
            if temporary_worktree is not None:
                status_after = _clean_worktree_status(source_worktree)
                worktree["clean_after"] = not status_after
                worktree["status_after"] = status_after
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(source_worktree)],
                    cwd=root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True,
                )
                temporary_worktree.cleanup()

        report = build_report(
            root=root,
            host=args.host,
            suites=suites,
            sandbox=args.sandbox,
            timeout_seconds=float(args.timeout),
            launcher=launcher,
            results=results,
            dry_run=args.dry_run,
            strict_observation=args.strict_observation,
            commit=commit,
            live_radar_network=args.live_radar_network,
            network_allowed_domains=(LIVE_RADAR_NETWORK_DOMAINS if args.live_radar_network else []),
            worktree=worktree,
            launcher_config=(
                [
                    "sandbox_workspace_write.network_access=true",
                    'network_proxy={enabled=true,allowed_domains=["aiworkstation.cn"]}',
                    'approval_policy="never"',
                ]
                if args.live_radar_network else []
            ),
        )
        attach_authoritative_grades(report)
    except HostEvalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        destination = args.output.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        print(
            json.dumps(
                {
                    "schema": REPORT_SCHEMA,
                    "output": str(destination),
                    "summary": report["summary"],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(rendered, end="")
    return 0 if args.dry_run else (
        1
        if any(
            _result_is_gate_failure(
                result, strict_observation=args.strict_observation
            )
            for result in results
        )
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run Topic Intelligence eval cases in fresh host processes.

The runner is intentionally host-observability tooling, not a semantic judge and
not a Skill installer.  It records what a fresh host process did, preserves the
raw trace, and classifies only behavior that is directly observable.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


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
) -> list[str]:
    command = [*launcher, "exec", "--sandbox", sandbox]
    if json_trace:
        command.append("--json")
    command.append(prompt)
    return command


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


def _result_is_gate_failure(result: Mapping[str, Any]) -> bool:
    return str(result.get("runtime_status")) != "completed" or str(result.get("route_observation")) in {
        "fail_unexpected_skill", "fail_wrong_skill_observed", "partial_workflow_observed"
    }


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
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    if dry_run:
        return {
            "id": case.case_id,
            "suite": case.suite,
            "prompt": case.prompt,
            "expected_skill": case.expected_skill,
            "expected_workflow": list(case.expected_workflow),
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
    stdout, stdout_truncated = _truncate(stdout, max_output_chars)
    stderr, stderr_truncated = _truncate(stderr, max_output_chars)

    return {
        "id": case.case_id,
        "suite": case.suite,
        "prompt": case.prompt,
        "expected_skill": case.expected_skill,
        "expected_workflow": list(case.expected_workflow),
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
    for result in results:
        route = str(result.get("route_observation"))
        runtime = str(result.get("runtime_status"))
        route_counts[route] = route_counts.get(route, 0) + 1
        runtime_counts[runtime] = runtime_counts.get(runtime, 0) + 1
    return {
        "total": len(results),
        "route_observations": dict(sorted(route_counts.items())),
        "runtime_statuses": dict(sorted(runtime_counts.items())),
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
) -> dict[str, Any]:
    version_path = root / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else None
    return {
        "schema": REPORT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": host,
        "skill_version": version,
        "suites": list(suites),
        "sandbox": sandbox,
        "timeout_seconds": timeout_seconds,
        "launcher": list(launcher),
        "dry_run": dry_run,
        "summary": summarize(results),
        "cases": list(results),
        "grading_note": (
            "route_observation is based only on tokens visible in the host trace; "
            "semantic must_show/must_not grading remains a separate review step"
        ),
    }


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
        cwd = (args.cwd or root).expanduser().resolve()
        if not cwd.is_dir():
            raise HostEvalError(f"working directory does not exist: {cwd}")

        results: list[dict[str, Any]] = []
        for case in cases:
            command = build_codex_command(
                launcher,
                case.prompt,
                sandbox=args.sandbox,
                json_trace=True,
            )
            results.append(
                run_case(
                    case,
                    command=command,
                    cwd=cwd,
                    timeout_seconds=float(args.timeout),
                    max_output_chars=args.max_output_chars,
                    dry_run=args.dry_run,
                )
            )

        report = build_report(
            root=root,
            host=args.host,
            suites=suites,
            sandbox=args.sandbox,
            timeout_seconds=float(args.timeout),
            launcher=launcher,
            results=results,
            dry_run=args.dry_run,
        )
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
    return 0 if args.dry_run else (1 if any(_result_is_gate_failure(result) for result in results) else 0)


if __name__ == "__main__":
    raise SystemExit(main())

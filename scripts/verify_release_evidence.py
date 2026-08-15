#!/usr/bin/env python3
"""Verify the persistent live Host Eval evidence required for new releases."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

# Support both `python -m scripts.verify_release_evidence` and the direct
# workflow/CLI form `python scripts/verify_release_evidence.py`.  In the latter
# form Python puts `scripts/` (rather than the repository root) on sys.path.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.grade_host_eval import EvidenceGradeError, PASS_GRADES, grade_report
from scripts.run_host_evals import analyze_jsonl_trace, load_suite


LIVE_RADAR_NETWORK_DOMAINS = ["aiworkstation.cn"]
LIVE_RADAR_LAUNCHER_CONFIG = [
    "sandbox_workspace_write.network_access=true",
    'network_proxy={enabled=true,allowed_domains=["aiworkstation.cn"]}',
    'approval_policy="never"',
]
PASSING_TRACE_INTEGRITY_STATUSES = {
    "complete_clean",
    "complete_after_recovery",
}
TRACE_FIELDS = (
    "jsonl_event_count",
    "invalid_jsonl_line_count",
    "turn_started_count",
    "turn_completed_count",
    "turn_failed_count",
    "error_event_count",
    "stream_disconnect_event_count",
    "non_stream_error_event_count",
    "final_agent_message_observed",
    "tool_activity_after_final_agent_message",
    "incomplete_item_ids",
    "last_event_type",
    "trace_integrity_status",
    "stream_disconnect_observed",
    "stream_recovered",
    "stream_terminal_failure",
    "stream_disconnected",
)


class ReleaseEvidenceError(RuntimeError):
    pass


REQUIRED_FILES = ("host-eval.json", "host-evidence.json", "manual-review.json")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _object(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseEvidenceError(f"invalid evidence JSON: {path}") from exc
    if not isinstance(value, Mapping):
        raise ReleaseEvidenceError(f"evidence must be a JSON object: {path}")
    return value


def _case_id(value: Any) -> str:
    return str(value.get("id")) if isinstance(value, Mapping) else "<non-object>"


def _command_strings(value: Any) -> list[str]:
    """Extract executed command fields without scanning documentation output."""

    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "command":
                if isinstance(item, str):
                    found.append(item)
                elif isinstance(item, list):
                    found.extend(str(part) for part in item)
            else:
                found.extend(_command_strings(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_command_strings(item))
    return found


def _contains_forbidden_origin(raw: Mapping[str, Any]) -> bool:
    commands = _command_strings(raw)
    return any(
        "--base-url" in command.lower()
        or "aiworkstation_topic_radar_base_url" in command.lower()
        for command in commands
    )


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode != 0:
        raise ReleaseEvidenceError(f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def _manifest_at_commit(
    root: Path, commit: str, skill: str
) -> list[dict[str, Any]]:
    prefix = f"skills/{skill}/"
    files = [
        path
        for path in _git(root, "ls-tree", "-r", "--name-only", commit, prefix).splitlines()
        if path.startswith(prefix)
    ]
    if not files:
        raise ReleaseEvidenceError(
            f"evaluated commit is missing Skill fixture source: {skill}"
        )
    rows: list[dict[str, Any]] = []
    for path in files:
        completed = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise ReleaseEvidenceError(f"could not read evaluated Skill file: {path}")
        payload = completed.stdout
        rows.append(
            {
                "path": path[len(prefix):],
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return rows


def _verify_commit_binding(root: Path, evidence_dir: Path, evaluated_commit: str) -> None:
    if not COMMIT_RE.fullmatch(evaluated_commit):
        raise ReleaseEvidenceError("raw Host Eval commit is not a full Git SHA")
    current_commit = _git(root, "rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", evaluated_commit, current_commit],
        cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode != 0:
        raise ReleaseEvidenceError("evaluated commit is not an ancestor of the release commit")
    allowed_prefix = evidence_dir.relative_to(root).as_posix().rstrip("/") + "/"
    changed = [line for line in _git(root, "diff", "--name-only", f"{evaluated_commit}..{current_commit}").splitlines() if line]
    disallowed = [path for path in changed if not path.startswith(allowed_prefix)]
    if disallowed:
        raise ReleaseEvidenceError(
            "release code changed after Host Eval: " + ", ".join(disallowed)
        )
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise ReleaseEvidenceError(
            "release worktree must be clean when verifying Host Eval evidence"
        )


def verify(root: Path, version: str) -> Path:
    suite_by_version = {
        "0.2.2": "v0.2.1",
        "0.3.0": "v0.3.0",
        "0.3.1": "v0.3.1",
    }
    try:
        evidence_suite = suite_by_version[version]
    except KeyError as exc:
        raise ReleaseEvidenceError(
            f"no release-evidence suite is defined for v{version}"
        ) from exc
    evidence_dir = root / "release-evidence" / f"v{version}"
    missing = [name for name in REQUIRED_FILES if not (evidence_dir / name).is_file()]
    if missing:
        raise ReleaseEvidenceError(
            f"missing persistent live Host Eval evidence for v{version}: {', '.join(missing)}"
        )

    raw = _object(evidence_dir / "host-eval.json")
    graded = _object(evidence_dir / "host-evidence.json")
    if raw.get("schema") != "ati.host-eval.v1":
        raise ReleaseEvidenceError("host-eval.json must use ati.host-eval.v1")
    if graded.get("schema") != "ati.host-evidence.v1":
        raise ReleaseEvidenceError("host-evidence.json must use ati.host-evidence.v1")
    try:
        expected_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ReleaseEvidenceError("VERSION is missing or unreadable") from exc
    if version != expected_version or raw.get("skill_version") != expected_version or graded.get("skill_version") != expected_version:
        raise ReleaseEvidenceError("evidence version does not match VERSION")
    if raw.get("dry_run") is not False or raw.get("strict_observation") is not True:
        raise ReleaseEvidenceError("raw Host Eval must be a live strict-observation run")
    if raw.get("sandbox") != "workspace-write":
        raise ReleaseEvidenceError("live Host Eval evidence must use workspace-write sandbox")
    if raw.get("live_radar_network") is not True:
        raise ReleaseEvidenceError("live Host Eval evidence must explicitly enable live Radar networking")
    if raw.get("network_allowed_domains") != LIVE_RADAR_NETWORK_DOMAINS:
        raise ReleaseEvidenceError(
            "live Host Eval network allowlist must be exactly ['aiworkstation.cn']"
        )
    if raw.get("launcher_config") != LIVE_RADAR_LAUNCHER_CONFIG:
        raise ReleaseEvidenceError("live Host Eval launcher config is not the approved restricted policy")
    if _contains_forbidden_origin(raw):
        raise ReleaseEvidenceError("live Host Eval evidence contains a custom Radar origin override")
    worktree = raw.get("worktree")
    if (
        not isinstance(worktree, Mapping)
        or worktree.get("temporary") is not True
        or worktree.get("detached") is not True
        or worktree.get("clean_before") is not True
        or worktree.get("clean_after") is not True
    ):
        raise ReleaseEvidenceError("live Host Eval must run in a clean detached worktree")
    if raw.get("suites") != [evidence_suite] or graded.get("suites") != [evidence_suite]:
        raise ReleaseEvidenceError(f"evidence must cover exactly the {evidence_suite} suite")
    commit = str(raw.get("commit") or "")
    _verify_commit_binding(root, evidence_dir, commit)

    raw_cases = raw.get("cases")
    graded_cases = graded.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ReleaseEvidenceError("host-eval.json contains no cases")
    expected_cases = load_suite(root, evidence_suite)
    expected_ids = [case.case_id for case in expected_cases]
    raw_ids = [_case_id(case) for case in raw_cases]
    graded_ids = [
        _case_id(case) for case in graded_cases
    ] if isinstance(graded_cases, list) else []
    if raw_ids != expected_ids or len(set(raw_ids)) != len(raw_ids):
        raise ReleaseEvidenceError(
            f"raw Host Eval case IDs do not exactly match {evidence_suite} eval definitions"
        )
    if graded_ids != expected_ids or len(set(graded_ids)) != len(graded_ids):
        raise ReleaseEvidenceError("graded Host Eval case IDs do not exactly match raw/eval definitions")
    for submitted, expected in zip(raw_cases, expected_cases):
        required = {
            "id": expected.case_id,
            "suite": expected.suite,
            "prompt": expected.prompt,
            "expected_skill": expected.expected_skill,
            "expected_workflow": list(expected.expected_workflow),
            "requires_live_network": expected.requires_live_network,
            "installed_skills": list(expected.installed_skills),
            "provided_topic_snapshot": (
                dict(expected.provided_topic_snapshot)
                if expected.provided_topic_snapshot is not None
                else None
            ),
        }
        if not isinstance(submitted, Mapping) or any(submitted.get(key) != value for key, value in required.items()):
            raise ReleaseEvidenceError(f"raw Host Eval case contract differs from eval definition: {expected.case_id}")
        if (
            submitted.get("skill_environment_isolated") is not True
            or submitted.get("codex_home_preserved") is not True
            or submitted.get("authentication_material_copied") is not False
            or submitted.get("authentication_content_recorded") is not False
            or submitted.get("skill_source_commit") != commit
        ):
            raise ReleaseEvidenceError(
                f"raw Host Eval Skill visibility contract is missing or unbound: {expected.case_id}"
            )
        roots = submitted.get("skill_fixture_roots")
        manifest = submitted.get("skill_fixture_manifest")
        disabled = submitted.get("disabled_skill_paths")
        source_path = str(worktree.get("path") or "")
        execution_root = str(submitted.get("execution_workspace_root") or "")
        if (
            not isinstance(roots, Mapping)
            or set(roots) != set(expected.installed_skills)
            or not all(
                isinstance(roots.get(skill), str)
                and str(roots[skill]).startswith("/tmp/ati-host-eval-home-")
                and str(roots[skill]).endswith(f"/.agents/skills/{skill}")
                and source_path not in str(roots[skill])
                for skill in expected.installed_skills
            )
            or not isinstance(disabled, list)
            or not all(isinstance(path, str) for path in disabled)
            or any(
                str(Path(str(roots[skill])) / "SKILL.md") in disabled
                for skill in expected.installed_skills
            )
            or not execution_root.startswith("/tmp/ati-host-eval-workspace-")
            or execution_root == source_path
            or any(execution_root == str(roots[skill]) for skill in expected.installed_skills)
            or not isinstance(manifest, Mapping)
            or set(manifest) != set(expected.installed_skills)
            or any(
                manifest.get(skill) != _manifest_at_commit(root, commit, skill)
                for skill in expected.installed_skills
            )
            or any(
                any(
                    forbidden in str(row.get("path") or "").lower()
                    for forbidden in ("auth.json", "token", "session", "cookie", "config.toml")
                )
                for skill in expected.installed_skills
                for row in (manifest.get(skill) or [])
                if isinstance(row, Mapping)
            )
        ):
            raise ReleaseEvidenceError(
                f"raw Host Eval fixture manifest is missing or differs from RC: {expected.case_id}"
            )
        if (
            submitted.get("execution_workspace_isolated") is not True
            or submitted.get("execution_workspace_neutral") is not True
            or submitted.get("execution_workspace_clean_before") is not True
            or submitted.get("execution_workspace_clean_after") is not True
            or submitted.get("source_worktree_used_as_host_cwd") is not False
            or submitted.get("source_worktree_clean_after") is not True
            or submitted.get("skill_fixture_clean_after") is not True
        ):
            raise ReleaseEvidenceError(
                f"raw Host Eval neutral execution workspace contract failed: {expected.case_id}"
            )

    bad_trace = []
    for case in raw_cases:
        if not isinstance(case, Mapping):
            bad_trace.append(_case_id(case))
            continue
        regenerated_trace = analyze_jsonl_trace(
            str(case.get("stdout") or ""),
            exit_code=case.get("exit_code"),
            runtime_status=str(case.get("runtime_status") or ""),
            timed_out=case.get("timed_out") is True,
            stdout_truncated=case.get("stdout_truncated") is True,
            stderr_truncated=case.get("stderr_truncated") is True,
            worktree_clean_after=case.get("worktree_clean_after") is True,
        )
        if any(case.get(field) != regenerated_trace.get(field) for field in TRACE_FIELDS):
            bad_trace.append(_case_id(case))
    bad_trace.extend([
        _case_id(case)
        for case in raw_cases
        if not isinstance(case, Mapping)
        or case.get("trace_integrity_status") not in PASSING_TRACE_INTEGRITY_STATUSES
        or case.get("turn_started_count") != 1
        or case.get("turn_completed_count") != 1
        or case.get("turn_failed_count") != 0
        or case.get("non_stream_error_event_count") != 0
        or case.get("final_agent_message_observed") is not True
        or case.get("tool_activity_after_final_agent_message") is not False
        or case.get("incomplete_item_ids") != []
        or case.get("last_event_type") != "turn.completed"
        or (
            case.get("trace_integrity_status") == "complete_after_recovery"
            and (
                case.get("stream_disconnect_observed") is not True
                or case.get("stream_recovered") is not True
                or case.get("stream_terminal_failure") is not False
            )
        )
        or (
            case.get("trace_integrity_status") == "complete_clean"
            and (
                case.get("stream_disconnect_observed") is not False
                or case.get("stream_recovered") is not False
                or case.get("stream_terminal_failure") is not False
                or case.get("error_event_count") != 0
            )
        )
    ])
    bad_trace = sorted(set(bad_trace))
    if bad_trace:
        raise ReleaseEvidenceError(
            "Host Eval trace lifecycle is incomplete or invalid: " + ", ".join(bad_trace)
        )
    bad_runtime = [
        _case_id(case)
        for case in raw_cases
        if (
            not isinstance(case, Mapping)
            or case.get("runtime_status") != "completed"
            or case.get("exit_code") != 0
            or case.get("timed_out") is not False
            or case.get("stdout_truncated") is not False
            or case.get("stderr_truncated") is not False
            or case.get("worktree_clean_after") is not True
            or case.get("execution_workspace_clean_after") is not True
            or case.get("source_worktree_clean_after") is not True
            or case.get("skill_fixture_clean_after") is not True
            or case.get("source_worktree_used_as_host_cwd") is not False
        )
    ]
    if bad_runtime:
        raise ReleaseEvidenceError(
            "Host Eval cases did not complete cleanly: " + ", ".join(bad_runtime)
        )
    try:
        regenerated = grade_report(raw)
    except EvidenceGradeError as exc:
        raise ReleaseEvidenceError(f"raw Host Eval could not be graded: {exc}") from exc
    if graded != regenerated:
        raise ReleaseEvidenceError("submitted graded report does not match regenerated evidence")
    regenerated_cases = regenerated.get("cases") or []
    bad_grades = [
        _case_id(submitted)
        for submitted, actual in zip(graded_cases, regenerated_cases)
        if not isinstance(submitted, Mapping)
        or submitted.get("evidence_grade") != actual.get("evidence_grade")
        or actual.get("evidence_grade") not in PASS_GRADES
    ]
    bad_authoritative = [
        _case_id(raw_case)
        for raw_case, actual in zip(raw_cases, regenerated_cases)
        if not isinstance(raw_case, Mapping)
        or raw_case.get("authoritative_evidence_grade") != actual.get("evidence_grade")
    ]
    if bad_authoritative:
        raise ReleaseEvidenceError(
            "raw Host Eval authoritative grade does not match regenerated evidence: "
            + ", ".join(bad_authoritative)
        )
    if bad_grades:
        raise ReleaseEvidenceError("Host Eval evidence is not fully passing: " + ", ".join(bad_grades))

    manual = _object(evidence_dir / "manual-review.json")
    if manual.get("approved") is not True:
        raise ReleaseEvidenceError("manual Host Eval review is not approved")
    if manual.get("anonymous_server_insight_calls") != 0 or manual.get("handoff_reselection") != "none":
        raise ReleaseEvidenceError("manual review has unsafe workflow attestations")
    reviews = manual.get("cases")
    if (
        not isinstance(reviews, list)
        or len(reviews) != len(expected_ids)
        or not all(isinstance(item, Mapping) for item in reviews)
        or [str(item.get("id")) for item in reviews] != expected_ids
    ):
        raise ReleaseEvidenceError("manual review must contain one ordered record per eval case")
    for item, expected in zip(reviews, expected_cases):
        must_show = expected.source.get("must_show") or []
        must_not = expected.source.get("must_not") or []
        if (
            not isinstance(item, Mapping)
            or item.get("decision") != "pass"
            or item.get("must_show_reviewed") != must_show
            or item.get("must_not_reviewed") != must_not
        ):
            raise ReleaseEvidenceError(
                f"manual review does not exactly cover must_show/must_not: {expected.case_id}"
            )
    return evidence_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify persistent live Host Eval release evidence")
    parser.add_argument("--version", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        evidence_dir = verify(args.root.resolve(), args.version.strip())
    except ReleaseEvidenceError as exc:
        print(f"release evidence blocked: {exc}")
        return 1
    print(f"release evidence verified: {evidence_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

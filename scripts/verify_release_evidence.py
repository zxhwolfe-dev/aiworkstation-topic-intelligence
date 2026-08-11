#!/usr/bin/env python3
"""Verify the persistent live Host Eval evidence required for new releases."""

from __future__ import annotations

import argparse
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
from scripts.run_host_evals import load_suite


LIVE_RADAR_NETWORK_DOMAINS = ["aiworkstation.cn"]
LIVE_RADAR_LAUNCHER_CONFIG = [
    "sandbox_workspace_write.network_access=true",
    'network_proxy={enabled=true,allowed_domains=["aiworkstation.cn"]}',
    "features.network_proxy=true",
    'approval_policy="never"',
]


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
    if raw.get("suites") != ["v0.2.1"] or graded.get("suites") != ["v0.2.1"]:
        raise ReleaseEvidenceError("evidence must cover exactly the v0.2.1 suite")
    commit = str(raw.get("commit") or "")
    _verify_commit_binding(root, evidence_dir, commit)

    raw_cases = raw.get("cases")
    graded_cases = graded.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ReleaseEvidenceError("host-eval.json contains no cases")
    expected_cases = load_suite(root, "v0.2.1")
    expected_ids = [case.case_id for case in expected_cases]
    raw_ids = [_case_id(case) for case in raw_cases]
    graded_ids = [
        _case_id(case) for case in graded_cases
    ] if isinstance(graded_cases, list) else []
    if raw_ids != expected_ids or len(set(raw_ids)) != len(raw_ids):
        raise ReleaseEvidenceError("raw Host Eval case IDs do not exactly match v0.2.1 eval definitions")
    if graded_ids != expected_ids or len(set(graded_ids)) != len(graded_ids):
        raise ReleaseEvidenceError("graded Host Eval case IDs do not exactly match raw/eval definitions")
    for submitted, expected in zip(raw_cases, expected_cases):
        required = {
            "id": expected.case_id,
            "suite": "v0.2.1",
            "prompt": expected.prompt,
            "expected_skill": expected.expected_skill,
            "expected_workflow": list(expected.expected_workflow),
            "requires_live_network": expected.requires_live_network,
        }
        if not isinstance(submitted, Mapping) or any(submitted.get(key) != value for key, value in required.items()):
            raise ReleaseEvidenceError(f"raw Host Eval case contract differs from eval definition: {expected.case_id}")

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
            or case.get("stream_disconnected") is not False
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

#!/usr/bin/env python3
"""Verify the persistent live Host Eval evidence required for new releases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


class ReleaseEvidenceError(RuntimeError):
    pass


REQUIRED_FILES = ("host-eval.json", "host-evidence.json", "manual-review.md")


def _object(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseEvidenceError(f"invalid evidence JSON: {path}") from exc
    if not isinstance(value, Mapping):
        raise ReleaseEvidenceError(f"evidence must be a JSON object: {path}")
    return value


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

    raw_cases = raw.get("cases")
    graded_cases = graded.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ReleaseEvidenceError("host-eval.json contains no cases")
    if not isinstance(graded_cases, list) or len(graded_cases) != len(raw_cases):
        raise ReleaseEvidenceError("raw and graded Host Eval case counts differ")

    bad_runtime = [
        str(case.get("id"))
        for case in raw_cases
        if not isinstance(case, Mapping) or case.get("runtime_status") != "completed"
    ]
    if bad_runtime:
        raise ReleaseEvidenceError("Host Eval cases did not complete: " + ", ".join(bad_runtime))
    bad_grades = [
        str(case.get("id"))
        for case in graded_cases
        if not isinstance(case, Mapping)
        or str(case.get("evidence_grade", "")).startswith(("unobservable", "partial", "fail"))
        or not str(case.get("evidence_grade", "")).startswith("pass")
    ]
    if bad_grades:
        raise ReleaseEvidenceError("Host Eval evidence is not fully passing: " + ", ".join(bad_grades))

    review = (evidence_dir / "manual-review.md").read_text(encoding="utf-8")
    required_attestations = (
        "APPROVED: yes",
        "must_show: reviewed",
        "must_not: reviewed",
        "anonymous_server_insight_calls: 0",
        "handoff_reselection: none",
    )
    missing_attestations = [item for item in required_attestations if item not in review]
    if missing_attestations:
        raise ReleaseEvidenceError(
            "manual Host Eval review is incomplete: " + ", ".join(missing_attestations)
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

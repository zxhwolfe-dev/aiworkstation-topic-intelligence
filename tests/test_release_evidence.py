from __future__ import annotations

import json
from pathlib import Path

import unittest

from scripts.verify_release_evidence import ReleaseEvidenceError, verify


def _write_case(root: Path, *, grade: str = "pass_expected_workflow_evidence_observed", runtime: str = "completed") -> Path:
    evidence = root / "release-evidence" / "v0.2.2"
    evidence.mkdir(parents=True)
    (evidence / "host-eval.json").write_text(
        json.dumps({"schema": "ati.host-eval.v1", "cases": [{"id": "one", "runtime_status": runtime}]}),
        encoding="utf-8",
    )
    (evidence / "host-evidence.json").write_text(
        json.dumps({"schema": "ati.host-evidence.v1", "cases": [{"id": "one", "evidence_grade": grade}]}),
        encoding="utf-8",
    )
    (evidence / "manual-review.md").write_text(
        "APPROVED: yes\nmust_show: reviewed\nmust_not: reviewed\n"
        "anonymous_server_insight_calls: 0\nhandoff_reselection: none\n",
        encoding="utf-8",
    )
    return evidence


class ReleaseEvidenceTests(unittest.TestCase):
    def test_release_evidence_requires_all_persistent_artifacts(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ReleaseEvidenceError, "missing persistent"):
                verify(Path(directory), "0.2.2")


    def test_release_evidence_rejects_incomplete_live_run(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_case(root, runtime="timeout")
            with self.assertRaisesRegex(ReleaseEvidenceError, "did not complete"):
                verify(root, "0.2.2")


    def test_release_evidence_accepts_completed_review(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = _write_case(root)
            self.assertEqual(verify(root, "0.2.2"), evidence)

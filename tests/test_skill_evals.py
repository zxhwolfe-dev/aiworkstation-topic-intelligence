from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.run_host_evals import HostEvalError, load_suite


class SkillEvalTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    PUBLIC_CALLS = {"feed", "sources", "history"}

    @classmethod
    def _payload(cls):
        return json.loads((cls.ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))

    def test_active_trigger_matrix_covers_unified_positive_and_negative_intent(self) -> None:
        payload = self._payload()
        cases = payload["cases"]
        self.assertEqual(payload["schema"], "ati.skill-evals.v1")
        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        positives = [case for case in cases if case["expected_skill"]]
        negatives = [case for case in cases if case["expected_skill"] is None]
        self.assertGreaterEqual(len(positives), 10)
        self.assertGreaterEqual(len(negatives), 8)
        self.assertEqual({case["expected_skill"] for case in positives}, {"topic-intelligence"})
        required_negative_ids = {
            "negative-current-company-news",
            "negative-translation",
            "negative-user-supplied-summary",
            "negative-generic-content-writing",
            "negative-platform-style-comparison",
            "negative-provided-material-script",
            "negative-market-facts-without-content-intent",
        }
        self.assertLessEqual(required_negative_ids, {case["id"] for case in negatives})

    def test_trigger_calls_stay_inside_public_read_contract(self) -> None:
        for case in self._payload()["cases"]:
            expected = set(case["expected_calls"])
            optional = set(case["optional_calls"])
            self.assertLessEqual(expected | optional, self.PUBLIC_CALLS, case["id"])
            if case["expected_skill"] is None:
                self.assertFalse(expected | optional, case["id"])

    def test_current_quality_suite_has_dynamic_freshness_and_no_conflicts(self) -> None:
        cases = load_suite(self.ROOT, "v0.3.1")
        self.assertGreaterEqual(len(cases), 8)
        snapshots = [case.provided_topic_snapshot for case in cases if case.provided_topic_snapshot]
        self.assertTrue(any(s["generated_at"] == "$CURRENT_TIME" for s in snapshots))
        self.assertTrue(any(s["generated_at"] == "$CURRENT_TIME_MINUS_2H" for s in snapshots))
        supplied = [case for case in cases if case.provided_topic_snapshot]
        self.assertTrue(all(case.requires_live_network is False for case in supplied))

        non_trigger = next(
            case for case in cases if case.case_id == "topic-intelligence-non-trigger"
        )
        self.assertIn("随着人工智能技术", non_trigger.prompt)
        self.assertIn(
            "ordinary rewriting completed without Radar", non_trigger.source["must_show"]
        )

    def test_quality_suite_rejects_contradictory_review_criteria(self) -> None:
        original = self.ROOT / "evals" / "v0.3.1-skill-quality.json"
        payload = json.loads(original.read_text(encoding="utf-8"))
        payload["cases"][0]["must_not"].append(payload["cases"][0]["must_show"][0])
        # Exercise the normalized rule directly through a temporary repository shape.
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            (root / "evals" / original.name).write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(HostEvalError, "contradictory"):
                load_suite(root, "v0.3.1")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from pathlib import Path


class SkillEvalTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    SKILLS = {
        "cross-market-trend-research",
        "evidence-backed-content-brief",
    }
    CALLS = {"feed", "sources", "history", "insight"}

    @classmethod
    def _cases(cls):
        payload = json.loads((cls.ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        return payload, payload["cases"]

    def test_eval_matrix_has_positive_and_negative_trigger_cases(self) -> None:
        payload, cases = self._cases()
        self.assertEqual(payload["schema"], "ati.skill-evals.v1")
        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))

        positive = [case for case in cases if case["expected_skill"]]
        negative = [case for case in cases if case["expected_skill"] is None]
        self.assertGreaterEqual(len(negative), 4)
        self.assertEqual({case["expected_skill"] for case in positive}, self.SKILLS)
        for skill in self.SKILLS:
            self.assertGreaterEqual(
                sum(case["expected_skill"] == skill for case in positive),
                3,
            )

    def test_eval_calls_use_only_existing_topic_radar_contract(self) -> None:
        _, cases = self._cases()
        for case in cases:
            expected = set(case["expected_calls"])
            optional = set(case["optional_calls"])
            self.assertLessEqual(expected | optional, self.CALLS, case["id"])
            if case["expected_skill"] == "cross-market-trend-research":
                self.assertIn("feed", expected, case["id"])
                self.assertNotIn("insight", expected, case["id"])
            if case["expected_skill"] == "evidence-backed-content-brief":
                self.assertIn("feed", expected, case["id"])
                self.assertIn("insight", expected, case["id"])
            if case["expected_skill"] is None:
                self.assertEqual(expected, set(), case["id"])
                self.assertEqual(optional, set(), case["id"])

    def test_each_skill_has_openai_metadata_for_discovery(self) -> None:
        for skill in self.SKILLS:
            path = self.ROOT / "skills" / skill / "agents" / "openai.yaml"
            content = path.read_text(encoding="utf-8")
            self.assertIn("interface:", content)
            self.assertIn("display_name:", content)
            self.assertIn("short_description:", content)
            self.assertIn("default_prompt:", content)
            self.assertIn("policy:", content)
            self.assertIn("allow_implicit_invocation: true", content)

    def test_acceptance_guide_requires_fresh_conversations_for_implicit_cases(self) -> None:
        content = (self.ROOT / "docs" / "codex-m1-acceptance.md").read_text(encoding="utf-8")
        self.assertIn("fresh Codex conversation", content)
        self.assertIn("/skills", content)
        self.assertIn("$HOME/.agents/skills", content)
        self.assertIn("Do not merge or modify Skill descriptions during acceptance", content)


if __name__ == "__main__":
    unittest.main()

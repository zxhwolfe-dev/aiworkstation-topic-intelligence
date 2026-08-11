from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V021SkillQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(
            (ROOT / "evals" / "v0.2.1-skill-quality.json").read_text(
                encoding="utf-8"
            )
        )
        self.cases = {item["id"]: item for item in self.payload["cases"]}

    def test_schema_and_expected_cases(self) -> None:
        self.assertEqual(self.payload["schema"], "ati.v0.2.1-skill-quality.v1")
        self.assertEqual(
            set(self.cases),
            {
                "brief-format-constraint-not-platform-filter",
                "ai-domain-preserved-from-first-query",
                "ai-domain-substring-noise-is-rejected",
                "creator-host-judgment-provenance",
                "brief-public-host-reasoning-zero-server-llm",
                "both-skills-no-second-selection-or-server-llm",
                "premium-insight-requires-authenticated-native-connection",
            },
        )

    def test_format_case_blocks_false_platform_mapping(self) -> None:
        case = self.cases["brief-format-constraint-not-platform-filter"]
        must_not = "\n".join(case["must_not"])
        self.assertIn("short video", must_not)
        self.assertIn("2–3 minute", must_not)
        self.assertIn("Chinese-language", must_not)
        self.assertIn("anonymous server insight", must_not)

    def test_ai_domain_is_preserved_from_first_bounded_query(self) -> None:
        case = self.cases["ai-domain-preserved-from-first-query"]
        self.assertEqual(case["expected_workflow"], ["creator-topic-opportunity-research"])
        self.assertIn(
            "AI domain retained in the first bounded candidate query",
            case["must_show"],
        )
        must_not = "\n".join(case["must_not"])
        self.assertIn("generic technology feed", must_not)
        self.assertIn("drop explicit user topic/domain scope", must_not)

    def test_ai_domain_rejects_literal_substring_noise(self) -> None:
        case = self.cases["ai-domain-substring-noise-is-rejected"]
        self.assertIn(
            "literal substring collision removed before selection",
            case["must_show"],
        )
        must_not = "\n".join(case["must_not"])
        self.assertIn("proof of semantic AI relevance", must_not)
        self.assertIn("unrestricted generic technology scan", must_not)

    def test_public_brief_uses_host_reasoning_without_server_llm(self) -> None:
        case = self.cases["brief-public-host-reasoning-zero-server-llm"]
        self.assertIn("host model produces the creative plan", case["must_show"])
        must_not = "\n".join(case["must_not"])
        self.assertIn("POST /insight", must_not)
        self.assertIn("server-side model quota", must_not)
        self.assertIn("paste an API key", must_not)

    def test_composed_case_blocks_second_selection_and_server_llm(self) -> None:
        case = self.cases["both-skills-no-second-selection-or-server-llm"]
        self.assertEqual(
            case["expected_workflow"],
            [
                "creator-topic-opportunity-research",
                "ati.topic-opportunity-handoff.v1",
                "evidence-backed-content-brief:host-reasoning",
            ],
        )
        must_not = "\n".join(case["must_not"])
        self.assertIn("another broad or bounded candidate selection", must_not)
        self.assertIn("anonymous server insight", must_not)
        self.assertIn("shared server credential", must_not)

    def test_premium_insight_requires_authenticated_native_connection(self) -> None:
        case = self.cases["premium-insight-requires-authenticated-native-connection"]
        self.assertIn("Premium Insight is optional", case["must_show"])
        self.assertIn(
            "authenticated connection is responsible for membership and quota enforcement",
            case["must_show"],
        )
        must_not = "\n".join(case["must_not"])
        self.assertIn("shared public bearer token", must_not)
        self.assertIn("private credential", must_not)
        self.assertIn("without explicit authenticated AI Workstation connection", must_not)


if __name__ == "__main__":
    unittest.main()

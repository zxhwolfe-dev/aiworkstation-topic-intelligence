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
                "creator-host-judgment-provenance",
                "brief-insight-provenance-and-reuse",
                "both-skills-no-second-selection-after-handoff",
            },
        )

    def test_format_case_blocks_false_platform_mapping(self) -> None:
        case = self.cases["brief-format-constraint-not-platform-filter"]
        must_not = "\n".join(case["must_not"])
        self.assertIn("short video", must_not)
        self.assertIn("2–3 minute", must_not)
        self.assertIn("Chinese-language", must_not)

    def test_provenance_cases_keep_fact_and_analysis_layers_separate(self) -> None:
        creator = self.cases["creator-host-judgment-provenance"]
        brief = self.cases["brief-insight-provenance-and-reuse"]
        self.assertIn("Radar facts", creator["must_show"])
        self.assertIn(
            "Radar facts separated from server Topic Insight analysis",
            brief["must_show"],
        )
        self.assertIn(
            "present server insight as independently verified fact",
            brief["must_not"],
        )

    def test_composed_case_blocks_second_selection(self) -> None:
        case = self.cases["both-skills-no-second-selection-after-handoff"]
        self.assertEqual(
            case["expected_workflow"],
            [
                "creator-topic-opportunity-research",
                "ati.topic-opportunity-handoff.v1",
                "evidence-backed-content-brief",
            ],
        )
        self.assertIn(
            "run another broad or bounded candidate selection after a valid handoff",
            case["must_not"],
        )


if __name__ == "__main__":
    unittest.main()

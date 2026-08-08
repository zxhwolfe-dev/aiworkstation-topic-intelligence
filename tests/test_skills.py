from __future__ import annotations

import unittest
from pathlib import Path


class SkillPackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _read(self, slug: str) -> str:
        return (self.ROOT / "skills" / slug / "SKILL.md").read_text(encoding="utf-8")

    def test_cross_market_skill_has_live_freshness_and_evidence_gates(self) -> None:
        content = self._read("cross-market-trend-research")
        self.assertIn("name: cross-market-trend-research", content)
        self.assertIn("/feed", content)
        self.assertIn("/history", content)
        self.assertIn("partial", content)
        self.assertIn("stale", content)
        self.assertIn("opportunity_score", content)
        self.assertIn("cross-market hypothesis", content.lower())
        self.assertIn("Source facts", content)
        self.assertIn("Unknowns", content)

    def test_content_brief_reuses_existing_insight_and_claim_boundaries(self) -> None:
        content = self._read("evidence-backed-content-brief")
        self.assertIn("name: evidence-backed-content-brief", content)
        self.assertIn("/insight", content)
        self.assertIn("recommended_angle_index", content)
        self.assertIn("opening_3_seconds", content)
        self.assertIn("must_verify", content)
        self.assertIn("avoid_claims", content)
        self.assertIn("Insight is analysis, not evidence", content)
        self.assertNotIn("new scoring engine", content.lower())


if __name__ == "__main__":
    unittest.main()

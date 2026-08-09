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
        self.assertIn("refreshing", content)
        self.assertIn("opportunity_score", content)
        self.assertIn("cross-market hypothesis", content.lower())
        self.assertIn("feed `id`", content)
        self.assertIn("Source facts", content)
        self.assertIn("Unknowns", content)

    def test_cross_market_skill_forbids_local_snapshot_fallback(self) -> None:
        content = self._read("cross-market-trend-research").lower()
        self.assertIn("live evidence is exclusive", content)
        self.assertIn("do not search local files for a substitute", content)
        self.assertIn("sibling repositories", content)
        self.assertIn("sqlite databases", content)
        self.assertIn("network-restricted sandbox", content)

    def test_content_brief_reuses_existing_insight_and_claim_boundaries(self) -> None:
        content = self._read("evidence-backed-content-brief")
        self.assertIn("name: evidence-backed-content-brief", content)
        self.assertIn("/insight", content)
        self.assertIn("recommended_angle_index", content)
        self.assertIn("opening_3_seconds", content)
        self.assertIn("must_verify", content)
        self.assertIn("avoid_claims", content)
        self.assertIn("Insight is analysis, not evidence", content)
        self.assertIn("Feed topic cards expose the stable identifier as `id`", content)
        self.assertIn("refreshing=true", content)
        self.assertNotIn("new scoring engine", content.lower())

    def test_content_brief_forbids_local_snapshot_fallback(self) -> None:
        content = self._read("evidence-backed-content-brief").lower()
        self.assertIn("live topic evidence is mandatory", content)
        self.assertIn("do not search sibling repositories", content)
        self.assertIn("old topic radar snapshots", content)
        self.assertIn("network-restricted sandbox", content)
        self.assertIn("if the live feed itself is unavailable", content)


if __name__ == "__main__":
    unittest.main()

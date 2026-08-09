from __future__ import annotations

import unittest
from pathlib import Path


class SkillPackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _read(self, slug: str) -> str:
        return (self.ROOT / "skills" / slug / "SKILL.md").read_text(encoding="utf-8")

    def test_topic_opportunity_skill_has_live_freshness_and_evidence_gates(self) -> None:
        content = self._read("creator-topic-opportunity-research")
        self.assertIn("name: creator-topic-opportunity-research", content)
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
        self.assertIn("references/quality-contract.md", content)

    def test_topic_opportunity_skill_forbids_local_snapshot_fallback(self) -> None:
        content = self._read("creator-topic-opportunity-research").lower()
        self.assertIn("live evidence is exclusive", content)
        self.assertIn("do not search local files for a substitute", content)
        self.assertIn("sibling repositories", content)
        self.assertIn("sqlite databases", content)
        self.assertIn("network-restricted sandbox", content)

    def test_content_brief_uses_public_radar_plus_host_reasoning(self) -> None:
        content = self._read("evidence-backed-content-brief")
        self.assertIn("name: evidence-backed-content-brief", content)
        self.assertIn("Public no-cost live contract", content)
        self.assertIn("current host model's own reasoning", content)
        self.assertIn("GET /api/v1/ai/topic-radar/feed", content)
        self.assertIn("GET /api/v1/ai/topic-radar/history", content)
        self.assertIn("must_verify", content)
        self.assertIn("avoid_claims", content)
        self.assertIn("Never call anonymous/public server `/insight`", content)
        self.assertIn("native authenticated AI Workstation connection", content)
        self.assertIn("Never embed or share a server credential", content)
        self.assertNotIn("Use exactly one of these entry modes before calling `/insight`", content)
        self.assertNotIn("do not call `/insight` for every candidate", content)

    def test_content_brief_forbids_local_snapshot_fallback(self) -> None:
        content = self._read("evidence-backed-content-brief").lower()
        self.assertIn("live topic evidence is mandatory", content)
        self.assertIn("do not search sibling repositories", content)
        self.assertIn("old radar snapshots", content)
        self.assertIn("network-restricted sandbox", content)
        self.assertIn("if live feed evidence cannot be reached", content)

    def test_public_skills_do_not_embed_credentials(self) -> None:
        for slug in (
            "creator-topic-opportunity-research",
            "evidence-backed-content-brief",
        ):
            root = self.ROOT / "skills" / slug
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                self.assertNotIn("authorization: bearer ", text, str(path))
                self.assertNotIn("api_key =", text, str(path))


if __name__ == "__main__":
    unittest.main()

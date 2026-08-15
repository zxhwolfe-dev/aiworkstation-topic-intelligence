from __future__ import annotations

import unittest
from pathlib import Path


class SkillPackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    SKILL = ROOT / "skills" / "topic-intelligence"

    def test_only_unified_skill_is_active(self) -> None:
        active = sorted(
            path.parent.name
            for path in (self.ROOT / "skills").glob("*/SKILL.md")
        )
        self.assertEqual(active, ["topic-intelligence"])
        for name in (
            "creator-topic-opportunity-research",
            "evidence-backed-content-brief",
        ):
            self.assertTrue(
                (self.ROOT / "legacy" / "skills" / name / "SKILL.md").is_file()
            )

    def test_unified_skill_has_narrow_trigger_boundary(self) -> None:
        content = (self.SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = content.split("---", 2)[1].lower()
        self.assertIn("live-topic choice", frontmatter)
        self.assertIn("current radar card", frontmatter)
        for excluded in (
            "news or factual lookup",
            "translation",
            "rewriting",
            "summarization",
            "generic titles or ideas",
            "platform-style advice",
            "complete supplied material",
        ):
            self.assertIn(excluded, frontmatter)
        self.assertNotIn("publishing decision", frontmatter)

    def test_unified_skill_enforces_current_evidence_and_provenance(self) -> None:
        content = (self.SKILL / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "one hour",
            "stale=true",
            "not independent verification",
            "research leads",
            "must_verify",
            "Radar observations",
            "snapshot_age_seconds",
        ):
            self.assertIn(required, content)
        self.assertNotIn("snapshot ID", content)

    def test_public_skill_uses_only_no_cost_read_contract(self) -> None:
        content = (self.SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("feed", content)
        self.assertIn("sources", content)
        self.assertIn("history", content)
        self.assertIn("Never call anonymous/public `/insight`", content)
        self.assertIn("never use `--base-url`", content)
        self.assertIn("--limit 12", content)

    def test_public_skill_does_not_embed_credentials(self) -> None:
        for path in self.SKILL.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            self.assertNotIn("authorization: bearer ", text, str(path))
            self.assertNotIn("api_key =", text, str(path))


if __name__ == "__main__":
    unittest.main()

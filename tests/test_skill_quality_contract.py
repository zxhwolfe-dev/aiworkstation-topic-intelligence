from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "topic-intelligence"
CANONICAL = ROOT / "references" / "topic-intelligence-quality-contract.md"


class SkillQualityContractTests(unittest.TestCase):
    def test_single_skill_has_three_intent_modes(self) -> None:
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("Mode 1: selection only", content)
        self.assertIn("Mode 2: brief for a supplied current topic", content)
        self.assertIn("Mode 3: selection followed by brief", content)
        self.assertIn("Do not make the user choose a mode name", normalized)

    def test_quality_contract_is_identical_in_skill_copy(self) -> None:
        self.assertEqual(CANONICAL.read_bytes(), (SKILL / "references" / "quality-contract.md").read_bytes())
        self.assertEqual(
            (ROOT / "references" / "topic-intelligence-selection-workflow.md").read_bytes(),
            (SKILL / "references" / "selection-workflow.md").read_bytes(),
        )
        self.assertEqual(
            (ROOT / "references" / "topic-intelligence-brief-workflow.md").read_bytes(),
            (SKILL / "references" / "brief-workflow.md").read_bytes(),
        )

    def test_portable_helper_invocation_is_deterministic(self) -> None:
        contract = CANONICAL.read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for content in (contract, skill):
            normalized = " ".join(content.split())
            self.assertIn("python3", content)
            self.assertIn("--timeout 30 feed --q AI --limit 12", content)
            self.assertIn("--timeout 30 sources", content)
            self.assertIn("--timeout 30 history <exact-feed-id>", content)
            self.assertIn("options", normalized.lower())
            self.assertIn("subcommand", normalized.lower())
            self.assertIn("history", content.lower())
            self.assertIn("positional", content.lower())
            self.assertIn("standalone direct command", normalized)
            self.assertIn("another Python process", normalized)
            self.assertIn("never use a repository-root", normalized.lower())
            self.assertTrue(
                "never repeat" in normalized.lower()
                or "do not repeat" in normalized.lower()
            )
            self.assertIn("display-truncated output", normalized)
            self.assertIn("exactly one successful", normalized)
        self.assertIn("never `python`", skill)
        self.assertIn("never exceed 24", skill)

    def test_quality_contract_preserves_radar_provenance_and_cost_boundary(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        for marker in (
            "Radar observations",
            "Host editorial analysis",
            "GET /api/v1/ai/topic-radar/feed",
            "GET /api/v1/ai/topic-radar/sources",
            "GET /api/v1/ai/topic-radar/history",
            "anonymous AI Workstation server-side LLM calls",
            "server-side LLM calls",
        ):
            self.assertIn(marker, content)

    def test_radar_observation_section_excludes_host_authored_framing(self) -> None:
        contract = CANONICAL.read_text(encoding="utf-8")
        selection = (ROOT / "references" / "topic-intelligence-selection-workflow.md").read_text(
            encoding="utf-8"
        )
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for content in (contract, selection, skill):
            normalized = " ".join(content.split())
            with self.subTest(source=content[:40]):
                self.assertIn("rewritten", normalized.lower())
                self.assertIn("Radar observations", normalized)
                self.assertIn("Host editorial analysis", normalized)
        self.assertIn("host-authored framing", contract)
        self.assertIn("verification effort", contract)
        self.assertIn("technical value", contract)
        self.assertIn("verbatim returned titles", selection)
        self.assertIn("End this section before ranking or comparing candidates", selection)
        self.assertIn("advantages, disadvantages", selection)
        self.assertIn("Never shorten, translate, or paraphrase", selection)

    def test_quality_contract_blocks_reselection_after_composition(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("exactly one bounded feed", normalized)
        self.assertIn("must not re-run broad selection", normalized)
        self.assertIn(
            "bounded selection → preserve the exact current-task topic identity and "
            "freshness → host-model Brief reasoning",
            normalized,
        )
        self.assertIn("exact finalist ID", content)

    def test_supplied_topic_name_only_resolves_the_same_topic(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        brief = (SKILL / "references" / "brief-workflow.md").read_text(
            encoding="utf-8"
        )
        contract = CANONICAL.read_text(encoding="utf-8")
        for content in (skill, brief, contract):
            normalized = " ".join(content.split())
            with self.subTest(source=content[:40]):
                self.assertIn("feed --q <supplied-topic-name>", normalized)
                self.assertIn("same topic", normalized)
                self.assertIn("semantic match", normalized)
                self.assertIn("exact", normalized)
        self.assertIn("at most one bounded", " ".join(skill.split()))
        self.assertIn("never choose a different topic", " ".join(skill.split()))

    def test_provenance_copy_does_not_call_radar_observations_verified_facts(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        self.assertNotIn("tell a verified fact from an editorial judgment", content)
        self.assertIn("what Radar returned", content)
        self.assertIn("what the host inferred", content)
        self.assertIn("requires independent verification", content)

    def test_unknowns_are_explicitly_disclosed(self) -> None:
        for path in (CANONICAL, SKILL / "SKILL.md"):
            content = path.read_text(encoding="utf-8")
            normalized = " ".join(content.split())
            with self.subTest(path=path):
                self.assertIn("actual audience size", normalized)
                self.assertTrue(
                    "content/topic saturation" in normalized
                    or "topic/content saturation" in normalized
                )
                self.assertIn("future reach/virality", normalized)
                self.assertIn("host editorial judgment", normalized)
                self.assertTrue(
                    "not Radar fact" in normalized
                    or "not Radar observations" in normalized
                )

    def test_release_and_sync_scripts_use_unified_runtime(self) -> None:
        release = (ROOT / "scripts" / "build_release.py").read_text(encoding="utf-8")
        sync = (ROOT / "scripts" / "sync_skill_runtime.py").read_text(encoding="utf-8")
        installer = (ROOT / "scripts" / "install_codex_skills.py").read_text(encoding="utf-8")
        self.assertIn('"topic-intelligence"', release)
        self.assertIn("topic-intelligence-selection-workflow", sync)
        self.assertIn("topic-intelligence-brief-workflow", sync)
        self.assertIn('"topic-intelligence"', installer)
        self.assertIn('"selection_workflow"', installer)
        self.assertIn('"brief_workflow"', installer)


if __name__ == "__main__":
    unittest.main()

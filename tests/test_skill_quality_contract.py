from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CREATOR = ROOT / "skills" / "creator-topic-opportunity-research"
BRIEF = ROOT / "skills" / "evidence-backed-content-brief"
QUALITY_RELATIVE = Path("references") / "quality-contract.md"
CANONICAL = ROOT / "references" / "topic-intelligence-quality-contract.md"


class SkillQualityContractTests(unittest.TestCase):
    def test_quality_contract_is_present_and_identical_everywhere(self) -> None:
        canonical = CANONICAL.read_bytes()
        creator = (CREATOR / QUALITY_RELATIVE).read_bytes()
        brief = (BRIEF / QUALITY_RELATIVE).read_bytes()
        self.assertTrue(canonical)
        self.assertEqual(canonical, creator)
        self.assertEqual(canonical, brief)

    def test_quality_contract_blocks_content_format_to_platform_mapping(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("Separate Radar query constraints from content constraints", content)
        self.assertIn("短视频", content)
        self.assertIn("2–3 分钟", content)
        self.assertIn("Chinese-language", content)
        self.assertIn("Never map content format", content)
        self.assertIn("Preserve explicit topic/domain scope", content)
        self.assertIn("Reject literal substring noise", content)
        self.assertIn("semantic relevance constraint", content)
        self.assertIn("unrestricted generic-technology scan", content)

    def test_quality_contract_enforces_zero_server_llm_public_mode(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("Public Skill cost boundary", content)
        self.assertIn("GET /feed", content)
        self.assertIn("GET /sources", content)
        self.assertIn("GET /history", content)
        self.assertIn("must **not** expose or call anonymous/public `POST /insight`", content)
        self.assertIn("current host model", content)
        self.assertIn("shared public bearer token", content)
        self.assertIn("paste private AI Workstation credentials", content)
        self.assertIn("native authenticated AI Workstation connection", content)

    def test_quality_contract_preserves_provenance(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("Radar facts", content)
        self.assertIn("Host editorial analysis", content)
        self.assertIn("Authenticated Premium Topic Insight", content)
        self.assertIn("分析/判断", content)
        self.assertIn("verified fact", content)

    def test_quality_contract_blocks_duplicate_selection_after_handoff(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("Composition must not re-run broad selection", content)
        self.assertIn("ati.topic-opportunity-handoff.v1", content)
        self.assertIn("do **not** run another broad/bounded candidate-selection feed pass", content)
        self.assertIn("finalist `/history` request is normal", content)
        self.assertIn("Creator selection → current-task handoff → Brief host reasoning", content)
        self.assertIn("evidence-backed-content-brief:host-reasoning", content)
        self.assertIn("topic_snapshot.id == topic_id", content)

    def test_portable_helper_invocation_is_deterministic(self) -> None:
        canonical = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("`python3` is the only supported interpreter entry point", canonical)
        self.assertIn("Do not use `python`, `python2`", canonical)
        self.assertIn("helper-wide arguments before the subcommand", canonical)
        self.assertIn("--timeout 30 feed --q AI --limit 12", canonical)
        self.assertIn("--timeout 30 sources", canonical)
        self.assertIn("--timeout 30 history <exact-feed-id>", canonical)
        self.assertIn("sole positional argument", canonical)
        self.assertIn("Never use `history --topic-id <id>`", canonical)
        self.assertIn("one standalone, direct command", canonical)
        self.assertIn("another Python process", canonical)
        self.assertIn("helper's own stdout", canonical)
        self.assertIn("defaults to 12", canonical)
        self.assertIn("should not exceed 24", canonical)
        self.assertIn("Do not fetch 100 candidates", canonical)

        for skill in (CREATOR, BRIEF):
            content = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("only with `python3`", content)
            self.assertIn("Do not use `python`, `python2`", content)
            self.assertIn("helper-wide arguments", content)
            self.assertIn("--timeout 30 feed --q AI --limit 12", content)
            self.assertIn("--timeout 30 sources", content)
            self.assertIn("--timeout 30 history <exact-feed-id>", content)
            self.assertIn("sole positional argument", content)
            self.assertIn("Never use `history --topic-id <id>`", content)
            self.assertIn("one standalone, direct command", content)
            self.assertIn("another Python process", content)
            self.assertIn("helper's own stdout", content)
            self.assertIn("initial `feed --limit 12`", content)
            self.assertIn("do not exceed 24 candidates", content)
            self.assertIn("currently loaded, installed Skill root", content)
            self.assertIn("never run `python3 scripts/topic_radar_client.py`", content)

        self.assertIn("currently loaded, installed Skill root", canonical)
        self.assertIn("reject `python3 scripts/topic_radar_client.py`", canonical)

    def test_skill_contracts_require_explicit_unmeasured_disclosures(self) -> None:
        for path in (
            CANONICAL,
            CREATOR / "SKILL.md",
            BRIEF / "SKILL.md",
        ):
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("actual audience size", content)
                self.assertIn("content/topic saturation", content)
                self.assertIn("future reach/virality", content)
                self.assertIn("host editorial judgment", content)
                self.assertIn("not Radar fact", content)

    def test_skill_definitions_and_openai_metadata_point_to_quality_contract(self) -> None:
        creator_skill = (CREATOR / "SKILL.md").read_text(encoding="utf-8")
        brief_skill = (BRIEF / "SKILL.md").read_text(encoding="utf-8")
        creator_yaml = (CREATOR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        brief_yaml = (BRIEF / "agents" / "openai.yaml").read_text(encoding="utf-8")

        for content in (creator_skill, brief_skill, creator_yaml, brief_yaml):
            self.assertIn("references/quality-contract.md", content)

        self.assertIn("Host quality contract", creator_skill)
        self.assertIn("Host quality and cost contract", brief_skill)
        self.assertIn("server-side model quota", creator_yaml)
        self.assertIn("must not call anonymous", brief_yaml)
        self.assertIn("authenticated Premium", brief_yaml)

    def test_release_and_sync_scripts_treat_quality_contract_as_portable(self) -> None:
        release = (ROOT / "scripts" / "build_release.py").read_text(encoding="utf-8")
        sync = (ROOT / "scripts" / "sync_skill_runtime.py").read_text(encoding="utf-8")
        doctor = (ROOT / "scripts" / "install_codex_skills.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('"references/quality-contract.md"', release)
        self.assertIn('"references/topic-intelligence-quality-contract.md"', release)
        self.assertIn("canonical_quality", sync)
        self.assertIn('"quality_contract"', doctor)


if __name__ == "__main__":
    unittest.main()

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

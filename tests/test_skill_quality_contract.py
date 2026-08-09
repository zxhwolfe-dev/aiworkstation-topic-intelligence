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
        self.assertIn("User content constraints are not Radar platform filters", content)
        self.assertIn("短视频", content)
        self.assertIn("2–3 分钟", content)
        self.assertIn("Chinese-language", content)
        self.assertIn("Never map a content-format", content)

    def test_quality_contract_preserves_three_provenance_layers(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("Radar facts", content)
        self.assertIn("Server Topic Insight", content)
        self.assertIn("Host editorial analysis", content)
        self.assertIn("分析/判断", content)
        self.assertIn("must be supported by current Radar evidence", content)

    def test_quality_contract_blocks_duplicate_selection_after_handoff(self) -> None:
        content = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("must not re-run broad selection", content.lower())
        self.assertIn("ati.topic-opportunity-handoff.v1", content)
        self.assertIn("do **not** run another broad/bounded candidate-selection feed pass", content)

    def test_openai_metadata_points_hosts_to_quality_contract(self) -> None:
        creator_yaml = (CREATOR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        brief_yaml = (BRIEF / "agents" / "openai.yaml").read_text(encoding="utf-8")

        for content in (creator_yaml, brief_yaml):
            self.assertIn("references/quality-contract.md", content)

        self.assertIn("content-format/language/audience", creator_yaml)
        self.assertIn("another broad selection pass", creator_yaml)
        self.assertIn("duration, language, audience, or tone", brief_yaml)
        self.assertIn("server Topic Insight", brief_yaml)

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

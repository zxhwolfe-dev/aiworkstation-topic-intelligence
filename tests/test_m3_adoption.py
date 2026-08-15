from __future__ import annotations

import json
import unittest
from pathlib import Path


class M3AdoptionTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_m3_has_three_user_scenarios_and_product_metrics(self) -> None:
        payload = json.loads(
            (self.ROOT / "evals" / "m3-scenarios.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema"], "ati.m3-user-scenarios.v1")
        self.assertEqual(len(payload["scenarios"]), 3)
        self.assertEqual(
            {item["id"] for item in payload["scenarios"]},
            {
                "daily-ai-topic-assistant",
                "cross-market-early-opportunity",
                "live-topic-to-research-brief",
            },
        )
        self.assertIn("next_day_return_rate", payload["product_metrics"])
        self.assertIn("scan_to_brief_rate", payload["product_metrics"])

    def test_chatgpt_install_guide_does_not_claim_universal_plan_access(self) -> None:
        content = (self.ROOT / "docs" / "chatgpt-install.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Business, Enterprise, Healthcare, and Edu", content)
        self.assertIn("Do not assume every ChatGPT account has the upload entry", content)
        self.assertIn("topic-intelligence", content)
        self.assertIn("three requests", content)

    def test_website_entry_is_user_value_first_and_keeps_evidence_boundary(self) -> None:
        content = (self.ROOT / "docs" / "website-entry-copy.zh-CN.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("把实时热点变成可执行的内容选题", content)
        self.assertIn("使用 Topic Intelligence", content)
        self.assertIn("不把模型记忆或旧快照冒充当前证据", content)
        self.assertIn("不承诺受众规模、内容饱和度、未来传播量或“爆款”", content)
        self.assertIn("Smoke、Host Eval、raw trace", content)

    def test_public_copy_omits_internal_release_process(self) -> None:
        surfaces = (
            "README.md",
            "README.zh-CN.md",
            "docs/chatgpt-install.md",
            "docs/releases/v0.3.0.md",
            "plugin-candidate/listing.md",
        )
        content = "\n".join(
            (self.ROOT / path).read_text(encoding="utf-8") for path in surfaces
        )
        for internal_term in (
            "Host Eval",
            "raw trace",
            "validation-ready",
            "temporarily blocked",
            "Developer Showcase",
            "Premium Insight",
        ):
            self.assertNotIn(internal_term, content)

    def test_v0_2_release_history_is_preserved_under_current_v0_3_line(self) -> None:
        version = (self.ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (self.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        acceptance = (
            self.ROOT / "docs" / "m3.1-final-acceptance-2026-08-09.md"
        ).read_text(encoding="utf-8")
        decision = (self.ROOT / "docs" / "release-v0.2.0-decision.md").read_text(
            encoding="utf-8"
        )
        v021_decision = (
            self.ROOT / "docs" / "release-v0.2.1-decision.md"
        ).read_text(encoding="utf-8")
        v021_acceptance = (
            self.ROOT / "docs" / "v0.2.1-non-ui-host-acceptance-2026-08-10.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(version, "0.3.0")
        self.assertIn("## [0.3.0]", changelog)
        self.assertIn("## [0.2.2] - 2026-08-11", changelog)
        self.assertIn("## [0.2.1] - 2026-08-10", changelog)
        self.assertIn("## [0.2.0] - 2026-08-09", changelog)
        self.assertIn("## [0.1.0] - 2026-08-09", changelog)
        self.assertIn("M3_1_SKILL_QUALITY_PASS", acceptance)
        self.assertIn("RELEASE_ELIGIBLE", decision)
        self.assertIn("RELEASE_ELIGIBLE", v021_decision)
        self.assertIn("NON_UI_HOST_ACCEPTANCE_PASS", v021_acceptance)
        self.assertIn("does not claim that the v0.2.1 ZIP upload UI was tested", v021_decision)


if __name__ == "__main__":
    unittest.main()

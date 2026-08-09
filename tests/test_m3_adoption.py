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
        self.assertIn("Do not market Topic Intelligence as a one-click install for every ChatGPT plan", content)
        self.assertIn("added separately on desktop and web/mobile", content)
        self.assertIn("creator-topic-opportunity-research", content)
        self.assertIn("evidence-backed-content-brief", content)

    def test_website_entry_is_user_value_first_and_keeps_evidence_boundary(self) -> None:
        content = (self.ROOT / "docs" / "website-entry-copy.zh-CN.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("今天什么 AI 题材值得做？", content)
        self.assertIn("看看今天值得研究的题材", content)
        self.assertIn("直接在 AI Workstation 使用", content)
        self.assertIn("事实、分析和建议分开", content)
        self.assertIn("不会用模型记忆或本地旧数据冒充", content)
        self.assertNotIn("保证抓住热点", content.split("## 首页不应该承诺的内容", 1)[0])

    def test_public_release_stays_v0_1_0_while_0_2_is_unreleased_development(self) -> None:
        version = (self.ROOT / "VERSION").read_text(encoding="utf-8").strip()
        readme = (self.ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (self.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(version, "0.2.0")
        self.assertIn("Latest public release: **v0.1.0", readme)
        self.assertIn("Development line: **v0.2.0 unreleased**", readme)
        self.assertIn("## [0.2.0] - Unreleased", changelog)


if __name__ == "__main__":
    unittest.main()

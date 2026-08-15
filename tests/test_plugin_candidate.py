import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginCandidateTests(unittest.TestCase):
    def test_manifest_is_skills_only_and_has_public_listing_contract(self) -> None:
        manifest = json.loads((ROOT / "plugin-candidate/ai-topic-intelligence/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "ai-topic-intelligence")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("apps", manifest)
        self.assertEqual(len(manifest["interface"]["defaultPrompt"]), 3)
        self.assertTrue(all(len(value) <= 128 for value in manifest["interface"]["defaultPrompt"]))
        self.assertEqual(manifest["interface"]["privacyPolicyURL"], "https://aiworkstation.cn/privacy/")
        self.assertEqual(manifest["interface"]["termsOfServiceURL"], "https://aiworkstation.cn/terms/")
        self.assertEqual(manifest["homepage"], "https://aiworkstation.cn/topic-intelligence/")
        self.assertEqual(manifest["interface"]["websiteURL"], "https://aiworkstation.cn/topic-intelligence/")
        self.assertEqual(manifest["interface"]["displayName"], "Topic Intelligence")
        self.assertEqual(manifest["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        for field in ("composerIcon", "logo"):
            asset = ROOT / "plugin-candidate/ai-topic-intelligence" / manifest["interface"][field]
            self.assertTrue(asset.is_file(), field)
        screenshots = manifest["interface"]["screenshots"]
        self.assertTrue(screenshots)
        self.assertTrue(all(
            (ROOT / "plugin-candidate/ai-topic-intelligence" / path).is_file()
            for path in screenshots
        ))
        plugin_showcase = (
            ROOT / "plugin-candidate/ai-topic-intelligence" / screenshots[0]
        )
        public_showcase = ROOT / "docs/assets/ai-topic-intelligence-showcase.png"
        localized_showcase = (
            ROOT / "docs/assets/ai-topic-intelligence-showcase.zh-CN.png"
        )
        self.assertEqual(plugin_showcase.read_bytes(), public_showcase.read_bytes())
        for asset in (public_showcase, localized_showcase):
            self.assertGreater(asset.stat().st_size, 100_000)
            self.assertTrue(asset.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("ai-topic-intelligence-showcase.zh-CN.png", readme_zh)

    def test_submission_cases_have_five_positive_and_three_negative(self) -> None:
        payload = json.loads((ROOT / "plugin-candidate/submission-tests.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(payload["positive_cases"]), 5)
        self.assertGreaterEqual(len(payload["negative_cases"]), 3)
        self.assertEqual(len({item["id"] for item in payload["positive_cases"] + payload["negative_cases"]}), 8)

    def test_plugin_skill_copy_is_synchronized(self) -> None:
        subprocess.run([sys.executable, "scripts/sync_plugin_candidate.py", "--check"], cwd=ROOT, check=True)

    def test_plugin_candidate_excludes_python_cache_files(self) -> None:
        tracked = subprocess.run(
            ["git", "ls-files", "plugin-candidate/ai-topic-intelligence"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.splitlines()
        self.assertFalse(any("/__pycache__/" in path for path in tracked))
        self.assertFalse(any(Path(path).suffix in {".pyc", ".pyo"} for path in tracked))

    def test_submission_checklist_does_not_invent_payment_requirement(self) -> None:
        content = (ROOT / "plugin-candidate/submission-checklist.md").read_text(encoding="utf-8")
        self.assertNotIn("payment method", content.lower())
        self.assertIn("developer-identity", content)
        self.assertIn("Apps Management write", content)
        self.assertIn("country/region", content)
        self.assertIn("release", content.lower())


if __name__ == "__main__":
    unittest.main()

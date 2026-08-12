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


if __name__ == "__main__":
    unittest.main()

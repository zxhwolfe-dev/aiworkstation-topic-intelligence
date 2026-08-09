from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HostCapabilityMatrixTests(unittest.TestCase):
    def test_matrix_keeps_chatgpt_unverified_until_manual_smoke(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "host-capabilities.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema"], "ati.host-capabilities.v1")
        hosts = {item["id"]: item for item in payload["hosts"]}
        self.assertEqual(set(hosts), {"codex", "standalone-shell", "chatgpt"})

        chatgpt = hosts["chatgpt"]
        self.assertEqual(chatgpt["status"], "manual_smoke_required")
        for key in (
            "skill_discovery",
            "standalone_package",
            "bundled_runtime_execution",
            "live_topic_radar_access",
            "multi_skill_composition",
        ):
            self.assertEqual(chatgpt[key], "unverified", key)

    def test_codex_and_standalone_evidence_are_not_promoted_to_chatgpt(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "host-capabilities.json").read_text(encoding="utf-8")
        )
        hosts = {item["id"]: item for item in payload["hosts"]}
        self.assertEqual(hosts["codex"]["skill_discovery"], "validated")
        self.assertEqual(hosts["standalone-shell"]["live_topic_radar_access"], "validated")
        self.assertEqual(hosts["chatgpt"]["evidence"], [])

    def test_m4_doc_preserves_transport_decision_boundary(self) -> None:
        content = (ROOT / "docs" / "m4-host-integration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not add Hosted MCP", content)
        self.assertIn("scripts/run_host_evals.py", content)
        self.assertIn("does **not** mutate `$HOME/.agents/skills`", content)
        self.assertIn("creator-only, brief-only, and both-Skills", content)
        self.assertIn("Skills-only is sufficient", content)


if __name__ == "__main__":
    unittest.main()

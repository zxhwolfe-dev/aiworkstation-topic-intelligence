from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HostCapabilityMatrixTests(unittest.TestCase):
    def test_matrix_records_real_chatgpt_manual_smoke(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "host-capabilities.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema"], "ati.host-capabilities.v1")
        hosts = {item["id"]: item for item in payload["hosts"]}
        self.assertEqual(set(hosts), {"codex", "standalone-shell", "chatgpt"})

        chatgpt = hosts["chatgpt"]
        self.assertEqual(
            chatgpt["status"], "skills_only_pass_with_ui_observability_limit"
        )
        self.assertEqual(chatgpt["skill_discovery"], "validated")
        self.assertEqual(chatgpt["standalone_package"], "validated")
        self.assertEqual(chatgpt["bundled_runtime_execution"], "validated")
        self.assertEqual(chatgpt["live_topic_radar_access"], "validated")
        self.assertEqual(
            chatgpt["multi_skill_composition"],
            "validated_behaviorally_handoff_trace_not_exposed",
        )
        self.assertEqual(
            chatgpt["evidence"],
            ["docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md"],
        )

    def test_chatgpt_evidence_is_not_overclaimed_as_hidden_handoff_trace(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "host-capabilities.json").read_text(encoding="utf-8")
        )
        hosts = {item["id"]: item for item in payload["hosts"]}
        chatgpt = hosts["chatgpt"]
        joined_notes = "\n".join(chatgpt["notes"])

        self.assertIn("raw ati.topic-opportunity-handoff.v1", joined_notes)
        self.assertIn("not claimed as directly observed", joined_notes)
        self.assertIn("No Hosted MCP transport is justified", joined_notes)

    def test_codex_and_standalone_evidence_remain_separate(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "host-capabilities.json").read_text(encoding="utf-8")
        )
        hosts = {item["id"]: item for item in payload["hosts"]}
        self.assertEqual(hosts["codex"]["skill_discovery"], "validated")
        self.assertEqual(hosts["standalone-shell"]["live_topic_radar_access"], "validated")
        self.assertNotEqual(hosts["chatgpt"]["evidence"], hosts["codex"]["evidence"])

    def test_m4_doc_preserves_transport_decision_boundary(self) -> None:
        content = (ROOT / "docs" / "m4-host-integration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not add Hosted MCP", content)
        self.assertIn("scripts/run_host_evals.py", content)
        self.assertIn("does **not** mutate `$HOME/.agents/skills`", content)
        self.assertIn("creator-only, brief-only, and both-Skills", content)
        self.assertIn("Skills-only is sufficient", content)

    def test_chatgpt_smoke_result_records_skills_only_pass(self) -> None:
        content = (
            ROOT / "docs" / "chatgpt-v0.2.0-smoke-result-2026-08-09.md"
        ).read_text(encoding="utf-8")
        self.assertIn("SKILLS_ONLY_PASS", content)
        self.assertIn("Brief-only", content)
        self.assertIn("validated_behaviorally_handoff_trace_not_exposed", content)
        self.assertIn("Do not build Hosted MCP", content)


if __name__ == "__main__":
    unittest.main()

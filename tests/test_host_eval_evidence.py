from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.grade_host_eval import (
    HANDOFF_SCHEMA,
    OUTPUT_SCHEMA,
    classify_case,
    grade_report,
    observe_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
CREATOR = "creator-topic-opportunity-research"
BRIEF = "evidence-backed-content-brief"


def _event(item: dict[str, object]) -> str:
    return json.dumps({"type": "item.completed", "item": item})


def _trigger_case(expected_skill: str | None) -> dict[str, object]:
    return {
        "id": "case",
        "suite": "trigger",
        "expected_skill": expected_skill,
        "expected_workflow": [] if expected_skill is None else [expected_skill],
    }


class HostEvalEvidenceTests(unittest.TestCase):
    def test_negative_catalog_scan_is_not_runtime_invocation(self) -> None:
        stdout = _event(
            {
                "type": "command_execution",
                "command": (
                    f"cat ~/.agents/skills/{CREATOR}/SKILL.md "
                    f"~/.agents/skills/{BRIEF}/SKILL.md"
                ),
                "aggregated_output": (
                    f"docs mention {CREATOR}/scripts/topic_radar_client.py and "
                    f"{BRIEF}/scripts/topic_radar_client.py"
                ),
            }
        )
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["definition_read_skills"], [CREATOR, BRIEF])
        self.assertEqual(evidence["runtime_use_skills"], [])
        self.assertEqual(
            classify_case(_trigger_case(None), evidence),
            "pass_no_skill_runtime_observed",
        )

    def test_positive_definition_read_is_consultation_evidence(self) -> None:
        stdout = _event(
            {
                "type": "command_execution",
                "command": f"sed -n '1,180p' ~/.agents/skills/{CREATOR}/SKILL.md",
                "aggregated_output": "skill body",
            }
        )
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["definition_read_skills"], [CREATOR])
        self.assertEqual(
            classify_case(_trigger_case(CREATOR), evidence),
            "pass_expected_skill_definition_consulted",
        )

    def test_runtime_helper_command_is_strong_use_evidence(self) -> None:
        stdout = _event(
            {
                "type": "command_execution",
                "command": (
                    f"python3 ~/.agents/skills/{CREATOR}/scripts/"
                    "topic_radar_client.py feed --limit 3"
                ),
                "aggregated_output": "network unavailable",
            }
        )
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_use_skills"], [CREATOR])
        self.assertEqual(
            classify_case(_trigger_case(CREATOR), evidence),
            "pass_expected_skill_runtime_observed",
        )

    def test_wrong_runtime_helper_is_a_real_negative_signal(self) -> None:
        stdout = _event(
            {
                "type": "command_execution",
                "command": (
                    f"python3 ~/.agents/skills/{BRIEF}/scripts/"
                    "topic_radar_client.py feed --limit 3"
                ),
            }
        )
        evidence = observe_evidence(stdout)
        self.assertEqual(
            classify_case(_trigger_case(CREATOR), evidence),
            "fail_wrong_skill_runtime_observed",
        )

    def test_agent_message_name_alone_does_not_fail_negative_case(self) -> None:
        stdout = _event(
            {
                "type": "agent_message",
                "text": (
                    f"I inspected whether {CREATOR} or {BRIEF} was relevant, "
                    "but this request is a direct company-news lookup."
                ),
            }
        )
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_use_skills"], [])
        self.assertEqual(
            classify_case(_trigger_case(None), evidence),
            "pass_no_skill_runtime_observed",
        )

    def test_handoff_requires_agent_message_not_file_output(self) -> None:
        command_output_only = _event(
            {
                "type": "command_execution",
                "command": f"cat ~/.agents/skills/{CREATOR}/references/handoff-contract.md",
                "aggregated_output": HANDOFF_SCHEMA,
            }
        )
        self.assertFalse(
            observe_evidence(command_output_only)["handoff_agent_message_observed"]
        )

        agent_output = _event(
            {"type": "agent_message", "text": f"ATI_HANDOFF_AUDIT {HANDOFF_SCHEMA}"}
        )
        self.assertTrue(observe_evidence(agent_output)["handoff_agent_message_observed"])

    def test_grade_report_preserves_collector_result_but_adds_evidence_grade(self) -> None:
        stdout = _event(
            {
                "type": "command_execution",
                "command": (
                    f"cat ~/.agents/skills/{CREATOR}/SKILL.md "
                    f"~/.agents/skills/{BRIEF}/SKILL.md"
                ),
            }
        )
        payload = {
            "schema": "ati.host-eval.v1",
            "host": "codex",
            "skill_version": "0.2.0",
            "generated_at": "2026-08-09T00:00:00Z",
            "cases": [
                {
                    "id": "negative-current-company-news",
                    "suite": "trigger",
                    "expected_skill": None,
                    "expected_workflow": [],
                    "runtime_status": "timeout",
                    "route_observation": "fail_unexpected_skill",
                    "stdout": stdout,
                    "stderr": "",
                }
            ],
        }
        graded = grade_report(payload)
        self.assertEqual(graded["schema"], OUTPUT_SCHEMA)
        case = graded["cases"][0]
        self.assertEqual(case["collector_route_observation"], "fail_unexpected_skill")
        self.assertEqual(case["evidence_grade"], "pass_no_skill_runtime_observed")

    def test_cli_grades_report_without_host_or_network(self) -> None:
        payload = {
            "schema": "ati.host-eval.v1",
            "host": "codex",
            "skill_version": "0.2.0",
            "generated_at": "2026-08-09T00:00:00Z",
            "cases": [
                {
                    "id": "positive",
                    "suite": "trigger",
                    "expected_skill": CREATOR,
                    "expected_workflow": [CREATOR],
                    "runtime_status": "timeout",
                    "route_observation": "pass_expected_skill_observed",
                    "stdout": _event(
                        {
                            "type": "command_execution",
                            "command": f"cat ~/.agents/skills/{CREATOR}/SKILL.md",
                        }
                    ),
                    "stderr": "",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw.json"
            output_path = Path(tmp) / "graded.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "grade_host_eval.py"),
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                result["cases"][0]["evidence_grade"],
                "pass_expected_skill_definition_consulted",
            )


if __name__ == "__main__":
    unittest.main()

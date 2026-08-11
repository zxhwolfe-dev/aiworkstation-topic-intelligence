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


def _feed_payload() -> str:
    return json.dumps({
        "generated_at": "2026-08-11T00:00:00Z",
        "status": "ok",
        "partial": False,
        "stale": False,
        "items": [],
        "source_status": [],
    })


def _sources_payload() -> str:
    return json.dumps({"generated_at": "2026-08-11T00:00:00Z", "sources": []})


def _history_payload() -> str:
    return json.dumps({"topic_id": "topic-1", "points": []})


def _helper_event(
    skill: str = CREATOR,
    *,
    operation: str = "feed",
    output: str | None = None,
    exit_code: int = 0,
    status: str = "completed",
    arguments: str = "",
) -> str:
    payload = output if output is not None else _feed_payload()
    return _event({
        "type": "command_execution",
        "command": (
            f"python3 ~/.agents/skills/{skill}/scripts/topic_radar_client.py "
            f"{operation}{arguments}"
        ),
        "aggregated_output": payload,
        "exit_code": exit_code,
        "status": status,
    })


def _helper_command_event(command: str) -> str:
    return _event({
        "type": "command_execution",
        "command": command,
        "aggregated_output": _feed_payload(),
        "exit_code": 0,
        "status": "completed",
    })


def _agent_message(text: str) -> str:
    return _event({"type": "agent_message", "text": text})


def _composite_checkpoint(topic_id: str = "topic:abc123") -> str:
    return _agent_message(
        "ati.topic-opportunity-handoff.v1\n"
        f"topic_id: {topic_id}\n"
        f"topic_snapshot.id: {topic_id}\n"
        "snapshot.generated_at: 2026-08-11T00:00:00Z\n"
        "snapshot.partial: false\n"
        "snapshot.stale: false\n"
        "evidence-backed-content-brief:host-reasoning"
    )


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
        stdout = _helper_event(arguments=" --limit 3")
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_use_skills"], [CREATOR])
        self.assertEqual(evidence["runtime_operations"], [f"{CREATOR}:feed"])
        self.assertEqual(evidence["runtime_attempt_count"], 1)
        self.assertEqual(evidence["invalid_runtime_attempts"], [])
        self.assertEqual(evidence["failed_runtime_attempts"], [])
        self.assertEqual(
            classify_case(_trigger_case(CREATOR), evidence),
            "pass_expected_skill_runtime_observed",
        )

    def test_only_python3_is_runtime_evidence(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        valid = observe_evidence(_helper_command_event(
            f"python3 {helper} --timeout 30 feed --q AI --limit 12"
        ))
        self.assertEqual(valid["runtime_operations"], [f"{CREATOR}:feed"])

        for command in (
            f"python {helper} --timeout 30 feed --q AI --limit 12",
            f"python2 {helper} --timeout 30 feed --q AI --limit 12",
            f"{helper} --timeout 30 feed --q AI --limit 12",
        ):
            with self.subTest(command=command):
                evidence = observe_evidence(_helper_command_event(command))
                self.assertEqual(evidence["runtime_use_skills"], [])
                self.assertEqual(evidence["runtime_attempt_count"], 1)
                reason = (
                    "unsupported_interpreter"
                    if command.startswith("python")
                    else "missing_python3_interpreter"
                )
                self.assertIn(reason, evidence["runtime_violation_reasons"])

    def test_wrong_runtime_helper_is_a_real_negative_signal(self) -> None:
        stdout = _helper_event(BRIEF, arguments=" --limit 3")
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

    def test_v021_quality_case_is_graded_like_quality_suite(self) -> None:
        payload = {
            "schema": "ati.host-eval.v1", "host": "codex", "skill_version": "0.2.1",
            "suites": ["v0.2.1"], "cases": [{
                "id": "v021", "suite": "v0.2.1", "expected_workflow": [CREATOR],
                "runtime_status": "completed", "stdout": _helper_event(), "stderr": "",
            }],
        }
        graded = grade_report(payload)
        self.assertEqual(graded["cases"][0]["evidence_grade"], "pass_expected_workflow_evidence_observed")

    def test_v021_quality_definition_read_alone_is_not_live_workflow_evidence(self) -> None:
        payload = {
            "schema": "ati.host-eval.v1", "host": "codex", "skill_version": "0.2.1",
            "suites": ["v0.2.1"], "cases": [{
                "id": "v021", "suite": "v0.2.1", "expected_workflow": [CREATOR],
                "runtime_status": "completed", "stdout": _event({
                    "type": "command_execution",
                    "command": f"sed -n '1,180p' ~/.agents/skills/{CREATOR}/SKILL.md",
                }), "stderr": "",
            }],
        }
        graded = grade_report(payload)
        self.assertEqual(graded["cases"][0]["evidence_grade"], "unobservable")

    def test_helper_source_reads_and_help_are_not_runtime_use(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        for command in (
            f"cat {helper}",
            f"sed -n '1,20p' {helper}",
            f"rg feed {helper}",
            f"head -20 {helper}",
            f"tail -20 {helper}",
            f"python3 -m py_compile {helper}",
            f"python3 {helper} --help",
            f"python3 {helper} feed --help",
        ):
            stdout = _event({
                "type": "command_execution", "command": command,
                "aggregated_output": _feed_payload(), "exit_code": 0, "status": "completed",
            })
            with self.subTest(command=command):
                evidence = observe_evidence(stdout)
                self.assertEqual(evidence["runtime_use_skills"], [])
                self.assertEqual(evidence["runtime_attempt_count"], 0)
                self.assertEqual(evidence["invalid_runtime_attempts"], [])

    def test_non_skill_local_helper_attempts_are_explicitly_rejected(self) -> None:
        for command in (
            "python3 scripts/topic_radar_client.py --timeout 30 feed --q AI --limit 12",
            "python3 /work/aiworkstation-topic-intelligence/scripts/topic_radar_client.py feed",
            f"python3 /work/aiworkstation-topic-intelligence/skills/{CREATOR}/scripts/topic_radar_client.py feed",
            f"python3 /work/sibling/skills/{CREATOR}/scripts/topic_radar_client.py feed",
        ):
            with self.subTest(command=command):
                evidence = observe_evidence(_helper_command_event(command))
                self.assertEqual(evidence["runtime_attempt_count"], 1)
                self.assertEqual(evidence["runtime_use_skills"], [])
                self.assertIn("non_skill_local_helper", evidence["runtime_violation_reasons"])
                self.assertEqual(
                    classify_case({"suite": "v0.2.1", "expected_workflow": [CREATOR]}, evidence),
                    "fail_noncompliant_skill_runtime_attempt_observed",
                )

    def test_composite_creator_checkpoint_proves_brief_without_duplicate_radar(self) -> None:
        stdout = "\n".join((
            _helper_event(CREATOR),
            _composite_checkpoint(),
            _agent_message("Terminal research-ready brief"),
        ))
        evidence = observe_evidence(stdout)
        self.assertTrue(evidence["handoff_agent_message_observed"])
        self.assertTrue(evidence["brief_host_reasoning_checkpoint_observed"])
        self.assertTrue(evidence["post_handoff_agent_message_observed"])
        self.assertEqual(evidence["handoff_checkpoint_topic_id"], "topic:abc123")
        self.assertEqual(evidence["runtime_attempt_count"], 1)
        self.assertEqual(
            classify_case({
                "suite": "v0.2.1",
                "expected_workflow": [CREATOR, HANDOFF_SCHEMA, f"{BRIEF}:host-reasoning"],
            }, evidence),
            "pass_expected_workflow_evidence_observed",
        )

    def test_incomplete_composite_checkpoint_paths_do_not_pass(self) -> None:
        rows = (
            (_helper_event(CREATOR), "missing_handoff"),
            ("\n".join((_helper_event(CREATOR), _agent_message(HANDOFF_SCHEMA), _agent_message("final"))), "missing_checkpoint"),
            ("\n".join((_helper_event(CREATOR), _composite_checkpoint())), "missing_terminal"),
        )
        case = {
            "suite": "v0.2.1",
            "expected_workflow": [CREATOR, HANDOFF_SCHEMA, f"{BRIEF}:host-reasoning"],
        }
        for stdout, label in rows:
            with self.subTest(label=label):
                self.assertNotEqual(
                    classify_case(case, observe_evidence(stdout)),
                    "pass_expected_workflow_evidence_observed",
                )

    def test_checkpoint_does_not_override_failed_runtime_attempt(self) -> None:
        stdout = "\n".join((
            _helper_event(CREATOR),
            _composite_checkpoint(),
            _helper_event(CREATOR, operation="history", arguments=" topic-1", output=_history_payload(), exit_code=2, status="failed"),
            _agent_message("Terminal research-ready brief"),
        ))
        evidence = observe_evidence(stdout)
        self.assertEqual(
            classify_case({
                "suite": "v0.2.1",
                "expected_workflow": [CREATOR, HANDOFF_SCHEMA, f"{BRIEF}:host-reasoning"],
            }, evidence),
            "fail_unsuccessful_skill_runtime_attempt_observed",
        )

    def test_failed_or_invalid_helper_calls_are_not_runtime_use(self) -> None:
        for stdout in (
            _helper_event(exit_code=2, status="failed"),
            _helper_event(output="network unavailable"),
            _helper_event(operation="invalid", output=_feed_payload()),
            _helper_event(output="{}"),
            _helper_event(status="in_progress", exit_code=0),
        ):
            with self.subTest(stdout=stdout):
                self.assertEqual(observe_evidence(stdout)["runtime_use_skills"], [])

    def test_shell_wrapped_successful_helper_call_is_observed(self) -> None:
        stdout = _event({
            "type": "command_execution",
            "command": (
                f"/bin/bash -lc 'python3 /skills/{CREATOR}/scripts/"
                "topic_radar_client.py --timeout 20 feed --q AI --limit 3'"
            ),
            "aggregated_output": _feed_payload(),
            "exit_code": 0,
            "status": "completed",
        })
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_use_skills"], [CREATOR])
        self.assertEqual(evidence["runtime_operations"], [f"{CREATOR}:feed"])

    def test_composed_redirected_or_custom_origin_helper_calls_are_not_runtime_use(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        for command in (
            f"cat /tmp/file && python3 {helper} feed",
            f"python3 {helper} feed && printf '{{}}'",
            f"python3 {helper} feed | tee /tmp/feed.json",
            f"python3 {helper} feed > /tmp/feed.json",
            f"python3 {helper} feed 2>&1",
            f"python3 {helper} feed $(printf AI)",
            f"python3 {helper} --base-url https://example.test feed",
        ):
            stdout = _event({
                "type": "command_execution", "command": command,
                "aggregated_output": _feed_payload(), "exit_code": 0, "status": "completed",
            })
            with self.subTest(command=command):
                evidence = observe_evidence(stdout)
                self.assertEqual(evidence["runtime_use_skills"], [])
                self.assertEqual(evidence["runtime_attempt_count"], 1)
                self.assertTrue(evidence["invalid_runtime_attempts"])

    def test_standalone_feed_sources_and_positional_history_are_compliant(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        rows = (
            (
                f"python3 {helper} --timeout 30 feed --q AI --limit 12",
                "feed",
                _feed_payload(),
            ),
            (
                f"python3 {helper} --timeout 30 sources",
                "sources",
                _sources_payload(),
            ),
            (
                f"python3 {helper} --timeout 30 history topic-1",
                "history",
                _history_payload(),
            ),
        )
        for command, operation, output in rows:
            with self.subTest(operation=operation):
                stdout = _event({
                    "type": "command_execution", "command": command,
                    "aggregated_output": output, "exit_code": 0, "status": "completed",
                })
                evidence = observe_evidence(stdout)
                self.assertEqual(evidence["runtime_operations"], [f"{CREATOR}:{operation}"])
                self.assertEqual(evidence["runtime_attempt_count"], 1)
                self.assertEqual(evidence["invalid_runtime_attempts"], [])
                self.assertEqual(evidence["failed_runtime_attempts"], [])

    def test_history_topic_id_option_is_a_noncompliant_attempt(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        stdout = _helper_command_event(
            f"python3 {helper} --timeout 30 history --topic-id topic-1"
        )
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_attempt_count"], 1)
        self.assertIn("invalid_cli_arguments", evidence["runtime_violation_reasons"])
        self.assertEqual(
            classify_case({"suite": "v0.2.1", "expected_workflow": [CREATOR]}, evidence),
            "fail_noncompliant_skill_runtime_attempt_observed",
        )

    def test_shell_composition_forms_are_noncompliant_attempts(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        for command in (
            f"python3 {helper} feed | jq .",
            f"python3 {helper} feed > /tmp/feed.json",
            f"python3 {helper} feed && printf done",
            f"python3 {helper} feed ; printf done",
            f"python3 {helper} feed $(printf AI)",
            f"python3 {helper} feed `printf AI`",
        ):
            with self.subTest(command=command):
                evidence = observe_evidence(_helper_command_event(command))
                self.assertIn("composed_or_redirected_command", evidence["runtime_violation_reasons"])
                self.assertTrue(evidence["invalid_runtime_attempts"])

    def test_valid_feed_does_not_hide_later_invalid_history(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        stdout = "\n".join((
            _helper_command_event(f"python3 {helper} --timeout 30 feed --q AI --limit 12"),
            _helper_command_event(f"python3 {helper} --timeout 30 history --topic-id topic-1"),
        ))
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_operations"], [f"{CREATOR}:feed"])
        self.assertEqual(evidence["runtime_attempt_count"], 2)
        self.assertEqual(
            classify_case({"suite": "v0.2.1", "expected_workflow": [CREATOR]}, evidence),
            "fail_noncompliant_skill_runtime_attempt_observed",
        )

    def test_valid_feed_does_not_hide_later_piped_attempt(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        stdout = "\n".join((
            _helper_command_event(f"python3 {helper} --timeout 30 feed --q AI --limit 12"),
            _helper_command_event(f"python3 {helper} feed | jq ."),
        ))
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_attempt_count"], 2)
        self.assertEqual(
            classify_case({"suite": "v0.2.1", "expected_workflow": [CREATOR]}, evidence),
            "fail_noncompliant_skill_runtime_attempt_observed",
        )

    def test_compliant_nonzero_helper_attempt_fails_case(self) -> None:
        evidence = observe_evidence(_helper_event(exit_code=127, status="failed"))
        self.assertEqual(evidence["runtime_attempt_count"], 1)
        self.assertIn("nonzero_exit", evidence["runtime_violation_reasons"])
        self.assertTrue(evidence["failed_runtime_attempts"])
        self.assertEqual(
            classify_case({"suite": "v0.2.1", "expected_workflow": [CREATOR]}, evidence),
            "fail_unsuccessful_skill_runtime_attempt_observed",
        )

    def test_valid_feed_does_not_hide_later_nonzero_helper_attempt(self) -> None:
        stdout = "\n".join((
            _helper_event(),
            _helper_event(
                operation="history",
                arguments=" topic-1",
                output=_history_payload(),
                exit_code=2,
                status="failed",
            ),
        ))
        evidence = observe_evidence(stdout)
        self.assertEqual(evidence["runtime_operations"], [f"{CREATOR}:feed"])
        self.assertEqual(evidence["runtime_attempt_count"], 2)
        self.assertEqual(
            classify_case({"suite": "v0.2.1", "expected_workflow": [CREATOR]}, evidence),
            "fail_unsuccessful_skill_runtime_attempt_observed",
        )

    def test_started_and_completed_events_count_as_one_runtime_attempt(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        command = f"python3 {helper} --timeout 30 feed --q AI --limit 12"
        started = json.dumps({"type": "item.started", "item": {
            "id": "item-1", "type": "command_execution", "command": command,
            "status": "in_progress", "exit_code": None,
        }})
        completed = json.dumps({"type": "item.completed", "item": {
            "id": "item-1", "type": "command_execution", "command": command,
            "status": "completed", "exit_code": 0, "aggregated_output": _feed_payload(),
        }})
        evidence = observe_evidence(f"{started}\n{completed}")
        self.assertEqual(evidence["runtime_attempt_count"], 1)
        self.assertEqual(evidence["runtime_operations"], [f"{CREATOR}:feed"])
        self.assertEqual(evidence["failed_runtime_attempts"], [])

    def test_all_allowed_operations_require_their_response_contract(self) -> None:
        sources = json.dumps({"generated_at": "2026-08-11T00:00:00Z", "sources": []})
        history = json.dumps({"topic_id": "topic-1", "points": []})
        for operation, arguments, output in (("sources", "", sources), ("history", " topic-1", history)):
            with self.subTest(operation=operation):
                evidence = observe_evidence(_helper_event(operation=operation, arguments=arguments, output=output))
                self.assertEqual(evidence["runtime_operations"], [f"{CREATOR}:{operation}"])

        malformed = json.dumps({
            "generated_at": "2026-08-11T00:00:00Z", "status": "ok",
            "partial": False, "stale": False, "items": [{"title": "missing id"}],
            "source_status": [],
        })
        self.assertEqual(
            observe_evidence(_helper_event(output=malformed))["runtime_use_skills"],
            [],
        )

    def test_invalid_operation_arguments_are_not_runtime_use(self) -> None:
        helper = f"/skills/{CREATOR}/scripts/topic_radar_client.py"
        for command in (
            f"python3 {helper} invalid feed",
            f"python3 {helper} feed invalid",
            f"python3 {helper} sources extra",
            f"python3 {helper} history",
            f"python3 {helper} history --help",
            f"python3 {helper} --timeout nope feed",
            f"python3 {helper} --timeout=-1 feed",
        ):
            stdout = _event({
                "type": "command_execution", "command": command,
                "aggregated_output": _feed_payload(), "exit_code": 0, "status": "completed",
            })
            with self.subTest(command=command):
                self.assertEqual(observe_evidence(stdout)["runtime_use_skills"], [])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.run_host_evals import (
    HANDOFF_SCHEMA,
    REPORT_SCHEMA,
    EvalCase,
    HostEvalError,
    _result_is_gate_failure,
    _repository_commit,
    analyze_jsonl_trace,
    build_codex_command,
    build_report,
    classify_observation,
    load_suite,
    observe_tokens,
    prepare_case_skill_environment,
    run_case,
    select_cases,
    summarize,
    trace_text,
)


ROOT = Path(__file__).resolve().parents[1]
CREATOR = "creator-topic-opportunity-research"
BRIEF = "evidence-backed-content-brief"
TEST_COMMIT = "0" * 40


class HostEvalRunnerTests(unittest.TestCase):
    def test_existing_eval_suites_load_without_rewriting_contracts(self) -> None:
        trigger = load_suite(ROOT, "trigger")
        quality = load_suite(ROOT, "quality")

        self.assertEqual(len(trigger), 20)
        self.assertGreaterEqual(len(quality), 24)
        self.assertEqual(trigger[0].suite, "trigger")
        self.assertEqual(quality[0].suite, "quality")
        self.assertTrue(any(case.requires_live_network is True for case in quality))
        self.assertTrue(any(case.requires_live_network is False for case in quality))

    def test_v021_cases_bind_the_declared_installed_skill_sets(self) -> None:
        cases = load_suite(ROOT, "v0.2.1")
        self.assertEqual(len(cases), 7)
        self.assertTrue(all(
            case.installed_skills == tuple(case.source["installed_skills"])
            for case in cases
        ))
        self.assertEqual(cases[0].installed_skills, (BRIEF,))
        self.assertEqual(cases[5].installed_skills, (CREATOR, BRIEF))

    def test_quality_suite_rejects_duplicate_and_unknown_installed_skills(self) -> None:
        rows = ([BRIEF, BRIEF], [BRIEF, "unknown-topic-skill"])
        for installed_skills in rows:
            with self.subTest(installed_skills=installed_skills):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    evals = root / "evals"
                    evals.mkdir()
                    (evals / "v0.2.1-skill-quality.json").write_text(
                        json.dumps({
                            "schema": "ati.v0.2.1-skill-quality.v1",
                            "cases": [{
                                "id": "invalid-install-set",
                                "prompt": "test",
                                "installed_skills": installed_skills,
                                "expected_workflow": [BRIEF],
                            }],
                        }),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(HostEvalError, "installed_skills"):
                        load_suite(root, "v0.2.1")

    def test_case_skill_environment_copies_only_declared_skills(self) -> None:
        case = EvalCase(
            suite="v0.2.1",
            case_id="brief-only",
            prompt="test",
            expected_skill=None,
            expected_workflow=(f"{BRIEF}:bounded-selection",),
            requires_live_network=True,
            source={},
            installed_skills=(BRIEF,),
        )
        with (
            tempfile.TemporaryDirectory() as temporary_home,
            tempfile.TemporaryDirectory() as temporary_codex,
            tempfile.TemporaryDirectory() as temporary_original,
        ):
            home = Path(temporary_home)
            codex_home = Path(temporary_codex)
            original_home = Path(temporary_original)
            auth_marker = "test-auth-content-that-must-not-be-copied"
            (codex_home / "auth.json").write_text(auth_marker, encoding="utf-8")
            duplicate = original_home / ".agents/skills" / CREATOR
            duplicate.mkdir(parents=True)
            (duplicate / "SKILL.md").write_text("duplicate", encoding="utf-8")

            environment, disabled, fixture_roots, fixture_manifest = prepare_case_skill_environment(
                case,
                source_root=ROOT,
                source_commit=TEST_COMMIT,
                home=home,
                codex_home=codex_home,
                original_home=original_home,
            )

            fixture_root = home / ".agents/skills"
            self.assertEqual(
                sorted(path.parent.name for path in fixture_root.glob("*/SKILL.md")),
                [BRIEF],
            )
            self.assertFalse((fixture_root / CREATOR).exists())
            self.assertEqual(environment["HOME"], str(home))
            self.assertEqual(environment["CODEX_HOME"], str(codex_home))
            self.assertEqual(
                environment["ATI_HOST_EVAL_SKILL_SOURCE_COMMIT"], TEST_COMMIT
            )
            self.assertIn((duplicate / "SKILL.md").resolve(), disabled)
            self.assertIn(
                (ROOT / "skills" / BRIEF / "SKILL.md").resolve(), disabled
            )
            fixture_text = "\n".join(
                path.read_bytes().decode("utf-8", errors="ignore")
                for path in fixture_root.rglob("*")
                if path.is_file()
            )
            self.assertNotIn(auth_marker, fixture_text)
            self.assertFalse((home / ".codex").exists())
            self.assertEqual(
                fixture_roots,
                {BRIEF: str((fixture_root / BRIEF).resolve())},
            )
            self.assertTrue(fixture_manifest[BRIEF])
            self.assertNotIn(
                (fixture_root / BRIEF / "SKILL.md").resolve(), disabled
            )

    def test_disabled_duplicate_skill_paths_use_one_shot_config(self) -> None:
        duplicate = Path("/tmp/duplicate-skill/SKILL.md")
        command = build_codex_command(
            ["codex"],
            "hello",
            sandbox="workspace-write",
            json_trace=True,
            live_radar_network=True,
            disabled_skill_paths=[duplicate],
        )
        config = command[command.index("skills.config=[{path=\"/tmp/duplicate-skill/SKILL.md\",enabled=false}]")]
        self.assertEqual(
            config,
            'skills.config=[{path="/tmp/duplicate-skill/SKILL.md",enabled=false}]',
        )
        self.assertNotIn("auth", " ".join(command).lower())

    def test_live_command_supports_a_neutral_non_git_workspace(self) -> None:
        command = build_codex_command(
            ["codex"], "hello", sandbox="workspace-write", json_trace=True,
            live_radar_network=True, neutral_workspace=True,
        )
        self.assertIn("--skip-git-repo-check", command)

    def test_neutral_workspace_is_separate_empty_and_must_stay_empty(self) -> None:
        case = EvalCase(
            suite="trigger", case_id="neutral", prompt="x", expected_skill=None,
            expected_workflow=(), requires_live_network=None, source={},
        )
        with tempfile.TemporaryDirectory(prefix="ati-source-test-") as source_dir:
            source = Path(source_dir)
            subprocess.run(["git", "init", "-q"], cwd=source, check=True)
            with tempfile.TemporaryDirectory(
                prefix="ati-host-eval-workspace-"
            ) as workspace_dir:
                workspace = Path(workspace_dir)
                result = run_case(
                    case,
                    command=[
                        sys.executable, "-c",
                        "from pathlib import Path; Path('residue').write_text('x')",
                    ],
                    cwd=workspace,
                    source_worktree=source,
                    execution_workspace_isolated=True,
                    timeout_seconds=5,
                    max_output_chars=10_000,
                    dry_run=False,
                )
                self.assertNotEqual(workspace.resolve(), source.resolve())
                self.assertTrue(result["execution_workspace_neutral"])
                self.assertFalse(result["execution_workspace_clean_after"])
                self.assertFalse(result["worktree_clean_after"])
                self.assertFalse(result["source_worktree_used_as_host_cwd"])

    def test_select_cases_can_span_suites_and_reject_unknown_ids(self) -> None:
        selected = select_cases(
            ROOT,
            ["trigger", "quality"],
            ["negative-code-task", "composed-pick-and-brief-zh"],
        )
        self.assertEqual(
            {case.case_id for case in selected},
            {"negative-code-task", "composed-pick-and-brief-zh"},
        )

        with self.assertRaisesRegex(HostEvalError, "unknown case id"):
            select_cases(ROOT, ["trigger"], ["definitely-missing"])

    def test_build_codex_command_is_fresh_exec_read_only_json_by_default_shape(self) -> None:
        command = build_codex_command(
            ["codex_yinhe"],
            "hello",
            sandbox="read-only",
            json_trace=True,
        )
        self.assertEqual(
            command,
            ["codex_yinhe", "exec", "--sandbox", "read-only", "--json", "hello"],
        )

    def test_live_network_requires_workspace_write(self) -> None:
        with self.assertRaisesRegex(HostEvalError, "workspace-write"):
            build_codex_command(
                ["codex"], "hello", sandbox="read-only", json_trace=True,
                live_radar_network=True,
            )

    def test_live_network_command_is_explicitly_allowlisted(self) -> None:
        command = build_codex_command(
            ["codex"], "hello", sandbox="workspace-write", json_trace=True,
            live_radar_network=True,
        )
        self.assertIn("sandbox_workspace_write.network_access=true", command)
        self.assertIn('network_proxy={enabled=true,allowed_domains=["aiworkstation.cn"]}', command)
        self.assertNotIn("danger-full-access", command)
        self.assertNotIn("--yolo", command)
    def test_trace_parser_observes_nested_jsonl_skill_and_handoff_tokens(self) -> None:
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "type": "item",
                        "payload": {
                            "path": "/tmp/creator-topic-opportunity-research/SKILL.md"
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "message",
                        "text": f"handoff schema {HANDOFF_SCHEMA}",
                    }
                ),
            ]
        )
        text = trace_text(stdout, "")
        observed = observe_tokens(
            text,
            ["creator-topic-opportunity-research", HANDOFF_SCHEMA],
        )
        self.assertEqual(observed["skills"], ["creator-topic-opportunity-research"])
        self.assertTrue(observed["handoff_schema_observed"])
        self.assertIn(HANDOFF_SCHEMA, observed["workflow_tokens"])

    def test_trigger_observation_never_guesses_when_skill_is_not_visible(self) -> None:
        positive = EvalCase(
            suite="trigger",
            case_id="positive",
            prompt="x",
            expected_skill="creator-topic-opportunity-research",
            expected_workflow=("creator-topic-opportunity-research",),
            requires_live_network=None,
            source={},
        )
        negative = EvalCase(
            suite="trigger",
            case_id="negative",
            prompt="x",
            expected_skill=None,
            expected_workflow=(),
            requires_live_network=None,
            source={},
        )

        self.assertEqual(
            classify_observation(positive, {"skills": [], "workflow_tokens": []}),
            "unobservable",
        )
        self.assertEqual(
            classify_observation(negative, {"skills": [], "workflow_tokens": []}),
            "pass_no_skill_observed",
        )
        self.assertEqual(
            classify_observation(
                positive,
                {
                    "skills": ["evidence-backed-content-brief"],
                    "workflow_tokens": ["evidence-backed-content-brief"],
                },
            ),
            "fail_wrong_skill_observed",
        )

    def test_quality_observation_reports_partial_instead_of_inventing_completion(self) -> None:
        case = EvalCase(
            suite="quality",
            case_id="compose",
            prompt="x",
            expected_skill=None,
            expected_workflow=(
                "creator-topic-opportunity-research",
                HANDOFF_SCHEMA,
                "evidence-backed-content-brief",
            ),
            requires_live_network=True,
            source={},
        )
        observation = {
            "skills": ["creator-topic-opportunity-research"],
            "workflow_tokens": ["creator-topic-opportunity-research"],
        }
        self.assertEqual(
            classify_observation(case, observation),
            "partial_workflow_observed",
        )

    def test_run_case_records_process_output_and_observable_skill(self) -> None:
        case = EvalCase(
            suite="trigger",
            case_id="fake",
            prompt="x",
            expected_skill="creator-topic-opportunity-research",
            expected_workflow=("creator-topic-opportunity-research",),
            requires_live_network=None,
            source={},
        )
        command = [
            sys.executable,
            "-c",
            (
                "import json; "
                "print(json.dumps({'event': {'skill': "
                "'creator-topic-opportunity-research'}}))"
            ),
        ]
        result = run_case(
            case,
            command=command,
            cwd=ROOT,
            timeout_seconds=5,
            max_output_chars=10_000,
            dry_run=False,
        )
        self.assertEqual(result["runtime_status"], "completed")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["route_observation"], "pass_expected_skill_observed")
        self.assertIn(
            "creator-topic-opportunity-research", result["observation"]["skills"]
        )

    def test_run_case_records_timeout_as_environment_observation(self) -> None:
        case = EvalCase(
            suite="trigger",
            case_id="timeout",
            prompt="x",
            expected_skill="creator-topic-opportunity-research",
            expected_workflow=("creator-topic-opportunity-research",),
            requires_live_network=None,
            source={},
        )
        result = run_case(
            case,
            command=[sys.executable, "-c", "import time; time.sleep(2)"],
            cwd=ROOT,
            timeout_seconds=0.05,
            max_output_chars=10_000,
            dry_run=False,
        )
        self.assertEqual(result["runtime_status"], "timeout")
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["route_observation"], "unobservable")

    def test_strict_observation_marks_unobservable_as_failure(self) -> None:
        case = EvalCase("trigger", "strict", "x", "creator-topic-opportunity-research", ("creator-topic-opportunity-research",), None, {})
        result = run_case(case, command=[sys.executable, "-c", "pass"], cwd=ROOT, timeout_seconds=5, max_output_chars=1000, dry_run=False, strict_observation=True)
        self.assertEqual(result["route_observation"], "fail_unobservable")

    def test_stream_disconnect_is_a_gate_failure_even_when_process_exits_zero(self) -> None:
        self.assertTrue(_result_is_gate_failure({
            "runtime_status": "completed",
            "route_observation": "pass_expected_workflow_observed",
            "stream_disconnected": True,
            "worktree_clean_after": True,
        }))

    def test_recovered_stream_is_allowed_by_environment_gate(self) -> None:
        self.assertFalse(_result_is_gate_failure({
            "runtime_status": "completed",
            "route_observation": "pass_expected_workflow_observed",
            "trace_integrity_status": "complete_after_recovery",
            "worktree_clean_after": True,
            "execution_workspace_clean_after": True,
            "source_worktree_used_as_host_cwd": False,
            "authoritative_evidence_grade": "pass_expected_workflow_evidence_observed",
        }))

    def test_authoritative_grade_resolves_collector_disagreement(self) -> None:
        base = {
            "runtime_status": "completed",
            "trace_integrity_status": "complete_clean",
            "worktree_clean_after": True,
            "execution_workspace_clean_after": True,
            "source_worktree_used_as_host_cwd": False,
        }
        self.assertFalse(_result_is_gate_failure({
            **base,
            "route_observation": "partial_workflow_observed",
            "authoritative_evidence_grade": "pass_expected_workflow_evidence_observed",
        }))
        self.assertTrue(_result_is_gate_failure({
            **base,
            "route_observation": "pass_expected_workflow_observed",
            "authoritative_evidence_grade": "unobservable",
        }))

    def test_recovered_disconnect_has_passing_trace_integrity(self) -> None:
        trace = "\n".join([
            json.dumps({"type": "thread.started"}),
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "error", "message": "stream disconnected before completion"}),
            json.dumps({"type": "item.started", "item": {"id": "cmd", "type": "command_execution", "status": "in_progress"}}),
            json.dumps({"type": "item.completed", "item": {"id": "cmd", "type": "command_execution", "status": "completed", "exit_code": 0}}),
            json.dumps({"type": "item.completed", "item": {"id": "msg", "type": "agent_message", "text": "done"}}),
            json.dumps({"type": "turn.completed"}),
        ])
        result = analyze_jsonl_trace(trace, exit_code=0, runtime_status="completed", timed_out=False, stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True)
        self.assertEqual(result["trace_integrity_status"], "complete_after_recovery")
        self.assertTrue(result["stream_recovered"])

    def test_structured_codex_disconnect_code_is_recovered(self) -> None:
        trace = "\n".join([
            json.dumps({"type": "turn.started"}),
            json.dumps({
                "type": "error",
                "codexErrorInfo": {"code": "ResponseStreamDisconnected"},
            }),
            json.dumps({"type": "item.completed", "item": {"id": "msg", "type": "agent_message", "text": "done"}}),
            json.dumps({"type": "turn.completed"}),
        ])
        result = analyze_jsonl_trace(trace, exit_code=0, runtime_status="completed", timed_out=False, stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True)
        self.assertEqual(result["stream_disconnect_event_count"], 1)
        self.assertEqual(result["trace_integrity_status"], "complete_after_recovery")

    def test_helper_error_is_not_misclassified_as_stream_disconnect(self) -> None:
        trace = "\n".join([
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "error", "message": "Radar helper HTTP 502"}),
            json.dumps({"type": "item.completed", "item": {"id": "msg", "type": "agent_message", "text": "done"}}),
            json.dumps({"type": "turn.completed"}),
        ])
        result = analyze_jsonl_trace(trace, exit_code=0, runtime_status="completed", timed_out=False, stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True)
        self.assertEqual(result["stream_disconnect_event_count"], 0)
        self.assertEqual(result["non_stream_error_event_count"], 1)
        self.assertEqual(result["trace_integrity_status"], "incomplete_or_failed")

    def test_missing_turn_completed_is_incomplete(self) -> None:
        trace = "\n".join([json.dumps({"type": "turn.started"}), json.dumps({"type": "error", "message": "stream disconnected"})])
        result = analyze_jsonl_trace(trace, exit_code=0, runtime_status="completed", timed_out=False, stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True)
        self.assertEqual(result["trace_integrity_status"], "incomplete_or_failed")

    def test_non_stream_error_and_unfinished_item_fail(self) -> None:
        trace = "\n".join([
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "error", "message": "provider failed"}),
            json.dumps({"type": "item.started", "item": {"id": "cmd", "type": "command_execution"}}),
            json.dumps({"type": "item.completed", "item": {"id": "msg", "type": "agent_message"}}),
            json.dumps({"type": "turn.completed"}),
        ])
        result = analyze_jsonl_trace(trace, exit_code=0, runtime_status="completed", timed_out=False, stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True)
        self.assertEqual(result["trace_integrity_status"], "incomplete_or_failed")

    def test_final_message_followed_by_tool_activity_fails(self) -> None:
        trace = "\n".join([
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "item.completed", "item": {"id": "msg", "type": "agent_message"}}),
            json.dumps({"type": "item.started", "item": {"id": "cmd", "type": "command_execution"}}),
            json.dumps({"type": "item.completed", "item": {"id": "cmd", "type": "command_execution", "exit_code": 0}}),
            json.dumps({"type": "turn.completed"}),
        ])
        result = analyze_jsonl_trace(trace, exit_code=0, runtime_status="completed", timed_out=False, stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True)
        self.assertTrue(result["tool_activity_after_final_agent_message"])
        self.assertEqual(result["trace_integrity_status"], "incomplete_or_failed")

    def test_turn_failed_invalid_json_and_truncation_fail(self) -> None:
        trace = "\n".join([
            json.dumps({"type": "turn.started"}),
            "not-json",
            json.dumps({"type": "item.completed", "item": {"id": "msg", "type": "agent_message"}}),
            json.dumps({"type": "turn.failed"}),
        ])
        result = analyze_jsonl_trace(trace, exit_code=1, runtime_status="nonzero_exit", timed_out=False, stdout_truncated=True, stderr_truncated=False, worktree_clean_after=True)
        self.assertEqual(result["turn_failed_count"], 1)
        self.assertEqual(result["invalid_jsonl_line_count"], 1)
        self.assertEqual(result["trace_integrity_status"], "incomplete_or_failed")

    def test_clean_completion_has_passing_trace_integrity(self) -> None:
        trace = "\n".join([
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "item.completed", "item": {"id": "msg", "type": "agent_message", "text": "done"}}),
            json.dumps({"type": "turn.completed"}),
        ])
        result = analyze_jsonl_trace(trace, exit_code=0, runtime_status="completed", timed_out=False, stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True)
        self.assertEqual(result["trace_integrity_status"], "complete_clean")
        self.assertFalse(result["stream_disconnect_observed"])

    def test_report_schema_and_summary_are_stable(self) -> None:
        results = [
            {
                "route_observation": "pass_expected_skill_observed",
                "runtime_status": "completed",
                "authoritative_evidence_grade": "pass_expected_skill_observed",
            },
            {
                "route_observation": "unobservable",
                "runtime_status": "timeout",
            },
        ]
        self.assertEqual(
            summarize(results),
            {
                "total": 2,
                "route_observations": {
                    "pass_expected_skill_observed": 1,
                    "unobservable": 1,
                },
                "runtime_statuses": {"completed": 1, "timeout": 1},
                "authoritative_evidence_grades": {
                    "pass_expected_skill_observed": 1,
                },
            },
        )
        report = build_report(
            root=ROOT,
            host="codex",
            suites=["trigger"],
            sandbox="read-only",
            timeout_seconds=45.0,
            launcher=["codex"],
            results=results,
            dry_run=True,
            strict_observation=True,
            commit="abc123",
        )
        self.assertEqual(report["schema"], REPORT_SCHEMA)
        self.assertEqual(report["host"], "codex")
        self.assertIn("semantic", report["grading_note"])
        self.assertTrue(report["strict_observation"])
        self.assertEqual(report["commit"], "abc123")

    def test_report_commit_is_captured_before_cases_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "VERSION").write_text("0.2.1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Host Eval Test"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
            commit = _repository_commit(root)
            report = build_report(
                root=root,
                host="codex",
                suites=["v0.2.1"],
                sandbox="read-only",
                timeout_seconds=1,
                launcher=["codex"],
                results=[],
                dry_run=True,
                strict_observation=True,
                commit=commit,
            )
            self.assertEqual(report["commit"], commit)

    def test_cli_dry_run_needs_no_codex_login_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            report_path = Path(output_dir) / "report.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "run_host_evals.py"),
                    "--dry-run",
                    "--suite",
                    "trigger",
                    "--case",
                    "negative-code-task",
                    "--launcher",
                    "codex_yinhe",
                    "--output",
                    str(report_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], REPORT_SCHEMA)
            self.assertEqual(payload["summary"]["total"], 1)
            self.assertEqual(payload["cases"][0]["runtime_status"], "dry_run")
            self.assertEqual(payload["launcher"], ["codex_yinhe"])


if __name__ == "__main__":
    unittest.main()

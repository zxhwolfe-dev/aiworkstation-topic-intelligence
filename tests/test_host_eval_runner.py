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
    _repository_commit,
    build_codex_command,
    build_report,
    classify_observation,
    load_suite,
    observe_tokens,
    run_case,
    select_cases,
    summarize,
    trace_text,
)


ROOT = Path(__file__).resolve().parents[1]


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
        from scripts.run_host_evals import _result_is_gate_failure

        self.assertTrue(_result_is_gate_failure({
            "runtime_status": "completed",
            "route_observation": "pass_expected_workflow_observed",
            "stream_disconnected": True,
            "worktree_clean_after": True,
        }))

    def test_report_schema_and_summary_are_stable(self) -> None:
        results = [
            {
                "route_observation": "pass_expected_skill_observed",
                "runtime_status": "completed",
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

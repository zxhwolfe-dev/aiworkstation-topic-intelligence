from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.grade_host_eval import HANDOFF_SCHEMA, grade_report
from scripts.run_host_evals import analyze_jsonl_trace, load_suite
from scripts.verify_release_evidence import ReleaseEvidenceError, verify


ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True,
    ).stdout.strip()


def _event(item: dict) -> str:
    return json.dumps({"type": "item.completed", "item": item})


def _typed_event(event_type: str, **payload: object) -> str:
    return json.dumps({"type": event_type, **payload})


def _feed_payload() -> str:
    return json.dumps({
        "generated_at": "2026-08-11T00:00:00Z",
        "status": "ok",
        "partial": False,
        "stale": False,
        "items": [],
        "source_status": [],
    })


def _brief_checkpoint(topic_id: str = "topic:abc123") -> str:
    handoff = {
        "schema": HANDOFF_SCHEMA,
        "topic_id": topic_id,
        "snapshot": {
            "generated_at": "2026-08-11T00:00:00Z",
            "partial": False,
            "stale": False,
        },
        "topic_snapshot": {"id": topic_id},
    }
    return json.dumps({
        "type": "item.completed",
        "item": {
            "type": "agent_message",
            "id": "handoff",
            "text": json.dumps(handoff) + "\n"
            "evidence-backed-content-brief:host-reasoning",
        },
    })


def _repo() -> tuple[tempfile.TemporaryDirectory, Path, str]:
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    (root / "evals").mkdir()
    shutil.copy2(ROOT / "evals/v0.2.1-skill-quality.json", root / "evals/v0.2.1-skill-quality.json")
    (root / "skills").mkdir()
    for skill in (
        "creator-topic-opportunity-research",
        "evidence-backed-content-brief",
    ):
        shutil.copytree(
            ROOT / "skills" / skill,
            root / "skills" / skill,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    (root / "VERSION").write_text("0.2.2\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Release Evidence Test")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "evaluated release candidate")
    return temporary, root, _git(root, "rev-parse", "HEAD")


def _fixture_manifest(root: Path, skill: str) -> list[dict[str, object]]:
    skill_root = root / "skills" / skill
    rows = []
    for path in sorted(item for item in skill_root.rglob("*") if item.is_file()):
        payload = path.read_bytes()
        rows.append({
            "path": path.relative_to(skill_root).as_posix(),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        })
    return rows


def _write_valid_evidence(root: Path, evaluated_commit: str) -> Path:
    evidence = root / "release-evidence/v0.2.2"
    evidence.mkdir(parents=True)
    cases = load_suite(root, "v0.2.1")
    raw_cases = []
    for case in cases:
        fixture_roots = {
            skill: (
                f"/tmp/ati-host-eval-home-test/.agents/skills/{skill}"
            )
            for skill in case.installed_skills
        }
        commands = [
            _typed_event("thread.started", thread_id="test-thread"),
            _typed_event("turn.started"),
        ]
        runtime_skills: set[str] = set()
        for token in case.expected_workflow:
            if token == "creator-topic-opportunity-research":
                runtime_skills.add("creator-topic-opportunity-research")
            elif token == "evidence-backed-content-brief":
                runtime_skills.add("evidence-backed-content-brief")
            elif token in {
                "evidence-backed-content-brief:bounded-selection",
                "evidence-backed-content-brief:public-radar",
                "evidence-backed-content-brief:host-reasoning",
            } and not (
                token == "evidence-backed-content-brief:host-reasoning"
                and "ati.topic-opportunity-handoff.v1" in case.expected_workflow
            ):
                runtime_skills.add("evidence-backed-content-brief")
        for skill in sorted(runtime_skills):
            commands.append(_event({
                "type": "command_execution",
                "command": f"python3 {fixture_roots[skill]}/scripts/topic_radar_client.py --timeout 30 feed --q AI --limit 12",
                "aggregated_output": _feed_payload(),
                "exit_code": 0,
                "status": "completed",
            }))
        if HANDOFF_SCHEMA in case.expected_workflow:
            commands.append(_brief_checkpoint())
        commands.append(_event({"type": "agent_message", "id": "final-agent", "text": "done"}))
        commands.append(_typed_event("turn.completed"))
        raw_case = {
            "id": case.case_id, "suite": "v0.2.1", "prompt": case.prompt,
            "expected_skill": case.expected_skill,
            "expected_workflow": list(case.expected_workflow),
            "requires_live_network": case.requires_live_network,
            "runtime_status": "completed", "route_observation": "pass_expected_workflow_observed",
            "exit_code": 0, "timed_out": False, "stdout": "\n".join(commands), "stderr": "",
            "stdout_truncated": False, "stderr_truncated": False,
            "worktree_clean_after": True,
            "installed_skills": list(case.installed_skills),
            "skill_environment_isolated": True,
            "skill_source_commit": evaluated_commit,
            "codex_home_preserved": True,
            "authentication_material_copied": False,
            "authentication_content_recorded": False,
            "skill_fixture_roots": fixture_roots,
            "skill_fixture_manifest": {
                skill: _fixture_manifest(root, skill)
                for skill in case.installed_skills
            },
            "execution_workspace_isolated": True,
            "execution_workspace_root": "/tmp/ati-host-eval-workspace-test",
            "execution_workspace_neutral": True,
            "execution_workspace_clean_before": True,
            "execution_workspace_clean_after": True,
            "source_worktree_used_as_host_cwd": False,
            "source_worktree_clean_after": True,
            "skill_fixture_clean_after": True,
            "disabled_skill_paths": [],
        }
        raw_case.update(analyze_jsonl_trace(
            raw_case["stdout"], exit_code=0, runtime_status="completed",
            timed_out=False, stdout_truncated=False, stderr_truncated=False,
            worktree_clean_after=True,
        ))
        raw_cases.append(raw_case)
    raw = {
        "schema": "ati.host-eval.v1", "generated_at": "2026-08-11T00:00:00+00:00",
        "host": "codex", "skill_version": "0.2.2", "commit": evaluated_commit,
        "suites": ["v0.2.1"], "sandbox": "workspace-write", "dry_run": False,
        "strict_observation": True, "live_radar_network": True,
        "network_allowed_domains": ["aiworkstation.cn"],
        "launcher_config": [
            "sandbox_workspace_write.network_access=true",
            'network_proxy={enabled=true,allowed_domains=["aiworkstation.cn"]}',
            'approval_policy="never"',
        ],
        "worktree": {
            "path": "/tmp/ati-host-eval-source-test/worktree",
            "temporary": True,
            "detached": True,
            "clean_before": True,
            "clean_after": True,
        },
        "cases": raw_cases,
    }
    graded = grade_report(raw)
    for raw_case, graded_case in zip(raw_cases, graded["cases"]):
        raw_case["authoritative_evidence_grade"] = graded_case["evidence_grade"]
    raw["cases"] = raw_cases
    graded = grade_report(raw)
    review = {
        "approved": True, "anonymous_server_insight_calls": 0, "handoff_reselection": "none",
        "cases": [{
            "id": case.case_id, "decision": "pass",
            "must_show_reviewed": case.source.get("must_show") or [],
            "must_not_reviewed": case.source.get("must_not") or [],
        } for case in cases],
    }
    (evidence / "host-eval.json").write_text(json.dumps(raw), encoding="utf-8")
    (evidence / "host-evidence.json").write_text(json.dumps(graded), encoding="utf-8")
    (evidence / "manual-review.json").write_text(json.dumps(review), encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "persist release evidence")
    return evidence


class ReleaseEvidenceTests(unittest.TestCase):
    def test_complete_bound_evidence_passes(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            self.assertEqual(verify(root, "0.2.2"), evidence)
        finally:
            temporary.cleanup()

    def test_dry_run_non_strict_wrong_version_and_suite_block(self) -> None:
        for field, value, message in (
            ("dry_run", True, "live strict"),
            ("strict_observation", False, "live strict"),
            ("skill_version", "0.1.0", "version"),
            ("suites", ["quality"], "suite"),
        ):
            temporary, root, evaluated = _repo()
            try:
                evidence = _write_valid_evidence(root, evaluated)
                raw_path = evidence / "host-eval.json"
                raw = json.loads(raw_path.read_text())
                raw[field] = value
                raw_path.write_text(json.dumps(raw))
                _git(root, "add", ".")
                _git(root, "commit", "-qm", f"tamper {field}")
                with self.subTest(field=field), self.assertRaisesRegex(ReleaseEvidenceError, message):
                    verify(root, "0.2.2")
            finally:
                temporary.cleanup()

    def test_missing_or_expanded_live_network_policy_blocks(self) -> None:
        for field, value, message in (
            ("sandbox", "read-only", "workspace-write"),
            ("live_radar_network", False, "explicitly enable"),
            ("network_allowed_domains", ["aiworkstation.cn", "example.com"], "allowlist"),
            ("network_allowed_domains", ["*"], "allowlist"),
        ):
            temporary, root, evaluated = _repo()
            try:
                evidence = _write_valid_evidence(root, evaluated)
                raw_path = evidence / "host-eval.json"
                raw = json.loads(raw_path.read_text())
                raw[field] = value
                raw_path.write_text(json.dumps(raw))
                _git(root, "add", ".")
                _git(root, "commit", "-qm", f"tamper network policy {field}")
                with self.subTest(field=field, value=value), self.assertRaisesRegex(
                    ReleaseEvidenceError, message
                ):
                    verify(root, "0.2.2")
            finally:
                temporary.cleanup()

    def test_custom_radar_origin_blocks(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            raw = json.loads(raw_path.read_text())
            raw["cases"][0]["command"] = ["python3", "helper.py", "--base-url", "https://example.com"]
            raw_path.write_text(json.dumps(raw))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "tamper custom origin")
            with self.assertRaisesRegex(ReleaseEvidenceError, "custom Radar origin"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_dirty_or_nondetached_eval_worktree_blocks(self) -> None:
        for field in ("detached", "clean_before", "clean_after"):
            temporary, root, evaluated = _repo()
            try:
                evidence = _write_valid_evidence(root, evaluated)
                raw_path = evidence / "host-eval.json"
                raw = json.loads(raw_path.read_text())
                raw["worktree"][field] = False
                raw_path.write_text(json.dumps(raw))
                _git(root, "add", ".")
                _git(root, "commit", "-qm", f"tamper worktree {field}")
                with self.subTest(field=field), self.assertRaisesRegex(
                    ReleaseEvidenceError, "clean detached"
                ):
                    verify(root, "0.2.2")
            finally:
                temporary.cleanup()

    def test_missing_mismatched_or_duplicate_case_ids_block(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            raw = json.loads(raw_path.read_text())
            raw["cases"][0]["id"] = raw["cases"][1]["id"]
            raw_path.write_text(json.dumps(raw))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "tamper IDs")
            with self.assertRaisesRegex(ReleaseEvidenceError, "case IDs"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_missing_or_mismatched_skill_visibility_contract_blocks(self) -> None:
        rows = (
            ("installed_skills", [], "case contract"),
            ("skill_environment_isolated", False, "visibility contract"),
            ("codex_home_preserved", False, "visibility contract"),
            ("skill_source_commit", "0" * 40, "visibility contract"),
        )
        for field, value, message in rows:
            with self.subTest(field=field):
                temporary, root, evaluated = _repo()
                try:
                    evidence = _write_valid_evidence(root, evaluated)
                    raw_path = evidence / "host-eval.json"
                    raw = json.loads(raw_path.read_text())
                    raw["cases"][0][field] = value
                    raw_path.write_text(json.dumps(raw))
                    _git(root, "add", ".")
                    _git(root, "commit", "-qm", f"tamper visibility {field}")
                    with self.assertRaisesRegex(ReleaseEvidenceError, message):
                        verify(root, "0.2.2")
                finally:
                    temporary.cleanup()

    def test_fixture_manifest_and_neutral_workspace_tampering_blocks(self) -> None:
        rows = (
            ("skill_fixture_manifest", {}, "fixture manifest"),
            ("execution_workspace_isolated", False, "neutral execution"),
            ("execution_workspace_neutral", False, "neutral execution"),
            ("execution_workspace_clean_before", False, "neutral execution"),
            ("execution_workspace_clean_after", False, "neutral execution"),
            ("source_worktree_used_as_host_cwd", True, "neutral execution"),
            ("source_worktree_clean_after", False, "neutral execution"),
        )
        for field, value, message in rows:
            with self.subTest(field=field):
                temporary, root, evaluated = _repo()
                try:
                    evidence = _write_valid_evidence(root, evaluated)
                    raw_path = evidence / "host-eval.json"
                    raw = json.loads(raw_path.read_text())
                    raw["cases"][0][field] = value
                    raw_path.write_text(json.dumps(raw))
                    _git(root, "add", ".")
                    _git(root, "commit", "-qm", f"tamper {field}")
                    with self.assertRaisesRegex(ReleaseEvidenceError, message):
                        verify(root, "0.2.2")
                finally:
                    temporary.cleanup()

    def test_fixture_cannot_be_disabled_or_share_source_cwd(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            raw = json.loads(raw_path.read_text())
            case = raw["cases"][0]
            skill = case["installed_skills"][0]
            case["disabled_skill_paths"] = [
                str(Path(case["skill_fixture_roots"][skill]) / "SKILL.md")
            ]
            raw_path.write_text(json.dumps(raw))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "disable evaluated fixture")
            with self.assertRaisesRegex(ReleaseEvidenceError, "fixture manifest"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_runner_authoritative_grade_must_match_regenerated_grade(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            raw = json.loads(raw_path.read_text())
            raw["cases"][0]["authoritative_evidence_grade"] = "unobservable"
            raw_path.write_text(json.dumps(raw))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "tamper runner authority")
            with self.assertRaisesRegex(ReleaseEvidenceError, "authoritative grade"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_collector_partial_does_not_override_authoritative_pass(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            raw = json.loads(raw_path.read_text())
            raw["cases"][0]["route_observation"] = "partial_workflow_observed"
            raw_path.write_text(json.dumps(raw))
            (evidence / "host-evidence.json").write_text(
                json.dumps(grade_report(raw))
            )
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "preserve collector diagnostic")
            self.assertEqual(verify(root, "0.2.2"), evidence)
        finally:
            temporary.cleanup()

    def test_fabricated_grade_and_global_only_manual_review_block(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            graded_path = evidence / "host-evidence.json"
            graded = json.loads(graded_path.read_text())
            graded["cases"][0]["evidence_grade"] = "pass_fabricated"
            graded_path.write_text(json.dumps(graded))
            (evidence / "manual-review.json").write_text(json.dumps({
                "approved": True, "anonymous_server_insight_calls": 0,
                "handoff_reselection": "none", "cases": [],
            }))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "fabricate evidence")
            with self.assertRaisesRegex(ReleaseEvidenceError, "graded report|manual"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_nonzero_timeout_or_truncated_case_blocks(self) -> None:
        for field, value in (
            ("exit_code", 1),
            ("timed_out", True),
            ("stdout_truncated", True),
            ("stderr_truncated", True),
        ):
            temporary, root, evaluated = _repo()
            try:
                evidence = _write_valid_evidence(root, evaluated)
                raw_path = evidence / "host-eval.json"
                raw = json.loads(raw_path.read_text())
                raw["cases"][0][field] = value
                raw_path.write_text(json.dumps(raw))
                _git(root, "add", ".")
                _git(root, "commit", "-qm", f"tamper execution {field}")
                with self.subTest(field=field), self.assertRaisesRegex(ReleaseEvidenceError, "cleanly|trace lifecycle"):
                    verify(root, "0.2.2")
            finally:
                temporary.cleanup()

    def test_complete_source_read_only_evidence_package_blocks(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            graded_path = evidence / "host-evidence.json"
            raw = json.loads(raw_path.read_text())
            for case in raw["cases"]:
                events = []
                for skill in ("creator-topic-opportunity-research", "evidence-backed-content-brief"):
                    if any(
                        token == skill or token.startswith(skill + ":")
                        for token in case["expected_workflow"]
                    ):
                        events.append(_event({
                            "type": "command_execution",
                            "command": f"sed -n '1,20p' /skills/{skill}/scripts/topic_radar_client.py",
                            "aggregated_output": _feed_payload(),
                            "exit_code": 0,
                            "status": "completed",
                        }))
                if HANDOFF_SCHEMA in case["expected_workflow"]:
                    events.append(_event({"type": "agent_message", "text": HANDOFF_SCHEMA}))
                case["stdout"] = "\n".join(events)
            raw_path.write_text(json.dumps(raw))
            graded_path.write_text(json.dumps(grade_report(raw)))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "replace execution with source reads")
            with self.assertRaisesRegex(ReleaseEvidenceError, "trace lifecycle|not fully passing"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_complete_after_recovery_evidence_passes(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            raw = json.loads(raw_path.read_text())
            for case in raw["cases"]:
                trace = case["stdout"].splitlines()
                trace.insert(2, json.dumps({"type": "error", "message": "stream disconnected before completion"}))
                case["stdout"] = "\n".join(trace)
                case.update(analyze_jsonl_trace(
                    case["stdout"], exit_code=0, runtime_status="completed", timed_out=False,
                    stdout_truncated=False, stderr_truncated=False, worktree_clean_after=True,
                ))
            raw_path.write_text(json.dumps(raw))
            (evidence / "host-evidence.json").write_text(json.dumps(grade_report(raw)))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "recovered stream evidence")
            self.assertEqual(verify(root, "0.2.2"), evidence)
        finally:
            temporary.cleanup()

    def test_forged_recovery_without_lifecycle_blocks(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            raw_path = evidence / "host-eval.json"
            raw = json.loads(raw_path.read_text())
            raw["cases"][0]["trace_integrity_status"] = "complete_after_recovery"
            raw["cases"][0]["stream_recovered"] = True
            raw["cases"][0]["stream_disconnect_observed"] = True
            raw_path.write_text(json.dumps(raw))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "forge recovered evidence")
            with self.assertRaisesRegex(ReleaseEvidenceError, "trace lifecycle"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_extra_non_object_manual_case_blocks(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            evidence = _write_valid_evidence(root, evaluated)
            manual_path = evidence / "manual-review.json"
            manual = json.loads(manual_path.read_text())
            manual["cases"].append("unexpected")
            manual_path.write_text(json.dumps(manual))
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "tamper manual case shape")
            with self.assertRaisesRegex(ReleaseEvidenceError, "manual review must contain"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_old_report_is_invalid_after_non_evidence_code_change(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            _write_valid_evidence(root, evaluated)
            (root / "VERSION").write_text("0.2.2\nchanged\n")
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "change release code")
            with self.assertRaisesRegex(ReleaseEvidenceError, "release code changed|version"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()

    def test_direct_cli_entrypoint_loads_package_imports(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "verify_release_evidence.py"),
                "--version",
                "0.2.2",
                "--root",
                str(ROOT),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing persistent live Host Eval evidence", completed.stdout)

    def test_dirty_worktree_blocks_evidence_verification(self) -> None:
        temporary, root, evaluated = _repo()
        try:
            _write_valid_evidence(root, evaluated)
            (root / "uncommitted.txt").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ReleaseEvidenceError, "worktree must be clean"):
                verify(root, "0.2.2")
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()

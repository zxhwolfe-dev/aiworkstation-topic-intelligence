#!/usr/bin/env python3
"""Conservatively grade Topic Intelligence host-eval traces.

`run_host_evals.py` is a collector. This module performs a second-stage evidence
classification that deliberately distinguishes passive Skill discovery from
stronger runtime/workflow evidence. Codex `exec --json` does not currently
expose a first-class "Skill X triggered" event, so a Skill name appearing in a
file path or command output must never be treated as proof of invocation by
itself.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


INPUT_SCHEMA = "ati.host-eval.v1"
OUTPUT_SCHEMA = "ati.host-evidence.v1"
HANDOFF_SCHEMA = "ati.topic-opportunity-handoff.v1"
TOPIC_INTELLIGENCE_SKILLS = (
    "creator-topic-opportunity-research",
    "evidence-backed-content-brief",
)
CREATOR_SKILL = TOPIC_INTELLIGENCE_SKILLS[0]
BRIEF_SKILL = TOPIC_INTELLIGENCE_SKILLS[1]
HELPER_BASENAME = "topic_radar_client.py"
RADAR_OPERATIONS = {"feed", "sources", "history"}
SHELL_EXECUTABLES = {"bash", "dash", "sh", "zsh"}
INSPECTION_EXECUTABLES = {
    "cat", "sed", "rg", "head", "tail", "less", "more", "grep",
    "py_compile", "compileall",
}
FEED_VALUE_OPTIONS = {
    "--q", "--platform", "--target-platform", "--region", "--category",
    "--source", "--stage", "--signal", "--keywords", "--exclude-sources",
    "--min-score", "--max-age-hours", "--offset", "--limit",
}
SUPPORTED_QUALITY_SUITES = {"quality", "v0.2.1"}
PASS_GRADES = {
    "pass_no_skill_runtime_observed",
    "pass_expected_skill_runtime_observed",
    "pass_expected_skill_definition_consulted",
    "pass_expected_workflow_evidence_observed",
}


class EvidenceGradeError(RuntimeError):
    pass


def _iter_jsonl(stdout: str) -> Iterable[Mapping[str, Any]]:
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            yield value


def _collect_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _collect_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _collect_strings(item)


def _skills_in_text(text: str) -> set[str]:
    return {skill for skill in TOPIC_INTELLIGENCE_SKILLS if skill in text}


def _looks_like_definition_read(text: str, skill: str) -> bool:
    normalized = text.replace("\\", "/")
    if skill not in normalized:
        return False
    return any(
        marker in normalized
        for marker in (
            f"/{skill}/SKILL.md",
            f"/{skill}/agents/openai.yaml",
            f"/{skill}/references/handoff-contract.md",
        )
    )


def _shell_tokens(text: str) -> list[str]:
    """Return shell-aware words/operators without executing the command."""

    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return []


def _command_tokens(command: str) -> list[str]:
    """Unwrap the normal `shell -lc` trace shape and tokenize its payload."""

    try:
        outer = shlex.split(command, posix=True)
    except ValueError:
        return []
    if not outer:
        return []
    executable = outer[0].replace("\\", "/").rsplit("/", 1)[-1]
    if executable in SHELL_EXECUTABLES and len(outer) >= 3 and outer[1] in {"-c", "-lc"}:
        return _shell_tokens(outer[2])
    return _shell_tokens(command)


def _helper_path_info(command: str) -> tuple[list[str], int, str] | None:
    """Return command tokens, helper token index, and normalized helper path."""

    tokens = _command_tokens(command)
    if not tokens:
        return None
    helper_indexes = [
        index
        for index, token in enumerate(tokens)
        if (
            token.replace("\\", "/").rstrip("/") == HELPER_BASENAME
            or token.replace("\\", "/").rstrip("/").endswith(f"scripts/{HELPER_BASENAME}")
        )
    ]
    if not helper_indexes:
        return None
    index = helper_indexes[0]
    return tokens, index, tokens[index].replace("\\", "/")


def _skill_for_helper_path(path: str) -> str | None:
    """Recognize only helpers under an installed Skill root.

    `/skills/<name>/scripts/...` is the deterministic fixture form used by the
    tests; real installs use `~/.agents/skills/<name>/scripts/...`. Repository
    checkouts and sibling repositories are deliberately excluded.
    """

    normalized = path.rstrip("/")
    match = re.search(
        r"/(creator-topic-opportunity-research|evidence-backed-content-brief)/scripts/"
        + re.escape(HELPER_BASENAME)
        + r"$",
        normalized,
    )
    if not match:
        return None
    skill = match.group(1)
    prefix = normalized[: match.start()]
    if "aiworkstation-topic-intelligence" in prefix or "akaiagents" in prefix:
        return None
    if "/.agents/skills" in prefix or prefix in {"", "/", "/skills"}:
        return skill
    return None


def _runtime_attempt(command: str) -> dict[str, Any] | None:
    """Describe any attempted helper execution, including non-Skill helpers."""

    info = _helper_path_info(command)
    if info is None:
        return None
    tokens, helper_index, helper_path = info

    arguments = tokens[helper_index + 1:]
    # Reading source, compiling it, and asking argparse for help are inspection,
    # not attempts to obtain live Radar evidence.
    command_executable = tokens[0].replace("\\", "/").rsplit("/", 1)[-1]
    shell_operators = {";", ";;", "&", "&&", "|", "||", ">", ">>", "<", "<<"}
    if command_executable in INSPECTION_EXECUTABLES and not any(
        token in shell_operators for token in tokens
    ):
        return None
    if command_executable.startswith("python") and "-m" in tokens[:helper_index]:
        module_index = tokens.index("-m") + 1
        if module_index < len(tokens) and tokens[module_index] in {"py_compile", "compileall"}:
            return None
    if "-h" in arguments or "--help" in arguments:
        return None

    if helper_index == 0:
        executable = ""
    else:
        executable = tokens[helper_index - 1].replace("\\", "/").rsplit("/", 1)[-1]
        if executable in INSPECTION_EXECUTABLES:
            return None

    skill = _skill_for_helper_path(helper_path)
    violations: list[str] = []
    if skill is None:
        violations.append("non_skill_local_helper")
    if helper_index == 0:
        violations.append("missing_python3_interpreter")
    elif executable != "python3":
        violations.append("unsupported_interpreter")
    if helper_index not in {0, 1}:
        violations.append("non_standalone_helper_command")
    if any(any(character in token for character in ";|&<>`$") for token in tokens):
        violations.append("composed_or_redirected_command")
    if any(token == "--base-url" or token.startswith("--base-url=") for token in arguments):
        violations.append("custom_radar_origin")

    operation = _validated_operation_arguments(arguments)
    if operation is None:
        violations.append("invalid_cli_arguments")

    return {
        "skill": skill,
        "helper_path": helper_path,
        "command": command,
        "operation": operation,
        "violation_reasons": sorted(set(violations)),
    }


def _validated_operation_arguments(arguments: Sequence[str]) -> str | None:
    """Recognize only the helper's supported CLI grammar."""

    remaining = list(arguments)
    while remaining and remaining[0].startswith("--timeout"):
        option = remaining.pop(0)
        if option == "--timeout":
            if not remaining:
                return None
            value = remaining.pop(0)
        elif option.startswith("--timeout="):
            value = option.split("=", 1)[1]
        else:
            return None
        try:
            if float(value) <= 0:
                return None
        except ValueError:
            return None

    if not remaining:
        return None
    operation = remaining.pop(0)
    if operation not in RADAR_OPERATIONS:
        return None

    if operation == "sources":
        return operation if not remaining else None
    if operation == "history":
        return operation if len(remaining) == 1 and remaining[0] and not remaining[0].startswith("-") else None

    while remaining:
        option = remaining.pop(0)
        if option == "--new-only":
            continue
        if "=" in option:
            name, value = option.split("=", 1)
            if name not in FEED_VALUE_OPTIONS or not value:
                return None
            continue
        if option not in FEED_VALUE_OPTIONS or not remaining:
            return None
        value = remaining.pop(0)
        if not value or value.startswith("--"):
            return None
    return operation


def _validated_radar_response(operation: str, output: Any) -> bool:
    """Require JSON emitted only after the bundled helper validates its response."""

    if not isinstance(output, str) or not output.strip():
        return False
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, Mapping):
        return False
    if operation == "feed":
        if not (
            isinstance(payload.get("generated_at"), str)
            and bool(payload["generated_at"].strip())
            and isinstance(payload.get("status"), str)
            and bool(payload["status"].strip())
            and isinstance(payload.get("partial"), bool)
            and isinstance(payload.get("stale"), bool)
            and isinstance(payload.get("items"), list)
            and isinstance(payload.get("source_status"), list)
        ):
            return False
        return all(
            isinstance(item, Mapping)
            and isinstance(item.get("id"), str)
            and bool(item["id"].strip())
            for item in payload["items"]
        ) and all(
            isinstance(item, Mapping)
            and isinstance(item.get("id"), str)
            and bool(item["id"].strip())
            and isinstance(item.get("status"), str)
            and bool(item["status"].strip())
            for item in payload["source_status"]
        )
    if operation == "sources":
        return (
            isinstance(payload.get("generated_at"), str)
            and bool(payload["generated_at"].strip())
            and isinstance(payload.get("sources"), list)
        )
    if operation == "history":
        if not (
            isinstance(payload.get("topic_id"), str)
            and bool(payload["topic_id"].strip())
            and isinstance(payload.get("points"), list)
        ):
            return False
        return all(
            isinstance(point, Mapping)
            and isinstance(point.get("observed_at"), str)
            and bool(point["observed_at"].strip())
            and not isinstance(point.get("opportunity_score"), bool)
            and isinstance(point.get("opportunity_score"), (int, float))
            for point in payload["points"]
        )
    return False


def _item(event: Mapping[str, Any]) -> Mapping[str, Any]:
    value = event.get("item")
    return value if isinstance(value, Mapping) else {}


def _checkpoint_topic_ids(text: str) -> list[str]:
    return re.findall(r"topic:[A-Za-z0-9_-]+", text)


def _is_brief_checkpoint(text: str) -> tuple[bool, str | None]:
    """Validate the explicit Creator→Brief checkpoint marker in an agent message."""

    if HANDOFF_SCHEMA not in text or "evidence-backed-content-brief:host-reasoning" not in text:
        return False, None
    if not all(field in text for field in ("topic_id", "topic_snapshot", "generated_at", "partial", "stale")):
        return False, None
    ids = _checkpoint_topic_ids(text)
    if not ids:
        return False, None
    # The checkpoint must expose the same exact topic identity for the handoff
    # and topic snapshot. Two identical visible IDs are the trace-level proof.
    for topic_id in sorted(set(ids)):
        if ids.count(topic_id) >= 2:
            return True, topic_id
    return False, None


def _command_text(item: Mapping[str, Any]) -> str:
    for key in ("command", "cmd"):
        value = item.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list) and all(isinstance(part, str) for part in value):
            return " ".join(value)
    return ""


def observe_evidence(stdout: str, stderr: str = "") -> dict[str, Any]:
    mentioned: set[str] = set()
    definition_reads: set[str] = set()
    runtime_uses: set[str] = set()
    runtime_operations: set[str] = set()
    agent_message_mentions: set[str] = set()
    handoff_agent_message = False
    brief_checkpoint = False
    post_handoff_agent_message = False
    checkpoint_topic_ids: list[str] = []
    checkpoint_seen = False
    command_execution_count = 0
    agent_message_count = 0
    command_items_by_id: dict[str, Mapping[str, Any]] = {}
    anonymous_command_items: list[Mapping[str, Any]] = []

    mentioned.update(_skills_in_text(stdout))
    mentioned.update(_skills_in_text(stderr))

    for event in _iter_jsonl(stdout):
        item = _item(event)
        item_type = str(item.get("type") or "")
        joined = "\n".join(_collect_strings(item))
        mentioned.update(_skills_in_text(joined))

        if item_type == "command_execution":
            command_execution_count += 1
            command = _command_text(item)
            for skill in TOPIC_INTELLIGENCE_SKILLS:
                if _looks_like_definition_read(command, skill):
                    definition_reads.add(skill)
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                command_items_by_id[item_id] = item
            else:
                anonymous_command_items.append(item)

        elif item_type == "agent_message":
            agent_message_count += 1
            agent_message_mentions.update(_skills_in_text(joined))
            if HANDOFF_SCHEMA in joined:
                handoff_agent_message = True
            is_checkpoint, topic_id = _is_brief_checkpoint(joined)
            if is_checkpoint:
                brief_checkpoint = True
                checkpoint_seen = True
                if topic_id:
                    checkpoint_topic_ids.append(topic_id)
            elif checkpoint_seen:
                post_handoff_agent_message = True

    runtime_attempt_count = 0
    invalid_runtime_attempts: list[dict[str, Any]] = []
    failed_runtime_attempts: list[dict[str, Any]] = []
    runtime_violation_reasons: set[str] = set()
    command_items = [*command_items_by_id.values(), *anonymous_command_items]
    for item in command_items:
        command = _command_text(item)
        attempt = _runtime_attempt(command)
        if attempt is None:
            continue
        runtime_attempt_count += 1
        violations = list(attempt["violation_reasons"])
        if violations:
            invalid_runtime_attempts.append({
                **attempt,
                "status": item.get("status"),
                "exit_code": item.get("exit_code"),
            })
            runtime_violation_reasons.update(violations)
            continue

        skill = attempt.get("skill")
        operation = str(attempt["operation"])
        failure_reasons: list[str] = []
        if item.get("status") != "completed":
            failure_reasons.append("command_not_completed")
        if item.get("exit_code") != 0:
            failure_reasons.append("nonzero_exit")
        if not failure_reasons and not _validated_radar_response(
            operation, item.get("aggregated_output")
        ):
            failure_reasons.append("invalid_radar_json")
        if failure_reasons:
            failed = {
                **attempt,
                "status": item.get("status"),
                "exit_code": item.get("exit_code"),
                "violation_reasons": sorted(set(failure_reasons)),
            }
            failed_runtime_attempts.append(failed)
            runtime_violation_reasons.update(failure_reasons)
            continue

        if isinstance(skill, str):
            runtime_uses.add(skill)
            runtime_operations.add(f"{skill}:{operation}")

    return {
        "mentioned_skills": sorted(mentioned),
        "definition_read_skills": sorted(definition_reads),
        "runtime_use_skills": sorted(runtime_uses),
        "runtime_operations": sorted(runtime_operations),
        "runtime_attempt_count": runtime_attempt_count,
        "invalid_runtime_attempts": invalid_runtime_attempts,
        "failed_runtime_attempts": failed_runtime_attempts,
        "runtime_violation_reasons": sorted(runtime_violation_reasons),
        "agent_message_skill_mentions": sorted(agent_message_mentions),
        "handoff_agent_message_observed": handoff_agent_message,
        "brief_host_reasoning_checkpoint_observed": brief_checkpoint,
        "post_handoff_agent_message_observed": post_handoff_agent_message,
        "handoff_checkpoint_topic_id": (
            checkpoint_topic_ids[0]
            if len(set(checkpoint_topic_ids)) == 1
            else None
        ),
        "handoff_checkpoint_topic_ids": sorted(set(checkpoint_topic_ids)),
        "command_execution_count": command_execution_count,
        "agent_message_count": agent_message_count,
    }


def _expected_workflow(case: Mapping[str, Any]) -> tuple[str, ...]:
    value = case.get("expected_workflow")
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def classify_case(case: Mapping[str, Any], evidence: Mapping[str, Any]) -> str:
    if evidence.get("invalid_runtime_attempts"):
        return "fail_noncompliant_skill_runtime_attempt_observed"
    if evidence.get("failed_runtime_attempts"):
        return "fail_unsuccessful_skill_runtime_attempt_observed"

    suite = str(case.get("suite") or "")
    runtime = set(evidence.get("runtime_use_skills") or [])
    definitions = set(evidence.get("definition_read_skills") or [])
    mentioned = set(evidence.get("mentioned_skills") or [])

    if suite == "trigger":
        expected = case.get("expected_skill")
        if expected is None:
            if runtime:
                return "fail_unexpected_skill_runtime_observed"
            return "pass_no_skill_runtime_observed"

        expected = str(expected)
        wrong_runtime = runtime - {expected}
        if expected in runtime:
            return "pass_expected_skill_runtime_observed"
        if wrong_runtime:
            return "fail_wrong_skill_runtime_observed"
        if expected in definitions:
            return "pass_expected_skill_definition_consulted"
        if expected in mentioned:
            return "expected_skill_mentioned_only"
        return "unobservable"

    if suite in SUPPORTED_QUALITY_SUITES:
        workflow = _expected_workflow(case)
        if not workflow:
            return "unobservable"

        observed_tokens: set[str] = set()
        for token in workflow:
            if token in TOPIC_INTELLIGENCE_SKILLS:
                # Quality/release workflows require observable helper use. A
                # definition read is useful trigger evidence, but cannot prove
                # that the host actually executed the live Radar workflow.
                if token in runtime:
                    observed_tokens.add(token)
            elif any(token.startswith(f"{skill}:") for skill in TOPIC_INTELLIGENCE_SKILLS):
                skill = token.split(":", 1)[0]
                if skill in runtime:
                    observed_tokens.add(token)
                elif (
                    token == f"{BRIEF_SKILL}:host-reasoning"
                    and CREATOR_SKILL in runtime
                    and evidence.get("brief_host_reasoning_checkpoint_observed") is True
                    and evidence.get("post_handoff_agent_message_observed") is True
                ):
                    observed_tokens.add(token)
            elif token == HANDOFF_SCHEMA:
                if evidence.get("handoff_agent_message_observed") is True:
                    observed_tokens.add(token)
            else:
                # Sub-workflow labels such as `:bounded-selection` currently have no
                # first-class Codex event. Do not infer them from a bare Skill mention.
                continue

        expected = set(workflow)
        if expected <= observed_tokens:
            return "pass_expected_workflow_evidence_observed"
        if expected & observed_tokens:
            return "partial_workflow_evidence_observed"
        return "unobservable"

    return "unobservable"


def grade_report(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise EvidenceGradeError(
            f"expected {INPUT_SCHEMA}, got {payload.get('schema')!r}"
        )
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise EvidenceGradeError("input report is missing cases list")
    graded_cases: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for raw in raw_cases:
        if not isinstance(raw, Mapping):
            raise EvidenceGradeError("case result must be an object")
        stdout = str(raw.get("stdout") or "")
        stderr = str(raw.get("stderr") or "")
        evidence = observe_evidence(stdout, stderr)
        grade = classify_case(raw, evidence)
        counts[grade] = counts.get(grade, 0) + 1
        graded_cases.append(
            {
                "id": raw.get("id"),
                "suite": raw.get("suite"),
                "runtime_status": raw.get("runtime_status"),
                "collector_route_observation": raw.get("route_observation"),
                "evidence_grade": grade,
                "evidence": evidence,
            }
        )

    return {
        "schema": OUTPUT_SCHEMA,
        "source_schema": INPUT_SCHEMA,
        "host": payload.get("host"),
        "skill_version": payload.get("skill_version"),
        "commit": payload.get("commit"),
        "suites": payload.get("suites"),
        "dry_run": payload.get("dry_run"),
        "strict_observation": payload.get("strict_observation"),
        "source_generated_at": payload.get("generated_at"),
        "summary": {
            "total": len(graded_cases),
            "evidence_grades": dict(sorted(counts.items())),
        },
        "cases": graded_cases,
        "grading_note": (
            "passive Skill names/file reads are discovery evidence, not invocation; "
            "every attempted Skill-local helper call must be a standalone, compliant "
            "python3 feed/sources/history invocation that completes successfully with "
            "validated Radar JSON; any noncompliant or unsuccessful attempt fails the "
            "case, and handoff use requires the schema in an agent message"
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Conservatively grade an ati.host-eval.v1 trace report"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise EvidenceGradeError("input report must be a JSON object")
        result = grade_report(payload)
    except (OSError, json.JSONDecodeError, EvidenceGradeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(str(args.output))
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

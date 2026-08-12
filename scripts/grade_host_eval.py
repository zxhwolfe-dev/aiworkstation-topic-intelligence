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
    "topic-intelligence",
)
CREATOR_SKILL = TOPIC_INTELLIGENCE_SKILLS[0]
BRIEF_SKILL = TOPIC_INTELLIGENCE_SKILLS[1]
UNIFIED_SKILL = TOPIC_INTELLIGENCE_SKILLS[2]
HELPER_BASENAME = "topic_radar_client.py"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
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
SUPPORTED_QUALITY_SUITES = {"quality", "v0.2.1", "v0.3.0"}
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


def _named_skill_for_helper_path(path: str) -> str | None:
    """Return the apparent Skill name without granting fixture ownership."""

    normalized = path.replace("\\", "/").rstrip("/")
    match = re.search(
        r"/(creator-topic-opportunity-research|evidence-backed-content-brief|topic-intelligence)/scripts/"
        + re.escape(HELPER_BASENAME)
        + r"$",
        normalized,
    )
    if not match:
        return None
    return match.group(1)


def _skill_for_helper_path(
    path: str,
    fixture_roots: Mapping[str, str] | None,
) -> tuple[str | None, list[str]]:
    """Require exact ownership by this case's recorded Skill fixture."""

    normalized = path.replace("\\", "/").rstrip("/")
    apparent_skill = _named_skill_for_helper_path(normalized)
    # Unit-level callers may omit roots and use the deterministic /skills test
    # fixture. All real reports pass their recorded roots through grade_report.
    roots = (
        dict(fixture_roots)
        if fixture_roots is not None
        else {
            skill: f"/skills/{skill}" for skill in TOPIC_INTELLIGENCE_SKILLS
        }
    )
    for skill, root in roots.items():
        if skill not in TOPIC_INTELLIGENCE_SKILLS or not isinstance(root, str):
            continue
        expected = root.replace("\\", "/").rstrip("/") + f"/scripts/{HELPER_BASENAME}"
        if normalized == expected:
            return skill, []

    violations = ["runtime_outside_case_fixture"]
    if apparent_skill is None:
        violations.insert(0, "non_skill_local_helper")
    elif apparent_skill not in roots:
        violations.insert(0, "unavailable_skill_runtime")
    else:
        violations.insert(0, "non_skill_local_helper")
    return apparent_skill, violations


def _runtime_attempt(
    command: str,
    fixture_roots: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
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

    skill, path_violations = _skill_for_helper_path(helper_path, fixture_roots)
    violations: list[str] = list(path_violations)
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
        "request_arguments": list(arguments),
        "operation": operation,
        "topic_id": (
            arguments[-1]
            if operation == "history" and arguments
            else None
        ),
        "violation_reasons": sorted(set(violations)),
    }


def _radar_response_topic_ids(operation: str, output: str) -> list[str]:
    payload = json.loads(output)
    if operation == "feed":
        return [
            str(item["id"])
            for item in payload.get("items", [])
            if isinstance(item, Mapping) and isinstance(item.get("id"), str)
        ]
    if operation == "history" and isinstance(payload.get("topic_id"), str):
        return [str(payload["topic_id"])]
    return []


def _runtime_request_signature(attempt: Mapping[str, Any]) -> tuple[Any, ...]:
    """Return a helper-path-independent signature for one Radar request."""

    arguments = list(attempt.get("request_arguments") or [])
    while arguments and str(arguments[0]).startswith("--timeout"):
        option = str(arguments.pop(0))
        if option == "--timeout" and arguments:
            arguments.pop(0)
    operation = str(attempt.get("operation") or "")
    if arguments and arguments[0] == operation:
        arguments.pop(0)

    if operation == "feed":
        normalized: list[tuple[str, str | None]] = []
        while arguments:
            option = str(arguments.pop(0))
            if option == "--new-only":
                normalized.append((option, None))
                continue
            if "=" in option:
                name, value = option.split("=", 1)
            else:
                name = option
                value = str(arguments.pop(0)) if arguments else ""
            normalized.append((name, value))
        return (attempt.get("skill"), operation, tuple(sorted(normalized)))
    return (attempt.get("skill"), operation, tuple(str(value) for value in arguments))


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


def _json_objects_in_text(text: str) -> Iterable[Mapping[str, Any]]:
    """Decode embedded JSON objects without treating surrounding prose as data."""

    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            yield value


def _valid_handoff_checkpoint(text: str) -> tuple[bool, str | None]:
    """Validate handoff identity and freshness in one agent message."""

    if HANDOFF_SCHEMA not in text:
        return False, None
    for value in _json_objects_in_text(text):
        if value.get("schema") != HANDOFF_SCHEMA:
            continue
        topic_id = value.get("topic_id")
        snapshot = value.get("snapshot")
        topic_snapshot = value.get("topic_snapshot")
        if not (
            isinstance(topic_id, str)
            and topic_id.strip()
            and isinstance(snapshot, Mapping)
            and isinstance(topic_snapshot, Mapping)
            and topic_snapshot.get("id") == topic_id
            and isinstance(snapshot.get("generated_at"), str)
            and bool(str(snapshot["generated_at"]).strip())
            and isinstance(snapshot.get("partial"), bool)
            and isinstance(snapshot.get("stale"), bool)
        ):
            continue
        return True, topic_id
    return False, None


def _is_brief_checkpoint(text: str) -> tuple[bool, str | None]:
    """Validate the explicit Creator→Brief checkpoint marker in an agent message."""

    valid, topic_id = _valid_handoff_checkpoint(text)
    return (
        valid and "evidence-backed-content-brief:host-reasoning" in text,
        topic_id,
    )


def _command_text(item: Mapping[str, Any]) -> str:
    for key in ("command", "cmd"):
        value = item.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list) and all(isinstance(part, str) for part in value):
            return " ".join(value)
    return ""


def observe_evidence(
    stdout: str,
    stderr: str = "",
    *,
    skill_fixture_roots: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    mentioned: set[str] = set()
    definition_reads: set[str] = set()
    runtime_uses: set[str] = set()
    runtime_operations: set[str] = set()
    runtime_operation_counts: dict[str, int] = {}
    agent_message_mentions: set[str] = set()
    handoff_schema_mention = False
    handoff_agent_message = False
    brief_checkpoint = False
    post_handoff_agent_message = False
    checkpoint_topic_ids: list[str] = []
    checkpoint_seen = False
    command_execution_count = 0
    agent_message_count = 0
    command_items_by_id: dict[str, tuple[int, Mapping[str, Any]]] = {}
    anonymous_command_items: list[tuple[int, Mapping[str, Any]]] = []
    agent_message_positions: list[int] = []
    checkpoint_positions: list[int] = []
    agent_message_texts: list[str] = []

    mentioned.update(_skills_in_text(stdout))
    mentioned.update(_skills_in_text(stderr))

    for position, event in enumerate(_iter_jsonl(stdout)):
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
                command_items_by_id[item_id] = (position, item)
            else:
                anonymous_command_items.append((position, item))

        elif item_type == "agent_message":
            agent_message_count += 1
            agent_message_positions.append(position)
            agent_message_texts.append(joined)
            agent_message_mentions.update(_skills_in_text(joined))
            if HANDOFF_SCHEMA in joined:
                handoff_schema_mention = True
            valid_handoff, _ = _valid_handoff_checkpoint(joined)
            if valid_handoff:
                handoff_agent_message = True
            is_checkpoint, topic_id = _is_brief_checkpoint(joined)
            if is_checkpoint:
                brief_checkpoint = True
                checkpoint_seen = True
                checkpoint_positions.append(position)
                if topic_id:
                    checkpoint_topic_ids.append(topic_id)
            elif checkpoint_seen:
                post_handoff_agent_message = True

    runtime_attempt_count = 0
    invalid_runtime_attempts: list[dict[str, Any]] = []
    failed_runtime_attempts: list[dict[str, Any]] = []
    successful_runtime_attempts: list[dict[str, Any]] = []
    successful_request_signatures: set[tuple[Any, ...]] = set()
    runtime_violation_reasons: set[str] = set()
    runtime_attempt_skills: set[str] = set()
    runtime_positions_by_skill: dict[str, list[int]] = {
        skill: [] for skill in TOPIC_INTELLIGENCE_SKILLS
    }
    command_items = [*command_items_by_id.values(), *anonymous_command_items]
    for position, item in command_items:
        command = _command_text(item)
        attempt = _runtime_attempt(command, skill_fixture_roots)
        if attempt is None:
            continue
        runtime_attempt_count += 1
        attempted_skill = attempt.get("skill")
        if isinstance(attempted_skill, str):
            runtime_attempt_skills.add(attempted_skill)
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

        request_signature = _runtime_request_signature(attempt)
        if request_signature in successful_request_signatures:
            invalid_runtime_attempts.append({
                **attempt,
                "status": item.get("status"),
                "exit_code": item.get("exit_code"),
                "violation_reasons": ["duplicate_runtime_request"],
            })
            runtime_violation_reasons.add("duplicate_runtime_request")
            continue
        successful_request_signatures.add(request_signature)

        if isinstance(skill, str):
            runtime_uses.add(skill)
            runtime_operations.add(f"{skill}:{operation}")
            operation_key = f"{skill}:{operation}"
            runtime_operation_counts[operation_key] = runtime_operation_counts.get(operation_key, 0) + 1
            runtime_positions_by_skill[skill].append(position)
            successful_runtime_attempts.append({
                **attempt,
                "status": item.get("status"),
                "exit_code": item.get("exit_code"),
                "event_position": position,
                "response_topic_ids": _radar_response_topic_ids(
                    operation, str(item.get("aggregated_output") or "")
                ),
            })

    post_runtime_agent_message_skills = sorted(
        skill
        for skill, positions in runtime_positions_by_skill.items()
        if positions and any(
            message_position > max(positions)
            for message_position in agent_message_positions
        )
    )
    creator_runtime_before_checkpoint = bool(
        runtime_positions_by_skill[CREATOR_SKILL]
        and checkpoint_positions
        and min(checkpoint_positions) > max(runtime_positions_by_skill[CREATOR_SKILL])
    )

    return {
        "mentioned_skills": sorted(mentioned),
        "definition_read_skills": sorted(definition_reads),
        "runtime_use_skills": sorted(runtime_uses),
        "runtime_operations": sorted(runtime_operations),
        "runtime_operation_counts": dict(sorted(runtime_operation_counts.items())),
        "runtime_attempt_count": runtime_attempt_count,
        "runtime_attempt_skills": sorted(runtime_attempt_skills),
        "successful_runtime_attempts": successful_runtime_attempts,
        "invalid_runtime_attempts": invalid_runtime_attempts,
        "failed_runtime_attempts": failed_runtime_attempts,
        "runtime_violation_reasons": sorted(runtime_violation_reasons),
        "agent_message_skill_mentions": sorted(agent_message_mentions),
        "handoff_schema_mention_observed": handoff_schema_mention,
        "handoff_agent_message_observed": handoff_agent_message,
        "brief_host_reasoning_checkpoint_observed": brief_checkpoint,
        "post_handoff_agent_message_observed": post_handoff_agent_message,
        "handoff_checkpoint_topic_id": (
            checkpoint_topic_ids[0]
            if len(set(checkpoint_topic_ids)) == 1
            else None
        ),
        "handoff_checkpoint_topic_ids": sorted(set(checkpoint_topic_ids)),
        "creator_runtime_before_checkpoint": creator_runtime_before_checkpoint,
        "post_runtime_agent_message_skills": post_runtime_agent_message_skills,
        "command_execution_count": command_execution_count,
        "agent_message_count": agent_message_count,
        "agent_message_texts": agent_message_texts,
    }


def _expected_workflow(case: Mapping[str, Any]) -> tuple[str, ...]:
    value = case.get("expected_workflow")
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _skill_visibility_contract_is_valid(case: Mapping[str, Any]) -> bool:
    installed = case.get("installed_skills")
    if (
        not isinstance(installed, list)
        or not installed
        or not all(isinstance(item, str) for item in installed)
        or len(installed) != len(set(installed))
        or any(item not in TOPIC_INTELLIGENCE_SKILLS for item in installed)
    ):
        return False
    source_commit = case.get("skill_source_commit")
    report_commit = case.get("_report_commit")
    roots = case.get("skill_fixture_roots")
    manifest = case.get("skill_fixture_manifest")
    return bool(
        case.get("skill_environment_isolated") is True
        and case.get("codex_home_preserved") is True
        and case.get("authentication_material_copied") is False
        and case.get("authentication_content_recorded") is False
        and isinstance(source_commit, str)
        and COMMIT_RE.fullmatch(source_commit)
        and source_commit == report_commit
        and isinstance(roots, Mapping)
        and set(roots) == set(installed)
        and all(
            isinstance(roots.get(skill), str) and bool(str(roots[skill]).strip())
            for skill in installed
        )
        and isinstance(manifest, Mapping)
        and set(manifest) == set(installed)
        and all(isinstance(manifest.get(skill), list) for skill in installed)
        and case.get("execution_workspace_isolated") is True
        and isinstance(case.get("execution_workspace_root"), str)
        and bool(str(case.get("execution_workspace_root")).strip())
        and case.get("execution_workspace_neutral") is True
        and case.get("execution_workspace_clean_before") is True
        and case.get("execution_workspace_clean_after") is True
        and case.get("source_worktree_used_as_host_cwd") is False
        and case.get("source_worktree_clean_after") is True
    )


def _provided_topic_snapshot(case: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return a validated current-task snapshot supplied by the eval input."""

    value = case.get("provided_topic_snapshot")
    if not isinstance(value, Mapping):
        return None
    topic_id = value.get("id")
    generated_at = value.get("generated_at")
    evidence = value.get("evidence")
    if (
        not isinstance(topic_id, str)
        or not topic_id.strip()
        or not isinstance(generated_at, str)
        or not generated_at.strip()
        or not isinstance(value.get("partial"), bool)
        or not isinstance(value.get("stale"), bool)
        or not isinstance(value.get("title"), str)
        or not str(value["title"]).strip()
        or not isinstance(value.get("summary"), str)
        or not str(value["summary"]).strip()
        or not isinstance(evidence, list)
    ):
        return None
    return value


def _complete_case_lifecycle(case: Mapping[str, Any]) -> bool:
    return bool(
        case.get("runtime_status") == "completed"
        and case.get("exit_code") == 0
        and case.get("timed_out") is False
        and case.get("stdout_truncated") is False
        and case.get("stderr_truncated") is False
        and case.get("worktree_clean_after") is True
        and case.get("execution_workspace_clean_after") is True
        and case.get("source_worktree_used_as_host_cwd") is False
        and case.get("trace_integrity_status") in {
            "complete_clean", "complete_after_recovery"
        }
        and case.get("final_agent_message_observed") is True
    )


def _quality_workflow_token_observed(
    token: str,
    case: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> bool:
    runtime = set(evidence.get("runtime_use_skills") or [])
    operations = set(evidence.get("runtime_operations") or [])
    installed = set(case.get("installed_skills") or [])
    lifecycle_complete = _complete_case_lifecycle(case)

    if token == f"{UNIFIED_SKILL}:selection":
        counts = evidence.get("runtime_operation_counts") or {}
        return bool(
            f"{UNIFIED_SKILL}:feed" in operations
            and counts.get(f"{UNIFIED_SKILL}:feed") == 1
            and lifecycle_complete
            and evidence.get("post_runtime_agent_message_skills")
        )
    if token == f"{UNIFIED_SKILL}:brief":
        supplied = _provided_topic_snapshot(case)
        attempts = evidence.get("successful_runtime_attempts") or []
        history_attempts_match = bool(
            supplied
            and all(
                attempt.get("operation") != "history"
                or (
                    attempt.get("topic_id") == supplied["id"]
                    and attempt.get("response_topic_ids") == [supplied["id"]]
                )
                for attempt in attempts
                if isinstance(attempt, Mapping)
            )
        )
        supplied_snapshot_observed = bool(
            supplied
            and evidence.get("agent_message_texts")
            and supplied["id"] in evidence["agent_message_texts"][-1]
        )
        if supplied is not None:
            return bool(
                lifecycle_complete
                and supplied_snapshot_observed
                and f"{UNIFIED_SKILL}:feed" not in operations
                and history_attempts_match
            )
        return bool(
            lifecycle_complete
            and evidence.get("agent_message_count", 0) > 0
            and bool({
                f"{UNIFIED_SKILL}:history",
                f"{UNIFIED_SKILL}:sources",
            } & operations)
            and f"{UNIFIED_SKILL}:feed" not in operations
            and evidence.get("post_runtime_agent_message_skills")
        )
    if token == f"{UNIFIED_SKILL}:selection-and-brief":
        counts = evidence.get("runtime_operation_counts") or {}
        feed_ids = {
            topic_id
            for attempt in evidence.get("successful_runtime_attempts") or []
            if isinstance(attempt, Mapping)
            and attempt.get("operation") == "feed"
            for topic_id in attempt.get("response_topic_ids") or []
        }
        final_message = (
            evidence["agent_message_texts"][-1]
            if evidence.get("agent_message_texts")
            else ""
        )
        return bool(
            counts.get(f"{UNIFIED_SKILL}:feed") == 1
            and any(topic_id in final_message for topic_id in feed_ids)
            and lifecycle_complete
            and evidence.get("post_runtime_agent_message_skills")
        )
    if token == f"{UNIFIED_SKILL}:no-radar":
        return bool(not evidence.get("runtime_attempt_count") and lifecycle_complete)

    if token in TOPIC_INTELLIGENCE_SKILLS:
        return token in runtime
    if token == f"{BRIEF_SKILL}:bounded-selection":
        return f"{BRIEF_SKILL}:feed" in operations
    if token == f"{BRIEF_SKILL}:public-radar":
        return bool({
            f"{BRIEF_SKILL}:feed",
            f"{BRIEF_SKILL}:history",
            f"{BRIEF_SKILL}:sources",
        } & operations)
    if token == f"{BRIEF_SKILL}:host-reasoning":
        brief_only = bool(
            installed == {BRIEF_SKILL}
            and BRIEF_SKILL in runtime
            and BRIEF_SKILL in set(
                evidence.get("post_runtime_agent_message_skills") or []
            )
            and lifecycle_complete
        )
        composite = bool(
            CREATOR_SKILL in runtime
            and evidence.get("brief_host_reasoning_checkpoint_observed") is True
            and evidence.get("creator_runtime_before_checkpoint") is True
            and evidence.get("post_handoff_agent_message_observed") is True
            and lifecycle_complete
        )
        return brief_only or composite
    if token == HANDOFF_SCHEMA:
        return evidence.get("handoff_agent_message_observed") is True
    return False


def classify_case(case: Mapping[str, Any], evidence: Mapping[str, Any]) -> str:
    suite = str(case.get("suite") or "")
    if suite in SUPPORTED_QUALITY_SUITES:
        if not _skill_visibility_contract_is_valid(case):
            return "fail_missing_skill_visibility_contract"
        unavailable = set(evidence.get("runtime_attempt_skills") or []) - set(
            case.get("installed_skills") or []
        )
        if unavailable:
            return "fail_unavailable_skill_runtime_observed"
    if evidence.get("invalid_runtime_attempts"):
        return "fail_noncompliant_skill_runtime_attempt_observed"
    if evidence.get("failed_runtime_attempts"):
        return "fail_unsuccessful_skill_runtime_attempt_observed"

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
            if _quality_workflow_token_observed(token, case, evidence):
                observed_tokens.add(token)

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
        roots = raw.get("skill_fixture_roots")
        evidence = observe_evidence(
            stdout,
            stderr,
            skill_fixture_roots=roots if isinstance(roots, Mapping) else {},
        )
        case_contract = dict(raw)
        case_contract["_report_commit"] = payload.get("commit")
        grade = classify_case(case_contract, evidence)
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
            "validated Radar JSON; duplicate successful requests, noncompliant calls, "
            "or unsuccessful attempts fail the "
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

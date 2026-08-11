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
RADAR_OPERATIONS = {"feed", "sources", "history"}
SHELL_EXECUTABLES = {"bash", "dash", "sh", "zsh"}
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


def _runtime_invocation(command: str, skill: str) -> str | None:
    """Return the allowed Radar operation for a real Python helper invocation."""

    tokens = _command_tokens(command)
    if not tokens or any(any(character in token for character in ";|&<>`$") for token in tokens):
        return None
    marker = f"/{skill}/scripts/topic_radar_client.py"
    executable = tokens[0].replace("\\", "/").rsplit("/", 1)[-1]
    if executable != "python3":
        return None
    helper = tokens[1].replace("\\", "/") if len(tokens) > 1 else ""
    if not helper.endswith(marker):
        return None
    arguments = tokens[2:]
    if "-h" in arguments or "--help" in arguments or "--base-url" in arguments:
        return None
    return _validated_operation_arguments(arguments)


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


def _completed_successfully(item: Mapping[str, Any]) -> bool:
    return item.get("status") == "completed" and item.get("exit_code") == 0


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
    command_execution_count = 0
    agent_message_count = 0

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
                operation = _runtime_invocation(command, skill)
                if (
                    operation is not None
                    and _completed_successfully(item)
                    and _validated_radar_response(operation, item.get("aggregated_output"))
                ):
                    runtime_uses.add(skill)
                    runtime_operations.add(f"{skill}:{operation}")

        elif item_type == "agent_message":
            agent_message_count += 1
            agent_message_mentions.update(_skills_in_text(joined))
            if HANDOFF_SCHEMA in joined:
                handoff_agent_message = True

    return {
        "mentioned_skills": sorted(mentioned),
        "definition_read_skills": sorted(definition_reads),
        "runtime_use_skills": sorted(runtime_uses),
        "runtime_operations": sorted(runtime_operations),
        "agent_message_skill_mentions": sorted(agent_message_mentions),
        "handoff_agent_message_observed": handoff_agent_message,
        "command_execution_count": command_execution_count,
        "agent_message_count": agent_message_count,
    }


def _expected_workflow(case: Mapping[str, Any]) -> tuple[str, ...]:
    value = case.get("expected_workflow")
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def classify_case(case: Mapping[str, Any], evidence: Mapping[str, Any]) -> str:
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
            "runtime use requires a successful python3 invocation of a Skill-local helper "
            "feed/sources/history operation plus validated JSON output, and handoff use "
            "requires the schema in an agent message"
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

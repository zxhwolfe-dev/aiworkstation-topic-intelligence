#!/usr/bin/env python3
"""Conservatively grade Topic Intelligence host-eval traces.

`run_host_evals.py` is a collector.  This module performs a second-stage evidence
classification that deliberately distinguishes passive Skill discovery from
stronger runtime/workflow evidence.  Codex `exec --json` does not currently
expose a first-class "Skill X triggered" event, so a Skill name appearing in a
file path must never be treated as proof of invocation by itself.
"""

from __future__ import annotations

import argparse
import json
import re
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
    lowered = text.replace("\\", "/")
    if skill not in lowered:
        return False
    return any(
        marker in lowered
        for marker in (
            f"/{skill}/SKILL.md",
            f"/{skill}/agents/openai.yaml",
            f"/{skill}/references/handoff-contract.md",
        )
    )


def _looks_like_runtime_use(text: str, skill: str) -> bool:
    normalized = text.replace("\\", "/")
    if skill not in normalized:
        return False
    return f"/{skill}/scripts/topic_radar_client.py" in normalized


def _item(event: Mapping[str, Any]) -> Mapping[str, Any]:
    value = event.get("item")
    return value if isinstance(value, Mapping) else {}


def observe_evidence(stdout: str, stderr: str = "") -> dict[str, Any]:
    mentioned: set[str] = set()
    definition_reads: set[str] = set()
    runtime_uses: set[str] = set()
    agent_message_mentions: set[str] = set()
    handoff_agent_message = False
    command_execution_count = 0
    agent_message_count = 0

    mentioned.update(_skills_in_text(stdout))
    mentioned.update(_skills_in_text(stderr))

    for event in _iter_jsonl(stdout):
        item = _item(event)
        item_type = str(item.get("type") or "")
        strings = list(_collect_strings(item))
        joined = "\n".join(strings)
        mentioned.update(_skills_in_text(joined))

        if item_type == "command_execution":
            command_execution_count += 1
            for skill in TOPIC_INTELLIGENCE_SKILLS:
                if _looks_like_definition_read(joined, skill):
                    definition_reads.add(skill)
                if _looks_like_runtime_use(joined, skill):
                    runtime_uses.add(skill)

        elif item_type == "agent_message":
            agent_message_count += 1
            agent_message_mentions.update(_skills_in_text(joined))
            if HANDOFF_SCHEMA in joined:
                handoff_agent_message = True

    # Some Codex versions/tool wrappers expose command records outside item.completed.
    # Inspect each parsed event conservatively as a fallback, but never upgrade a plain
    # mention into runtime evidence unless the Skill-local helper path is present.
    for event in _iter_jsonl(stdout):
        event_text = "\n".join(_collect_strings(event))
        for skill in TOPIC_INTELLIGENCE_SKILLS:
            if _looks_like_definition_read(event_text, skill):
                definition_reads.add(skill)
            if _looks_like_runtime_use(event_text, skill):
                runtime_uses.add(skill)

    return {
        "mentioned_skills": sorted(mentioned),
        "definition_read_skills": sorted(definition_reads),
        "runtime_use_skills": sorted(runtime_uses),
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

    if suite == "quality":
        workflow = _expected_workflow(case)
        if not workflow:
            return "unobservable"

        observed_tokens: set[str] = set()
        for token in workflow:
            if token in TOPIC_INTELLIGENCE_SKILLS:
                if token in runtime or token in definitions:
                    observed_tokens.add(token)
            elif token == HANDOFF_SCHEMA:
                if evidence.get("handoff_agent_message_observed") is True:
                    observed_tokens.add(token)
            else:
                # Sub-workflow labels such as `:bounded-selection` currently have no
                # first-class Codex event.  Do not infer them from a bare Skill mention.
                if token in runtime:
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
        "source_generated_at": payload.get("generated_at"),
        "summary": {
            "total": len(graded_cases),
            "evidence_grades": dict(sorted(counts.items())),
        },
        "cases": graded_cases,
        "grading_note": (
            "passive Skill names/file reads are discovery evidence, not invocation; "
            "runtime use requires an observed Skill-local helper path, and handoff use "
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

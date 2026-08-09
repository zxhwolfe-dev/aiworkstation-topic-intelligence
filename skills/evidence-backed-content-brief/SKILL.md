---
name: evidence-backed-content-brief
description: Turn a live AI Workstation Global Topic Radar topic into an evidence-aware content strategy and research-ready brief using the existing feed, history, and topic-insight contracts. Use when the user wants to evaluate or select a current topic and plan its angle, audience, format, hook, verification, or research handoff. Do not use when the user already supplied the complete material and only wants rewriting, scripting, summarization, translation, or generic title generation without a live-topic decision.
---

# Evidence-Backed Content Brief

Use this Skill when the user wants to turn a **current Radar topic** into a practical content plan.

This Skill does not create a second topic-analysis backend. Reuse the existing Topic Radar `/insight` output whenever a server-known topic is available.

## Required live contract

Use:

- `GET /api/v1/ai/topic-radar/feed`;
- `GET /api/v1/ai/topic-radar/history?topic_id=...` when movement matters;
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`.

### Self-contained runtime

This Skill package is self-contained for local/Codex execution. Resolve the bundled helper relative to this `SKILL.md`:

```text
scripts/topic_radar_client.py
```

Do not assume a repository-root helper, sibling checkout, or `../akaiagents` exists. A native HTTP/MCP-capable host may call the same public contract directly.

The `/insight` endpoint accepts a server-known `topic_id`. Do not send arbitrary user prompts or raw copied articles to it.

## Live topic evidence is mandatory

A brief about a **current** Radar topic must be anchored to a topic resolved from live Topic Radar data during the current task, to a valid current-task Topic Opportunity handoff, or to an equivalent current Topic Radar response explicitly supplied by the user/native host connection.

Do not search sibling repositories or local storage for a substitute when the live contract is unavailable. In particular, never use old Topic Radar snapshots, SQLite databases, fixtures, cached JSON exports, test captures, generated reports, logs, or other persisted local artifacts to establish that a topic is current.

`../akaiagents` may contain implementation code and historical/local data. Its data files are not a fallback source for this Skill.

If the live feed cannot be reached and the user has not supplied a current server-known topic plus current evidence:

1. do not produce a current-topic verdict or evidence-backed angle;
2. do not recover a topic from local files or model memory;
3. explain that live Topic Radar evidence is unavailable in this execution environment;
4. offer a clearly labeled blank/research template or explain what fields would be filled once live evidence is available.

A network-restricted sandbox is an unavailable-live-data state, not permission to use stale local evidence.

## Choose the input mode

Use exactly one of these entry modes before calling `/insight`.

### Mode A — current-task Topic Opportunity handoff

If `creator-topic-opportunity-research` has already selected the topic in the current task, accept the handoff defined by:

```text
references/handoff-contract.md
```

Expected schema:

```text
ati.topic-opportunity-handoff.v1
```

Accept it only when:

- the handoff was produced in this current task/session workflow;
- `topic_id` is a non-empty string and exactly equals `topic_snapshot.id`;
- `snapshot.generated_at`, `partial`, `stale`, and other material freshness fields are visible;
- `stale` is not true;
- `partial=true` does not remove evidence required for the requested claim;
- it is not a loaded cache, saved file, old log, prior-task artifact, or model-memory reconstruction.

When valid, **do not re-identify the topic from its title**. Continue with the exact handed-off `topic_id`, call `/history` only when movement matters, then call `/insight` for that selected topic.

Refresh live feed evidence instead of trusting the handoff when it is stale, materially partial, missing freshness/identity fields, from another task, or the user explicitly asks for a new current re-check.

### Mode B — user supplies a current topic ID or name

If the user supplies a topic ID, verify that the topic still exists in live Radar data before relying on it, unless the user also supplied the current Topic Radar response containing that ID.

If the user supplies only a topic name:

1. query `/feed` with `q`;
2. show or choose the closest server-known topic only when identity is reasonably clear;
3. if multiple materially different clusters match, ask the user only when the choice would change the brief; otherwise explain which one you selected.

Feed topic cards expose the stable identifier as `id`, not `topic_id`. When calling `/history` or `/insight`, pass that exact feed `id` value as the request's `topic_id`. Those endpoint responses expose the same identity under `topic_id`.

### Mode C — user asks this Skill to pick one topic, but Opportunity Research is unavailable

When the user asks “pick the best current topic for me”:

1. if `creator-topic-opportunity-research` is installed/available, prefer that Skill to perform opportunity research and consume its formal handoff;
2. if it is not available, this Skill may perform a **bounded standalone selection pass** so the standalone Skill remains useful;
3. use one bounded live `/feed` query with the user's relevant constraints, a recent `max_age_hours`, and a small candidate limit (normally no more than 5);
4. select at most one candidate using the Radar-provided `opportunity_score`, `trend_stage`, freshness, evidence breadth, and user constraints;
5. never invent a second score or recreate a broad cross-market opportunity study;
6. do not call `/insight` for every candidate—call it only after one topic is selected;
7. if no candidate is useful or evidence is too weak, say so instead of forcing a selection.

If the request specifically depends on multi-market timing, saturation, or broad opportunity comparison and Opportunity Research is unavailable, state that the full opportunity-research workflow is unavailable and keep any fallback comparison narrowly scoped and explicitly limited.

## Check freshness and evidence

Before producing the brief, inspect the parent live feed/handoff context:

- `generated_at`;
- `partial`;
- `stale`;
- `snapshot_age_seconds`;
- `refreshing`;
- topic `evidence`;
- topic `trend`;
- `source_status` when relevant.

If the snapshot is stale/partial, carry that caveat into the brief and refresh first when the limitation is material to the requested decision.

Use `/history` when “why now” depends on acceleration, persistence, or cooling.

When `refreshing=true`, a subsequent history request may include a newly persisted point that was not yet represented in the parent feed's `trend.history_points`. Compare timestamps and identity; do not require exact point-count equality across sequential requests during refresh.

A source status of `empty` means no current items were returned by that source in the snapshot; it is not automatically a connector failure. A source status that explicitly reports an error/outage is a coverage limitation and should be surfaced when relevant.

## Reuse existing Topic Insight

The current insight contract can provide:

- `verdict`;
- `can_make_short_video`;
- `content_readiness`;
- `editorial_stage`;
- `recommended_format`;
- `target_audience`;
- `audience_payoff`;
- `why_now`;
- `why_this_can_work`;
- `attention_points`;
- `recommended_angle_index`;
- exactly three `angles`;
- `short_video_handoff`;
- `watchouts`;
- `generation_quality`;
- optional `score_breakdown`;
- provider/model metadata.

Each angle can include:

- `title`;
- `hook`;
- `format`;
- `angle_type`;
- `viewer_question`;
- `core_conflict`;
- `promise`;
- `narrative_beats`;
- `opening_3_seconds`;
- `visual_moments`;
- `platform_fit`;
- `research_questions`;
- `search_queries`;
- `preferred_source_types`;
- `must_verify`;
- `avoid_claims`;
- `fact_basis`;
- `unsupported_assumptions`.

Do not regenerate these fields just to make them sound different. Adapt and prioritize them for the user's goal.

## Insight is analysis, not evidence

The `/insight` result is model-generated analysis over a known Radar topic.

Therefore:

- `verdict`, `why_now`, hooks, audience, and recommended angle are **analysis/recommendations**;
- Topic Radar evidence/timestamps/observed metrics remain the source facts;
- `fact_basis` may point to supporting facts, but do not expand it with invented specifics;
- `unsupported_assumptions` must remain visible when they matter.

Never present an insight sentence as independently verified merely because it came from the server.

## Choose the angle

Default to `recommended_angle_index` only when it fits the user's platform, audience, and goal.

Override it when the user has a concrete constraint, and explain why.

Useful selection criteria:

- strongest evidence basis;
- clearest audience payoff;
- platform fit;
- feasibility of required visuals;
- number/severity of `must_verify` items;
- avoidable speculation;
- differentiation from generic coverage.

Do not choose the most sensational angle when its verification burden is materially worse.

## Produce a research-ready brief

A strong final brief should contain:

### Topic

- title / stable topic ID;
- current stage and opportunity score;
- snapshot freshness.

### Recommendation

- make / conditional / watch;
- selected format;
- target audience;
- audience payoff.

### Why now

Separate observed Radar facts from model/Skill interpretation.

### Selected angle

Include angle title, hook, opening 3 seconds, viewer question, core conflict, promise, narrative beats, and platform fit.

### Visual plan

Use `visual_moments` and `short_video_handoff.visual_material_needs`. Distinguish must-have factual visuals from optional illustrative B-roll.

### Research handoff

Preserve `research_questions`, `search_queries`, `preferred_source_types`, `must_verify`, and known unknowns.

### Claims boundary

Show `avoid_claims` explicitly. Do not hide them in a generic disclaimer.

### Alternatives

Briefly show the other two existing angles when useful instead of inventing ten more.

## Degraded or unavailable insight handling

If `generation_quality=degraded`:

1. say so;
2. rely more heavily on live source facts;
3. do not fill missing creative fields with confident invented detail;
4. preserve watchouts and verification requirements.

If `/insight` is unavailable **but live feed/history evidence is available**, you may provide an evidence-based skeleton, clearly labeling the creative plan as your own analysis rather than server insight.

If the live feed itself is unavailable, do not use local snapshots to create a current-topic brief. Provide only a template or blocked-state explanation.

## Quality rules

- Never call `/insight` with arbitrary raw text.
- Never call `/insight` across a broad candidate list before selecting one topic.
- Never use local/sibling-repository snapshots, fixtures, databases, exports, logs, or persisted handoffs as fallback current evidence.
- Never use insight output to overwrite contradictory source facts.
- Never omit `must_verify` or `avoid_claims` when present.
- Never claim a short video will perform because `can_make_short_video=yes`.
- Never convert `editorial_stage` into a guaranteed viral stage.
- Never confuse feed `id` with a separate topic identity; it is the value handed to `topic_id` parameters.
- Never treat normal point-count changes during `refreshing=true` as a contradiction without checking timestamps.
- Never invent a fallback ranking score when selecting a topic in standalone mode.
- Never force a candidate when the live evidence does not support a useful choice.
- Prefer one executable angle and a research handoff over a generic list of ideas.

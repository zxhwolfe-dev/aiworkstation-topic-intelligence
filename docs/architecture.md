# Architecture

## Goal

Expose the existing AI Workstation Global Topic Radar as reusable, evidence-aware AI workflows without reproducing its backend.

## Layers

```text
User / ChatGPT / Codex
          |
          v
Topic Intelligence Skills
- intent routing
- freshness/evidence policy
- comparison reasoning
- content brief orchestration
- current-task Skill handoff
          |
          +----------------------------------+
          |                                  |
          v                                  v
native HTTP/MCP-capable host       Skill-local stdlib helper
          |                                  |
          +------------------+---------------+
                             v
AI Workstation public Topic Radar API
                             |
                             v
akaiagents / ai_topic_radar
collection, clustering, scores, history,
source health, persistence, GPT topic insight
```

## Responsibilities

### `akaiagents`

Owns the product/data plane:

- source connectors and authorization boundaries;
- public-data normalization;
- clustering and topic identity;
- deterministic opportunity scoring;
- trend/history calculations;
- caching, partial/stale behavior and source status;
- existing GPT topic insight.

### Topic Intelligence

Owns the workflow/reasoning plane:

- choose the right existing endpoint and filters;
- inspect freshness before current-state claims;
- preserve source facts separately from analysis;
- compare regions/platforms without inventing a propagation path;
- select a useful topic without inventing a second score;
- preserve selected topic identity across Skill composition;
- turn one verified topic into a research-ready content brief.

The Skills are:

- `creator-topic-opportunity-research` — compare and prioritize live topic candidates for creator/editorial decisions;
- `evidence-backed-content-brief` — convert a live Radar topic into an evidence-aware research-ready content brief.

## Standalone Skill runtime

Starting on the 0.2 development line, each Skill directory is a complete portable runtime unit for the capabilities it claims:

```text
skill-name/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/handoff-contract.md
  LICENSE                 # injected into release ZIP
```

The local helper is deliberately duplicated into each Skill package because a standalone Skill archive cannot refer to files outside its own top-level directory.

The repository-root `scripts/topic_radar_client.py` remains the development/canonical copy. Tests require both bundled copies to be byte-identical to it, preventing silent runtime drift.

A host with a native live HTTP/MCP connection can ignore the helper and call the same public API directly.

## Thin helper

The bundled/root `topic_radar_client.py` is a transport adapter, not a provider framework. It contains only:

- URL/parameter construction;
- timeout/error normalization;
- lightweight public-contract shape and topic-identity checks;
- a CLI.

It has no crawler, database, scoring, clustering, local model implementation, persisted cache, or topic-matching algorithm.

The `insight` command can trigger the **existing upstream Topic Radar GPT insight** endpoint. The helper only transports that request; it does not implement or replace the model-analysis backend.

## Skill composition contract

The Opportunity Skill and Brief Skill compose through:

```text
ati.topic-opportunity-handoff.v1
```

The contract is included identically in both Skill packages under:

```text
references/handoff-contract.md
```

The handoff carries one selected live topic plus current-task snapshot context:

```text
Opportunity Skill
  live feed/sources/history as needed
  -> select one finalist
  -> ati.topic-opportunity-handoff.v1
       topic_id
       snapshot freshness
       observed topic fields
       selection analysis / unknowns / risks
  -> Brief Skill
       preserve same topic_id
       history when movement matters
       insight for selected topic only
       research-ready brief
```

The handoff is a workflow optimization, **not persistence**. It may be consumed without redundant title-based re-identification only inside the same current task when identity and freshness are intact. A handoff loaded from another task, cache, file, log, or model memory is not current evidence and requires a new live check.

## Brief-only fallback

`evidence-backed-content-brief` remains useful when installed alone.

If the user supplies a topic name/ID, the Brief Skill resolves/verifies it against live Radar normally.

If the user asks Brief alone to choose a topic and `creator-topic-opportunity-research` is unavailable, Brief may run one bounded feed selection pass (normally no more than five candidates), choose at most one using existing Radar score/stage/freshness/evidence plus user constraints, and call insight only for the selected topic.

This fallback must **not**:

- invent another opportunity score;
- recreate a full cross-market opportunity study;
- run insight across a broad feed;
- force a candidate when evidence/constraints do not support one.

When both Skills are available, the full Opportunity → handoff → Brief workflow is preferred.

## Contract consistency

The public Topic Radar API remains the source of truth.

Two details are intentionally handled explicitly:

1. Feed topic cards expose the stable identity as `id`; history/insight accept and return the same value under the name `topic_id`.
2. When `refreshing=true`, sequential requests are not guaranteed to be one atomic generation. A later history request may contain an additional observation compared with the parent feed.

The helper enforces identity equality for history/insight responses, while Skills use freshness and timestamps to reason about legitimate between-request refresh changes.

## Evidence model

Current-topic workflows keep these layers separate:

1. **Source facts** — live feed/source/history fields from the current task.
2. **Analysis** — Skill interpretation of observed signals.
3. **Recommendations** — which topic/angle to pursue.
4. **Unknowns** — claims the contract does not establish.
5. **Risks** — stale/partial coverage, weak evidence, source gaps, verification burden.
6. **Insight analysis** — model-generated upstream Topic Insight, never promoted into independent verified facts.

No local/sibling artifact may replace live current evidence.

## Runtime dependency policy

Do not use `../akaiagents/.venv` as this repository's runtime environment.

The helper needs only Python 3.10+ standard library. If future code adds a real dependency, declare it here rather than depending on a sibling project's environment.

Do not import private `akaiagents` modules. The public API is the boundary.

## M3.1 quality validation

The 0.2 development line adds quality acceptance beyond Skill triggering:

- standalone ZIP content/runtime checks;
- extracted ZIP helper E2E against an offline local fake Radar server;
- creator-only, brief-only, and composed installation scenarios;
- stale/partial/source-empty/source-error/refreshing states;
- invalid or ambiguous topic identity;
- no-useful-candidate behavior;
- degraded/unavailable insight behavior;
- exact handoff identity preservation;
- Chinese and English task completion.

Machine-readable scenarios live in `evals/m3-skill-quality.json`.

## Future decision: Skills-only vs hosted connection

The project continues to validate Skills first.

If a target host cannot reliably access the public API from a Skill/local helper, a small hosted tool/MCP surface may be considered later. That is a transport/productization decision, not a reason to duplicate Topic Radar logic.

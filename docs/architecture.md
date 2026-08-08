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
          |
          +------------------------------+
          |                              |
          v                              v
native HTTP/MCP-capable host     thin local stdlib helper
          |                              |
          +---------------+--------------+
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
- turn one verified topic into a research-ready content brief.

### Thin helper

`scripts/topic_radar_client.py` is an optional transport adapter for local hosts.

It is intentionally not a provider framework. It has:

- URL/parameter construction;
- timeout/error normalization;
- lightweight public-contract shape and topic-identity checks;
- a CLI.

It has no crawler, database, scoring, clustering, local model implementation, or topic-matching algorithm.

The `insight` command is different from ordinary feed/sources/history reads: it can trigger the **existing upstream Topic Radar GPT insight** endpoint. The helper only transports that request; it does not implement or replace the model-analysis backend.

## Contract consistency

The public Topic Radar API remains the source of truth.

Two details are intentionally handled explicitly:

1. Feed topic cards expose the stable identity as `id`; history/insight accept and return the same value under the name `topic_id`.
2. When `refreshing=true`, sequential requests are not guaranteed to be one atomic generation. A later history request may contain an additional observation compared with the parent feed.

The helper enforces identity equality for history/insight responses, while Skills use freshness and timestamps to reason about legitimate between-request refresh changes.

## Runtime dependency policy

Do not use `../akaiagents/.venv` as this repository's runtime environment.

The helper currently needs only Python 3.10+ standard library. If future code adds a real dependency, declare it here rather than depending on a sibling project's environment.

Do not import private `akaiagents` modules. The public API is the boundary.

## Current M0

Included:

- `cross-market-trend-research`;
- `evidence-backed-content-brief`;
- thin public API helper;
- offline unit tests and minimal CI;
- contract and architecture documentation.

Not included:

- new data sources;
- new scoring;
- new persistence;
- OAuth/billing;
- hosted MCP;
- duplicated GPT analysis.

## Future decision: Skills-only vs hosted connection

M0 intentionally validates the Skills first.

If a target host cannot reliably access the public API from a Skill/local helper, add a small hosted tool/MCP surface later. That is a transport/productization decision, not a reason to duplicate Topic Radar logic.

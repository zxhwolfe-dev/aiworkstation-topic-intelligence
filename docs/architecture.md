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
- lightweight top-level JSON shape checks;
- a CLI.

It has no crawler, database, scoring, clustering, model call, or topic-matching algorithm.

## Runtime dependency policy

Do not use `../akaiagents/.venv` as this repository's runtime environment.

The helper currently needs only Python 3.10+ standard library. If future code adds a real dependency, declare it here rather than depending on a sibling project's environment.

Do not import private `akaiagents` modules. The public API is the boundary.

## Current M0

Included:

- `cross-market-trend-research`;
- `evidence-backed-content-brief`;
- thin public API helper;
- offline unit tests;
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

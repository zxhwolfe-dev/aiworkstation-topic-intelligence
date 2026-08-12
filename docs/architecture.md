# Architecture

## Goal

Expose AI Workstation Global Topic Radar as one reusable, evidence-aware Skill without reproducing its backend and without making anonymous Skill users consume AI Workstation server-side LLM quota.

## Layers

```text
User / ChatGPT / Codex
          |
          v
Topic Intelligence public Skill
- intent routing
- freshness/evidence policy
- comparison reasoning
- host-model content brief
          |
          +----------------------------------+
          |                                  |
          v                                  v
native public HTTP-capable host     Skill-local stdlib helper
          |                                  |
          +------------------+---------------+
                             v
AI Workstation public Topic Radar read API
- feed
- sources
- history
                             |
                             v
akaiagents / ai_topic_radar
collection, clustering, scores, history,
source health, persistence

Separate future Premium plane:
Authenticated AI Workstation App/Plugin/OAuth
          -> user identity / plan / quota
          -> optional server Topic Insight
```

## Responsibilities

### `akaiagents`

Owns the product/data plane:

- source connectors;
- normalization;
- clustering/topic identity;
- deterministic opportunity scoring;
- trend/history;
- caching and stale/partial state;
- source health;
- website authentication/membership/quota;
- server-side model capabilities such as Premium Topic Insight.

### Topic Intelligence public repository

Owns the portable workflow layer:

- choose the right public Radar read filters;
- inspect freshness before current-state claims;
- preserve facts separately from host analysis;
- compare regions/platforms without inventing propagation;
- select useful topics without inventing a second score;
- preserve exact topic identity across composition;
- create a research-ready brief using the current host model;
- enforce the public Skill cost/credential boundary.

It does **not** own website accounts, billing, membership, server quota, or Premium authentication.

## Public Skill runtime

The Skill directory is a complete portable unit:

```text
topic-intelligence/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/selection-workflow.md
  references/brief-workflow.md
  references/quality-contract.md
  LICENSE
```

Portable copies are synchronized from canonical sources in the repository root.

## Public helper

`topic_radar_client.py` is deliberately read-only and no-cost from the AI Workstation model-budget perspective.

It exposes only:

- `feed`;
- `sources`;
- `history`.

It contains only:

- URL/parameter construction;
- timeout/error normalization;
- lightweight response-shape/identity checks;
- CLI plumbing.

It contains no:

- crawler;
- database;
- score;
- clustering;
- local model;
- persisted cache;
- Premium Topic Insight command;
- AI Workstation secret/API key.

All bundled public helper HTTP operations are GET-only.

## Cost boundary

Normal public Skill flow:

```text
public Radar facts
      ↓
current ChatGPT / Codex / agent host model
      ↓
selection / explanation / content brief
```

This means the public Skill completes normally with **zero AI Workstation server-side LLM calls**.

Do not solve authentication by embedding one shared token in the ZIP or asking users to paste secrets into chat.

## Optional Premium Topic Insight

A server-generated Topic Insight can remain part of the broader AI Workstation product, but it sits outside the bundled public Skill transport.

Acceptable future path:

```text
host-native AI Workstation connection
          ↓
OAuth / account authentication
          ↓
user_id / plan / remaining quota
          ↓
optional Premium Topic Insight
```

The authenticated connection, not the portable Skill, must enforce usage rights and cost accounting.

A Premium Insight response remains model-generated analysis, not independent evidence.

## Automatic modes

```text
topic-intelligence
  -> selection only: one bounded feed, then stop
  -> supplied current topic: preserve exact id, no selection feed
  -> selection + brief: one bounded feed, preserve the finalist id,
     then produce the host-model research-ready brief
```

A selection-followed-by-brief request must not trigger another broad/bounded
topic-selection pass. Current-task state is not persistence; an old saved result
cannot replace a new live check.

For a brief based on a supplied current topic:

1. preserve the supplied stable ID and current snapshot;
2. do not run a selection feed;
3. use history only when movement matters;
4. use the host model to build the brief.

It must not:

- invent another score;
- map content-format words to Radar platforms;
- broaden `AI` into generic technology without reason;
- call anonymous server `/insight`;
- force a weak candidate.

## Evidence model

Public mode separates:

1. **Radar facts** — live feed/source/history data;
2. **Host editorial analysis** — selection, audience, hook, angle, narrative, research/visual plan;
3. **Unknowns / verification** — unsupported claims and evidence gaps.

If an authenticated Premium connection explicitly supplies server Topic Insight, treat it as a fourth layer of model analysis and preserve its provenance.

## Runtime dependency policy

- Python 3.10+ standard library only for the public helper;
- no dependency on `../akaiagents/.venv`;
- no private `akaiagents` imports;
- public API remains the repository boundary.

## Validation

Current validation includes:

- standalone ZIP content/runtime checks;
- byte-identical portable helper/reference copies;
- extracted ZIP helper E2E;
- exact topic identity preservation;
- selection-only / supplied-topic brief / combined scenarios;
- ChatGPT-derived query/provenance rules;
- public helper CLI contains no `insight` command;
- public helper requests are GET-only;
- public Brief quality eval requires host reasoning with zero AI Workstation server model spend.

## Future transport decision

ChatGPT v0.2.0 smoke already proved that the standalone Skill can reach public Radar data, so Hosted MCP is **not needed for public transport**.

A future App/Plugin/MCP may still be justified as a thin **authenticated Premium account connection**. If added, it must not duplicate collection, clustering, score, history, persistence, or model logic.

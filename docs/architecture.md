# Architecture

## Goal

Expose AI Workstation Global Topic Radar as reusable, evidence-aware Skills without reproducing its backend and without making anonymous Skill users consume AI Workstation server-side LLM quota.

## Layers

```text
User / ChatGPT / Codex
          |
          v
Topic Intelligence public Skills
- intent routing
- freshness/evidence policy
- comparison reasoning
- current-task handoff
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

Each Skill directory is a complete portable unit:

```text
skill-name/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/handoff-contract.md
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

## Skill composition

```text
creator-topic-opportunity-research
  live feed/sources/history as needed
  -> select one finalist
  -> ati.topic-opportunity-handoff.v1
       topic_id
       snapshot freshness
       observed topic fields
       selection analysis / unknowns / risks
  -> evidence-backed-content-brief
       preserve same topic_id
       history if movement matters
       host-model research-ready brief
```

A valid current-task handoff must not trigger another broad/bounded topic-selection pass.

The handoff is workflow context, not persistence. Old handoffs cannot replace a new live check.

## Brief-only fallback

If Brief is installed alone:

1. resolve a user-supplied topic live, or run one bounded feed selection pass;
2. preserve explicit subject/domain scope from the first query;
3. normally inspect no more than five candidates;
4. select at most one using existing Radar fields;
5. use history only when movement matters;
6. use the host model to build the brief.

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
- handoff identity preservation;
- Creator-only / Brief-only / composed scenarios;
- ChatGPT-derived query/provenance rules;
- public helper CLI contains no `insight` command;
- public helper requests are GET-only;
- public Brief quality eval requires host reasoning with zero AI Workstation server model spend.

## Future transport decision

ChatGPT v0.2.0 smoke already proved that the standalone Skill can reach public Radar data, so Hosted MCP is **not needed for public transport**.

A future App/Plugin/MCP may still be justified as a thin **authenticated Premium account connection**. If added, it must not duplicate collection, clustering, score, history, persistence, or model logic.

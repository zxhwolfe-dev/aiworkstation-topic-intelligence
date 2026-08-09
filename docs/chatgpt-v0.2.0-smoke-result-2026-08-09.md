# ChatGPT v0.2.0 smoke result — 2026-08-09

This record captures manual ChatGPT web behavior for the immutable published v0.2.0 Skill artifacts. It is a product-surface observation, not a replacement for Codex/runtime acceptance.

## Overall classification

```text
SKILLS_ONLY_PASS
```

with one UI observability limitation:

```text
raw ati.topic-opportunity-handoff.v1 payload / internal handoff trace not exposed by ChatGPT UI
```

The current evidence does **not** justify adding Hosted MCP only for transport. ChatGPT accepted the standalone package, executed the bundled runtime path, and reached the live `https://aiworkstation.cn` Topic Radar endpoints.

## Shape A — Creator only

Published Skill:

```text
creator-topic-opportunity-research
```

Observed:

- ZIP upload accepted by ChatGPT web;
- Skill automatically discovered for the creator/editorial live-topic prompt;
- Skill instructions/documents were read;
- bundled runtime actions executed;
- live Radar feed/source/history data was reachable;
- freshness fields were surfaced rather than hidden;
- an initially old snapshot was not presented as newly observed; the workflow waited/re-read until a fresh snapshot was available;
- source gaps and single-source limitations were exposed;
- current-topic recommendations were produced without local/model-memory fallback.

Quality observation:

The answer sometimes presented host editorial judgments such as audience breadth or China-market suitability in prose close to Radar facts. v0.2.1 should make provenance boundaries more explicit.

## Shape B — Brief only

Published Skill:

```text
evidence-backed-content-brief
```

Observed:

- ZIP upload/discovery succeeded;
- live Radar access succeeded;
- the Skill used its standalone bounded-selection mode;
- one finalist was selected before history/Insight;
- server `/insight` succeeded for the selected topic;
- required output sections were present: audience payoff, selected angle, opening, narrative structure, `must_verify`, `avoid_claims`, research handoff, and visual/material needs;
- low evidence breadth was kept visible and the result was framed conditionally rather than as an established viral trend.

Quality issue discovered:

The first query incorrectly treated the user's content-format word `短视频` as a Radar platform constraint and returned no useful candidates. The host self-corrected to a bounded technology/AI query, but this mapping error should be prevented by Skill guidance.

Required v0.2.1 rule:

```text
content format / duration / language / audience != Radar platform/source filter
```

## Shape C — Both Skills

Installed:

```text
creator-topic-opportunity-research
evidence-backed-content-brief
```

Observed user-visible flow:

1. ChatGPT entered the Brief Skill for the requested final job;
2. Brief explicitly stated that it should prefer the installed Creator Skill for current-topic selection;
3. Creator-related Skill instructions were consulted and a live AI-focused shortlist was produced;
4. one finalist was selected;
5. after selection, ChatGPT stated it would query history and Topic Insight only for that finalist;
6. the final brief used one stable Topic Radar ID and contained the requested research-ready sections;
7. no second broad/bounded candidate-selection pass was visible after the finalist was selected.

This is sufficient to validate **behavioral multi-Skill composition** in ChatGPT.

Not directly observable in the ChatGPT UI:

- the raw serialized `ati.topic-opportunity-handoff.v1` object;
- an internal trace proving `handoff.topic_id == handoff.topic_snapshot.id` inside the host.

Therefore the host matrix records composition as:

```text
validated_behaviorally_handoff_trace_not_exposed
```

rather than claiming a hidden trace was observed.

## Cross-smoke Skill-quality findings

The three ChatGPT tests produced four concrete Skill-side improvements for the next patch line:

1. **Constraint mapping** — content format, duration, language, audience and tone must not be converted into Radar platform/source filters.
2. **Provenance visibility** — make Radar facts, server Topic Insight analysis and host editorial judgments easier to distinguish in the user-facing answer.
3. **No duplicate selection** — after a valid current-task Opportunity handoff, Brief must not re-run broad/bounded candidate selection unless freshness/identity validity requires it.
4. **Insight reuse** — when server Insight is complete, adapt and prioritize it instead of generating a second unrelated creative plan from scratch.

These are Skill/workflow quality changes only. They do not require a new Radar backend, score, persistence system, or Hosted MCP.

## Transport decision

Current ChatGPT evidence:

```text
Skill upload/package      PASS
Skill discovery           PASS
bundled runtime execution PASS
live Radar access         PASS
Brief-only Insight access PASS
multi-Skill composition   PASS (behaviorally; raw handoff trace not exposed)
```

Decision:

```text
Do not build Hosted MCP solely to make the current ChatGPT v0.2.0 Skills work.
```

Revisit transport only if a future host or product surface demonstrates a concrete connectivity limitation.

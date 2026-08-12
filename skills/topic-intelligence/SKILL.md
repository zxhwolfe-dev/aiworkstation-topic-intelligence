---
name: topic-intelligence
description: Find and compare live creator or editorial topic opportunities with AI Workstation Global Topic Radar, or turn one current Radar topic into an evidence-aware, research-ready content brief. Use when the user wants a current-topic shortlist, a publishing decision, a brief for a supplied current topic, or selection followed by a brief. Do not use for ordinary factual lookup, translation, rewriting, summarization, generic title generation, or complete supplied material that needs no live-topic decision.
---

# Topic Intelligence

Use one public Skill for current-topic selection and evidence-backed content planning.

Before querying or reasoning, read and follow:

```text
references/quality-contract.md
```

Read `references/selection-workflow.md` when selecting or comparing topics. Read
`references/brief-workflow.md` when the request includes a content brief.

## Choose exactly one mode

Infer the smallest mode that satisfies the request. Do not make the user choose a
mode name.

### Mode 1: selection only

Use when the user asks what to research, cover, or publish. Run one bounded live
feed query, compare the relevant candidates, and stop after the requested
shortlist or finalist. Do not add an unsolicited content brief.

### Mode 2: brief for a supplied current topic

Use when the user supplies an exact current Radar topic ID or a current Radar
topic snapshot. Preserve that identity and do not run `feed` to select again.
Use `history <exact-feed-id>` only when movement matters. If an ID alone does not
provide enough topic facts, ask for the current topic card or explain the missing
evidence; do not silently replace it with another topic.

### Mode 3: selection followed by brief

Use when one request asks both to choose a current topic and create a brief. Run
exactly one bounded selection feed, choose one finalist, preserve its exact feed
`id`, and build the brief from the same evidence. Do not run a second feed. Use
history only for that finalist when movement matters.

## Public runtime contract

The bundled helper may call only the public no-cost Radar endpoints for `feed`,
`sources`, and `history`. The current host model performs all comparison and
editorial reasoning.

Resolve the helper from this loaded Skill's own root:

```text
scripts/topic_radar_client.py
```

Use only these command forms:

```text
python3 <skill-local-helper> --timeout 30 feed --q AI --limit 12
python3 <skill-local-helper> --timeout 30 sources
python3 <skill-local-helper> --timeout 30 history <exact-feed-id>
```

Requirements:

- use `python3`, never `python`, `python2`, or direct execution;
- place helper-wide options before the subcommand;
- pass the history topic ID as the sole positional argument, never
  `history --topic-id <id>`;
- run each helper call as one standalone direct command;
- never combine it with `|`, `&&`, `;`, redirection, command substitution,
  backticks, a here-doc, `jq`, or another Python process;
- read the helper's JSON directly from stdout;
- never guess or repeatedly probe CLI syntax;
- never use a repository-root, sibling-repository, user-global, or other copied
  helper, even when the current directory contains one;
- never use `--base-url` or an origin override in the official public workflow.

For ordinary selection, start with `--limit 12` and never exceed 24 unless the
user explicitly asks for a large list, export, or larger sample.

## Live evidence gate

Do not use model memory or local files as current evidence. Current claims require
one of:

1. a live Radar response obtained in this task;
2. equivalent current Radar data from a native host connection; or
3. a current Radar response explicitly supplied by the user.

Never substitute sibling repositories, snapshots, databases, fixtures, caches,
logs, reports, exports, or prior-task artifacts. If live evidence is unavailable,
say so and offer only a clearly labeled research framework or template.

Inspect `generated_at`, `partial`, `stale`, `snapshot_age_seconds`, `refreshing`,
`source_status`, and topic evidence before interpreting the result. Surface
material gaps. Missing values are unknown, not zero.

## Selection invariants

- Preserve an explicit domain such as AI in the first query.
- Treat domain scope as semantic relevance after retrieval; reject literal
  substring collisions.
- Treat duration, language, audience, tone, and content format as editorial
  constraints, not Radar platform/source filters.
- Use Radar's `opportunity_score`, `trend_stage`, freshness, evidence breadth,
  and trend fields; never invent another score.
- Call history only for a finalist when movement changes the decision.
- Label cross-market lead/lag as a hypothesis unless directly evidenced.

## Brief invariants

- Preserve one exact Radar `id` from evidence through the final brief.
- Separate Radar facts from host editorial analysis and recommendations.
- Include the stable Radar ID, freshness, source limitations, angle, audience
  payoff, hook, narrative beats, research questions, preferred source types,
  `must_verify`, `avoid_claims`, unknowns, risks, and a visual/material plan as
  relevant to the request.
- Do not claim that Radar measured audience fit, likely reach, or content quality.

When discussing audience, ordinary technology users, China-market fit, or
distribution potential, state explicitly that Radar does not measure actual
audience size, topic/content saturation, or future reach/virality. Label claims
such as "适合中国用户" or "受众可能更广" as host editorial judgment, not Radar
fact.

## Safety and cost boundary

- Never call anonymous/public `/insight` or another AI Workstation model-backed
  endpoint from the public Skill.
- Never embed a shared credential or ask the user to paste a private key into
  chat.
- An optional Premium Topic Insight is allowed only through a native connection
  explicitly authenticated to the user's account and enforcing that user's
  quota. Treat it as model analysis, not independent evidence.
- Never present `opportunity_score`, `target_platforms`, or host judgment as a
  performance guarantee.
- Never force a topic when evidence is weak.

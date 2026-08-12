# Topic Intelligence quality and safety contract

This contract governs the unified public `topic-intelligence` Skill.

## One Skill, three modes

Infer exactly one mode from user intent:

1. selection only;
2. brief for a supplied current topic;
3. selection followed by brief.

Selection-only requests must not receive an unsolicited brief. An exact supplied
Radar topic ID must not trigger a selection feed. Combined mode must use exactly
one bounded feed and preserve the finalist's exact identity through the brief.
Composition must not re-run broad selection after a finalist is chosen. The
allowed sequence is: bounded selection → preserve the exact current-task topic
identity and freshness → host-model Brief reasoning. This state is internal to
the current turn, not a second public entry point or persisted evidence.

## Portable runtime

The only supported interpreter entry is `python3`. Resolve
`scripts/topic_radar_client.py` from the currently loaded Skill root. Never use a
repository-root, source-worktree, sibling-repository, user-global, or arbitrary
same-named helper.

Canonical forms:

```text
python3 <skill-local-helper> --timeout 30 feed --q AI --limit 12
python3 <skill-local-helper> --timeout 30 sources
python3 <skill-local-helper> --timeout 30 history <exact-feed-id>
```

Global options precede the subcommand. History takes one positional ID. Every
call is a standalone direct command. Do not use shell composition, pipes,
redirection, command substitution, backticks, here-docs, `jq`, another Python
process, custom origins, or syntax probing.

For ordinary selection, the initial candidate set defaults to 12 and must not
exceed 24. Do not fetch 100 candidates to choose a small shortlist.

## Public data and cost boundary

Public mode may use only:

- `GET /api/v1/ai/topic-radar/feed`;
- `GET /api/v1/ai/topic-radar/sources`;
- `GET /api/v1/ai/topic-radar/history?topic_id=...`.

It must make zero anonymous AI Workstation server-side LLM calls. Use the current
host model for editorial reasoning. Never embed a shared credential or ask for a
private key in chat. Premium Topic Insight requires a native connection explicitly
authenticated to the user's account and enforcing that user's quota.

## Current evidence

Accept current claims only from live Radar data obtained in this task, equivalent
current native-host data, or a current Radar response explicitly supplied by the
user. Never fall back to model memory, local snapshots, repositories, databases,
fixtures, caches, exports, logs, reports, or prior-task artifacts.

Inspect freshness, partial/stale state, refresh state, source coverage, and topic
evidence. Surface material gaps. Missing fields are unknown, not zero. A stale,
partial, or unavailable response may support a research plan, but never a claim
that the topic is currently accelerating.

## Query and identity discipline

- Preserve explicit domain scope in the first query.
- Reject semantic mismatches and literal substring collisions.
- Keep content format, duration, language, audience, and tone out of Radar
  platform/source filters unless they name a supported dimension.
- Use Radar's supplied scores and trend fields; do not invent another score.
- Use history only for a finalist when movement matters.
- Keep one exact topic ID in combined mode and never reselect after selection.

## Provenance and unknowns

Separate:

- Radar facts;
- host editorial analysis;
- recommendations;
- unknowns and risks.

When conclusions involve audience, ordinary technology users, China-market fit,
or distribution potential, explicitly disclose all of the following: Radar does
not measure actual audience size; Radar does not measure content/topic saturation;
Radar does not measure future reach/virality. "适合中国用户" and "受众可能更广"
are host editorial judgments, not Radar fact. Use the labels **Radar facts**,
**Host editorial analysis**, **recommendation**, and **unknowns / must_verify** so
the user can tell a verified fact from an editorial judgment.

## Combined workflow state

When one request asks for both a current selection and a research-ready brief,
the host keeps the exact finalist ID, snapshot ID, and freshness fields in its
current-turn reasoning before writing the final brief. It must not emit or ask
the user to manage an internal workflow payload, and it must not call another
feed just to make the brief visible.

## Non-trigger boundary

Do not invoke Radar for ordinary factual lookup, translation, rewriting,
summarization, generic title generation, or complete supplied material that does
not require a current-topic decision.

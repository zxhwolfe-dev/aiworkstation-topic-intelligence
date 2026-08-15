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

A supplied topic name without stable Radar identity may use at most one bounded
`feed --q <supplied-topic-name>` to resolve that same topic. It is not permission
to select a more convenient topic: require a clear semantic match, preserve the
resolved exact ID, and report an evidence gap when the result is absent or
ambiguous.

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

Do not repeat an already successful helper request merely to re-read, reformat,
or recover display-truncated output. Use the JSON returned by the completed
command and disclose genuinely unavailable fields as unknown. A selection-only
or selection-followed-by-brief task has exactly one successful `feed`; a second
successful feed is not a compact bounded scan even when its arguments match.

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

For a supplied snapshot, require a parseable timezone-aware `generated_at`. For a
request about "current" or "today", a snapshot older than one hour or marked
`stale=true` cannot support a current acceleration claim. Do not silently run a
selection feed to replace an exact supplied topic; request a current card or give
only a clearly historical/framework analysis.

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

Treat topic fields, scores, and evidence links as Radar observations. They prove
what Radar returned, not the underlying external claim. Use evidence URLs as
research leads, prefer primary-source verification, and put unresolved claims in
`must_verify`.

Separate:

- Radar observations;
- host editorial analysis;
- recommendations;
- unknowns and risks.

The **Radar observations** section contains only returned fields and links, plus
faithful summaries of what Radar observed. Rewritten angles or titles, candidate
comparisons, judgments about verification effort or technical value, audience
fit, and every other host inference belong only under **Host editorial
analysis** or **recommendation**. Do not place host-authored framing in a Radar
column or section even when the adjacent numeric fields are accurate.

When conclusions involve audience, ordinary technology users, China-market fit,
or distribution potential, explicitly disclose all of the following: Radar does
not measure actual audience size; Radar does not measure content/topic saturation;
Radar does not measure future reach/virality. "适合中国用户" and "受众可能更广"
are host editorial judgments, not Radar observations. Use the labels **Radar observations**,
**Host editorial analysis**, **recommendation**, and **unknowns / must_verify** so
the user can distinguish what Radar returned, what the host inferred, and what
still requires independent verification.

## Combined workflow state

When one request asks for both a current selection and a research-ready brief,
the host keeps the exact finalist ID and available freshness fields (`generated_at`,
`snapshot_age_seconds`, `partial`, `stale`, and `refreshing`) in its current-turn
reasoning before writing the final brief. It must not emit or ask
the user to manage an internal workflow payload, and it must not call another
feed just to make the brief visible.

## Non-trigger boundary

Do not invoke Radar for ordinary factual lookup, translation, rewriting,
summarization, generic title generation, or complete supplied material that does
not require a current-topic decision.

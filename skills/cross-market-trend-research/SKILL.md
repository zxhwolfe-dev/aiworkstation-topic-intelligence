---
name: cross-market-trend-research
description: Research current and rising content topics from AI Workstation Global Topic Radar, including early opportunities, platform or region differences, source freshness, and evidence-aware cross-market timing hypotheses. Use when the user asks what is trending now, what is accelerating, what topics to watch, or what overseas trends may be worth early attention.
---

# Cross-Market Trend Research

Use this Skill for **current topic discovery and trend interpretation** based on AI Workstation Global Topic Radar.

Do not use model memory as a substitute for live trend data.

## Product boundary

Global Topic Radar already owns:

- public-source collection;
- normalization and clustering;
- `opportunity_score`;
- `trend_stage`;
- trend/history calculations;
- source health and stale-data handling.

This Skill owns only:

- intent interpretation;
- efficient querying;
- evidence/freshness checks;
- comparison and cross-market reasoning;
- user-specific recommendations.

Never recreate a score from raw fields when the Radar already supplies it.

## Live-data gate

Before claiming that a topic is current, rising, accelerating, new, or region/platform-specific, obtain a live Topic Radar response.

The public contract is:

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`

A local/Codex host may use `scripts/topic_radar_client.py`. A host with a native HTTP or MCP connection may call the same contract directly.

If live data cannot be reached:

1. do not invent a current shortlist;
2. say that current Topic Radar evidence is unavailable;
3. offer only a research plan, filter strategy, or evaluation framework;
4. label user-supplied examples as unverified unless current evidence is supplied.

## Read freshness before interpretation

For every feed response, inspect:

- `generated_at`;
- `partial`;
- `stale`;
- `snapshot_age_seconds`;
- `refreshing`;
- `source_status`;
- `history_available`.

If `partial=true`, describe material source gaps before making a broad-market claim.

If `stale=true`, do not describe the snapshot as newly observed. State the age/freshness caveat.

A healthy aggregate does not mean every source is healthy; inspect `source_status` when the answer depends on a particular platform or region.

A source status of `empty` means the source returned no current items in that snapshot. Do not automatically describe `empty` as a connector failure; use its status/note and surrounding coverage to explain the limitation.

When `refreshing=true`, sequential feed/history/source reads may legitimately observe different generations. Do not treat a newly added history point or changed count as a contract violation merely because two requests were made during refresh.

## Route the request

### Broad current scan

For requests such as “what is worth watching today?”:

1. choose a bounded window with `max_age_hours`;
2. use relevant `category`, `region`, or `platform` filters only when the user supplied them;
3. prefer a compact candidate set;
4. rank discussion by the existing `opportunity_score`, `trend_stage`, freshness, evidence breadth, and trend fields rather than inventing a new score.

### Early-opportunity scan

Use available `stage`, `signal`, `new_only`, and `min_score` filters to find candidates such as early opportunities or multi-source signals.

Treat `opportunity_score` as a Radar-produced deterministic score, not as proof that content will perform.

### Platform or region comparison

Run comparable feed queries for the requested markets/platforms.

Preserve the same time window and other filters so the comparison is meaningful.

Do not infer a propagation path merely because two unrelated titles look similar.

### Cross-market timing hypothesis

A claim such as “US is leading and Chinese-language coverage may follow” requires stronger evidence than a normal shortlist.

Prefer, in order:

1. the same stable feed `id` observed through comparable region/platform queries;
2. direct evidence timestamps and source spread for one clustered topic;
3. history that supports sequential expansion.

If the live contract does not establish this, say **cross-market hypothesis**, not verified fact.

## Inspect candidate fields

For each serious candidate, pay attention to:

- `id`;
- `title` / `title_en`;
- `summary`;
- `platform`;
- `region`;
- `category`;
- `trend_stage`;
- `opportunity_score`;
- `rank`;
- `heat`;
- `first_seen_at`;
- `target_platforms`;
- `signal_count`;
- `evidence`;
- `trend`;
- `score_breakdown`.

The stable topic identifier is named `id` on feed items. Pass that exact value as the `topic_id` query/body field for `/history` or `/insight`; those endpoint responses identify it as `topic_id`. Do not search for a nonexistent feed `topic_id` alias.

Useful trend fields can include:

- `score_change_24h`;
- `score_change_7d`;
- `velocity_1h`;
- `velocity_6h`;
- `velocity_24h`;
- `source_count`;
- `source_spread_hours`;
- `is_new_24h`.

Do not require every field to be present. Missing data is an unknown, not zero.

## Use history selectively

Call `/history` for finalists when the user's decision depends on movement over time.

Do not call history for every item in a broad feed unless necessary.

History can help distinguish:

- a new spike;
- sustained momentum;
- cooling;
- a one-source anomaly.

Do not extrapolate beyond the observed series.

When a refresh is in progress, history can gain a point after the parent feed was generated. Compare timestamps and snapshot state rather than requiring `trend.history_points` to equal the later history response length exactly.

## Evidence boundary

Keep five layers explicit:

### Source facts

Facts returned by Topic Radar, including score, stage, timestamps, evidence entries, and trend metrics.

### Analysis

Your interpretation of what the observed signals may mean.

### Recommendations

What the user should consider researching or publishing first.

### Unknowns

Anything the current contract does not establish, including audience saturation, future virality, or a cross-market lead/lag without direct evidence.

### Risks

Partial/stale coverage, source outages, weak evidence breadth, one-platform concentration, or excessive dependence on a single observed metric.

## Output

Adapt the answer to the user, but for a shortlist usually include:

### Radar status

- snapshot time/freshness;
- partial/stale/refreshing state when material;
- important source coverage issues.

### Best candidates

For each candidate:

- topic and stable ID when useful;
- current Radar stage and opportunity score;
- observed momentum/evidence;
- why it matters;
- what is fact versus inference;
- recommended next verification step.

### Cross-market interpretation

State verified differences first.

Put timing-gap or propagation claims in a separate **hypotheses** section unless directly evidenced.

### Unknowns and risks

Do not bury them.

## Quality rules

- Never fabricate a current topic from memory.
- Never turn `target_platforms` into proof of actual platform performance.
- Never treat `opportunity_score` as a guaranteed outcome.
- Never call a snapshot “live/current” without checking freshness.
- Never silently ignore `partial` or `stale`.
- Never treat normal between-request changes during `refreshing=true` as contradictory evidence without checking timestamps.
- Never merge different topics only because their titles are semantically similar.
- Prefer a small evidence-backed shortlist over a long generic trend list.

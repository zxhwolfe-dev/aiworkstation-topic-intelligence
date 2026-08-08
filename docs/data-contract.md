# Topic Radar data contract used by the Skills

This document records only the existing public surface that Topic Intelligence depends on. `akaiagents` remains the source of truth.

## Feed

`GET /api/v1/ai/topic-radar/feed`

Important query parameters currently include:

- `q`
- `platform`
- `region`
- `category`
- `source`
- `stage`
- `signal`
- `keywords`
- `exclude_sources`
- `min_score`
- `new_only`
- `max_age_hours`
- `offset`
- `limit`

The Skills rely on feed-level freshness fields such as:

- `generated_at`
- `partial`
- `stale`
- `snapshot_age_seconds`
- `refreshing`
- `source_status`
- `history_available`

Topic cards can expose fields including:

- `id`
- `title` / `title_en`
- `summary` / `summary_en`
- `platform`
- `region`
- `category`
- `trend_stage`
- `opportunity_score`
- `rank`
- `heat`
- `first_seen_at`
- `target_platforms`
- `evidence`
- `signal_count`
- `trend`
- `score_breakdown`

### Topic identity handoff

The stable identifier on a feed item is `id`.

The `/history` and `/insight` request contracts call that same value `topic_id`, and their responses also expose it as `topic_id`.

Therefore the expected handoff is:

```text
feed.items[n].id
        |
        +--> history?topic_id=<same value>
        |
        +--> insight body {"topic_id": "<same value>"}
```

Do not expect a `topic_id` alias on feed items.

### Interpretation rule

`opportunity_score` is a deterministic Radar score. It is a source fact about the Radar's current scoring output, but it is not a guarantee of content performance.

## Sources

`GET /api/v1/ai/topic-radar/sources`

Use source status to qualify broad claims and platform-specific claims when the aggregate is partial, stale, or missing a relevant source.

A source with status `empty` returned no current items for that snapshot. `empty` should not automatically be described as a transport/connector failure; inspect the returned status note and surrounding coverage.

## History

`GET /api/v1/ai/topic-radar/history?topic_id=...`

History points can include:

- observation time;
- opportunity score;
- rank;
- heat;
- source count.

Use history to describe observed movement. Do not extrapolate an unobserved future path.

### Refresh consistency rule

The feed can report `refreshing=true`. In that state, two sequential public requests are not an atomic snapshot transaction.

For example, a feed item's `trend.history_points` may be 6 and a history request moments later may return 7 points because a new observation was persisted between the two reads. Treat this as expected refresh behavior when timestamps support it, not as a contract mismatch.

The client should enforce stable topic identity, but Skills should compare timestamps/generation state rather than demanding exact count equality across requests made during refresh.

## Insight

`POST /api/v1/ai/topic-radar/insight?locale=zh|en`

JSON body:

```json
{"topic_id": "server-known-topic-id"}
```

The existing response can include editorial verdict, readiness, audiences, three content angles, short-video handoff, verification tasks, claims to avoid, quality state, and model/provider metadata.

### Interpretation rule

Insight is model analysis, not a new verified-fact source.

## Cross-market limits

Current topic evidence is sufficient for many source/region/platform comparisons, but a strong claim about a propagation sequence or market lead/lag needs directly comparable evidence.

The Skills must downgrade such a claim to a hypothesis when:

- stable topic identity across compared slices is unclear;
- timestamps do not establish sequence;
- a required region/platform source is unhealthy;
- the snapshot is stale/partial in a way that changes the conclusion.

This explicit limit is preferable to adding a second, inconsistent cross-market scoring system in this repository.

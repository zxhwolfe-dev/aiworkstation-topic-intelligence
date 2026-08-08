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

### Interpretation rule

`opportunity_score` is a deterministic Radar score. It is a source fact about the Radar's current scoring output, but it is not a guarantee of content performance.

## Sources

`GET /api/v1/ai/topic-radar/sources`

Use source status to qualify broad claims and platform-specific claims when the aggregate is partial, stale, or missing a relevant source.

## History

`GET /api/v1/ai/topic-radar/history?topic_id=...`

History points can include:

- observation time;
- opportunity score;
- rank;
- heat;
- source count.

Use history to describe observed movement. Do not extrapolate an unobserved future path.

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

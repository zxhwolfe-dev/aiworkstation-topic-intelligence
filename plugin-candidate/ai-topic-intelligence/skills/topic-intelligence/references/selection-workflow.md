# Topic Intelligence selection workflow

Use this reference only when the request includes current-topic discovery,
comparison, ranking, or selection.

## Query once, then reason

1. Preserve the user's explicit subject in the first bounded `feed` query.
2. Start with 12 candidates and keep the hard ordinary-task ceiling at 24.
3. Check freshness and source coverage before ranking.
4. Remove semantic mismatches, including short-token substring collisions.
5. Compare the remaining candidates using Radar fields and the user's editorial
   constraints.
6. Select only the requested number of topics.
7. Call history only for a finalist when movement affects the decision.

Never translate content-format requirements into unsupported Radar filters.
`短视频`, `2–3 分钟`, language, audience, tone, and production style guide the
host's post-retrieval decision.

## Comparison evidence

Useful Radar fields include:

- `id`, title, summary, category, region, platform;
- `trend_stage`, `opportunity_score`, rank, heat;
- `first_seen_at`, evidence, signal count, source count;
- `score_change_24h`, `score_change_7d`, velocity fields, and source spread;
- snapshot freshness and source status.

Do not recalculate a replacement score. Do not infer a cross-market propagation
sequence merely because unrelated titles look similar.

## Selection output

For a shortlist, report snapshot status, observed Radar facts, host interpretation,
recommendation, next verification step, unknowns, and risks. For a sole finalist,
include its exact Radar `id` so a following brief can preserve identity.


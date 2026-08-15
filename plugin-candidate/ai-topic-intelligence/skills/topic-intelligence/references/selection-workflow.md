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

For a shortlist, report in this order:

1. **Radar observations** — snapshot status, exact IDs, verbatim returned titles,
   returned fields and links, and factual source/freshness limitations only.
   End this section before ranking or comparing candidates. Do not put
   advantages, disadvantages, verification effort, technical value, audience
   fit, editorial usefulness, or a recommendation in this section.
2. **Host editorial analysis** — candidate comparison, audience/format fit,
   verification effort, and rewritten content angles.
3. **recommendation** — the selected order or finalist and why.
4. **unknowns / must_verify** — next verification steps, unknowns, and risks.

When a column or field is labeled **Radar title** or **original title**, copy the
returned title verbatim. Never shorten, translate, or paraphrase text under that
label. A host-authored shorthand or angle must be labeled as such and appear only
in the host-analysis or recommendation section. For a sole finalist, include its
exact Radar `id` so a following brief can preserve identity.

# Topic Intelligence quality contract

This reference tightens host behavior learned from real ChatGPT v0.2.0 smoke tests. It does not change the Topic Radar API or evidence source of truth.

## 1. User content constraints are not Radar platform filters

Keep these concepts separate:

- **Radar filters**: actual supported source/platform/region/category dimensions such as YouTube, TikTok, Bilibili, Douyin, Xiaohongshu, region, category, or an explicit source name when the live contract supports it.
- **Content constraints**: short video, 2–3 minute explainer, article, graphic post, Chinese-language content, ordinary users, developers, parents, research-heavy, visual-first, and similar publishing requirements.

Never map a content-format, duration, language, audience, tone, or production constraint into the Radar `platform` or `source` query merely because the words resemble a platform/content concept.

Examples that must remain post-query selection constraints unless the user explicitly names a supported Radar platform:

- `短视频` / `short video`;
- `2–3 分钟` / `2 minute explainer`;
- `中文` / `Chinese-language`;
- `图文` / `article` / `explainer`;
- `普通用户` / `开发者` / `家长`.

If a query returns irrelevant candidates because a user constraint was mapped to the wrong Radar dimension, correct the mapping once and explain the correction briefly. Do not broaden into an unrelated full-market search.

## 2. Preserve provenance in user-facing claims

Keep three analytical layers distinguishable:

### Radar facts

Direct live Topic Radar fields from the current task, such as title, source, evidence, timestamps, `opportunity_score`, `trend_stage`, source count, freshness, and history.

### Server Topic Insight

Model-generated `/insight` fields such as verdict, audience payoff, hooks, angles, narrative beats, `must_verify`, `avoid_claims`, and visual needs. These are analysis/recommendations over a server-known topic, not independent evidence.

### Host editorial analysis

The current host/model's own adaptation, prioritization, comparison, audience judgment, or recommendation.

Do not phrase host judgments such as “更适合中国用户”, “受众更大”, “更容易传播”, “可能爆”, “监管更难”, or “最值得做” as though Radar directly measured them. Mark them as **分析/判断**, **编辑判断**, **假设**, or equivalent wording when the distinction matters.

Do not repeat a provenance label before every sentence; make the boundary visible at the section/claim level without making the answer unreadable.

## 3. Composition must not re-run broad selection after a valid handoff

When both Skills are installed:

1. `creator-topic-opportunity-research` selects exactly one finalist;
2. it hands off the exact live feed `id` through `ati.topic-opportunity-handoff.v1`;
3. `evidence-backed-content-brief` consumes that same `topic_id`;
4. after a valid current-task handoff, do **not** run another broad/bounded candidate-selection feed pass merely to choose again;
5. only refresh/re-resolve when the handoff is stale, materially partial for the requested claim, identity-invalid, from another task, or the user explicitly asks for a fresh re-check.

A follow-up history request and one selected-topic insight request are normal and are not duplicate selection.

## 4. Reuse complete server Insight instead of independently rewriting it from scratch

When `/insight` succeeds with a complete usable result:

- treat its creative fields as the primary editorial plan;
- adapt ordering, emphasis, length, wording, and user-specific constraints as needed;
- do not invent a second incompatible hook/angle/narrative solely for variety;
- any new factual claim added by the host must still be supported by current Radar evidence or explicitly marked for verification.

When `/insight` is degraded or unavailable, follow the Skill's existing degraded/evidence-skeleton rules and label the host-generated plan accordingly.

## 5. Quality target

The final answer should make it easy to tell:

- **what the live Radar observed**;
- **what the server Insight recommended** when used;
- **what the current host is judging or adapting**;
- **what remains unknown or must be verified**.

This contract strengthens interpretation and routing only. It must never create a second Radar score, local evidence fallback, or duplicate backend.

# Topic Intelligence quality contract

This reference tightens host behavior learned from real ChatGPT v0.2.0 smoke tests and defines the public Skill cost boundary. It does not change the Topic Radar evidence source of truth.

## 1. Separate Radar query constraints from content constraints

Keep these concepts separate:

- **Radar filters**: supported source/platform/region/category/topic dimensions such as YouTube, TikTok, Bilibili, Douyin, Xiaohongshu, region, category, source, `q`, or `keywords`.
- **Content constraints**: short video, 2–3 minute explainer, article, Chinese-language content, ordinary users, developers, parents, tone, research depth, and production style.

Never map content format, duration, language, audience, tone, or production constraints into Radar `platform` or `source` merely because the words resemble a platform/content concept.

Examples that remain post-query selection constraints unless the user explicitly names a supported Radar platform:

- `短视频` / `short video`;
- `2–3 分钟` / `2 minute explainer`;
- `中文` / `Chinese-language`;
- `图文` / `article` / `explainer`;
- `普通用户` / `开发者` / `家长`.

### Preserve explicit topic/domain scope from the first bounded query

Subject/domain constraints supplied by the user **must stay in the query**.

Examples:

- `AI 热点` / `AI topics` → the first bounded scan stays AI-focused instead of starting with generic technology;
- `机器人` / `robotics` → do not broaden to all technology unless necessary;
- `芯片` / `semiconductors` → preserve that domain with `q`, `keywords`, `category`, or another supported Radar field.

Only broaden the domain when the narrow live query produces too few useful candidates or the user asks for broader exploration. If broadening is necessary, say so briefly and retain the original domain as a relevance constraint.

### Reject literal substring noise without dropping the domain

A short query token such as `AI` may be matched literally inside an unrelated word or brand name. Treat the user-supplied domain as a **semantic relevance constraint**, not proof that every literal match belongs to that domain.

After the first domain-preserving bounded query:

1. verify that each candidate actually concerns the requested subject;
2. discard literal substring collisions and other clearly unrelated matches;
3. when noise leaves too few useful candidates, refine with supported domain terms, entities, or keywords while keeping the original domain constraint;
4. do not replace a noisy `AI` query with an unrestricted generic-technology scan.

For example, a title containing the letters `ai` only as part of an unrelated word must not become an AI finalist merely because `/feed?q=AI` returned it.

### Use the portable helper deterministically

Resolve `scripts/topic_radar_client.py` relative to the current Skill's `SKILL.md`; never hard-code an installation directory. `python3` is the only supported interpreter entry point. Do not use `python`, `python2`, or execute the helper directly without an interpreter.

Place helper-wide arguments before the subcommand. The canonical shortlist form is:

```text
python3 <skill-local-helper> --timeout 30 feed --q AI --limit 12
```

For a normal shortlist or topic-selection task, the initial candidate set defaults to 12 and should not exceed 24. Do not fetch 100 candidates merely to select three topics. Exceed 24 only when the user explicitly asks for a large list, export, or larger sample.

## 2. Public Skill cost boundary: no AI Workstation model spend

The downloadable/public Topic Intelligence Skills are intended to spread widely without consuming the publisher's server-side LLM quota for anonymous users.

Therefore the bundled public runtime may use only no-cost/read-only Radar evidence endpoints:

- `GET /feed`;
- `GET /sources`;
- `GET /history`.

The bundled helper must **not** expose or call anonymous/public `POST /insight` or another AI Workstation model-backed endpoint.

For the normal public Skill workflow:

1. fetch live Radar facts;
2. use the **current host model** (ChatGPT, Codex, or another agent host) to compare candidates and create the editorial brief;
3. label that creative/editorial work as host analysis, not Radar fact.

Never:

- embed an AI Workstation server API key in a Skill ZIP;
- use one shared public bearer token for all Skill users;
- ask users to paste private AI Workstation credentials into chat as a workaround;
- silently spend an AI Workstation member/free quota through an anonymous Skill call.

### Optional authenticated Premium capability

A server-generated Topic Insight may be used only through a **native authenticated AI Workstation connection** that itself identifies the user and enforces membership/quota/credits.

Examples of an acceptable future transport include an AI Workstation App/Plugin/OAuth connection or another host-native authenticated tool. The bundled public helper is not that authentication layer.

When no authenticated Premium connection exists, that is normal public-Skill mode—not a degraded error state. Generate the brief with host reasoning from live Radar evidence.

## 3. Preserve provenance in user-facing claims

Keep these layers distinguishable:

### Radar facts

Direct live fields from the current task such as title, evidence, source, timestamps, `opportunity_score`, `trend_stage`, freshness, source count, and history.

### Host editorial analysis

The current host/model's own comparison, recommendation, target-audience judgment, hook, angle, narrative, `must_verify`, `avoid_claims`, and visual/research plan when running in normal public mode.

Do not phrase judgments such as “更适合中国用户”, “受众更大”, “更容易传播”, “可能爆”, “监管更难”, or “最值得做” as though Radar directly measured them. Mark them as **分析/判断**, **编辑判断**, **假设**, or equivalent wording when the distinction matters.

### Authenticated Premium Topic Insight, when explicitly available

A Premium `/insight` response is still model-generated analysis over a server-known topic, not independent evidence. Preserve that provenance and do not treat it as verified fact merely because it came from the server.

Do not repeat a provenance label before every sentence; make the boundary visible at the section/claim level without making the answer unreadable.

## 4. Composition must not re-run broad selection after a valid handoff

When both Skills are installed:

1. `creator-topic-opportunity-research` selects exactly one finalist;
2. it hands off the exact live feed `id` through `ati.topic-opportunity-handoff.v1`;
3. `evidence-backed-content-brief` consumes that same `topic_id`;
4. after a valid current-task handoff, do **not** run another broad/bounded candidate-selection feed pass merely to choose again;
5. only refresh/re-resolve when the handoff is stale, materially partial, identity-invalid, from another task, or the user explicitly requests a fresh re-check.

A finalist `/history` request is normal and is not duplicate selection.

In normal public mode, continue from the handed-off Radar evidence with host reasoning. A selected-topic Premium Insight request is allowed only when an explicitly authenticated Premium AI Workstation transport is available and quota enforcement is outside the Skill package.

## 5. Public Brief uses host reasoning

In normal public mode the Brief Skill should create an evidence-bounded plan itself from live Radar facts. It may generate:

- make / conditional / watch recommendation;
- audience and audience payoff;
- why-now interpretation;
- one strongest angle;
- hook and opening three seconds;
- narrative beats;
- research questions and search queries;
- preferred source types;
- `must_verify`;
- `avoid_claims`;
- visual/material needs;
- known unknowns and risks.

These are editorial analysis unless directly backed by a Radar field. New factual specifics must be supported by current Radar evidence or clearly marked for verification.

## 6. Quality target

The final answer should make it easy to tell:

- **what the live Radar observed**;
- **what the current host is judging or adapting**;
- **what remains unknown or must be verified**;
- **whether an optional authenticated Premium Insight was actually used**.

This contract must never create a second Radar score, local evidence fallback, duplicate backend, shared secret, or anonymous server-side LLM spend.

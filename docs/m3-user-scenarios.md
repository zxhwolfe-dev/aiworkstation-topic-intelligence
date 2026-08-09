# M3 user scenarios

M3 shifts Topic Intelligence from "a correct distributable Skill package" to "a product people understand and return to use".

The product should not be evaluated only by trigger accuracy. The core M3 question is:

> Does a real user get a useful decision quickly enough that they want to use it again tomorrow?

v0.2.0 adds the M3.1 runtime/workflow quality layer without changing this product goal. See [`m3-skill-quality-acceptance.md`](m3-skill-quality-acceptance.md) and the final acceptance record in [`m3.1-final-acceptance-2026-08-09.md`](m3.1-final-acceptance-2026-08-09.md).

## Scenario 1 — Daily AI topic assistant

### User job

A creator, researcher, or operator wants a short list of AI/technology topics worth paying attention to **today**, without reading a generic news feed.

### Example prompt

```text
今天有哪些 AI 题材值得我继续研究或做内容？先检查 Radar 是否足够新，再给我最值得看的 3 个。
```

### Expected workflow

```text
creator-topic-opportunity-research
```

### Minimum useful answer

- Radar freshness/partial/stale status before recommendations;
- no more than 3–5 candidates by default;
- existing `opportunity_score`, stage, evidence breadth, and observed trend fields;
- one-sentence reason each candidate matters;
- clear fact vs inference boundary;
- next verification step;
- no generic list of unrelated company news.

### Activation signal

User gets at least one candidate they would save, research, or ask a follow-up about.

## Scenario 2 — Cross-market early opportunity

### User job

A Chinese-language creator/operator wants to know whether an overseas topic may deserve early attention before it becomes broadly covered in their target market.

### Example prompt

```text
海外现在有哪些科技话题正在升温、可能值得中文内容创作者提前研究？中文区是否已经做烂如果没有直接证据就明确说不知道。
```

### Expected workflow

```text
creator-topic-opportunity-research
```

### Minimum useful answer

- comparable time windows across markets/platforms;
- freshness and source coverage;
- observed multi-source/early-opportunity signals where available;
- cross-market propagation stated as a hypothesis unless directly evidenced;
- audience/content saturation explicitly labeled unknown when the Radar does not measure it;
- a suggested research angle, not a promise of virality.

### Activation signal

User chooses one candidate to investigate before publishing.

## Scenario 3 — From live topic to research-ready brief

### User job

The user wants the system to choose one current topic and continue directly into a structured research/production brief without manually rebuilding topic context.

### Example prompt

```text
从当前 AI 热点里挑一个适合 2–3 分钟解释型内容的题材，给我受众收益、最强角度、前三秒、叙事结构、必须核验的事实、不能乱说的内容和素材建议。
```

### Expected workflow when both Skills are available

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

The Opportunity Skill selects exactly one finalist. The handoff preserves the exact live feed `id`, parent freshness, observed topic fields, user constraints, and analysis/unknown/risk context. The Brief Skill consumes that same identity rather than rediscovering the topic by title.

### Brief-only fallback

If only `evidence-backed-content-brief` is installed, the scenario may still complete through the bounded standalone fallback:

```text
evidence-backed-content-brief:bounded-selection
  -> evidence-backed-content-brief
```

The fallback should normally inspect no more than five live feed candidates, select at most one using the existing Radar score/stage/freshness/evidence plus user constraints, and call insight only after selection. It must not recreate a full cross-market opportunity study or invent another score.

### Minimum useful answer

- current topic identity and freshness;
- one selected angle rather than a long brainstorm;
- audience payoff and platform/format fit;
- opening/hook and narrative beats;
- `must_verify` and `avoid_claims` visible;
- `fact_basis` separated from model/Skill analysis;
- research questions/search handoff;
- visual/material needs.

### Activation signal

User can hand the result directly to research, scripting, or production without rebuilding the brief from scratch.

## Non-scenarios

The following should normally **not** invoke Topic Intelligence:

- `OpenAI今天发布了什么新消息？`
- `把这段 AI 新闻翻译成英文。`
- `我资料都给你了，写成 3 分钟口播。`
- `TikTok 和 YouTube 视频风格有什么区别？`
- `英伟达现在市值多少？`

They may be current, AI-related, or content-related, but they do not contain the creator/editorial live-topic decision that Topic Intelligence is designed for.

## M3 adoption metrics

Do not optimize M3 around test count. Track the smallest product signals that show repeat value.

### Activation

A session is activated when the user does at least one of:

- selects/saves a proposed topic;
- asks to expand one candidate;
- requests the content-brief workflow for a candidate;
- requests follow-up verification/research for a candidate.

### Short-term return

The strongest early signal is a user returning on another day to ask for a fresh scan or another current-topic brief.

Suggested early metrics:

- `scan_to_followup_rate` — sessions where a shortlist produces a candidate-specific follow-up;
- `scan_to_brief_rate` — scans that continue into `evidence-backed-content-brief`;
- `next_day_return_rate` — users who run another fresh current-topic task the next day;
- `blocked_live_data_rate` — sessions blocked because live Radar evidence is unavailable;
- `no_useful_candidate_rate` — scans where the user rejects all candidates.

These are product signals, not new Radar scores. Do not feed them back into `opportunity_score` without a separate product decision.

## M3.1 acceptance result

The adoption scenario remains the product target; M3.1 was the runtime/task-quality gate that made the public Skill artifacts capable of delivering it reliably.

v0.2.0 completed the required validation before release:

- standalone ZIP runtime;
- creator-only install;
- brief-only install;
- both-Skills handoff continuity;
- previous trigger safety;
- live evidence boundaries;
- the M3.1 task-quality matrix;
- real network-capable fresh-session flows.

The release decision and final evidence are recorded in [`release-v0.2.0-decision.md`](release-v0.2.0-decision.md) and [`m3.1-final-acceptance-2026-08-09.md`](m3.1-final-acceptance-2026-08-09.md). The immutable `v0.2.0` tag is now the public release reference for this capability set.

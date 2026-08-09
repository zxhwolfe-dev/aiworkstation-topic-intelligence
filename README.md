# AI Workstation Topic Intelligence

**Find the current topics worth researching — then turn one into a research-ready content brief.**

[简体中文](README.zh-CN.md)

Latest public release: **v0.1.0 public preview**

Topic Intelligence sits on top of the existing AI Workstation Global Topic Radar. It does not build another crawler, score, database, or GPT backend. Its job is to help an AI host turn live Radar evidence into a useful creator/editorial decision without pretending stale files or model memory are current facts.

## What can I use it for?

### 1. What is worth researching today?

```text
今天有哪些 AI 题材值得我继续研究或做内容？先检查 Radar 是否足够新，再给我最值得看的 3 个。
```

Expected Skill:

```text
creator-topic-opportunity-research
```

You should get a compact shortlist with freshness, evidence, observed momentum, fact-vs-inference boundaries, and next verification steps — not a generic news feed.

### 2. Is there a cross-market early opportunity?

```text
海外现在有哪些科技话题正在升温、可能值得中文内容创作者提前研究？中文区是否已经做烂如果没有直接证据就明确说不知道。
```

The Skill can compare live platform/region signals, but audience saturation and propagation timing remain hypotheses unless the current evidence directly supports them.

### 3. Turn a live topic into a research-ready brief

```text
从当前 AI 热点里挑一个适合 2–3 分钟解释型内容的题材，给我受众收益、最强角度、前三秒、叙事结构、必须核验的事实、不能乱说的内容和素材建议。
```

Expected workflow:

```text
creator-topic-opportunity-research
  -> evidence-backed-content-brief
```

The output should be ready to hand off into research, scripting, or production rather than forcing you to rebuild the brief manually.

See [`docs/m3-user-scenarios.md`](docs/m3-user-scenarios.md) for the M3 product scenarios and adoption metrics.

## Choose your entry path

### Codex / developers

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

Default destination:

```text
$HOME/.agents/skills/
```

Explicit invocation:

```text
$creator-topic-opportunity-research
$evidence-backed-content-brief
```

The installer is idempotent, refuses unrelated paths, and safely migrates the internal pre-0.1.0 `cross-market-trend-research` symlink only when it belongs to this checkout.

### ChatGPT

OpenAI's current Help Center says Personal Skills are generally available for ChatGPT Business, Enterprise, Healthcare, and Edu users; workspace permissions can further restrict creation/upload/install. Personal Skills currently need to be added separately on desktop and web/mobile rather than automatically syncing across those surfaces.

For eligible users, ChatGPT currently exposes Skill upload under **Plugins → Skills → Create → Upload from your computer**. See [`docs/chatgpt-install.md`](docs/chatgpt-install.md) for the current install path and product caveats.

Official reference: https://help.openai.com/en/articles/20001066

Do not treat ChatGPT Skill upload as the only product entry: M3 is explicitly testing a direct AI Workstation user-facing entry for people who should not need to understand Agent Skills before receiving value. The proposed landing/CTA copy is in [`docs/website-entry-copy.zh-CN.md`](docs/website-entry-copy.zh-CN.md).

## The two Skills

### `creator-topic-opportunity-research`

Compare and prioritize live Topic Radar candidates for creator/editorial publishing decisions, including:

- rising/early opportunities;
- source freshness and coverage;
- platform or region differences;
- multi-source evidence;
- evidence-aware cross-market timing hypotheses.

### `evidence-backed-content-brief`

Turn a **current Topic Radar topic resolved from live evidence** into a practical content brief with:

- selected angle;
- audience payoff and format fit;
- hook/opening/narrative beats;
- research questions and search handoff;
- `must_verify`;
- `avoid_claims`;
- `fact_basis` and unsupported assumptions;
- visual/material needs.

## Hard evidence boundary

When the live Topic Radar contract is unavailable, the Skills must stop the current-topic workflow instead of searching local files for replacement evidence.

The following are **never valid substitutes for current live evidence**:

- sibling-repository data such as old `../akaiagents` snapshots;
- SQLite databases;
- fixtures or test captures;
- cached/exported JSON;
- logs, generated reports, or other persisted historical artifacts;
- model memory presented as current Radar evidence.

A network-restricted sandbox is an unavailable-live-data state, not permission to fabricate a current shortlist.

Also keep these layers separate:

1. **Source facts** — current Radar fields and evidence;
2. **Analysis** — interpretation of those fields;
3. **Recommendations** — what the user may want to research/publish;
4. **Unknowns** — what the current evidence does not establish;
5. **Risks** — stale/partial coverage, weak evidence, source gaps, unsupported claims.

## Product boundary

```text
AI Workstation Global Topic Radar (akaiagents)
  public sources -> aggregation -> clustering -> opportunity score
  -> trend/history -> source health -> optional GPT topic insight
                              |
                              | public API
                              v
AI Workstation Topic Intelligence
  Skills -> evidence checks -> cross-market interpretation
  -> topic opportunity decision -> content brief orchestration
```

Topic Intelligence intentionally does not duplicate crawlers, clustering, `opportunity_score`, persistence, source health, or the existing GPT topic-insight backend.

## Existing Topic Radar API

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`

Default public origin: `https://aiworkstation.cn`.

Feed cards expose stable topic identity as `id`; pass that exact value as `topic_id` to history/insight.

When `refreshing=true`, sequential feed/history/sources calls are not an atomic snapshot. Interpret between-request changes using timestamps and refresh state.

## Release / local helper

Build standalone Skill archives:

```bash
python3 scripts/build_release.py --output dist
```

The release contains two deterministic, Apache-2.0 licensed Skill ZIPs plus `release-manifest.json` and `SHA256SUMS`.

Optional read-only API helper:

```bash
python3 scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history TOPIC_ID
python3 scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

The helper uses only the Python standard library and does not implement new scoring, crawling, persistence, or model logic.

## Validation

```bash
python3 -m unittest discover -s tests -v
```

The existing trigger matrix contains 20 real-world positive/negative cases. M3 adds a separate user-scenario contract in [`evals/m3-scenarios.json`](evals/m3-scenarios.json) so product adoption is evaluated independently from Skill routing correctness.

## M3 product signals

M3 is not optimizing for more infrastructure or more unit tests. The early product signals are:

- `scan_to_followup_rate`;
- `scan_to_brief_rate`;
- `next_day_return_rate`;
- `blocked_live_data_rate`;
- `no_useful_candidate_rate`.

These are adoption metrics, not a replacement for Radar `opportunity_score`.

## More docs

- ChatGPT install/current availability: [`docs/chatgpt-install.md`](docs/chatgpt-install.md)
- M3 user scenarios: [`docs/m3-user-scenarios.md`](docs/m3-user-scenarios.md)
- Proposed AI Workstation website entry copy: [`docs/website-entry-copy.zh-CN.md`](docs/website-entry-copy.zh-CN.md)
- Distribution: [`docs/distribution.md`](docs/distribution.md)
- Release checklist: [`docs/release-checklist.md`](docs/release-checklist.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)

## Environment

- Python 3.10+
- no third-party runtime dependency for the helper, installer, or release builder
- do not depend on `../akaiagents/.venv`
- do not import private `akaiagents` modules

## Status

- **M0 complete:** Skill-first foundation and production API contract.
- **M1 complete:** Codex install/discovery, trigger evals, evidence-boundary hardening, real insight E2E.
- **M2 complete:** v0.1.0 public preview, deterministic artifacts, release automation, diagnostics, final Skill names, and expanded trigger boundaries.
- **M3 in progress:** user-facing entry, installation clarity, three real product scenarios, and adoption/return validation before deciding on v0.2.0 engineering.

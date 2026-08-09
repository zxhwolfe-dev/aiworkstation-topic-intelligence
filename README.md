# AI Workstation Topic Intelligence

**Find the current topics worth researching — then turn one into a research-ready content brief.**

[简体中文](README.zh-CN.md)

Latest public release: **v0.1.0 public preview**

Development line: **v0.2.0 unreleased** — standalone Skill runtime, formal Opportunity → Brief handoff, single-Skill fallback, and task-quality acceptance. No `v0.2.0` tag/release exists until fresh-session validation passes.

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

### 3. Pick a live topic and turn it into a brief

```text
从当前 AI 热点里挑一个适合 2–3 分钟解释型内容的题材，给我受众收益、最强角度、前三秒、叙事结构、必须核验的事实、不能乱说的内容和素材建议。
```

Preferred workflow when both Skills are installed:

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

The first Skill selects one current topic and hands the exact live feed `id`, freshness context, observed signals, unknowns, risks, and user constraints to the Brief Skill. A valid current-task handoff avoids rediscovering the same topic from its title.

If only `evidence-backed-content-brief` is installed, it remains useful: it can resolve a supplied topic directly or run one bounded live-feed selection pass (normally <=5 candidates), select at most one using the existing Radar score/stage/freshness/evidence, and call insight only for that selected topic. It never invents a second score or forces a weak candidate.

## The two Skills

### `creator-topic-opportunity-research`

Compare and prioritize live Topic Radar candidates for creator/editorial publishing decisions, including:

- rising/early opportunities;
- source freshness and coverage;
- platform or region differences;
- multi-source evidence;
- evidence-aware cross-market timing hypotheses;
- one structured handoff when a selected candidate continues into the Brief Skill.

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

It accepts a valid current-task `ati.topic-opportunity-handoff.v1`, a user-supplied current topic resolved from live Radar, or its bounded standalone selection fallback when the Opportunity Skill is unavailable.

## Standalone runtime — v0.2 development line

Each Skill directory is now designed to be a complete portable unit:

```text
skill-name/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/handoff-contract.md
  LICENSE   # included in release ZIP
```

That means a standalone Skill ZIP no longer depends on repository-root `scripts/topic_radar_client.py` or a sibling `../akaiagents` checkout.

The two bundled helper copies are tested byte-for-byte against the root development helper. Release building fails if the helper or handoff contract is missing.

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

`doctor` now validates the Skill definition, OpenAI metadata, bundled runtime helper, and handoff contract.

### Standalone ZIP

Build deterministic archives:

```bash
python3 scripts/build_release.py --output dist
```

Each ZIP contains one Skill root plus its own runtime/helper/reference files and Apache-2.0 license. See [`docs/distribution.md`](docs/distribution.md).

### ChatGPT

For eligible ChatGPT workspaces, use the currently supported Skill-upload flow documented by OpenAI. Personal Skill availability and workspace permissions can vary, and installed Skills do not necessarily sync automatically across every surface.

See [`docs/chatgpt-install.md`](docs/chatgpt-install.md). ChatGPT UI upload is a separate manual acceptance surface; Codex validation cannot prove that UI behavior.

## Hard evidence boundary

When the live Topic Radar contract is unavailable, the Skills must stop the current-topic workflow instead of searching local files for replacement evidence.

The following are **never valid substitutes for current live evidence**:

- sibling-repository data such as old `../akaiagents` snapshots;
- SQLite databases;
- fixtures or test captures;
- cached/exported JSON;
- logs, generated reports, or other persisted historical artifacts;
- an old saved Topic Opportunity handoff;
- model memory presented as current Radar evidence.

A network-restricted sandbox is an unavailable-live-data state, not permission to fabricate a current shortlist.

Also keep these layers separate:

1. **Source facts** — current Radar fields and evidence;
2. **Analysis** — interpretation of those fields;
3. **Recommendations** — what the user may want to research/publish;
4. **Unknowns** — what the current evidence does not establish;
5. **Risks** — stale/partial coverage, weak evidence, source gaps, unsupported claims;
6. **Topic Insight** — model-generated analysis over a known topic, not an independent fact source.

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
  -> topic opportunity decision -> current-task handoff
  -> content brief orchestration
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

## Validation

Offline suite:

```bash
python3 -m unittest discover -s tests -v
```

The suite now validates:

- previous trigger/evidence/release guarantees;
- Skill-local helper parity;
- deterministic standalone archives;
- extracted ZIP helper execution from outside the repository against a local fake Radar service;
- handoff contract consistency;
- bounded Brief fallback rules;
- a 24-case M3.1 task-quality matrix.

Quality scenarios:

- [`evals/m3-skill-quality.json`](evals/m3-skill-quality.json)
- [`docs/m3-skill-quality-acceptance.md`](docs/m3-skill-quality-acceptance.md)

Fresh Codex/live-network acceptance is still required before a v0.2.0 release decision.

## More docs

- M3.1 Skill quality acceptance: [`docs/m3-skill-quality-acceptance.md`](docs/m3-skill-quality-acceptance.md)
- Distribution: [`docs/distribution.md`](docs/distribution.md)
- Release checklist: [`docs/release-checklist.md`](docs/release-checklist.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- ChatGPT install/current availability: [`docs/chatgpt-install.md`](docs/chatgpt-install.md)
- M3 user scenarios: [`docs/m3-user-scenarios.md`](docs/m3-user-scenarios.md)

## Environment

- Python 3.10+
- no third-party runtime dependency for the helper, installer, or release builder
- do not depend on `../akaiagents/.venv`
- do not import private `akaiagents` modules

## Status

- **M0 complete:** Skill-first foundation and production API contract.
- **M1 complete:** Codex install/discovery, trigger evals, evidence-boundary hardening, real insight E2E.
- **M2 complete:** v0.1.0 public preview, deterministic artifacts, release automation, diagnostics, final Skill names, and expanded trigger boundaries.
- **M3 adoption baseline complete:** user-facing entry docs and three product scenarios.
- **M3.1 in progress:** self-contained standalone Skills, formal Opportunity → Brief handoff, brief-only fallback, package E2E, and task-quality/fresh-session acceptance for the unreleased 0.2 line.

# AI Workstation Topic Intelligence

**Find the current topics worth researching — then turn one into a research-ready content brief.**

[简体中文](README.zh-CN.md)

Current package version: **v0.3.0**

v0.2.0 proved the original standalone packages could upload/run in ChatGPT and reach the live Radar. v0.3.0 presents that capability as one public Skill and one install package with three intent-driven modes. It keeps deterministic `python3` helper invocation, bounded Radar scans, strict runtime/evidence grading, isolated Skill fixtures and neutral Host workspaces, and persistent release evidence. **Normal public Skill usage must not consume AI Workstation server-side LLM quota.**

Topic Intelligence sits on top of the existing AI Workstation Global Topic Radar. It does not build another crawler, score, database, or persistence layer.

## One Skill, three automatic modes

### 1. What is worth researching today?

```text
今天有哪些 AI 题材值得我继续研究或做内容？先检查 Radar 是否足够新，再给我最值得看的 3 个。
```

The `topic-intelligence` Skill reads live Radar evidence, checks freshness/source coverage, and uses the **host model** to explain which candidates may be worth researching. It stops at the requested shortlist and does not add an unsolicited brief.

### 2. Is there a cross-market early opportunity?

```text
海外现在有哪些科技话题正在升温、可能值得中文内容创作者提前研究？中文区是否已经做烂如果没有直接证据就明确说不知道。
```

Cross-market timing or audience saturation remain hypotheses unless the current Radar evidence directly establishes them.

### 3. Pick a live topic and turn it into a brief

```text
从当前 AI 热点里挑一个适合 2–3 分钟解释型内容的题材，给我受众收益、最强角度、前三秒、叙事结构、必须核验的事实、不能乱说的内容和素材建议。
```

The same Skill automatically selects the smallest workflow:

```text
selection only
supplied current topic -> brief
one bounded selection -> brief for the same finalist
```

The combined mode performs one bounded feed, preserves the exact live `id`, and does not reselect while writing the brief.

## Public Skill cost boundary — v0.3.0

The distributable public Skill is designed to spread without silently spending the publisher's model budget.

### Public bundled runtime

The bundled helper exposes only:

```text
GET /api/v1/ai/topic-radar/feed
GET /api/v1/ai/topic-radar/sources
GET /api/v1/ai/topic-radar/history?topic_id=...
```

Normal public Skill flow:

```text
live Radar facts
      ↓
user's current ChatGPT / Codex / agent host model
      ↓
selection / explanation / research-ready brief
```

Therefore normal public Skill usage produces **zero AI Workstation server-side LLM calls**.

The public ZIP does not:

- expose an anonymous `insight` CLI command;
- embed an AI Workstation API key;
- contain a shared bearer token;
- ask the user to paste a private credential into chat;
- silently consume the website's free/member model quota.

### Optional future Premium capability

AI Workstation may still provide server-generated Topic Insight as a paid/account-bound enhancement, but only through a **native authenticated AI Workstation connection** that identifies the user and enforces membership/quota/credits.

For example, a future AI Workstation App/Plugin/OAuth connection could expose Premium Insight. The public bundled helper is intentionally **not** that authentication layer.

No authenticated Premium connection is required to use the public Skill. The host model completes the brief itself.

## The public Skill

### `topic-intelligence`

Compare and prioritize live Radar candidates, or turn one current Radar topic into a practical, evidence-bounded content plan with:

- recommendation and audience payoff;
- strongest angle;
- hook / opening three seconds;
- narrative beats;
- research questions and search handoff;
- `must_verify`;
- `avoid_claims`;
- visual/material needs;
- known unknowns and risks;
- a single current-task selection-to-brief workflow when both are requested.

In normal public mode these editorial fields are produced by the **host model**, not by an AI Workstation server model.

## Query-quality rules

v0.3.0 carries forward the hardening from v0.2.2 and makes it the default public package:

- content format/duration/language/audience are **not** Radar platform/source filters;
- explicit topic scope must be preserved from the first query (`AI` should not first expand to generic technology);
- Radar facts and host editorial judgments must remain distinguishable;
- a valid handoff must not be followed by another broad candidate-selection pass.

Canonical rule set:

```text
references/topic-intelligence-quality-contract.md
```

The package carries the same contract at:

```text
references/quality-contract.md
```

## Standalone runtime

The single Skill release archive is self-contained:

```text
topic-intelligence/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/quality-contract.md
  references/selection-workflow.md
  references/brief-workflow.md
  LICENSE
```

Release building fails if portable runtime/reference copies drift from their canonical sources.

## Installation

### Codex / developers

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

Default destination:

```text
$HOME/.agents/skills/
```

### Standalone ZIP

```bash
python3 scripts/build_release.py --output dist
```

See [`docs/distribution.md`](docs/distribution.md).

### ChatGPT

The published v0.2.0 ZIPs were manually tested in ChatGPT web in Creator-only, Brief-only, and both-Skills shapes. v0.3.0 consolidates those user-facing workflows into one package; its Codex/Host Eval evidence does not claim a new ChatGPT Web upload test.

The v0.2.1 and v0.2.2 Host/Codex Eval results remain historical acceptance records, not claims that their ChatGPT Web ZIP upload UI was re-tested. v0.3.0 was published with its own complete live Host Eval evidence and verifier approval.

See:

- [`docs/chatgpt-install.md`](docs/chatgpt-install.md)
- [`docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md`](docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md)
- [`docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md`](docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md)

## Hard evidence boundary

For current-state claims, valid evidence comes from current live Radar responses (or equivalent current responses explicitly supplied by the user/native host).

Never substitute:

- sibling-repository snapshots;
- SQLite data;
- fixtures/test captures;
- cached/exported JSON;
- logs/generated reports;
- old saved handoffs;
- model memory presented as current Radar evidence.

Keep these layers clear:

1. **Radar facts** — current data/evidence/score/stage/history;
2. **Host editorial analysis** — selection, audience, angle, hook, narrative, recommendations;
3. **Unknowns / verification** — claims the current evidence does not establish;
4. **Authenticated Premium Insight** — optional server model analysis, when an authenticated account-bound connection explicitly provides it; still not independent fact evidence.

## Product boundary

```text
AI Workstation Global Topic Radar
  public sources -> aggregation -> clustering -> opportunity score
  -> trend/history -> source health
                         |
                         | public read API
                         v
AI Workstation Topic Intelligence public Skill
  evidence checks -> automatic selection / supplied-topic brief
  -> same-finalist host-model content brief when requested

Future optional Premium connection
  authenticated user -> membership/quota enforcement
  -> server Topic Insight
```

The public Skill repository intentionally does not duplicate crawlers, clustering, score, persistence, billing, authentication, or the server model backend.

For operating guidance, examples, the official download path, and anonymous metrics/privacy boundaries, see [`docs/topic-intelligence-operations.md`](docs/topic-intelligence-operations.md).

## Validation

```bash
python3 scripts/sync_skill_runtime.py --check
python3 -m unittest discover -s tests -v
```

The suite covers:

- trigger/evidence boundaries;
- portable helper/reference parity;
- deterministic standalone archives;
- extracted ZIP execution outside the repository;
- unified selection/brief mode rules;
- bounded scan and no-reselection rules;
- ChatGPT-derived v0.2.1 query/provenance/cost cases;
- proof that the public helper exposes no `insight` command and emits only GET requests.

Useful evidence:

- [`evals/v0.3.0-skill-quality.json`](evals/v0.3.0-skill-quality.json)
- [`evals/host-capabilities.json`](evals/host-capabilities.json)
- [`docs/m3.1-final-acceptance-2026-08-09.md`](docs/m3.1-final-acceptance-2026-08-09.md)
- [`docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md`](docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md)
- [`docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md`](docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md)

## Environment

- Python 3.10+
- no third-party runtime dependency for the public helper, installer, or release builder
- no dependency on `../akaiagents/.venv`
- no private `akaiagents` imports

## Status

- **v0.3.0:** current package line; one public Skill and one ZIP expose three intent-driven modes, with deterministic helper calls, isolated Host execution, and persistent live evidence.
- **v0.2.2:** immutable two-Skill historical package line with persistent Host Eval evidence.
- **v0.2.1:** prior immutable Host-validated package line; its Codex/Host Eval does not represent ChatGPT Web UI validation.
- **v0.2.0:** previous immutable release and the most recent version manually uploaded in ChatGPT web.

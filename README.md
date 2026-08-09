# AI Workstation Topic Intelligence

**Evidence-aware trend research and content-planning Skills on top of AI Workstation Global Topic Radar.**

[简体中文](README.zh-CN.md)

Current distributable version: **0.1.0 public preview**

This repository does **not** collect, crawl, cluster, score, or persist trend data. Those responsibilities remain in the AI Workstation Global Topic Radar inside `akaiagents`. Topic Intelligence is the thin Skills/workflow layer that teaches supported AI hosts how to use that live data without turning model guesses or stale local files into current facts.

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
  -> content opportunity reasoning -> content brief orchestration
```

Topic Intelligence intentionally does not duplicate crawlers, topic clustering, scoring, persistence, source health, or the existing GPT topic-insight backend.

## Skills

### `cross-market-trend-research`

Use live Topic Radar data to find current topics, rising/early opportunities, platform or region differences, and evidence-aware cross-market timing hypotheses.

Typical request:

> What overseas AI topics are rising now and may be worth early attention for Chinese creators?

### `evidence-backed-content-brief`

Turn a **current Topic Radar topic resolved from live evidence** into a practical content brief using the existing `/insight` contract for angles, hooks, audiences, research questions, verification requirements, and claims to avoid.

Typical request:

> Pick one current AI topic for a 2–3 minute explainer and give me a research-ready brief.

## Hard evidence boundary

When the live Topic Radar contract is unavailable, the Skills must stop the current-topic workflow instead of searching local files for replacement evidence.

The following are **never valid substitutes for current live evidence**:

- sibling-repository data such as old `../akaiagents` snapshots;
- SQLite databases;
- fixtures or test captures;
- cached/exported JSON;
- logs, generated reports, or other persisted historical artifacts.

A network-restricted sandbox is an unavailable-live-data state, not permission to use stale local data or model memory.

## Codex quick start

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

Default destination:

```text
$HOME/.agents/skills/
```

The installer uses safe symlinks, is idempotent, and refuses to overwrite unrelated paths.

Useful commands:

```bash
python3 scripts/install_codex_skills.py version
python3 scripts/install_codex_skills.py status
python3 scripts/install_codex_skills.py doctor
python3 scripts/install_codex_skills.py uninstall
```

Inside interactive Codex, `/skills` can confirm discovery when available. Explicit invocation uses `$cross-market-trend-research` or `$evidence-backed-content-brief`; implicit invocation is covered by the eval suite.

## Build standalone Skill archives

```bash
python3 scripts/build_release.py --output dist
```

Output:

```text
dist/
  aiworkstation-topic-intelligence-0.1.0-cross-market-trend-research.zip
  aiworkstation-topic-intelligence-0.1.0-evidence-backed-content-brief.zip
  release-manifest.json
  SHA256SUMS
```

Each ZIP contains one self-contained Skill directory. Builds are deterministic and symlinks inside a Skill package are rejected.

See [`docs/distribution.md`](docs/distribution.md) for Codex, ChatGPT upload, GitHub Release, upgrade, and future Plugin/Hosted-MCP policy.

## ChatGPT distribution

Current OpenAI product documentation supports reusable Skills in ChatGPT and allows eligible users/workspaces to create or upload Skills from a computer. OpenAI Skills follow the Agent Skills open standard.

Use the standalone archive for the Skill you want to install. Availability and workspace permissions depend on the current ChatGPT plan/surface configuration.

Do not assume a Skill installed on one ChatGPT surface automatically replaces or syncs every other installation.

## Existing Topic Radar API

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`

Default public origin: `https://aiworkstation.cn`.

### Topic identity

- feed cards expose stable identity as `id`;
- pass that exact value as `topic_id` to history or insight;
- history and insight return the same identity as `topic_id`.

### Refresh consistency

When `refreshing=true`, sequential feed/history/sources calls are not an atomic snapshot. Interpret between-request changes using timestamps and refresh state.

## Optional local API helper

`scripts/topic_radar_client.py` uses only the Python standard library and contains no scoring, clustering, crawler, persistence, or new model logic.

```bash
python3 scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history TOPIC_ID
python3 scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

Ordinary reads use a short timeout; the model-backed `/insight` call has a separate longer timeout budget.

## Validation

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions runs the offline suite on Python 3.10 and 3.12.

The eval matrix currently contains **20 real-world trigger cases** covering:

- current/rising/early topic research;
- platform and cross-market comparisons;
- content briefs and verification-heavy briefs;
- stale/partial source handling;
- generic writing, translation, supplied-material scripting, coding, company-news lookup, and platform-style questions that should **not** invoke Topic Intelligence.

M1 acceptance established zero observed false positives and zero false negatives on the original 12-case suite; M2 expands that boundary set before the first public-preview tag.

## Codex acceptance gates

### Gate A — discovery, trigger, evidence behavior

A safe network-restricted/read-only Codex sandbox is suitable for testing Skill selection, negative cases, safe degradation, and rejection of local/sibling snapshot fallback.

### Gate B — live Topic Radar E2E

Live E2E must use an execution path explicitly allowed to reach Topic Radar. Do not broaden filesystem permissions to a dangerous mode merely to regain network access.

See [`docs/codex-m1-acceptance.md`](docs/codex-m1-acceptance.md).

## Release process

- Version: [`VERSION`](VERSION)
- Changes: [`CHANGELOG.md`](CHANGELOG.md)
- Distribution: [`docs/distribution.md`](docs/distribution.md)
- Release gate: [`docs/release-checklist.md`](docs/release-checklist.md)

A Git tag `vX.Y.Z` that matches `VERSION` triggers the release workflow. It runs tests, builds deterministic Skill ZIPs, and publishes the archives plus manifest/checksums to GitHub Releases.

No tag is created automatically by normal branch/PR work.

## Plugin and Hosted MCP direction

OpenAI currently positions Plugins as a higher-level container that can package Skills and optionally Apps/app templates.

M2 deliberately does **not** invent an unofficial Plugin manifest. Plugin packaging should be added only when the relevant official builder/schema/submission path is publicly documented and can be validated.

Hosted MCP is also deferred. If later needed for reliable host networking, it must remain a thin transport/auth/tool layer over the existing Topic Radar rather than becoming a second backend.

## Environment

- Python 3.10+
- no third-party runtime dependency for the helper, installer, or release builder
- do not depend on `../akaiagents/.venv`
- do not import private `akaiagents` modules

## Status

- **M0 complete:** Skill-first foundation and production API contract.
- **M1 complete:** Codex install/discovery, trigger evals, evidence-boundary hardening, real insight E2E.
- **M2 in progress:** versioned public-preview distribution, deterministic artifacts, release automation, diagnostics, and expanded eval coverage.

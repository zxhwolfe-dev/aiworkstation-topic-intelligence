# AI Workstation Topic Intelligence

**Skills for evidence-aware trend research and content planning on top of AI Workstation Global Topic Radar.**

[简体中文](README.zh-CN.md)

This repository does **not** collect, crawl, cluster, score, or persist trend data. Those responsibilities remain in the AI Workstation Global Topic Radar inside `akaiagents`. This repository is the thin Skills/workflow layer that teaches an AI host how to use that live data without turning model guesses or stale local files into current facts.

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

### `evidence-backed-content-brief`

Turn a **current Topic Radar topic resolved from live evidence** into a practical content brief using the existing `/insight` contract for angles, hooks, audiences, research questions, verification requirements, and claims to avoid.

## Hard evidence boundary

When the live Topic Radar contract is unavailable, the Skills must stop the current-topic workflow instead of searching local files for replacement evidence.

The following are **never valid substitutes for current live evidence**:

- sibling-repository data such as old `../akaiagents` snapshots;
- SQLite databases;
- fixtures or test captures;
- cached/exported JSON;
- logs, generated reports, or other persisted historical artifacts.

Those materials can be used for development/testing, but they cannot support claims such as “this topic is trending now”.

A network-restricted sandbox is an unavailable-live-data state, not permission to use stale local data or model memory.

## Install locally in Codex

Install both Skills as safe symlinks into the Codex user Skill directory:

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py status
```

Default destination:

```text
$HOME/.agents/skills/
```

The installer is idempotent and refuses to overwrite an unrelated existing Skill path. It keeps this checkout as the source of truth.

Inside interactive Codex, `/skills` can confirm discovery when available. Explicit invocation uses `$cross-market-trend-research` or `$evidence-backed-content-brief`; M1 also evaluates implicit trigger selection.

## Codex M1 has two acceptance gates

### Gate A — discovery, trigger, and evidence behavior

A safe network-restricted/read-only Codex sandbox is suitable for testing:

- Skill discovery/selection;
- positive and negative triggers;
- safe degradation when live data is unavailable;
- rejection of local/sibling snapshot fallback.

### Gate B — live Topic Radar E2E

Codex sandbox policy can restrict network access. A DNS or connection failure inside a network-restricted sandbox is not, by itself, evidence that Topic Radar production is down.

Live E2E validation must use an execution path explicitly allowed to reach the Topic Radar origin, such as the normal shell running the read-only helper, a host configuration with suitable network permission, or an equivalent native host/MCP connection.

Do not broaden filesystem permissions to a dangerous mode merely to regain network access.

See [`docs/codex-m1-acceptance.md`](docs/codex-m1-acceptance.md).

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

When `refreshing=true`, sequential feed/history/sources calls are not an atomic snapshot. A newly persisted history point between reads is normal and should be interpreted using timestamps and refresh state.

## Optional local API helper

`scripts/topic_radar_client.py` uses only the Python standard library and contains no scoring, clustering, crawler, persistence, or new model logic.

```bash
python3 scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history TOPIC_ID
python3 scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

The `insight` command calls the existing Topic Radar GPT analysis capability.

## Environment

- Python 3.10+
- no third-party runtime dependency for the helper/installer
- do not depend on `../akaiagents/.venv`
- do not import private `akaiagents` modules

## Validation

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions runs the offline suite on Python 3.10 and 3.12. M1 additionally validates Skill installation, trigger behavior, negative cases, local-evidence rejection, and the live Radar contract.

## Evidence layers

Keep these distinct:

1. **Source facts** — current Topic Radar fields with freshness/evidence context.
2. **Analysis** — interpretation of those fields.
3. **Recommendations** — what the user should consider doing.
4. **Unknowns** — what current evidence does not establish.
5. **Risks** — stale/partial coverage, source outages, weak evidence, or unsupported claims.

`/insight` is model analysis over a server-known topic, not a new verified-fact source.

## Status

- M0 is merged and production-contract validated.
- M1 adds Codex installation/discovery metadata, trigger evals, and hardened live-evidence boundaries before plugin or hosted-MCP productization.

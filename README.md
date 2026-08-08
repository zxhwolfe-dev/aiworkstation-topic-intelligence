# AI Workstation Topic Intelligence

**Skills for evidence-aware trend research and content planning on top of AI Workstation Global Topic Radar.**

[简体中文](README.zh-CN.md)

This repository does **not** collect, crawl, cluster, score, or persist trend data. Those responsibilities already live in the AI Workstation Global Topic Radar inside `akaiagents`. This repository is the thin Skills/workflow layer that teaches an AI host how to use that existing live data without turning model guesses into current facts.

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

Topic Intelligence intentionally does not duplicate:

- NewsNow, TrendRadar, MediaCrawler, TikTok, YouTube, Hacker News, or RSS connectors;
- topic clustering or deduplication;
- `opportunity_score`, `trend_stage`, or history calculations;
- source-health, cache, stale-data, or persistence logic;
- the existing GPT topic-insight service.

## Skills

### `cross-market-trend-research`

Use live Topic Radar data to find current topics, rising/early opportunities, platform or region differences, and plausible cross-market timing gaps. It treats cross-market propagation as an inference unless the live evidence actually supports it.

### `evidence-backed-content-brief`

Turn a verified Topic Radar topic into a practical content brief. It can use the existing `/insight` contract for recommended formats, audiences, three content angles, hooks, opening seconds, research questions, verification requirements, and claims to avoid.

## Install locally in Codex

For local Codex validation, install both Skills as safe symlinks into the user Skill directory:

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py status
```

Default destination:

```text
$HOME/.agents/skills/
```

The installer is idempotent and refuses to overwrite an unrelated existing Skill path. It keeps this repository as the source of truth, so edits on the checked-out branch are immediately visible through the symlink.

Inside Codex, use `/skills` to confirm discovery. You can explicitly invoke a Skill with `$cross-market-trend-research` or `$evidence-backed-content-brief`. Implicit invocation is also enabled and is evaluated separately in M1.

To remove only symlinks created from this checkout:

```bash
python3 scripts/install_codex_skills.py uninstall
```

See [`docs/codex-m1-acceptance.md`](docs/codex-m1-acceptance.md) and [`evals/README.md`](evals/README.md).

## Existing Topic Radar API

The Skills are built around the current public contract:

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`

The default public origin is `https://aiworkstation.cn`. Local or staging environments can set:

```bash
export AIWORKSTATION_TOPIC_RADAR_BASE_URL=http://127.0.0.1:8000
```

### Topic identity

The production contract names the stable identifier differently across endpoint shapes:

- a feed topic card exposes `id`;
- pass that exact value as `topic_id` to history or insight;
- history and insight responses expose the same identity as `topic_id`.

Do not assume feed items also contain a `topic_id` alias.

### Refresh consistency

When a feed reports `refreshing=true`, sequential feed/history/sources requests are not one atomic snapshot transaction.

A feed item may therefore report `trend.history_points=6` while a history request moments later returns 7 points because another observation was persisted between reads. Compare identity, timestamps, and refresh state instead of treating this normal change as a contract mismatch.

## Optional local API helper

`scripts/topic_radar_client.py` is deliberately small and uses only the Python standard library. It does not contain scoring or business logic; it only calls the existing public API and performs lightweight contract checks.

Examples:

```bash
python3 scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history TOPIC_ID
python3 scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

The `insight` command calls the existing Topic Radar GPT analysis capability; ordinary feed/sources/history reads do not require that model call.

## Environment

This repository should remain isolated from sibling project virtual environments.

- Python: 3.10+
- Runtime dependencies for the helper/installer: none beyond the standard library
- Do **not** make this repository depend on `../akaiagents/.venv`
- Do **not** import private `akaiagents` modules

Sibling repositories are references for contracts and engineering conventions, not runtime dependencies.

## Validation

Run deterministic offline checks with:

```bash
python3 -m unittest discover -s tests -v
```

The tests do not require live network access. GitHub Actions runs the same suite on Python 3.10 and 3.12.

M1 additionally validates real Skill discovery, explicit invocation, implicit trigger selection, false positives, and the live Radar workflow. The cases live in [`evals/cases.json`](evals/cases.json).

## Evidence boundary

Always keep these layers separate:

1. **Source facts** — fields returned by the current Topic Radar API, with freshness/evidence context.
2. **Analysis** — interpretation of those fields.
3. **Recommendations** — what the user should consider doing.
4. **Unknowns** — facts the current data does not establish.
5. **Risks** — stale/partial coverage, weak cross-market evidence, source outages, or unsupported claims.

The existing `/insight` output is model analysis over a server-known topic. It is not a new verified-fact source.

## Status

M0 is merged and production-contract validated. M1 adds local Skill installation metadata plus trigger/workflow evals before any plugin or hosted-MCP productization.

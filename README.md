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
                              | public read-only API
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

## First two Skills

### `cross-market-trend-research`

Use live Topic Radar data to find current topics, rising/early opportunities, platform or region differences, and plausible cross-market timing gaps. It treats cross-market propagation as an inference unless the live evidence actually supports it.

### `evidence-backed-content-brief`

Turn a verified Topic Radar topic into a practical content brief. It can use the existing `/insight` contract for recommended formats, audiences, three content angles, hooks, opening seconds, research questions, verification requirements, and claims to avoid.

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

## Optional local helper

`scripts/topic_radar_client.py` is deliberately small and uses only the Python standard library. It does not contain scoring or business logic; it only calls the existing public API and performs lightweight shape checks.

Examples:

```bash
python scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python scripts/topic_radar_client.py sources
python scripts/topic_radar_client.py history TOPIC_ID
python scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

The helper is useful in Codex or another local environment. A host with a native HTTP/MCP connection can follow the same Skills without using this script.

## Environment

This repository should remain isolated from sibling project virtual environments.

- Python: 3.10+
- Runtime dependencies for the helper: none beyond the standard library
- Do **not** make this repository depend on `../akaiagents/.venv`
- Do **not** import private `akaiagents` modules

Sibling repositories are references for contracts and engineering conventions, not runtime dependencies.

## Validation

Run offline checks with:

```bash
python -m unittest discover -s tests -v
```

The tests do not require live network access.

## Evidence boundary

Always keep these layers separate:

1. **Source facts** — fields returned by the current Topic Radar API, with freshness/evidence context.
2. **Analysis** — interpretation of those fields.
3. **Recommendations** — what the user should consider doing.
4. **Unknowns** — facts the current data does not establish.
5. **Risks** — stale/partial coverage, weak cross-market evidence, source outages, or unsupported claims.

The existing `/insight` output is model analysis over a server-known topic. It is not a new verified-fact source.

## Status

M0 Skill-first foundation. No crawler, database, scoring engine, OAuth, billing, or hosted MCP is added here.

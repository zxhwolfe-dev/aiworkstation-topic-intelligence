# Changelog

All notable public changes to AI Workstation Topic Intelligence are recorded here.

The project follows Semantic Versioning for distributable Skill releases.

## [0.1.0] - 2026-08-09

### Added

- `creator-topic-opportunity-research` for evidence-aware creator/editorial topic discovery, opportunity prioritization, platform/region comparison, and cross-market timing hypotheses.
- `evidence-backed-content-brief` for turning a live Radar topic into a research-ready content brief with verification and claims boundaries.
- Thin standard-library Topic Radar client for `feed`, `sources`, `history`, and the existing model-backed `insight` endpoint.
- Separate timeout budgets for ordinary Radar reads and model-backed insight requests.
- Codex user-Skill installer using safe symlinks under `$HOME/.agents/skills`.
- Safe migration of the internal pre-0.1.0 `cross-market-trend-research` symlink to the final public `creator-topic-opportunity-research` name when the legacy link points to this checkout.
- Skill discovery metadata in `agents/openai.yaml`.
- Positive/negative trigger evals and explicit live-evidence boundaries.
- Gate A / Gate B acceptance model separating Skill-trigger testing from live-network E2E validation.
- Deterministic release archive builder, release manifest, and SHA256 checksums.

### Safety and evidence rules

- Live Topic Radar data is required for claims about what is current, rising, accelerating, or cross-market.
- Local sibling repositories, snapshots, SQLite files, fixtures, exports, logs, and cached historical artifacts cannot replace current live evidence.
- `/insight` is model analysis over a server-known topic, not an independent verified-fact source.

### Validation

- Codex implicit-trigger acceptance established the initial positive/negative baseline and M2 expands it with harder routing-boundary cases before the first tag.
- Production `feed`, `sources`, `history`, and one real `/insight` request validated before this public-preview release line.

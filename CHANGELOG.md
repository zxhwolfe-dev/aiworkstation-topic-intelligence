# Changelog

All notable public changes to AI Workstation Topic Intelligence are recorded here.

The project follows Semantic Versioning for distributable Skill releases.

## [0.1.0] - 2026-08-09

### Added

- `cross-market-trend-research` for evidence-aware current-topic discovery, trend interpretation, platform/region comparison, and cross-market timing hypotheses.
- `evidence-backed-content-brief` for turning a live Radar topic into a research-ready content brief with verification and claims boundaries.
- Thin standard-library Topic Radar client for `feed`, `sources`, `history`, and the existing model-backed `insight` endpoint.
- Separate timeout budgets for ordinary Radar reads and model-backed insight requests.
- Codex user-Skill installer using safe symlinks under `$HOME/.agents/skills`.
- Skill discovery metadata in `agents/openai.yaml`.
- Positive/negative trigger evals and explicit live-evidence boundaries.
- Gate A / Gate B acceptance model separating Skill-trigger testing from live-network E2E validation.
- Deterministic release archive builder, release manifest, and SHA256 checksums.

### Safety and evidence rules

- Live Topic Radar data is required for claims about what is current, rising, accelerating, or cross-market.
- Local sibling repositories, snapshots, SQLite files, fixtures, exports, logs, and cached historical artifacts cannot replace current live evidence.
- `/insight` is model analysis over a server-known topic, not an independent verified-fact source.

### Validation

- Codex implicit-trigger acceptance: 6 positive cases passed and 6 negative cases did not trigger Topic Intelligence.
- Production `feed`, `sources`, `history`, and one real `/insight` request validated before this public-preview release line.

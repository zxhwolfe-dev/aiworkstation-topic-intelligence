# Changelog

All notable public changes to AI Workstation Topic Intelligence are recorded here.

The project follows Semantic Versioning for distributable Skill releases.

## [0.2.0] - Unreleased

### Added

- Self-contained runtime helper inside each distributable Skill so standalone ZIP/ChatGPT/Codex installs do not depend on the repository root.
- `ati.topic-opportunity-handoff.v1` contract for passing one selected live Topic Radar candidate from `creator-topic-opportunity-research` into `evidence-backed-content-brief` without re-identifying the topic from scratch.
- Standalone fallback behavior for `evidence-backed-content-brief` when the opportunity-research Skill is not installed: one bounded feed selection pass, then insight only for the selected topic.
- M3.1 task-quality eval matrix covering stale/partial/refreshing data, source gaps, no-candidate states, invalid topics, degraded/unavailable insight, single-Skill installs, composed workflows, and Chinese/English tasks.
- Offline E2E validation that extracts each release ZIP and executes its bundled Topic Radar helper without access to repository-root runtime files.

### Changed

- Both Skills now resolve the local helper relative to their own Skill directory rather than assuming repository-root `scripts/topic_radar_client.py` exists.
- Codex `doctor` validates the files required for a self-contained Skill runtime, not only `SKILL.md` and `agents/openai.yaml`.
- Distribution and release acceptance now require the bundled runtime helper and handoff reference in each archive.

### Safety and workflow rules

- A handoff is current-task evidence context, not persisted evidence that may be reused as current on a later task.
- The receiving Brief Skill refreshes live evidence when a handoff is stale, materially partial, missing required freshness fields, or not from the current task.
- Standalone brief selection never invents a second score and does not recreate full cross-market opportunity research.
- The public v0.1.0 tag/release remains immutable; v0.2.0 is not published until real fresh-session Skill acceptance passes.

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

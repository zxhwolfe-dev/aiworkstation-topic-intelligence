# Changelog

All notable public changes to AI Workstation Topic Intelligence are recorded here.

The project follows Semantic Versioning for distributable Skill releases.

## [0.2.1] - Unreleased

### Changed

- Added a shared per-Skill `references/quality-contract.md` derived from real ChatGPT v0.2.0 host smoke testing.
- Content format, duration, language, audience, tone, and production constraints are explicitly kept separate from Radar `platform`/`source` filters unless the user names a real supported Radar dimension.
- User-facing answers must keep Radar facts, server Topic Insight analysis, and host/editorial analysis visibly distinguishable when the distinction matters.
- A valid current-task `ati.topic-opportunity-handoff.v1` must not be followed by another broad/bounded candidate-selection pass merely to choose the topic again.
- Complete server Topic Insight output is the primary creative plan for Brief; hosts may adapt it for the user but should not generate a second incompatible plan solely for variety.

### Validation

- Added four ChatGPT-derived Skill-quality evals covering false platform mapping, editorial provenance, Insight reuse, and duplicate selection after handoff.
- Recorded real ChatGPT web smoke evidence for Creator-only, Brief-only, and both-Skills v0.2.0 installs.
- ChatGPT standalone package upload, Skill discovery, bundled runtime execution, live Topic Radar access, selected-topic Insight access, and behavioral multi-Skill composition all passed.
- The ChatGPT UI did not expose the raw internal handoff payload, so exact internal handoff serialization is not overclaimed as directly observed.

### Distribution

- `v0.2.0` remains the latest public immutable release until the 0.2.1 quality patch is fully tested and explicitly released.
- No Hosted MCP transport is planned solely for ChatGPT connectivity because the current standalone Skills successfully reached the live Topic Radar service.

## [0.2.0] - 2026-08-09

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
- The public v0.1.0 tag/release remains immutable.
- Upstream Topic Insight failure degrades to an evidence-based skeleton; the Skill must not fabricate model output or use local/sibling evidence as fallback.

### Validation

- Python 3.10 and 3.12 GitHub CI passed the full offline suite.
- Managed-sandbox acceptance completed with 57 passed, 1 environment-only loopback-socket skip, and exit code 0.
- Standalone release archives were built twice with identical SHA256 values.
- Creator-only, Brief-only, and both-Skills fresh-session behavior was checked without observable trigger false positives or false negatives.
- `ati.topic-opportunity-handoff.v1` preserved one selected live feed `id` exactly through handoff and history lookup, with no title-based rediscovery observed.
- A real selected-topic Insight request returned an upstream HTTP 503; degraded Brief behavior passed by exposing the limitation, preserving `must_verify`/`avoid_claims`, and not inventing Insight output. See `docs/m3.1-final-acceptance-2026-08-09.md`.

## [0.1.0] - 2026-08-09

### Added

- `creator-topic-opportunity-research` for evidence-aware creator/editorial topic discovery, opportunity prioritization, platform/region comparison, and cross-market timing hypotheses.
- `evidence-backed-content-brief` for turning a live Radar topic into a research-ready content brief with verification and claims boundaries.
- Thin standard-library Topic Radar client for `feed`, `sources`, `history`, and the existing model-backed `insight` endpoint.
- Separate timeout budgets for ordinary Radar reads and model-backed insight requests.
- Codex user-Skill installer using safe symlinks under `$HOME/.agents/skills`.
- Safe migration of the internal pre-0.1.0 `cross-market-trend-research` symlink to the final public `creator-topic-opportunity-research` name when the legacy link points to this checkout's old Skill path. Unrelated paths are never removed automatically.
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

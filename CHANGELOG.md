# Changelog

All notable public changes to AI Workstation Topic Intelligence are recorded here.

The project follows Semantic Versioning for distributable Skill releases.

## [0.2.2] - 2026-08-11

Release candidate prepared for validation. This version is not tagged or published.

### Changed

- Added stricter public client origin and freshness contracts, target-platform CLI filtering, and real Host Eval failure exit codes.
- Documented the official Radar origin rule and the strict Host Eval observability/manual-review boundary.
- Kept packaged Skill runtime copies synchronized after the nested response-contract checks.
- Added a persistent post-v0.2.1 Host Eval evidence gate; v0.2.2 remains blocked until a completed live RC and manual semantic review are committed.
- Hardened the release evidence verifier against fabricated grades, wrong suites/versions, incomplete or truncated runs, case-contract drift, stale code revisions, and unstructured manual attestations; fixed grading for the v0.2.1 suite.
- Required successful `feed`/`sources`/`history` helper execution without an explicit custom origin and with contract-valid Radar JSON before Host Eval records runtime workflow evidence; source reads, help, failed calls, and composed shell commands no longer qualify.
- Synced authenticated Premium identity forwarding guidance and preserved the published v0.2.1 release record below.

## [Unreleased]

No unreleased changes.

## [0.2.1] - 2026-08-10

### Changed


- Added a shared per-Skill `references/quality-contract.md` derived from real ChatGPT v0.2.0 host smoke testing.
- Content format, duration, language, audience, tone, and production constraints are explicitly kept separate from Radar `platform`/`source` filters unless the user names a real supported Radar dimension.
- Explicit topic/domain constraints such as `AI` are preserved from the first bounded query instead of starting with a broader generic technology scan.
- User-facing answers keep live Radar facts and host/editorial analysis visibly distinguishable when the distinction matters.
- A valid current-task `ati.topic-opportunity-handoff.v1` must not be followed by another broad/bounded candidate-selection pass merely to choose the topic again.
- The public Brief workflow now uses the current host model (ChatGPT/Codex/agent host) to create the research-ready brief from live Radar facts instead of consuming AI Workstation server-side model quota.
- The bundled public helper exposes only `feed`, `sources`, and `history`; anonymous/public `insight` support and its model timeout option are removed from distributable Skills.
- Server-generated Topic Insight is reserved as an optional future Premium capability that may be used only through a native authenticated AI Workstation connection that enforces the user's membership/quota/credits.

### Cost and credential safety

- Normal public Skill usage must produce zero AI Workstation server-side LLM calls.
- No shared AI Workstation API key or bearer token may be embedded in a Skill ZIP.
- The Skill must not ask users to paste private AI Workstation credentials into chat as an authentication workaround.
- Lack of a Premium connection is normal public mode, not a degraded error state; the host model completes the editorial analysis itself.

### Validation

- Added ChatGPT-derived Skill-quality evals covering false platform mapping, explicit AI-domain preservation, editorial provenance, zero-server-LLM public Brief generation, duplicate-selection prevention, and Premium-auth requirements.
- Added helper tests proving public operations are GET-only and the packaged CLI has no `insight` command.
- Recorded real ChatGPT web smoke evidence for Creator-only, Brief-only, and both-Skills v0.2.0 installs.
- ChatGPT standalone package upload, Skill discovery, bundled runtime execution, live Topic Radar access, selected-topic Insight access under v0.2.0, and behavioral multi-Skill composition all passed.
- The ChatGPT UI did not expose the raw internal handoff payload, so exact internal handoff serialization is not overclaimed as directly observed.
- Validated the v0.2.1 release candidate without a ChatGPT login through three isolated fresh-agent runs, live public `feed`/`sources`/`history`, extracted-package execution, deterministic double-builds, and blocked-network/no-local-fallback checks.
- The v0.2.1 ChatGPT ZIP upload UI was not re-tested; the release does not claim otherwise and carries forward only the separately recorded v0.2.0 UI evidence.

### Distribution

- `v0.2.1` is the current public immutable release; `v0.2.0` remains immutable and retains the last manual ChatGPT web-upload evidence.
- No Hosted MCP transport is required for public Radar connectivity because standalone ChatGPT Skills already reach the live public read endpoints.
- A future authenticated App/Plugin/OAuth transport may be introduced only for Premium account-bound capabilities such as server Topic Insight.

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

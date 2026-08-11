# Distribution

AI Workstation Topic Intelligence is distributed as two reusable Skills over the existing AI Workstation Global Topic Radar.

Current package version: **v0.2.2**.

A `VERSION` change does not publish anything by itself; only a matching pushed `v*` tag can start the release workflow.

## Public distribution principle

The public Skill archives must be safe to distribute widely without giving anonymous users access to AI Workstation's server-side model budget.

The bundled runtime therefore exposes only public read operations:

```text
feed
sources
history
```

It intentionally does **not** expose a bundled `insight` command.

Normal public Brief generation uses live Radar facts plus the current host model. Premium server-generated Topic Insight is a separate future account-bound capability and requires a native authenticated AI Workstation connection that enforces membership/quota/credits.

Never distribute:

- an embedded AI Workstation API key;
- a shared public bearer token;
- a Skill that asks users to paste private credentials into chat;
- a bundled anonymous path that spends server-side model quota.

## Release channels

### 1. Codex checkout + symlink

Best for development/evaluation:

```bash
git clone <repository>
cd aiworkstation-topic-intelligence
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

The installer links the two Skill directories into `$HOME/.agents/skills` and refuses to overwrite unrelated paths.

`doctor` validates:

- `SKILL.md`;
- `agents/openai.yaml`;
- `scripts/topic_radar_client.py`;
- `references/handoff-contract.md`;
- `references/quality-contract.md`.

### 2. Standalone Skill archives

Build portable/self-contained archives with:

```bash
python3 scripts/build_release.py --output dist
```

Output:

```text
dist/
  aiworkstation-topic-intelligence-VERSION-creator-topic-opportunity-research.zip
  aiworkstation-topic-intelligence-VERSION-evidence-backed-content-brief.zip
  release-manifest.json
  SHA256SUMS
```

Each ZIP contains exactly one top-level Skill directory and must include:

```text
SKILL.md
agents/openai.yaml
scripts/topic_radar_client.py
references/handoff-contract.md
references/quality-contract.md
LICENSE
```

The bundled helper is the Skill-local standard-library **public read transport**. It does not require a repository-root helper or sibling `akaiagents` checkout.

Portable copies are byte-checked against canonical sources:

```text
scripts/topic_radar_client.py
references/topic-opportunity-handoff.md
references/topic-intelligence-quality-contract.md
```

The builder rejects:

- missing required files;
- portable-copy drift;
- symlinks inside a Skill archive.

Archives are deterministic: identical source/version produces identical ZIP hashes.

Published v0.2.0 hashes remain:

```text
7d7ca0266abd55df374e4ca37ff5affadf9eabffe694474d18be96c5402dc897  aiworkstation-topic-intelligence-0.2.0-creator-topic-opportunity-research.zip
9c90adccd61966321201c8c05b0fad963e18ea412bd3112c694a4fe0cea9dab8  aiworkstation-topic-intelligence-0.2.0-evidence-backed-content-brief.zip
```

Published v0.2.1 hashes:

```text
3381d798c29cc8f67b1bca3f1f6da8a34a34ab78e64b6af7bd48aff95b663bb6  aiworkstation-topic-intelligence-0.2.1-creator-topic-opportunity-research.zip
81d6aac45b42c27b8f24c27ac18b6a268509fb9a8a88a0813b96feab8f034d5e  aiworkstation-topic-intelligence-0.2.1-evidence-backed-content-brief.zip
```

v0.2.2 deterministic build hashes:

```text
e0c56957c95333ae8de28a2bfb71fcbaf59ec15bc65ace2f5d379a819a7fad68  aiworkstation-topic-intelligence-0.2.2-creator-topic-opportunity-research.zip
80a1d10cf46b25549a0abc803fef368144c166bb5356f571b452aa6f80c6332e  aiworkstation-topic-intelligence-0.2.2-evidence-backed-content-brief.zip
```

Consumers should verify release assets against `SHA256SUMS` / `release-manifest.json`.

### 3. ChatGPT Skill upload

The published v0.2.0 archives were manually tested in ChatGPT web. Upload/discovery/bundled runtime/live Radar access passed.

For v0.2.1, the intended public ChatGPT path is:

```text
ChatGPT host model
  + public Skill
  + live feed/sources/history
  -> research-ready result
```

The uploaded public Skill should not depend on a server-side AI Workstation model call.

The v0.2.1 and v0.2.2 candidates passed isolated non-UI Codex/Host acceptance. The v0.2.1 and v0.2.2 ChatGPT upload UIs were not re-tested; the last manual web-upload evidence remains the separately recorded v0.2.0 smoke.

If a future ChatGPT App/Plugin/OAuth integration provides an authenticated AI Workstation account connection, that native connection may expose separate Premium capabilities. Do not put that authentication responsibility inside the portable Skill ZIP.

### 4. GitHub Release

Public releases use a Semantic Version in `VERSION` and a matching tag:

```text
vX.Y.Z
```

Pushing a matching tag triggers `.github/workflows/release.yml`, which:

1. verifies tag == `VERSION`;
2. runs the offline full test suite, runtime sync, and eval dry-run;
3. verifies persistent live Host Eval evidence and manual review;
4. builds deterministic archives;
5. publishes ZIPs, manifest, and `SHA256SUMS`.

Existing tags such as `v0.1.0` and `v0.2.0` are immutable.

## Standalone acceptance

Before a new public release, acceptance should prove:

1. each ZIP contains all required files;
2. portable helper/reference copies match canonical sources;
3. two identical builds have identical hashes;
4. extracted helpers work outside the repository;
5. the helper CLI exposes `feed`, `sources`, `history` and **no anonymous `insight` command**;
6. public helper HTTP operations are GET-only;
7. creator-only, brief-only, and both-Skills host behavior remains correct;
8. composed workflows preserve the selected topic identity;
9. public Brief can complete using host reasoning without AI Workstation server-side LLM spend;
10. no tag is created until acceptance is complete.

## Integrity verification

Manifest schema:

```text
ati.release.v1
```

It records package/version/license/Skill/file/hash/size.

## Upgrade behavior

### Codex symlink install

```bash
git pull --ff-only
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

### Standalone / ChatGPT

Download/build the newer archive and install/upload it using the supported host flow. Do not assume an older uploaded Skill is auto-replaced.

## Premium / Plugin direction

A future AI Workstation Plugin/App may be useful for **authenticated account-bound capabilities**, not because public Skills need help reaching Radar.

A suitable future boundary is:

```text
public Skill
  -> public feed/sources/history
  -> host reasoning

AI Workstation authenticated App/Plugin
  -> user identity / plan / quota
  -> optional Premium Topic Insight
```

Do not add a Hosted MCP/Plugin merely to duplicate the already-working public Radar transport. If one is added for Premium auth/tooling, keep it thin and do not duplicate collection, clustering, score, history, persistence, or model logic.

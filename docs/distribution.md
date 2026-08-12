# Distribution

AI Workstation Topic Intelligence v0.3.0 is distributed as one public Skill and one self-contained install archive over the existing Global Topic Radar.

Current package version: **v0.3.0**.

A `VERSION` change does not publish anything by itself. Only a matching pushed `v*` tag starts the GitHub Release workflow.

## Public package

The builder produces:

```text
topic-intelligence-0.3.0.zip
release-manifest.json
SHA256SUMS
```

The archive contains one top-level `topic-intelligence/` directory with:

```text
SKILL.md
agents/openai.yaml
scripts/topic_radar_client.py
references/quality-contract.md
references/selection-workflow.md
references/brief-workflow.md
LICENSE
```

The Skill infers three modes from natural language: selection only, brief for a supplied current topic, and one bounded selection followed by a brief for the same finalist. These are workflows, not three install or website entry points.

## Runtime boundary

The bundled helper exposes only the public read operations `feed`, `sources`, and `history`. It uses `python3`, puts global options before the subcommand, defaults ordinary scans to `--limit 12`, and normally caps them at 24. It must read directly from the loaded Skill root and must not use a repository helper, shell composition, custom origin, or anonymous `/insight`.

Normal public Brief generation uses live Radar facts and the host model, producing zero AI Workstation server-side LLM calls. Premium server-generated Topic Insight remains a separate account-bound capability that requires a native authenticated connection enforcing the user's quota.

## Build and verify locally

```bash
python3 scripts/sync_skill_runtime.py --check
python3 scripts/build_release.py --output dist
sha256sum dist/*
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

The builder is deterministic. Build twice in independent directories and compare every file byte-for-byte and by SHA256. Consumers must verify `SHA256SUMS` and `release-manifest.json` before installation.

## Historical hashes

The v0.2.x history remains immutable and is retained for audit:

```text
7d7ca0266abd55df374e4ca37ff5affadf9eabffe694474d18be96c5402dc897  aiworkstation-topic-intelligence-0.2.0-creator-topic-opportunity-research.zip
9c90adccd61966321201c8c05b0fad963e18ea412bd3112c694a4fe0cea9dab8  aiworkstation-topic-intelligence-0.2.0-evidence-backed-content-brief.zip
3381d798c29cc8f67b1bca3f1f6da8a34a34ab78e64b6af7bd48aff95b663bb6  aiworkstation-topic-intelligence-0.2.1-creator-topic-opportunity-research.zip
81d6aac45b42c27b8f24c27ac18b6a268509fb9a8a88a0813b96feab8f034d5e  aiworkstation-topic-intelligence-0.2.1-evidence-backed-content-brief.zip
e0c56957c95333ae8de28a2bfb71fcbaf59ec15bc65ace2f5d379a819a7fad68  aiworkstation-topic-intelligence-0.2.2-creator-topic-opportunity-research.zip
80a1d10cf46b25549a0abc803fef368144c166bb5356f571b452aa6f80c6332e  aiworkstation-topic-intelligence-0.2.2-evidence-backed-content-brief.zip
```

The verified v0.3.0 archive from two independent byte-for-byte identical builds is:

```text
935bab465811a3efabd50ee46c3166c702ad719d19fd66ade718d871b69b066e  topic-intelligence-0.3.0.zip
```

## Release workflow

Pushing a matching tag runs `.github/workflows/release.yml` and must complete these gates:

1. tag/version equality and tag ancestry on `main`;
2. offline full unittest suite;
3. runtime synchronization and v0.3.0 eval dry-run;
4. persistent live Host Eval evidence and verifier;
5. deterministic build and manifest/checksum generation;
6. GitHub Release publication of the single ZIP, manifest, and `SHA256SUMS`.

The v0.2.0 release remains the last manual ChatGPT Web ZIP upload validation. v0.2.1 and v0.2.2 Host Eval evidence is not ChatGPT Web UI evidence. v0.3.0 carries its own complete live Host Eval evidence, but still does not claim a new ChatGPT Web upload test. Every future release must likewise carry version-bound Host Eval evidence unless a stronger release contract explicitly replaces it.

## Installation channels

For Codex development, clone the repository and run the installer. For normal users, download the ZIP from the GitHub Release linked by the AI Workstation Radar page. ChatGPT uploads are surface- and workspace-dependent; follow [`chatgpt-install.md`](chatgpt-install.md) and do not market universal plan availability.

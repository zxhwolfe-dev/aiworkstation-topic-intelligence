# Distribution

AI Workstation Topic Intelligence is distributed as two reusable Skills over the existing AI Workstation Global Topic Radar.

## Release channels

### 1. Codex checkout + symlink

Best for development, evaluation, and users who want to track the GitHub repository.

```bash
git clone <repository>
cd aiworkstation-topic-intelligence
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

The installer links the two Skill directories into `$HOME/.agents/skills` and refuses to overwrite unrelated paths.

Because installation uses symlinks, updating the checked-out repository updates the installed Skill source immediately. After changing versions or branches, run `doctor` again.

### 2. Standalone Skill archives

Build portable/self-contained release archives with:

```bash
python3 scripts/build_release.py --output dist
```

The builder produces:

```text
dist/
  aiworkstation-topic-intelligence-VERSION-cross-market-trend-research.zip
  aiworkstation-topic-intelligence-VERSION-evidence-backed-content-brief.zip
  release-manifest.json
  SHA256SUMS
```

Each ZIP contains exactly one top-level Skill directory and includes at least:

```text
SKILL.md
agents/openai.yaml
```

The archives are deterministic: file order, metadata timestamps, and ZIP format are fixed so identical source at the same version produces identical artifact hashes.

The builder rejects symlinks inside a Skill package so a release cannot accidentally point outside the archive.

### 3. ChatGPT Skill upload

Current OpenAI product documentation supports creating/installing Skills in ChatGPT, including upload from a computer, subject to plan/workspace availability and permissions. OpenAI Skills follow the Agent Skills open standard and can be used across supported OpenAI surfaces.

The GitHub release ZIP is the portable distribution artifact. Use the current ChatGPT product's supported Skill-upload flow; if that flow expects an unpacked Skill file/folder rather than the ZIP itself, unpack the archive and upload the contained Skill directory/files. Do not assume a particular upload container format until the product UI/documentation specifies it.

Treat ChatGPT installation as a separate distribution surface from the local Codex symlink installation; do not assume installed personal Skills automatically sync between every surface.

### 4. GitHub Release

Public releases use a Semantic Version in `VERSION` and a matching Git tag:

```text
vX.Y.Z
```

Pushing a matching tag triggers `.github/workflows/release.yml`, which:

1. verifies that the tag matches `VERSION`;
2. runs the full offline test suite;
3. builds deterministic Skill archives;
4. publishes the ZIPs, `release-manifest.json`, and `SHA256SUMS` to a GitHub Release.

## Integrity verification

Consumers can verify downloaded archives against `SHA256SUMS` or `release-manifest.json`.

The manifest schema is:

```text
ati.release.v1
```

It records the package name, release version, Skill name, file name, SHA256 digest, and byte size for each archive.

## Upgrade behavior

### Codex symlink install

1. switch to the desired release/main branch;
2. `git pull --ff-only` or checkout a release tag;
3. run `python3 scripts/install_codex_skills.py doctor`.

No reinstall is needed when the existing symlinks still point to this checkout.

### Standalone/ChatGPT install

Build or download the newer Skill archive and install/upload that version using the currently supported product flow. Do not assume an uploaded Skill is automatically replaced by a newer GitHub release.

## Plugin direction

OpenAI currently positions Plugins as a higher-level package that can contain Skills and can optionally include Apps or app templates. Topic Intelligence may eventually use that path if a stable app-backed live Topic Radar connection becomes part of the product.

M2 intentionally does **not** invent a Plugin manifest or marketplace submission format. Add Plugin packaging only when the relevant official OpenAI builder/schema/submission path is publicly documented and can be validated.

Until then, the supported public artifact is the Skill release itself.

## Hosted MCP direction

Hosted MCP remains a separate transport decision. It should be introduced only if supported hosts cannot reliably reach the existing Topic Radar contract through an approved network path.

If added later, it must remain thin: transport/auth/tool exposure only, without duplicating Topic Radar collection, clustering, scoring, history, persistence, or GPT insight logic.

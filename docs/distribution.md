# Distribution

AI Workstation Topic Intelligence is distributed as two reusable Skills over the existing AI Workstation Global Topic Radar.

Latest public release: **v0.1.0**.

The repository development line may be newer than the latest public release. A `VERSION` change does not publish anything by itself; only a matching pushed `v*` tag can start the release workflow.

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

Because installation uses symlinks, updating the checked-out repository updates the installed Skill source immediately. After changing versions or branches, run `install` and then `doctor`; `install` is idempotent and also performs safe pre-release name migration when needed.

The final public Skill name is `creator-topic-opportunity-research`. Internal pre-0.1.0 checkouts used `cross-market-trend-research`; the installer removes that legacy symlink only when it points to this checkout's old Skill path. Unrelated paths are never removed automatically.

For the 0.2 development line, `doctor` also requires each installed Skill to contain its standalone runtime helper and Topic Opportunity handoff contract.

### 2. Standalone Skill archives

Build portable/self-contained release archives with:

```bash
python3 scripts/build_release.py --output dist
```

The builder produces:

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
LICENSE
```

The bundled `scripts/topic_radar_client.py` is the Skill-local standard-library transport adapter. A user who downloads or uploads only one Skill archive does not need a repository-root helper or a sibling `akaiagents` checkout.

The two Skill-local helper copies are kept byte-identical to the repository development helper by tests. The copies exist because a portable Skill archive cannot depend on files outside its own top-level Skill directory.

`references/handoff-contract.md` defines `ati.topic-opportunity-handoff.v1`. It allows the two Skills to preserve a selected live Topic Radar identity and current-task evidence context when composed, while explicitly forbidding persisted handoffs from becoming replacement current evidence later.

The embedded license is Apache-2.0 and matches the repository root `LICENSE`. The release manifest also records `license: Apache-2.0`.

The archives are deterministic: file order, metadata timestamps, and ZIP format are fixed so identical source at the same version produces identical artifact hashes.

The builder rejects symlinks inside a Skill package and refuses to build a Skill missing any required runtime/handoff file.

### 3. ChatGPT Skill upload

Current OpenAI product documentation supports creating/installing Skills in ChatGPT, including upload from a computer, subject to plan/workspace availability and permissions. OpenAI Skills follow the Agent Skills open standard and can be used across supported OpenAI surfaces.

The GitHub release ZIP is the portable distribution artifact. Use the current ChatGPT product's supported Skill-upload flow; if that flow expects an unpacked Skill file/folder rather than the ZIP itself, unpack the archive and upload the contained Skill directory/files. Do not assume a particular upload container format until the product UI/documentation specifies it.

Treat ChatGPT installation as a separate distribution surface from the local Codex symlink installation; do not assume installed personal Skills automatically sync between every surface.

Because each 0.2-line Skill package contains its own helper and references, uploading one Skill does not require uploading the whole repository. Whether the host permits that helper to reach the live public Topic Radar endpoint remains a host/network capability question; live-evidence rules still apply when network access is unavailable.

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

Changing `VERSION` on a normal branch does **not** publish a release. The public v0.1.0 tag must never be moved to newer code.

## Standalone acceptance

Before a new public Skill release, acceptance must prove more than archive presence:

1. each ZIP contains every required Skill/runtime/reference file;
2. two builds from identical source have identical SHA256 values;
3. each ZIP can be extracted to a temporary directory outside the repository;
4. the extracted `scripts/topic_radar_client.py` can execute independently of repository-root files;
5. Codex fresh-session validation covers creator-only, brief-only, and both-Skills installs;
6. the composed workflow preserves the exact selected topic identity through `ati.topic-opportunity-handoff.v1`;
7. no release tag is created until live/fresh-session acceptance is complete.

Offline tests use a local fake Topic Radar HTTP server so portable helper execution is tested without relying on production network availability.

## Integrity verification

Consumers can verify downloaded archives against `SHA256SUMS` or `release-manifest.json`.

The manifest schema is:

```text
ati.release.v1
```

It records the package name, release version, license identifier, Skill name, file name, SHA256 digest, and byte size for each archive.

## Upgrade behavior

### Codex symlink install

1. switch to the desired release/main branch;
2. `git pull --ff-only` or checkout a release tag;
3. run `python3 scripts/install_codex_skills.py install`;
4. run `python3 scripts/install_codex_skills.py doctor`.

No manual reinstall/copy is needed. The idempotent installer keeps matching current links and performs safe legacy-name migration when necessary.

### Standalone/ChatGPT install

Build or download the newer Skill archive and install/upload that version using the currently supported product flow. Do not assume an uploaded Skill is automatically replaced by a newer GitHub release.

## Plugin direction

OpenAI currently positions Plugins as a higher-level package that can contain Skills and can optionally include Apps or app templates. Topic Intelligence may eventually use that path if a stable app-backed live Topic Radar connection becomes part of the product.

Do not add Plugin packaging merely to solve a Skill package problem. The 0.2 line first makes the individual Skills genuinely portable and validates their runtime/task quality.

## Hosted MCP direction

Hosted MCP remains a separate transport decision. It should be introduced only if supported hosts cannot reliably reach the existing Topic Radar contract through an approved network path.

If added later, it must remain thin: transport/auth/tool exposure only, without duplicating Topic Radar collection, clustering, scoring, history, persistence, or GPT insight logic.

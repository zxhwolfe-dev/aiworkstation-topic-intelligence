# Release checklist

Use this checklist for every public Topic Intelligence Skill release.

The public `v0.1.0` tag is immutable. A later development `VERSION` does not alter that release and must not be tagged until all release gates below pass.

## 1. Version, license, and source

```bash
VERSION="$(cat VERSION)"
git status --short
git rev-parse HEAD
```

Requirements:

- `VERSION` is valid Semantic Versioning;
- `CHANGELOG.md` contains `## [${VERSION}]`;
- root `LICENSE` is present and is the intended Apache-2.0 license;
- working tree is clean;
- release is built from the intended `main` commit;
- the previous public tag/release has not been moved or rewritten.

## 2. Offline validation

```bash
python3 -m unittest discover -s tests -v
```

All tests must pass without installing third-party dependencies or requiring external network access.

The 0.2 line additionally requires:

- both Skill-local helpers byte-match the root development helper;
- both handoff references are identical;
- standalone archive E2E passes against the local fake Radar HTTP server;
- `evals/m3-skill-quality.json` passes its contract tests.

## 3. Codex install health

For a local checkout used for release acceptance, run the idempotent installer first so any supported legacy-name migration is applied:

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py status
python3 scripts/install_codex_skills.py doctor
```

Requirements:

- `creator-topic-opportunity-research` and `evidence-backed-content-brief` both point to the intended checkout;
- the internal pre-0.1.0 `cross-market-trend-research` symlink is absent after migration;
- `legacy_clean=true`;
- both `SKILL.md` files exist;
- both `agents/openai.yaml` files exist;
- both `scripts/topic_radar_client.py` files exist;
- both `references/handoff-contract.md` files exist;
- supported Python version is reported;
- `doctor.ok=true`.

## 4. Trigger/evidence acceptance

Run the current eval matrix from `evals/cases.json` in fresh conversations/processes when doing a trigger-quality release.

At minimum confirm:

- positive cases route to the intended Skill/workflow;
- negative cases do not invoke Topic Intelligence;
- no local/sibling snapshot fallback is used as current evidence;
- stale/partial live data is surfaced rather than hidden.

## 5. M3.1 task-quality acceptance

For releases on/after the 0.2 development line, follow:

```text
docs/m3-skill-quality-acceptance.md
```

and grade the machine-readable cases in:

```text
evals/m3-skill-quality.json
```

Required dimensions include:

- standalone Skill runtime;
- creator-only install;
- brief-only install;
- both-Skills composition;
- `ati.topic-opportunity-handoff.v1` identity continuity;
- bounded Brief fallback;
- no-useful-candidate behavior;
- stale/partial/source-gap handling;
- degraded/unavailable insight handling;
- Chinese and English task completion.

## 6. Live Gate B

Before a release that changes API transport, opportunity workflow, handoff behavior, or content-brief behavior, validate through an approved network-capable path.

Use the **bundled helper from the Skill being tested**, not only the repository-root helper. Example from a checkout:

```bash
python3 skills/creator-topic-opportunity-research/scripts/topic_radar_client.py feed --max-age-hours 24 --limit 3
python3 skills/creator-topic-opportunity-research/scripts/topic_radar_client.py sources
python3 skills/evidence-backed-content-brief/scripts/topic_radar_client.py history REAL_TOPIC_ID
```

If the release changes `/insight` handling, perform intentional real insight calls only for already-selected server-known topics. Do not fan out insight across a broad feed.

For 0.2, validate:

- one creator-only current scan;
- one brief-only bounded selection or named-topic flow;
- one both-Skills Opportunity → handoff → Brief flow with exact topic identity preservation;
- one blocked-live-data/sandbox regression proving no local fallback.

## 7. Build artifacts

```bash
rm -rf dist
python3 scripts/build_release.py --output dist
cat dist/release-manifest.json
cat dist/SHA256SUMS
```

Verify that:

- each archive contains one expected Skill directory and no unrelated repository files;
- each archive contains `SKILL.md`;
- each archive contains `agents/openai.yaml`;
- each archive contains `scripts/topic_radar_client.py`;
- each archive contains `references/handoff-contract.md`;
- each archive contains `LICENSE`;
- the two public Skill artifacts are `creator-topic-opportunity-research` and `evidence-backed-content-brief`;
- the manifest reports `license: Apache-2.0`;
- artifact hashes in the manifest match `SHA256SUMS`.

Required reproducibility check for a new minor release:

```bash
rm -rf /tmp/ati-release-a /tmp/ati-release-b
python3 scripts/build_release.py --output /tmp/ati-release-a
python3 scripts/build_release.py --output /tmp/ati-release-b
diff -u /tmp/ati-release-a/SHA256SUMS /tmp/ati-release-b/SHA256SUMS
```

Also extract each archive outside the checkout and execute its bundled helper at least with `--help`; the automated test suite additionally runs a real feed request against a local fake Radar server.

## 8. Fresh-session host acceptance

Before a minor release that changes Skill runtime/workflow behavior, validate fresh processes rather than relying on an already-loaded Skill catalog.

Required install matrix:

```text
creator only
brief only
both Skills
```

For both Skills, verify the composed workflow uses:

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

and preserves the exact live feed `id` as history/insight `topic_id`.

If an eligible ChatGPT workspace is used as a distribution target, perform the manual ChatGPT package smoke described in `docs/m3-skill-quality-acceptance.md`. Codex validation does not prove ChatGPT UI upload behavior.

## 9. Tag

Only after every applicable gate is green, the public tag must match `VERSION` exactly:

```bash
git tag -a "v${VERSION}" -m "AI Workstation Topic Intelligence v${VERSION}"
git push origin "v${VERSION}"
```

Do not tag a feature branch. Tag the validated `main` release commit.

Do not create/move/delete a release tag as part of ordinary M3.1 development or PR validation.

## 10. GitHub Release workflow

The tag triggers `.github/workflows/release.yml`.

Verify that the workflow:

- checks `v${VERSION}` against `VERSION`;
- runs tests;
- builds release artifacts;
- publishes both Skill ZIPs, `release-manifest.json`, and `SHA256SUMS`.

## 11. Post-release

Confirm:

- GitHub Release exists;
- archive checksums match the manifest;
- each standalone archive carries the Apache-2.0 license text;
- each standalone archive carries its runtime helper and handoff reference;
- release notes/changelog are accurate;
- README points users to the supported install path;
- no experimental Plugin or Hosted MCP claim is presented as a released capability.

# Release checklist

Use this checklist for every public Topic Intelligence Skill release.

## 1. Version and source

```bash
VERSION="$(cat VERSION)"
git status --short
git rev-parse HEAD
```

Requirements:

- `VERSION` is valid Semantic Versioning;
- `CHANGELOG.md` contains `## [${VERSION}]`;
- working tree is clean;
- release is built from the intended `main` commit.

## 2. Offline validation

```bash
python3 -m unittest discover -s tests -v
```

All tests must pass without installing third-party dependencies or requiring network access.

## 3. Codex install health

For a local checkout used for release acceptance:

```bash
python3 scripts/install_codex_skills.py status
python3 scripts/install_codex_skills.py doctor
```

Requirements:

- both Skills point to the intended checkout;
- both `SKILL.md` files exist;
- both `agents/openai.yaml` files exist;
- supported Python version is reported;
- `doctor.ok=true`.

## 4. Trigger/evidence acceptance

Run the current eval matrix from `evals/cases.json` in fresh conversations/processes when doing a trigger-quality release.

At minimum confirm:

- positive cases route to the intended Skill/workflow;
- negative cases do not invoke Topic Intelligence;
- no local/sibling snapshot fallback is used as current evidence;
- stale/partial live data is surfaced rather than hidden.

## 5. Live Gate B

Before a release that changes API transport or content-brief behavior, validate through an approved network-capable path:

```bash
python3 scripts/topic_radar_client.py feed --max-age-hours 24 --limit 3
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history REAL_TOPIC_ID
```

If the release changes `/insight` handling, perform one intentional real insight call for a server-known topic.

## 6. Build artifacts

```bash
rm -rf dist
python3 scripts/build_release.py --output dist
cat dist/release-manifest.json
cat dist/SHA256SUMS
```

Verify that each archive contains one expected Skill directory and no unrelated repository files.

Optional reproducibility check:

```bash
rm -rf /tmp/ati-release-a /tmp/ati-release-b
python3 scripts/build_release.py --output /tmp/ati-release-a
python3 scripts/build_release.py --output /tmp/ati-release-b
diff -u /tmp/ati-release-a/SHA256SUMS /tmp/ati-release-b/SHA256SUMS
```

## 7. Tag

The public tag must match `VERSION` exactly:

```bash
git tag -a "v${VERSION}" -m "AI Workstation Topic Intelligence v${VERSION}"
git push origin "v${VERSION}"
```

Do not tag a feature branch. Tag the validated `main` release commit.

## 8. GitHub Release workflow

The tag triggers `.github/workflows/release.yml`.

Verify that the workflow:

- checks `v${VERSION}` against `VERSION`;
- runs tests;
- builds release artifacts;
- publishes both Skill ZIPs, `release-manifest.json`, and `SHA256SUMS`.

## 9. Post-release

Confirm:

- GitHub Release exists;
- archive checksums match the manifest;
- release notes/changelog are accurate;
- README points users to the supported install path;
- no experimental Plugin or Hosted MCP claim is presented as a released capability.

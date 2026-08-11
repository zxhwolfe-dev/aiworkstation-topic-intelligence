# Release checklist

Use this checklist for every public Topic Intelligence Skill release.

Existing public tags are immutable. A later development `VERSION` must not be tagged until every applicable gate passes.

## 1. Version, license, source

```bash
VERSION="$(cat VERSION)"
git status --short
git rev-parse HEAD
```

Require valid SemVer, matching changelog entry, Apache-2.0 license, clean worktree, intended `main` commit, and unchanged previous tags/releases.

## 2. Offline validation

```bash
python3 scripts/sync_skill_runtime.py --check
python3 -m unittest discover -s tests -v
```

Require:

- both Skill-local helpers byte-match the canonical root helper;
- both handoff references match;
- both quality contracts match the canonical quality contract;
- standalone ZIP E2E passes (or the documented environment-only loopback skip applies in a restricted sandbox);
- current trigger and v0.2.1 quality contracts pass.

## 3. Public cost-boundary gate

For v0.2.1+ public Skills, this is a release blocker.

The bundled helper must expose only:

```text
feed
sources
history
```

Verify:

```bash
python3 scripts/topic_radar_client.py --help
python3 skills/creator-topic-opportunity-research/scripts/topic_radar_client.py --help
python3 skills/evidence-backed-content-brief/scripts/topic_radar_client.py --help
```

All three helpers must:

- have no `insight` command;
- have no model-specific timeout/credential option;
- perform public operations with GET requests only;
- contain no shared AI Workstation API key/bearer token.

The public Skills and metadata must require host reasoning in normal mode and forbid anonymous/public server `/insight`.

A Premium Topic Insight path is acceptable only when supplied by a **native authenticated AI Workstation connection** that identifies the user and enforces membership/quota/credits outside the portable Skill package.

## 4. Codex install health

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py status
python3 scripts/install_codex_skills.py doctor
```

Require both final Skill links to the intended checkout, no conflicting legacy link, supported Python, and these files present in both Skills:

- `SKILL.md`;
- `agents/openai.yaml`;
- `scripts/topic_radar_client.py`;
- `references/handoff-contract.md`;
- `references/quality-contract.md`.

`doctor.ok=true`.

## 5. Trigger/evidence acceptance

Run `evals/cases.json` in fresh processes when doing trigger-quality acceptance.

Require:

- positives route correctly;
- negatives do not invoke Topic Intelligence;
- public expected/optional calls contain only `feed`, `sources`, `history`;
- no anonymous server `insight` is called;
- no local/sibling fallback is used;
- stale/partial conditions are surfaced.

## 6. Current Skill-quality acceptance

Review:

```text
evals/v0.2.1-skill-quality.json
```

Require at minimum:

- content format/language/audience not misused as Radar platform/source filters;
- explicit AI/domain constraint preserved from the first bounded query;
- Radar facts separated from host editorial analysis;
- Brief public mode creates a complete research-ready result with host reasoning;
- public mode makes zero AI Workstation server-side LLM calls;
- Creator → handoff → Brief does not reselect after a valid handoff;
- Premium Insight requires an explicit authenticated native connection.

Historical M3.1 cases remain regression evidence but do not override the newer public cost boundary.

## 7. Live public Gate B

Use the **bundled helper from the Skill being tested**, not only the repository-root helper:

```bash
python3 skills/creator-topic-opportunity-research/scripts/topic_radar_client.py feed --max-age-hours 24 --limit 3
python3 skills/creator-topic-opportunity-research/scripts/topic_radar_client.py sources
python3 skills/evidence-backed-content-brief/scripts/topic_radar_client.py history REAL_TOPIC_ID
```

For public Skill release acceptance, **do not call server `/insight`**.

Validate:

- one Creator-only live current scan;
- one Brief-only bounded selection/named-topic flow using host reasoning;
- one both-Skills Opportunity → handoff → Brief flow with exact topic identity preservation;
- one blocked-live-data regression proving no local fallback;
- no anonymous server-side model call in any of the above.

Testing a separate authenticated Premium connection belongs to that connection's own acceptance, not the public Skill release gate.

## 8. Build artifacts

```bash
rm -rf dist
python3 scripts/build_release.py --output dist
cat dist/release-manifest.json
cat dist/SHA256SUMS
```

Each archive must contain one expected Skill root plus:

- `SKILL.md`;
- `agents/openai.yaml`;
- `scripts/topic_radar_client.py`;
- `references/handoff-contract.md`;
- `references/quality-contract.md`;
- `LICENSE`.

Verify manifest license/hash/size and deterministic double-build checks:

```bash
rm -rf /tmp/ati-release-a /tmp/ati-release-b
python3 scripts/build_release.py --output /tmp/ati-release-a
python3 scripts/build_release.py --output /tmp/ati-release-b
diff -u /tmp/ati-release-a/SHA256SUMS /tmp/ati-release-b/SHA256SUMS
```

Extract each archive outside the checkout; verify `--help` works and does not show `insight`.

## 9. Fresh-session host acceptance

Test:

```text
creator only
brief only
both Skills
```

Both-Skills conceptual path:

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

Require exact finalist identity preservation and host-generated Brief completion without anonymous server model calls.

Run the v0.2.1 release-candidate suite live with `--strict-observation`. Save both the raw `ati.host-eval.v1` report and the `ati.host-evidence.v1` graded report. This is an observability gate only: manually review the raw traces/output against each case's `must_show` and `must_not` before approval.

For every release after the immutable v0.2.1 line, persist those artifacts under `release-evidence/v<VERSION>/host-eval.json`, `host-evidence.json`, and structured `manual-review.json`. `scripts/verify_release_evidence.py` re-runs grading, binds raw/graded reports to the exact seven v0.2.1 case IDs, requires a live strict run at the current commit, and checks per-case `must_show`/`must_not` attestations plus zero anonymous `/insight` calls and no post-handoff reselection. The tag workflow hard-fails when this evidence is absent or incomplete. The v0.2.1 tag is the sole historical workflow exception.

If ChatGPT is a target surface, use a fresh uploaded release-candidate package; do not assume Codex proves ChatGPT behavior.

## 10. Tag

Only after all applicable gates are green:

```bash
git tag -a "v${VERSION}" -m "AI Workstation Topic Intelligence v${VERSION}"
git push origin "v${VERSION}"
```

Tag only the validated `main` release commit. Never move/rewrite an existing public tag.

## 11. GitHub Release workflow

Verify matching tag/version, tests, deterministic build, and publication of both Skill ZIPs, `release-manifest.json`, and `SHA256SUMS`.

## 12. Post-release

Confirm release existence, hashes, license, runtime/helper/references, README/changelog accuracy, and that no experimental authenticated Premium transport is marketed as a bundled public Skill capability.

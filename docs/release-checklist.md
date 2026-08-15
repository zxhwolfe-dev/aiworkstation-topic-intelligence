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

- the single Skill-local helper byte-matches the canonical root helper;
- selection and brief workflow references match;
- the quality contract matches the canonical quality contract;
- standalone ZIP E2E passes (or the documented environment-only loopback skip applies in a restricted sandbox);
- historical v0.2.1 regressions and the current unified trigger/v0.3.1 quality contract pass.
- current README, website-entry specification, release note, Plugin listing,
  localized showcase image, and Plugin screenshot describe the same Skill
  acquisition journey and evidence boundary;
- current public acquisition copy does not expose review status, host-eval
  evidence, raw traces, or unsupported installation surfaces.

## 3. Public cost-boundary gate

For v0.2.1+ public packages, this is a release blocker.

The bundled helper must expose only:

```text
feed
sources
history
```

Verify:

```bash
python3 scripts/topic_radar_client.py --help
python3 skills/topic-intelligence/scripts/topic_radar_client.py --help
```

The helper must:

- have no `insight` command;
- have no model-specific timeout/credential option;
- perform public operations with GET requests only;
- contain no shared AI Workstation API key/bearer token.

The public Skill and metadata must require host reasoning in normal mode and forbid anonymous/public server `/insight`.

A Premium Topic Insight path is acceptable only when supplied by a **native authenticated AI Workstation connection** that identifies the user and enforces membership/quota/credits outside the portable Skill package.

## 4. Codex install health

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py status
python3 scripts/install_codex_skills.py doctor
```

Require the final `topic-intelligence` link to the intended checkout, no conflicting legacy links, supported Python, and these files present:

- `SKILL.md`;
- `agents/openai.yaml`;
- `scripts/topic_radar_client.py`;
- `references/selection-workflow.md`;
- `references/brief-workflow.md`;
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
evals/v0.3.1-skill-quality.json
```

Require at minimum:

- content format/language/audience not misused as Radar platform/source filters;
- explicit AI/domain constraint preserved from the first bounded query;
- Radar observations separated from host editorial analysis;
- Brief public mode creates a complete research-ready result with host reasoning;
- public mode makes zero AI Workstation server-side LLM calls;
- selection → Brief preserves the same finalist and does not run a second feed;
- Premium Insight requires an explicit authenticated native connection.

Historical M3.1 cases remain regression evidence but do not override the newer public cost boundary.

## 7. Live public Gate B

Use the **bundled helper from the Skill being tested**, not only the repository-root helper:

```bash
python3 skills/topic-intelligence/scripts/topic_radar_client.py --timeout 30 feed --q AI --limit 12
python3 skills/topic-intelligence/scripts/topic_radar_client.py --timeout 30 sources
python3 skills/topic-intelligence/scripts/topic_radar_client.py --timeout 30 history REAL_TOPIC_ID
```

For public Skill release acceptance, **do not call server `/insight`**.

Validate:

- one selection-only live current scan;
- one supplied-topic or Brief planning flow using host reasoning;
- one selection-followed-by-brief flow with exact topic identity preservation;
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
- `references/selection-workflow.md`;
- `references/brief-workflow.md`;
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

Test the one public Skill in all three automatic modes:

```text
selection only
supplied current topic -> brief
selection -> brief
```

Both-Skills conceptual path:

```text
topic-intelligence
  -> one bounded feed when selection is needed
  -> same-finalist host-model brief when requested
```

Require exact finalist identity preservation and host-generated Brief completion without anonymous server model calls.

Run the v0.3.1 release-candidate suite live with `--strict-observation`. Save both the raw `ati.host-eval.v1` report and the `ati.host-evidence.v1` graded report. This is an observability gate only: manually review the raw traces/output against each case's `must_show` and `must_not` before approval.

For every release after the immutable v0.2.1 line, persist those artifacts under `release-evidence/v<VERSION>/host-eval.json`, `host-evidence.json`, and structured `manual-review.json`. `scripts/verify_release_evidence.py` re-runs grading, binds raw/graded reports to the exact release-suite cases, requires a live strict run at the current commit, and accepts runtime workflow evidence only from a successful Skill-helper `feed`/`sources`/`history` command without an explicit custom origin and with contract-valid Radar JSON, or from a complete current-task topic snapshot explicitly supplied by the eval input. It also checks per-case `must_show`/`must_not` attestations, zero anonymous `/insight` calls, and no post-selection reselection. The tag workflow hard-fails when this evidence is absent or incomplete. The v0.2.1 tag is the sole historical workflow exception.

Only advertise installation surfaces that were verified for the current release.
Do not infer one host's behavior from another host's acceptance evidence.

## 10. Tag

Only after all applicable gates are green:

```bash
git tag -a "v${VERSION}" -m "AI Workstation Topic Intelligence v${VERSION}"
git push origin "v${VERSION}"
```

Tag only the validated `main` release commit. Never move/rewrite an existing public tag.

## 11. GitHub Release workflow

Verify matching tag/version, tests, deterministic build, and publication of the single Skill ZIP, `release-manifest.json`, and `SHA256SUMS`.

## 12. Post-release

Confirm release existence, hashes, license, runtime/helper/references, README/changelog accuracy, and that no experimental authenticated Premium transport is marketed as a bundled public Skill capability.

When a target-surface validation occurs after publication, archive it as separate post-release manual UI evidence. Do not rewrite immutable `release-evidence/**`, historical Host Eval JSON, or manual-review JSON. Record user-visible behavior without claiming raw tool traces or exact internal command counts unless those were independently observed.

For v0.3.0, the final published ZIP completed a post-release ChatGPT Web three-mode smoke on 2026-08-12. All three user-facing modes passed; the canonical record is [`chatgpt-v0.3.0-smoke-result-2026-08-12.md`](chatgpt-v0.3.0-smoke-result-2026-08-12.md). This validation did not change the ZIP, tag, version, or release evidence.

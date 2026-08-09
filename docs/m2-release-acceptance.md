# M2 release acceptance

M2 validates Topic Intelligence as a versioned, reproducible Skill distribution rather than only a working source checkout.

Acceptance must not modify `akaiagents` or other sibling repositories.

## 1. Sync the M2 branch

```bash
git fetch origin
git switch feat/topic-intelligence-m2-release
git pull --ff-only
git status
```

Keep the working tree clean throughout acceptance.

## 2. Version

```bash
cat VERSION
python3 scripts/install_codex_skills.py version
```

Both must report the same Semantic Version.

For the first public preview:

```text
0.1.0
```

## 3. Offline tests

```bash
python3 -m unittest discover -s tests -v
```

Expected M2 suite size on the initial release branch: **35 tests**.

Do not install dependencies to make the suite pass; the project intentionally uses the Python standard library for these tools/tests.

## 4. Codex install health

```bash
python3 scripts/install_codex_skills.py status
python3 scripts/install_codex_skills.py doctor
```

Requirements:

- both Skills are `installed`;
- symlinks point to this checkout;
- both `SKILL.md` files exist;
- both `agents/openai.yaml` files exist;
- `python_supported=true`;
- `doctor.ok=true`.

## 5. Deterministic release build

Do not write acceptance artifacts into the repository.

```bash
rm -rf /tmp/ati-m2-release-a /tmp/ati-m2-release-b
python3 scripts/build_release.py --output /tmp/ati-m2-release-a
python3 scripts/build_release.py --output /tmp/ati-m2-release-b
```

Compare:

```bash
diff -u /tmp/ati-m2-release-a/SHA256SUMS /tmp/ati-m2-release-b/SHA256SUMS
diff -u /tmp/ati-m2-release-a/release-manifest.json /tmp/ati-m2-release-b/release-manifest.json
```

Both diffs must be empty.

Inspect each ZIP with Python's standard-library zip tool or equivalent read-only tooling. Each archive must contain only one top-level Skill directory and include:

```text
SKILL.md
agents/openai.yaml
LICENSE
```

The manifest must report:

```text
license: Apache-2.0
```

## 6. Expanded implicit-trigger evals

Run all 20 cases in `evals/cases.json` using fresh isolated conversations/processes when automated execution is safe.

The original M1 cases already established a baseline of zero observed false positives and zero false negatives. M2 adds ambiguous/boundary prompts.

For every case record:

```text
case_id:
expected_skill:
selected_skill:
pass_trigger:
observed_calls:
must_show_pass:
must_not_pass:
notes:
```

If selected Skill is not observable, record `not_observable`; never infer it from desired behavior alone.

### M2 boundary cases to watch closely

Positive:

- `trend-zh-less-crowded`: do not claim Chinese-market saturation is directly measured.
- `trend-en-freshness-first`: stale/partial/source gaps must be surfaced before recommendations.
- `brief-zh-xiaohongshu`: do not force a short-video format when the user asks for Xiaohongshu graphics/text.
- `brief-en-verification-heavy`: prioritize verification burden rather than sensationalism.

Negative:

- `negative-platform-style-comparison`
- `negative-provided-material-script`
- `negative-current-company-news`
- `negative-translation`

These must not trigger Topic Intelligence simply because the prompt contains AI, content, platforms, news, or current-language cues.

## 7. Evidence behavior

For positive cases:

- current claims require live Topic Radar evidence;
- sandbox/network failure must degrade safely;
- local/sibling snapshots remain forbidden as current evidence;
- cross-market saturation/lead-lag stays hypothesis/unknown unless directly supported;
- `/insight` remains model analysis, not source fact.

## 8. Release workflow inspection

Read-only verify `.github/workflows/release.yml`:

- triggers only on `v*` tags;
- verifies tag value against `VERSION`;
- runs tests before publishing;
- builds artifacts with `scripts/build_release.py`;
- publishes release assets only after those gates.

Do **not** create or push a release tag during M2 PR acceptance.

## 9. Final state

```bash
git status
```

Requirements:

- working tree clean;
- no project files modified by acceptance;
- no commit/push/merge/tag created by the acceptance operator;
- `/tmp` may contain generated acceptance artifacts.

## Final report

Return:

1. HEAD SHA;
2. version result;
3. 35-test result;
4. `doctor` result;
5. deterministic-build result and artifact names/hashes;
6. archive content and license validation;
7. all 20 eval results or an exact blocker if safe automation cannot observe them;
8. false-positive count;
9. false-negative count;
10. evidence/freshness issues;
11. final git status.

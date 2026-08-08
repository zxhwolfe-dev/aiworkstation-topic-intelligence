# Codex M1 acceptance

This guide validates Topic Intelligence as a real installed Codex Skill package, not just as repository documentation.

## 1. Sync the M1 branch

```bash
git fetch origin
git switch feat/topic-intelligence-m1-evals
git pull --ff-only
```

Keep the working tree clean during acceptance. The acceptance operator should report failures, not patch them.

## 2. Run offline tests

```bash
python3 -m unittest discover -s tests -v
```

No dependency installation is required.

## 3. Install the two local Skills

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py status
```

The installer creates symlinks under:

```text
$HOME/.agents/skills/
```

Expected entries:

```text
$HOME/.agents/skills/cross-market-trend-research
$HOME/.agents/skills/evidence-backed-content-brief
```

It refuses to overwrite an existing unrelated path.

Codex supports symlinked Skill directories. It normally detects changes automatically; restart Codex only if the Skills do not appear.

## 4. Verify discovery

Inside Codex:

```text
/skills
```

Confirm both Topic Intelligence Skills are visible.

Explicit invocation can also be selected by typing `$` and choosing the Skill.

## 5. Explicit smoke tests

Run the two explicit prompts from `evals/README.md` first.

Pass conditions:

- the requested Skill is selected;
- live Topic Radar is reached;
- the trend Skill checks freshness before current-state claims;
- the content-brief Skill uses a server-known topic and does not send arbitrary copied text to `/insight`;
- no unrelated repository files are modified.

## 6. Implicit trigger evals

Run all entries in `evals/cases.json`.

Use a fresh Codex conversation for each implicit-trigger case. Do not prefix the prompt with `$skill-name`.

For each case record:

```text
case_id:
selected_skill:
pass_trigger:
observed_calls:
must_show_pass:
must_not_pass:
notes:
```

When the expected Skill is `null`, `selected_skill` should be `none`.

## 7. Production-contract checks during evals

For live Radar calls preserve these rules:

- feed card identity is `id`;
- pass that exact value as `topic_id` to history/insight;
- inspect `generated_at`, `partial`, `stale`, `snapshot_age_seconds`, and relevant `source_status`;
- `empty` source status is not automatically a connector failure;
- if `refreshing=true`, sequential reads may legitimately see one more history point;
- `/insight` is model analysis, not independent source evidence.

## 8. Final M1 report

Return:

1. checked-out HEAD SHA;
2. offline test result;
3. installer/status result;
4. `/skills` discovery result;
5. explicit smoke-test results;
6. one result row for every eval case;
7. any implicit false positives/false negatives;
8. any API/contract failure;
9. final `git status`.

Do not merge or modify Skill descriptions during acceptance. Report the evidence back so the author can adjust the Skill intentionally.

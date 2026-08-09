# Codex M1 acceptance

This guide records the M1 validation workflow for Topic Intelligence as a real installed Codex Skill package. The final public 0.1.0 topic-research Skill name is `creator-topic-opportunity-research`; internal pre-0.1.0 M1 runs used the legacy name `cross-market-trend-research`.

M1 has two distinct gates:

1. **Skill discovery/trigger/evidence-boundary validation** — safe to run in a network-restricted read-only Codex sandbox.
2. **Live Topic Radar E2E validation** — requires an execution path that can actually reach the configured Topic Radar origin.

Do not confuse a sandbox network restriction with a Topic Radar production outage.

## 1. Sync the intended branch

Use the branch or release being validated and keep the working tree clean. Historical M1 acceptance used `feat/topic-intelligence-m1-evals`; current releases should validate the intended current ref instead.

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

Current expected entries:

```text
$HOME/.agents/skills/creator-topic-opportunity-research
$HOME/.agents/skills/evidence-backed-content-brief
```

It refuses to overwrite an existing unrelated path. On a checkout upgraded from the internal pre-0.1.0 name, `install` safely removes the legacy `cross-market-trend-research` symlink only when it points to this checkout's former Skill path.

## 4. Verify discovery

Inside interactive Codex, use `/skills` when available and confirm both Topic Intelligence Skills are visible.

Non-interactive `codex exec` may not expose the `/skills` UI. In that case, successful explicit Skill invocation in a fresh process is acceptable discovery evidence; report `/skills` itself as not directly observable rather than guessing.

## 5. Gate A — explicit and implicit trigger validation

For automated trigger/evidence-boundary tests, prefer fresh isolated Codex processes and a read-only sandbox when supported.

Run the two explicit prompts from `evals/README.md`, then the current entries in `evals/cases.json`.

Use a fresh Codex conversation/process for every implicit-trigger case. Do not prefix implicit prompts with `$skill-name`.

Pass conditions for Gate A:

- the expected Skill is selected;
- negative cases do not trigger Topic Intelligence;
- the Skill attempts the existing Topic Radar workflow instead of inventing a second backend;
- if network access is unavailable, it stops safely rather than inventing current topics;
- **it never searches sibling repositories, local snapshots, SQLite files, fixtures, exports, logs, or cached local artifacts as replacement current evidence**;
- no unrelated repository files are modified.

A network-restricted sandbox is expected to block or restrict some outbound calls. In that situation, record the live-data workflow as blocked and evaluate trigger/evidence behavior separately.

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

## 6. Gate B — live Topic Radar E2E validation

Gate B must use a network-capable execution path explicitly approved for the environment.

Do **not** switch to broad or dangerous filesystem permissions merely to regain network access.

Acceptable evidence includes:

- running `scripts/topic_radar_client.py` from the normal shell outside a network-disabled Codex sandbox; or
- running Codex in a user-approved configuration that preserves appropriate filesystem restrictions while allowing the required Topic Radar network destination; or
- using an equivalent native host/MCP connection to the live Topic Radar contract.

At minimum validate:

```bash
python3 scripts/topic_radar_client.py feed --max-age-hours 24 --limit 3
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history REAL_TOPIC_ID
```

For content-brief E2E, perform one intentional `/insight` call for a real server-known topic when model usage is acceptable:

```bash
python3 scripts/topic_radar_client.py insight REAL_TOPIC_ID --locale zh
```

This verifies the existing upstream insight contract. It does not by itself prove that a network-restricted Codex sandbox can call it.

## 7. Production-contract checks

For live Radar calls preserve these rules:

- feed card identity is `id`;
- pass that exact value as `topic_id` to history/insight;
- inspect `generated_at`, `partial`, `stale`, `snapshot_age_seconds`, and relevant `source_status`;
- `empty` source status is not automatically a connector failure;
- if `refreshing=true`, sequential reads may legitimately see one more history point;
- `/insight` is model analysis, not independent source evidence;
- local/sibling snapshots are never acceptable substitutes for a failed live call.

## 8. Final report

Return:

1. checked-out HEAD SHA;
2. offline test result;
3. installer/status result;
4. `/skills` discovery result or explicit non-observability;
5. explicit trigger smoke-test results;
6. one result row for every requested implicit eval case;
7. false positives/false negatives;
8. evidence-boundary regressions, especially local snapshot fallback;
9. Gate B live API/insight result when required;
10. any host/sandbox network limitation;
11. final `git status`.

Do not merge or modify Skill descriptions during acceptance. Report the evidence back so the author can adjust the Skill intentionally.

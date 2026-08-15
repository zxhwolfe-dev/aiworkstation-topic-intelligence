# Topic Intelligence Skill evals

Topic Intelligence keeps historical two-Skill fixtures outside the active discovery
path and uses the unified Skill for current trigger and release gates.

## Current v0.3.1 gate

`v0.3.1-skill-quality.json` exercises the one public `topic-intelligence` Skill in
fresh-host cases covering the three modes, provenance, compact scanning,
no-reselection, stale supplied evidence, and a non-trigger. Supplied-current
fixtures use `$CURRENT_TIME`, which the runner replaces only in the host prompt;
the stored case contract remains deterministic.

Run:

```bash
python3 scripts/run_host_evals.py --suite v0.3.1 --dry-run
```

The sections below describe immutable v0.2.x regression assets under
`legacy/skills/` and the historical quality suites.

## 1. `cases.json` — trigger/routing boundary

`cases.json` is the reusable acceptance matrix for real Codex/ChatGPT Skill discovery behavior.

The goal is not to grade prose style. It checks whether the host:

1. invokes the correct Skill for the user's intent;
2. avoids Topic Intelligence when the request is unrelated, evergreen, translation-only, supplied-material writing, direct company-news lookup, or generic platform analysis;
3. follows the existing Topic Radar workflow rather than inventing a second backend;
4. preserves freshness/evidence boundaries;
5. does not invent a second scoring system or promote model insight to source fact;
6. refuses local/sibling snapshot fallback when live evidence is unavailable.

The active unified trigger matrix contains **20 cases**:

- 11 `topic-intelligence` positives across selection and brief intent;
- 9 negative/boundary cases that should not invoke Topic Intelligence.

`expected_calls` describe logical endpoint use (`feed`, `sources`, `history`, `insight`), not a requirement to print internal commands to the user.

Use a **fresh conversation per implicit-trigger case** so a previous explicit Skill selection does not bias the next case.

## 2. `m3-skill-quality.json` — runtime/task quality

The 0.2 development line adds `m3-skill-quality.json` because correct triggering is necessary but no longer sufficient.

It covers 24+ realistic task and failure states across:

- creator-only install;
- brief-only install;
- both-Skills composition;
- Chinese and English;
- current-task `ati.topic-opportunity-handoff.v1`;
- bounded Brief standalone selection;
- invalid/ambiguous topic identity;
- no-useful-candidate behavior;
- stale/partial feed handling;
- source `empty` vs explicit source error;
- `refreshing=true` non-atomic reads;
- degraded/unavailable insight;
- blocked live data;
- stale/persisted or identity-invalid handoffs;
- verification-heavy and platform/audience-constrained tasks.

The quality matrix grades:

- correct workflow routing;
- live-evidence boundary;
- freshness handling;
- topic identity preservation;
- handoff continuity;
- standalone Skill runtime;
- bounded Brief fallback;
- insight-as-analysis boundary;
- task completion quality.

For synthetic failure states, use the fixture notes as evaluation semantics; do not manipulate production to force an outage or stale snapshot.

## Historical explicit smoke tests

Before implicit evals, verify explicit invocation works:

```text
$creator-topic-opportunity-research 过去24小时有哪些值得中国科技博主提前关注的海外AI选题？
```

and:

```text
$evidence-backed-content-brief 从当前AI热点中选一个适合2到3分钟短视频的题材，给我研究就绪的选题简报。
```

Explicit smoke tests prove installation/discovery. They do **not** replace implicit-trigger or task-quality evals.

## Gate A vs Gate B

Trigger/evidence behavior can be tested in a safe network-restricted sandbox. Live Topic Radar E2E requires a separately approved network-capable execution path.

Do not interpret sandbox DNS failure as production failure, and never replace unavailable live evidence with local/sibling data.

## Release quality bar

For a 0.2-line release candidate:

- previous trigger positives/negatives must not regress;
- standalone Skill ZIP runtime must pass;
- creator-only, brief-only, and both-Skills installs must behave correctly;
- composed Opportunity → handoff → Brief must preserve the exact topic identity;
- no case may invent current facts when live Radar data is unavailable;
- no case may use local/sibling snapshots or persisted handoffs as current evidence;
- stale/partial/source limitations must remain visible when material;
- no-useful-candidate must be allowed instead of forcing a recommendation;
- selected-topic insight must remain analysis, not independent evidence.

See `docs/m3-skill-quality-acceptance.md` for the full fresh-session/live E2E gate.

# M3.1 Skill Runtime & Workflow Quality Acceptance

This gate validates the 0.2 development line before any `v0.2.0` public tag is considered.

The goal is not more infrastructure. The goal is to prove that the two released Skill packages are independently runnable, compose without losing topic identity, degrade safely, and complete realistic user tasks.

## Scope

Skills:

- `creator-topic-opportunity-research`
- `evidence-backed-content-brief`

Contract:

- `ati.topic-opportunity-handoff.v1`

Runtime:

- bundled `scripts/topic_radar_client.py`
- existing public AI Workstation Global Topic Radar API only

Explicitly out of scope:

- new crawler/source provider;
- new opportunity score;
- new database/persistence;
- duplicate GPT backend;
- Hosted MCP/Plugin packaging;
- changes to the immutable public `v0.1.0` tag.

## Gate 1 — repository/offline contracts

Run:

```bash
python3 -m unittest discover -s tests -v
```

Must prove:

- both Skill-local helpers are byte-identical to the root development helper;
- both handoff reference files are identical;
- release builder refuses missing runtime/handoff files;
- Codex doctor refuses an incomplete Skill runtime;
- M3.1 quality eval matrix is valid and covers the required failure/task states;
- all existing M0/M1/M2 trigger, evidence, installer, and release tests remain green.

No network is required.

## Gate 2 — deterministic standalone package E2E

Build twice:

```bash
rm -rf /tmp/ati-m31-a /tmp/ati-m31-b
python3 scripts/build_release.py --output /tmp/ati-m31-a
python3 scripts/build_release.py --output /tmp/ati-m31-b
diff -u /tmp/ati-m31-a/SHA256SUMS /tmp/ati-m31-b/SHA256SUMS
```

Requirements:

- identical SHA256 outputs;
- each ZIP contains one Skill root only;
- each ZIP includes `SKILL.md`, `agents/openai.yaml`, `scripts/topic_radar_client.py`, `references/handoff-contract.md`, and `LICENSE`;
- each extracted helper executes from a working directory outside the repository;
- no repository-root helper or sibling repository is required.

The automated unit suite already exercises the extracted helper against an offline local fake Radar HTTP server. A release candidate must keep that test green.

## Gate 3 — isolated Codex install matrix

Use fresh processes/conversations. Do not rely on an already-loaded Skill catalog.

Validate three installation shapes separately:

### A. Creator only

Installed:

```text
creator-topic-opportunity-research
```

Expected:

- current topic scan works with live access;
- it does not pretend the Brief Skill ran;
- when the user asks to continue, it can expose one handoff-ready selected candidate and explain that the full Brief Skill is unavailable.

### B. Brief only

Installed:

```text
evidence-backed-content-brief
```

Expected:

- named topic resolution works;
- “pick one for me” uses the bounded fallback, normally <=5 candidates;
- no new score is invented;
- insight is called only after one topic is selected;
- no-useful-candidate is an allowed result.

### C. Both Skills

Installed:

```text
creator-topic-opportunity-research
evidence-backed-content-brief
```

Expected composed path:

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

The selected feed `id` must remain the exact `topic_id` consumed by history/insight. A valid current-task handoff must not trigger title-based topic rediscovery.

## Gate 4 — trigger safety

Run the existing `evals/cases.json` positive/negative trigger suite in fresh Codex sessions.

Requirements:

- no regression in previous trigger accuracy;
- direct single-company/current-news lookups that do not ask for creator/editorial opportunity research do not attract Topic Intelligence;
- pure rewriting/summarization/title-generation over fully supplied material does not attract Brief;
- explicit Skill invocation still works.

## Gate 5 — M3.1 task-quality matrix

Use `evals/m3-skill-quality.json`.

Do not grade only whether a Skill name appeared. Grade these dimensions:

- correct Skill/workflow routing;
- live-evidence boundary;
- freshness handling;
- topic identity preservation;
- handoff continuity;
- standalone runtime behavior;
- bounded Brief fallback;
- insight-as-analysis boundary;
- user-task completion quality.

For fixture-driven failure states that are impractical to force against production (`stale`, `partial`, explicit source error, degraded insight, no-useful-candidate), the offline contract/eval inspection is authoritative. Do not manipulate production merely to manufacture those states.

## Gate 6 — live network E2E

Use a normal network-capable environment, not a network-restricted trigger sandbox.

Minimum live checks:

1. Creator-only current scan:
   - feed reachable;
   - freshness fields surfaced;
   - compact current shortlist or explicit no-useful-candidate.
2. Brief-only current selection:
   - bounded feed selection;
   - exact selected feed ID preserved;
   - one real insight request after selection.
3. Both-Skills composed workflow:
   - Opportunity Skill selects one current topic;
   - formal handoff uses exact feed ID;
   - Brief consumes the same topic ID without title rediscovery;
   - one real insight request for that selected topic;
   - output includes `must_verify`, `avoid_claims`, and research handoff.
4. Network blocked/degraded check in read-only sandbox:
   - Skill stops current-state workflow;
   - no local/sibling snapshot fallback.

Do not run insight across a broad feed. A few intentional selected-topic calls are enough.

## Gate 7 — ChatGPT package smoke (manual UI, when eligible)

Codex cannot validate ChatGPT's product UI. If an eligible ChatGPT workspace is available, manually test the actual standalone release candidate package/folder:

- upload/install creator-only and confirm it is recognized;
- upload/install brief-only and confirm it is recognized;
- install both and run one composed prompt;
- verify the host either reaches live Radar or clearly reports unavailable live access;
- confirm no repository-root file is required.

This manual UI gate must not be replaced by assumptions about current ChatGPT upload behavior.

## Acceptance report

Record:

### Repository
- base/main SHA;
- tested head SHA;
- clean working tree;
- `VERSION`.

### Offline
- test count/result;
- deterministic archive check;
- standalone extracted-helper result.

### Install matrix
- creator-only;
- brief-only;
- both.

### Trigger
- positives passed;
- negatives passed;
- false positives;
- false negatives.

### Live E2E
- feed freshness/status;
- selected topic ID;
- handoff topic ID;
- Brief history/insight topic ID;
- insight elapsed/result quality;
- blocked-live-data behavior.

### Quality
- task-quality cases run;
- task-completion failures;
- evidence-boundary failures;
- handoff failures;
- standalone-runtime failures.

### Release decision

Choose exactly one:

```text
M3_1_SKILL_QUALITY_PASS
M3_1_SKILL_QUALITY_FAIL
```

Only `PASS` makes the code eligible for a separate `v0.2.0` release decision. It does **not** create or authorize the tag by itself.

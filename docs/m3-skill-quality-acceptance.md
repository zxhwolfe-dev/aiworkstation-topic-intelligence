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
- AI Workstation website analytics, `akaiagents` adoption-report scripts, or `report_topic_radar_m3_metrics.py`;
- changes to the immutable public `v0.1.0` tag.

Do not import acceptance requirements from sibling `akaiagents` work. Missing website analytics/report scripts are not Topic Intelligence Skill failures.

## Gate 1 — repository/offline contracts

Run:

```bash
python3 scripts/sync_skill_runtime.py --check
python3 -m unittest discover -s tests -v
```

Must prove:

- both Skill-local helpers are byte-identical to the root development helper;
- both handoff reference files are identical;
- release builder refuses missing runtime/handoff files;
- Codex doctor refuses an incomplete Skill runtime;
- M3.1 quality eval matrix is valid and covers the required failure/task states;
- all existing M0/M1/M2 trigger, evidence, installer, and release tests remain green.

The extracted-ZIP HTTP E2E uses a loopback socket. Some managed sandboxes deny even local socket bind. In that specific environment the test may report `skipped` for `PermissionError`; that is an environment limitation, not a code failure, provided the same commit has a successful normal CI run where the HTTP E2E executes. Other failures remain failures.

No public network is required for Gate 1.

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

The normal CI suite exercises the extracted helper against an offline local fake Radar HTTP server. A release candidate must keep that CI test green.

## Gate 3 — isolated Codex install matrix

Use fresh processes/conversations. Do not rely on an already-loaded Skill catalog.

A network-restricted Codex sandbox is acceptable for discovery, trigger routing, evidence-boundary behavior, and blocked-live-data checks. Do not classify its DNS failure as a production or Skill failure.

Validate three installation shapes separately:

### A. Creator only

Installed:

```text
creator-topic-opportunity-research
```

Expected:

- Skill discovery/selection works;
- with live access, current topic scan works;
- without live access, it stops safely and does not use local/sibling evidence;
- it does not pretend the Brief Skill ran;
- when the user asks to continue, it can expose one handoff-ready selected candidate and explain that the full Brief Skill is unavailable.

### B. Brief only

Installed:

```text
evidence-backed-content-brief
```

Expected:

- Skill discovery/selection works;
- named topic resolution works when live evidence is available;
- “pick one for me” uses the bounded fallback, normally <=5 candidates;
- no new score is invented;
- insight is called only after one topic is selected;
- no-useful-candidate is an allowed result;
- when live access is blocked, it stops instead of fabricating a candidate.

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

If the host does not expose internal Skill-to-Skill trace, run one audit prompt that explicitly asks it to surface the compact `ati.topic-opportunity-handoff.v1` object before continuing into the Brief. Validate `topic_id == topic_snapshot.id` and the same ID in downstream history/insight when those calls are observable. Do not guess hidden trace state.

## Gate 4 — trigger safety

Run the existing `evals/cases.json` positive/negative trigger suite in fresh Codex sessions.

Requirements:

- no regression in previous trigger accuracy;
- direct single-company/current-news lookups that do not ask for creator/editorial opportunity research do not attract Topic Intelligence;
- pure rewriting/summarization/title-generation over fully supplied material does not attract Brief;
- explicit Skill invocation still works.

Timeout or non-observable host traces must be reported separately from false positives/false negatives. Do not invent a selected Skill name when the host does not expose it.

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

Use an execution path explicitly allowed to reach the public Topic Radar API. A normal standalone helper shell is sufficient for transport validation. A managed Codex `read-only` or network-disabled sandbox is not required to pass live transport.

Do not switch to dangerous/full-access sandbox modes merely to regain network access. Keep live-network capability and filesystem permission decisions separate.

Minimum live checks:

1. Standalone Creator helper:
   - feed reachable;
   - freshness fields visible;
   - stable feed IDs present.
2. Standalone Brief helper:
   - history preserves the exact selected feed ID;
   - perform at most one intentional insight request for the selected topic;
   - capture stdout, stderr, exit code, and elapsed time separately;
   - if the request times out or the upstream returns no usable response, report `LIVE_INSIGHT_BLOCKED` and do not retry across other topics.
3. Fresh Codex workflows:
   - if the Codex sandbox itself cannot reach live Radar, use it only for discovery/blocked behavior;
   - current API responses obtained in the same acceptance run may be supplied to a fresh Skill session as current user-supplied Radar evidence when freshness fields are visible;
   - never substitute persisted historical/local data.
4. Both-Skills composition:
   - Opportunity Skill selects one current topic from live/current supplied evidence;
   - formal handoff uses exact feed ID;
   - Brief consumes the same topic ID without title rediscovery;
   - if live insight is separately unavailable, the Brief must degrade to an evidence-based skeleton and clearly label that limitation rather than breaking handoff continuity.
5. Network blocked/degraded check in read-only sandbox:
   - Skill stops current-state workflow;
   - no local/sibling snapshot fallback.

A `stale=true` live feed is valid transport evidence but is not sufficient for a confident “current/fresh” recommendation. Record that as `LIVE_DATA_STALE` and wait for a fresher snapshot for final live-quality acceptance rather than overriding the Skill evidence boundary.

## Gate 7 — ChatGPT package smoke (manual UI, when eligible)

Codex cannot validate ChatGPT's product UI. If an eligible ChatGPT workspace is available, manually test the actual standalone release candidate package/folder:

- upload/install creator-only and confirm it is recognized;
- upload/install brief-only and confirm it is recognized;
- install both and run one composed prompt;
- verify the host either reaches live Radar or clearly reports unavailable live access;
- confirm no repository-root file is required.

This manual UI gate must not be replaced by assumptions about current ChatGPT upload behavior.

## Acceptance classification

Keep failure classes separate:

- `CODE` — repository/runtime/contract defect reproduced outside environment restrictions;
- `CODEX_ENVIRONMENT` — sandbox/socket/trace/timeout limitation specific to Codex execution;
- `LIVE_NETWORK` — public Radar/Insight unavailable or stale enough to block the requested live-quality claim;
- `SKILL_DISCOVERY` — installed Skill is not discoverable/selected when observable;
- `HANDOFF` — observable ID continuity or handoff-schema violation;
- `INSTALL_RESTORE` — acceptance failed to restore the user's original Skill installation.

Do not report `CODE` merely because a managed sandbox blocks sockets or DNS when normal CI/standalone transport passes.

## Acceptance report

Record:

### Repository
- base/main SHA;
- tested head SHA;
- clean working tree;
- `VERSION`.

### Offline
- test count/result/skips;
- deterministic archive check;
- standalone extracted-helper result;
- normal CI status for the tested commit when local loopback is skipped.

### Install matrix
- creator-only;
- brief-only;
- both.

### Trigger
- positives passed;
- negatives passed;
- false positives;
- false negatives;
- unobservable/timeouts separately.

### Live E2E
- feed freshness/status;
- selected topic ID;
- handoff topic ID;
- Brief history/insight topic ID;
- insight exit code/stderr/elapsed/result quality;
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

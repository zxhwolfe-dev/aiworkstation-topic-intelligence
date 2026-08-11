# M4 Host Integration

M4 starts after the public v0.2.0 Skill release. Its goal is to validate how the same Topic Intelligence Skills behave across real agent hosts before adding another transport layer or expanding Skill business logic.

## Decision question

The main question is:

> Can the published standalone Skills deliver the intended workflow in the target host, and if not, is the missing capability Skill logic or host connectivity?

Do not add Hosted MCP, another backend, or host-specific Skill forks before this question is answered with evidence.

## Capability dimensions

The machine-readable matrix is:

```text
evals/host-capabilities.json
```

Track each host separately across:

- Skill discovery;
- standalone package acceptance;
- bundled runtime execution;
- live Topic Radar access;
- multi-Skill composition.

A pass on one host never implies a pass on another host.

## Current host state

### Codex

v0.2.0 acceptance proved:

- standalone Skill discovery;
- package-local runtime availability;
- safe blocked-live-data behavior;
- exact Opportunity handoff topic identity;
- composed Opportunity → Brief behavior when made observable with an audit prompt.

Managed Codex sandboxes can still impose DNS/socket restrictions. Treat those as host-environment observations rather than silently weakening the Skill evidence boundary.

Codex `exec --json` does not currently expose a first-class "Skill X triggered" event. A trace may contain Skill names because Codex inspected workspace files or Skill definitions while deciding what to do. Therefore a bare Skill-name occurrence is discovery/mention evidence, not proof of invocation.

### Standalone shell

The published package helper has been validated independently of an agent host. This isolates public API transport from host-specific Skill discovery and sandbox behavior.

### ChatGPT

The published v0.2.0 standalone Skills were manually exercised in ChatGPT web in all three target shapes:

- Creator-only;
- Brief-only;
- both Skills installed.

Observed ChatGPT capabilities:

- standalone ZIP upload/package acceptance: **validated**;
- Skill discovery: **validated**;
- bundled runtime execution: **validated**;
- live `https://aiworkstation.cn` Topic Radar access: **validated**;
- selected-topic server `/insight` access from Brief: **validated**;
- multi-Skill Opportunity → Brief composition: **validated behaviorally**.

In the both-Skills smoke, ChatGPT explicitly said Brief should first use the installed Creator Skill for current-topic selection, selected one finalist, and then continued only with finalist history/Topic Insight. No second broad/bounded candidate-selection pass was visible after selection.

The ChatGPT UI did **not** expose the raw serialized `ati.topic-opportunity-handoff.v1` object or an internal handoff-ID trace. Do not claim hidden serialization was directly observed. The host matrix therefore records composition as:

```text
validated_behaviorally_handoff_trace_not_exposed
```

Overall ChatGPT transport decision:

```text
SKILLS_ONLY_PASS
```

Do not add Hosted MCP solely to make these Skills reach Topic Radar in ChatGPT; the standalone packaged runtime already reached the live service successfully.

See:

```text
docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md
```

The ChatGPT smoke also surfaced Skill-quality improvements now tracked on the 0.2.1 patch line: content-format constraints must not become Radar platform filters, provenance should be clearer, valid handoffs must not trigger duplicate selection, and complete server Insight should be reused rather than independently regenerated.

## Host Eval tooling

M4 deliberately uses two stages.

This tooling is a strict observability check, not a complete semantic Host behavior gate. Codex JSON traces do not expose every Skill decision or HTTP request as a stable first-class event. Before a release candidate, run the live collector with `--strict-observation`, retain the raw and graded reports, then manually verify every selected eval case's `must_show` and `must_not` fields—including zero public `/insight` calls and no reselection after a valid handoff.

### Stage 1 — collect fresh host traces

Use:

```bash
python3 scripts/run_host_evals.py --help
```

The collector launches one fresh `codex exec --json` process per selected case and stores the raw trace in an `ati.host-eval.v1` report.

#### Executable launcher

When the launcher is a normal executable on `PATH`, pass it directly:

```bash
python3 scripts/run_host_evals.py \
  --suite trigger \
  --case trend-zh-current-ai \
  --launcher codex \
  --timeout 45 \
  --output /tmp/ati-host-eval-trigger.json
```

#### Bash-function launcher

Local launchers such as `codex_yinhe` may be Bash functions from `.bashrc`, not executables. Use the explicit adapter:

```bash
python3 scripts/run_host_evals.py \
  --suite trigger \
  --case trend-zh-current-ai \
  --launcher "python3 scripts/bash_function_launcher.py codex_yinhe" \
  --timeout 45 \
  --output /tmp/ati-host-eval-trigger.json
```

The adapter starts an interactive Bash so the user's `.bashrc` can define the requested function. The function name must be a normal Bash identifier, and all remaining Codex arguments/prompts are passed positionally rather than interpolated into shell source text.

This mode is explicit because reading interactive shell configuration can have user-specific side effects. Do not silently fall back from a missing executable to a shell function.

#### Dry-run

```bash
python3 scripts/run_host_evals.py \
  --dry-run \
  --suite trigger \
  --case trend-zh-current-ai \
  --launcher "python3 scripts/bash_function_launcher.py codex_yinhe"
```

#### Selected trigger cases

```bash
python3 scripts/run_host_evals.py \
  --suite trigger \
  --case trend-zh-current-ai \
  --case negative-current-company-news \
  --launcher "python3 scripts/bash_function_launcher.py codex_yinhe" \
  --timeout 45 \
  --output /tmp/ati-host-eval-trigger.json
```

The collector keeps a broad token-based `route_observation` for diagnostics and backward compatibility. Do not use a bare collector failure as final evidence that a Skill was invoked: passive file reads can contain Skill names.

### Stage 2 — conservatively grade observable behavior

Run:

```bash
python3 scripts/grade_host_eval.py \
  /tmp/ati-host-eval-trigger.json \
  --output /tmp/ati-host-evidence-trigger.json
```

The grader emits:

```text
ati.host-evidence.v1
```

It distinguishes:

- `mentioned_skills` — a Skill name appeared anywhere in the raw trace;
- `definition_read_skills` — a `command_execution.command` directly read `SKILL.md`, `agents/openai.yaml`, or the handoff reference;
- `runtime_use_skills` — a `command_execution.command` directly referenced the Skill-local `scripts/topic_radar_client.py` helper;
- `handoff_agent_message_observed` — the formal handoff schema appeared in an agent message.

Important rules:

- reading/listing a Skill definition is consultation/discovery evidence, not invocation;
- command output that merely prints a helper path is not runtime-use evidence;
- a negative trigger case fails only when unexpected Skill runtime use is actually observable;
- a positive trigger case can pass at a weaker evidence level when the expected Skill definition is clearly consulted, because Codex currently lacks a first-class Skill-trigger event;
- formal handoff use is not inferred merely because Codex read `handoff-contract.md`.

This conservative grading model prevents the false positive where Codex scans Topic Intelligence Skill files while correctly answering a non-Topic-Intelligence request.

### Quality suite

Collect:

```bash
python3 scripts/run_host_evals.py \
  --suite quality \
  --case composed-pick-and-brief-zh \
  --launcher "python3 scripts/bash_function_launcher.py codex_yinhe" \
  --timeout 60 \
  --output /tmp/ati-host-eval-quality.json
```

Then grade the raw report with `grade_host_eval.py`.

Semantic `must_show` / `must_not` review still remains a separate step. Neither script claims access to hidden reasoning.

## Safety boundary

The tooling intentionally does **not** mutate `$HOME/.agents/skills` in v1.

It assumes the desired Skill installation shape has already been prepared by an operator. This avoids making hidden changes to a user's real Skill directory until a host-supported isolated Skill-home mechanism is explicitly validated.

It also does not:

- modify Codex auth/config/proxy settings;
- widen sandbox permissions;
- silently source shell configuration unless the explicit Bash-function adapter is selected;
- retry live Topic Insight across multiple candidates;
- manufacture stale/partial/source-error production states;
- grade hidden reasoning or guess a Skill selection that is absent from observable evidence.

## Report schemas

Collector reports use:

```text
ati.host-eval.v1
```

Evidence grader reports use:

```text
ati.host-evidence.v1
```

Keep the raw collector report when diagnosing host-version changes. The evidence report is the preferred source for trigger/runtime conclusions.

## M4 sequence

Completed:

1. real ChatGPT v0.2.0 upload smoke in Creator-only, Brief-only, and both-Skills shapes;
2. ChatGPT capability evidence recorded in `evals/host-capabilities.json`;
3. Codex collector + conservative evidence grader made repeatable and validated;
4. Skills-only determined sufficient for current ChatGPT transport.

Also completed for v0.2.1:

5. improved Skill quality from the real v0.2.0 host findings;
6. ran isolated Creator-only, Brief-only, and both-Skills v0.2.1 acceptance without a ChatGPT login;
7. recorded that this is host/runtime evidence and does not claim the v0.2.1 ChatGPT upload UI was re-tested.

See `docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md`.

Hosted MCP/App transport should be reconsidered only if a future host demonstrates a concrete live-connectivity limitation.

## v0.3 decision boundary

Do not create a v0.3 product scope merely because M4 tooling exists.

A later Skill version should be driven by observed host/user failures such as:

- package incompatibility;
- missing live connectivity that requires a supported transport;
- unreliable composition that needs a Skill contract change;
- a repeatedly requested workflow extension such as research continuation.

Host Eval tooling changes alone are repository tooling and do not require moving the immutable v0.2.0 release tag.

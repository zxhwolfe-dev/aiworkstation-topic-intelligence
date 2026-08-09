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

### Standalone shell

The published package helper has been validated independently of an agent host. This isolates public API transport from host-specific Skill discovery and sandbox behavior.

### ChatGPT

ChatGPT remains a separate manual product-surface smoke. Do not infer any of the following from Codex:

- that the package will upload successfully;
- that bundled Python can execute;
- that the host can reach `https://aiworkstation.cn`;
- that two uploaded Skills will compose automatically.

Test the published v0.2.0 artifacts in creator-only, brief-only, and both-Skills shapes when the workspace supports Skill upload.

## Host Eval Runner

Use:

```bash
python3 scripts/run_host_evals.py --help
```

The first supported host is Codex.

### Executable launcher

When the launcher is a normal executable on `PATH`, pass it directly:

```bash
python3 scripts/run_host_evals.py \
  --suite trigger \
  --case trend-zh-current-ai \
  --launcher codex \
  --timeout 45 \
  --output /tmp/ati-host-eval-trigger.json
```

### Bash-function launcher

Local aliases such as `codex_yinhe` may be Bash functions from `.bashrc`, not executables. The runner intentionally does not source shell configuration itself. Use the explicit adapter instead:

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

### Trigger suite

Dry-run one case without invoking Codex:

```bash
python3 scripts/run_host_evals.py \
  --dry-run \
  --suite trigger \
  --case trend-zh-current-ai \
  --launcher "python3 scripts/bash_function_launcher.py codex_yinhe"
```

Run selected fresh-process cases and write a structured report:

```bash
python3 scripts/run_host_evals.py \
  --suite trigger \
  --case trend-zh-current-ai \
  --case negative-current-company-news \
  --launcher "python3 scripts/bash_function_launcher.py codex_yinhe" \
  --timeout 45 \
  --output /tmp/ati-host-eval-trigger.json
```

### Quality suite

```bash
python3 scripts/run_host_evals.py \
  --suite quality \
  --case composed-pick-and-brief-zh \
  --launcher "python3 scripts/bash_function_launcher.py codex_yinhe" \
  --timeout 60 \
  --output /tmp/ati-host-eval-quality.json
```

The runner always launches a fresh `codex exec` process per selected case. It does not reuse a conversation.

## Safety boundary

The runner intentionally does **not** mutate `$HOME/.agents/skills` in v1.

It assumes the desired Skill installation shape has already been prepared by an operator. This avoids making hidden changes to a user's real Skill directory until a host-supported isolated Skill-home mechanism is explicitly validated.

It also does not:

- modify Codex auth/config/proxy settings;
- widen sandbox permissions;
- silently source shell configuration unless the explicit Bash-function adapter is selected;
- retry live Topic Insight across multiple candidates;
- manufacture stale/partial/source-error production states;
- grade hidden reasoning or guess a Skill selection that is absent from the trace.

## Report schema

Reports use:

```text
ati.host-eval.v1
```

Each case records:

- suite and case ID;
- original prompt;
- expected Skill/workflow metadata from the existing eval file;
- fresh process command;
- runtime status and timeout;
- exit code and elapsed time;
- raw stdout/stderr, with bounded storage;
- Topic Intelligence Skill names visible in the trace;
- expected workflow tokens visible in the trace;
- an observation classification.

The runner's classification is deliberately narrow. It can say that an expected Skill/workflow token was observable, wrong, partial, or unobservable. It does **not** claim to automatically grade all `must_show` / `must_not` semantic requirements.

## M4 sequence

1. Run the real ChatGPT upload smoke with v0.2.0 artifacts.
2. Record ChatGPT capability evidence in `evals/host-capabilities.json`.
3. Use `run_host_evals.py` to make Codex regression runs repeatable.
4. Decide whether Skills-only is sufficient for ChatGPT.
5. Only if live access is the demonstrated blocker, design a thin Hosted MCP/App connection that exposes the existing Topic Radar contract without duplicating its business logic.

## v0.3 decision boundary

Do not create a v0.3 product scope merely because M4 tooling exists.

A later Skill version should be driven by observed host/user failures such as:

- package incompatibility;
- missing live connectivity that requires a supported transport;
- unreliable composition that needs a Skill contract change;
- a repeatedly requested workflow extension such as research continuation.

Host Eval Runner changes alone are repository tooling and do not require moving the immutable v0.2.0 release tag.

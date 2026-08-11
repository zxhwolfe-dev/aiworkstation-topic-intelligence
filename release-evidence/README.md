# Persistent release evidence

Each release after the immutable v0.2.1 line must add a directory named `v<VERSION>/` containing:

- `host-eval.json` — the raw `ati.host-eval.v1` report from a real `--strict-observation` run;
- `host-evidence.json` — the `ati.host-evidence.v1` graded report;
- `manual-review.json` — structured human review with `approved: true`, one ordered `cases` record per eval case, `decision: "pass"`, and exact `must_show_reviewed` / `must_not_reviewed` arrays copied from the evaluated contract after review; also require `anonymous_server_insight_calls: 0` and `handoff_reselection: "none"`.

Do not copy failed, dry-run, or merely unobservable reports into a release directory and do not mark them approved. The release workflow validates this structure for versions newer than v0.2.1.

Runtime workflow evidence requires a completed, exit-zero Python invocation of the Skill-local helper for a `feed`, `sources`, or `history` read without an explicit custom origin and whose stdout is contract-valid Radar JSON. Reading or compiling helper source, `--help`, failed/network-error calls, explicit `--base-url` overrides, pipes/redirections, and compound shell commands do not qualify. This trace gate is not a cryptographic attestation of the host process; protected release controls and the structured manual trace review remain required.

For a live release candidate, outer-shell network checks are insufficient: the Host
itself must run with the explicit `--live-radar-network` mode in a temporary,
clean, detached `workspace-write` worktree. The launcher records
`sandbox=workspace-write`, `live_radar_network=true`, and the exact network
allowlist `['aiworkstation.cn']`. Read-only or unrestricted sandboxes, missing or
expanded allowlists, custom Radar origins, and any Host-created worktree changes
are invalid evidence.

Raw reports also include a structured JSONL lifecycle classification. A transient
Codex response-stream disconnect may be recorded as `complete_after_recovery`
only when a complete, exit-zero turn still ends with `turn.completed`; it is not
equivalent to a terminal failure. `incomplete_or_failed`, timeouts, `turn.failed`,
non-stream errors, malformed/truncated JSONL, unfinished items, or tool activity
after the final agent message are rejected by the verifier.

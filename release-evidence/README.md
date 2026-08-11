# Persistent release evidence

Each release after the immutable v0.2.1 line must add a directory named `v<VERSION>/` containing:

- `host-eval.json` — the raw `ati.host-eval.v1` report from a real `--strict-observation` run;
- `host-evidence.json` — the `ati.host-evidence.v1` graded report;
- `manual-review.json` — structured human review with `approved: true`, one ordered `cases` record per eval case, `decision: "pass"`, and exact `must_show_reviewed` / `must_not_reviewed` arrays copied from the evaluated contract after review; also require `anonymous_server_insight_calls: 0` and `handoff_reselection: "none"`.

Do not copy failed, dry-run, or merely unobservable reports into a release directory and do not mark them approved. The release workflow validates this structure for versions newer than v0.2.1.

Runtime workflow evidence requires a completed, exit-zero Python invocation of the Skill-local helper for an official-origin `feed`, `sources`, or `history` read whose stdout is contract-valid Radar JSON. Reading or compiling helper source, `--help`, failed/network-error calls, custom origins, pipes/redirections, and compound shell commands do not qualify.

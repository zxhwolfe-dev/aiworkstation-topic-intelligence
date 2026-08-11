# Persistent release evidence

Each release after the immutable v0.2.1 line must add a directory named `v<VERSION>/` containing:

- `host-eval.json` — the raw `ati.host-eval.v1` report from a real `--strict-observation` run;
- `host-evidence.json` — the `ati.host-evidence.v1` graded report;
- `manual-review.md` — human review of every selected case's `must_show` and `must_not`, including:
  - `APPROVED: yes`;
  - `must_show: reviewed`;
  - `must_not: reviewed`;
  - `anonymous_server_insight_calls: 0`;
  - `handoff_reselection: none`.

Do not copy failed, dry-run, or merely unobservable reports into a release directory and do not mark them approved. The release workflow validates this structure for versions newer than v0.2.1.

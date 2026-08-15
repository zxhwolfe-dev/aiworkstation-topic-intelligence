# Contributing

Bug reports and focused improvements are welcome through GitHub Issues and pull requests.

Before opening a pull request:

1. keep the public product as one Skill and one install archive unless a proposal explicitly changes the product contract;
2. preserve the read-only Radar evidence boundary and do not add anonymous server-side model calls, shared credentials, or custom Radar origins;
3. update canonical runtime/reference sources and use the repository sync mechanism rather than editing generated copies independently;
4. add or update tests for trigger behavior, helper commands, evidence grading, and release determinism;
5. run:

```bash
python3 scripts/sync_skill_runtime.py --check
python3 scripts/sync_plugin_candidate.py --check
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts skills
python3 scripts/run_host_evals.py --suite v0.3.1 --dry-run
```

Changes to Skill behavior require a new version-bound live Host Eval and release evidence before publication. Do not include credentials, private traces, user conversations, or production data in issues, fixtures, or commits.

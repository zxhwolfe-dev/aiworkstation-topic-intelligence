# Topic Intelligence Plugin Candidate

This directory contains the skills-only Plugin candidate and its submission materials. Runtime behavior comes from the canonical `topic-intelligence` Skill.

After changing the canonical Skill, synchronize and validate the candidate:

```bash
python3 scripts/sync_plugin_candidate.py
python3 scripts/sync_plugin_candidate.py --check
python3 -m unittest tests.test_plugin_candidate -v
```

Submission status and operational prerequisites belong in `submission-checklist.md`, not in public listing copy.

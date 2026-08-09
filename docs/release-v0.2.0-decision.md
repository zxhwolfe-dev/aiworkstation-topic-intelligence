# v0.2.0 Release Decision

Date: 2026-08-09

Decision:

```text
RELEASE_ELIGIBLE
```

The M3.1 Skill quality gate passed on the 0.2.0 line. See `docs/m3.1-final-acceptance-2026-08-09.md` for the evidence.

## Why the upstream Insight 503 is not a release blocker

The final acceptance made exactly one real selected-topic `/insight` request. The upstream returned HTTP 503 with `gpt_request_failed`.

This does not invalidate the Skill release because the acceptance demonstrated the intended unavailable-Insight behavior:

- the selected live Topic Radar identity was preserved exactly through `ati.topic-opportunity-handoff.v1` and history;
- no broad-feed Insight fan-out or retry occurred;
- the Brief Skill explicitly reported Insight unavailable;
- it produced an evidence-based degraded skeleton instead of inventing model output;
- `must_verify`, `avoid_claims`, audience payoff, selected angle, opening/hook, research handoff, and visual/material needs remained present;
- no local/sibling/cached evidence was used as fallback.

The upstream model-backed Insight endpoint can be re-checked independently after release. A temporary upstream 503 is an operational dependency state, not a defect in the portable Skill runtime or workflow contract.

## Release constraints

- Tag only the validated `main` release-prep commit after CI is green.
- The tag must be exactly `v0.2.0` and must match `VERSION=0.2.0`.
- Never move, delete, or reuse `v0.1.0` or `v0.2.0` after publication.
- Do not tag a feature branch.
- The existing GitHub release workflow is responsible for rebuilding, testing, and publishing deterministic artifacts.
- After publication, verify the release assets and SHA256 values, then update user-facing docs from “v0.2.0 unreleased” to the published status.
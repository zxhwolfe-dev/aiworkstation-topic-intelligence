# Topic Opportunity Handoff Contract

Schema: `ati.topic-opportunity-handoff.v1`

This contract is the structured bridge from `creator-topic-opportunity-research` to `evidence-backed-content-brief`.

It is not a new backend or a persisted evidence store. It only carries one selected candidate and the live evidence context already obtained during the **current task** so the receiving Skill does not have to identify the same topic from scratch.

## Shape

```json
{
  "schema": "ati.topic-opportunity-handoff.v1",
  "topic_id": "feed.items[n].id",
  "snapshot": {
    "generated_at": "2026-08-09T00:00:00Z",
    "partial": false,
    "stale": false,
    "snapshot_age_seconds": 120,
    "refreshing": false
  },
  "topic_snapshot": {
    "id": "same value as topic_id",
    "title": "current Radar title",
    "title_en": "optional current Radar title",
    "summary": "optional current Radar summary",
    "platform": "optional",
    "region": "optional",
    "category": "optional",
    "trend_stage": "optional",
    "opportunity_score": 0,
    "first_seen_at": "optional",
    "signal_count": 0,
    "evidence": [],
    "trend": {}
  },
  "selection": {
    "reason": "why this candidate was selected for the user's stated goal",
    "observed_signals": [],
    "unknowns": [],
    "risks": []
  },
  "user_goal": {
    "platform": "optional",
    "format": "optional",
    "audience": "optional",
    "constraint": "optional"
  }
}
```

## Producer rules

1. `topic_id` must equal the stable live feed `id` exactly.
2. `topic_snapshot.id` must equal `topic_id`.
3. `snapshot` fields must come from the same live feed response used to select the topic.
4. `topic_snapshot` must contain only fields observed on that live feed item; do not fabricate missing values.
5. `evidence` and `trend` may be bounded to what is useful for the selected candidate, but copied values must remain faithful to the live response.
6. `selection.reason`, `observed_signals`, `unknowns`, and `risks` are Skill analysis, not source facts.
7. Produce a handoff for the selected finalist only; do not serialize an entire broad feed.

## Consumer rules

`evidence-backed-content-brief` may accept this handoff as the parent live-topic context when all of the following are true:

- it was produced in the current task/session workflow;
- `schema` is exactly `ati.topic-opportunity-handoff.v1`;
- `topic_id == topic_snapshot.id`;
- required freshness fields are visible;
- `stale` is not true;
- `partial` does not remove evidence needed for the requested claim;
- the handoff is not being loaded from a previous task, cache, log, saved file, or model memory.

When those conditions hold, the Brief Skill may skip a redundant topic-name/feed re-identification step and continue with `/history` when movement matters and host-model reasoning. Premium `/insight` is not part of the public handoff workflow and is allowed only through an explicitly authenticated native Premium connection.

Refresh the live feed before relying on the handoff when:

- `stale=true`;
- freshness fields are missing;
- `partial=true` materially affects the requested decision;
- the user asks for a new/current re-check after time has passed;
- the handoff comes from another task/session or persisted artifact;
- identity is inconsistent.

## Evidence boundary

The handoff does not upgrade analysis into fact. Keep separate:

- `snapshot` and `topic_snapshot`: source facts copied from the current Radar response;
- `selection`: analysis/recommendation/unknowns/risks;
- authenticated Premium Insight, when explicitly supplied by the native host: model analysis over the server-known topic.

A persisted handoff is never a substitute for a new live response in a later current-topic task.

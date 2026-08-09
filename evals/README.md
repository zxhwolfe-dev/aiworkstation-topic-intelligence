# Topic Intelligence Skill evals

`cases.json` is the reusable acceptance matrix for real Codex/ChatGPT Skill behavior.

The goal is not to grade prose style. It checks whether the host:

1. invokes the correct Skill for the user's intent;
2. avoids Topic Intelligence when the request is unrelated, evergreen, translation-only, supplied-material writing, direct company-news lookup, or generic platform analysis;
3. follows the existing Topic Radar workflow rather than inventing a second backend;
4. preserves freshness/evidence boundaries;
5. does not invent a second scoring system or promote model insight to source fact;
6. refuses local/sibling snapshot fallback when live evidence is unavailable.

## Current matrix

M2 expands the matrix to **20 cases**:

- 6 `cross-market-trend-research` positives;
- 5 `evidence-backed-content-brief` positives;
- 9 negative/boundary cases that should invoke neither Topic Intelligence Skill.

Newer boundary cases intentionally include natural, ambiguous wording such as:

- asking what overseas topic may not yet be crowded in Chinese content;
- asking for freshness/source limitations before recommendations;
- asking for a Xiaohongshu-oriented current-topic brief;
- asking for the lowest-verification-risk angle;
- comparing TikTok/YouTube content styles without requesting live trends;
- writing a script from material the user already supplied;
- asking for direct company news;
- translating an AI-news passage.

## Case fields

- `id`: stable case identifier.
- `prompt`: prompt to run in a fresh conversation when testing implicit invocation.
- `expected_skill`: expected implicitly selected Skill, or `null` when neither Skill should trigger.
- `expected_calls`: minimum logical Topic Radar calls needed for the workflow.
- `optional_calls`: calls that are appropriate only when the answer needs them.
- `must_show`: concepts or output sections that should be visible in a passing response.
- `must_not`: failure modes that should not occur.

`expected_calls` describe logical endpoint use (`feed`, `sources`, `history`, `insight`), not a requirement to print internal commands to the user.

## How to run implicit evals

Use a **fresh Codex/ChatGPT conversation per implicit-trigger case** so a previous explicit Skill selection does not bias the next case.

For each case:

1. paste only the `prompt`;
2. record whether a Topic Intelligence Skill was selected;
3. record the selected Skill name when observable;
4. inspect the answer and host/API activity for the required workflow;
5. mark each `must_show` and `must_not` item;
6. preserve exact failure text when something goes wrong.

For `expected_skill: null`, a pass means neither Topic Intelligence Skill is invoked.

## Explicit smoke tests

Before implicit evals, verify explicit invocation works:

```text
$cross-market-trend-research 过去24小时有哪些值得中国科技博主提前关注的海外AI选题？
```

and:

```text
$evidence-backed-content-brief 从当前AI热点中选一个适合2到3分钟短视频的题材，给我研究就绪的选题简报。
```

Explicit smoke tests prove installation/discovery. They do **not** replace implicit-trigger evals.

## Gate A vs Gate B

Trigger/evidence behavior can be tested in a safe network-restricted sandbox. Live Topic Radar E2E requires a separately approved network-capable execution path.

Do not interpret sandbox DNS failure as production failure, and never replace unavailable live evidence with local/sibling data.

## Release quality bar

For a trigger-quality release:

- all positive cases should select the expected Skill or an equivalent correct composed workflow;
- all negative cases should avoid both Topic Intelligence Skills;
- no case should invent current facts when live Radar data is unavailable;
- no case should use local/sibling snapshots as current evidence;
- stale/partial/source limitations must remain visible when material.

If a positive case misses the Skill or a negative case triggers it, adjust the Skill frontmatter `description` from observed evidence before adding backend complexity.

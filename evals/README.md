# Topic Intelligence Skill evals

`cases.json` is the M1 acceptance set for real Codex/ChatGPT Skill behavior.

The goal is not to grade prose style. It checks whether the host:

1. invokes the correct Skill for the user's intent;
2. avoids Topic Intelligence when the request is unrelated or evergreen;
3. follows the expected Topic Radar workflow;
4. preserves freshness/evidence boundaries;
5. does not invent a second scoring system or promote model insight to source fact.

## Case fields

- `id`: stable case identifier.
- `prompt`: prompt to run in a fresh conversation when testing implicit invocation.
- `expected_skill`: expected implicitly selected Skill, or `null` when neither Skill should trigger.
- `expected_calls`: minimum logical Topic Radar calls needed for the workflow.
- `optional_calls`: calls that are appropriate only when the answer needs them.
- `must_show`: concepts or output sections that should be visible in a passing response.
- `must_not`: failure modes that should not occur.

`expected_calls` describe logical endpoint use (`feed`, `sources`, `history`, `insight`), not a requirement to print internal commands to the user.

## How to run M1 manually

Use a **fresh Codex conversation per implicit-trigger case** so a previous explicit Skill selection does not bias the next case.

For each case:

1. paste only the `prompt`;
2. record whether Codex selected a Topic Intelligence Skill;
3. record the selected Skill name when visible;
4. inspect the answer and any local/API activity for the required workflow;
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

## Passing M1

M1 is ready to merge when:

- both Skills are discoverable in Codex;
- both explicit smoke tests reach live Topic Radar successfully;
- all positive implicit cases select the expected Skill or produce an equivalent correct routed workflow;
- all negative cases avoid both Skills;
- no case invents current facts when live Radar data is unavailable;
- no material contract/freshness/evidence regression is found.

If a positive case misses the Skill or a negative case triggers it, adjust the Skill frontmatter `description` before adding more backend code.

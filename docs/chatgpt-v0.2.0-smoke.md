# ChatGPT v0.2.0 manual smoke

This is the M4 product-surface check for the published v0.2.0 standalone Skills.

It is intentionally separate from Codex/runtime release acceptance. Do not infer ChatGPT behavior from Codex results.

## Published artifacts

Use the immutable v0.2.0 GitHub Release artifacts:

```text
aiworkstation-topic-intelligence-0.2.0-creator-topic-opportunity-research.zip
aiworkstation-topic-intelligence-0.2.0-evidence-backed-content-brief.zip
```

Expected SHA256:

```text
7d7ca0266abd55df374e4ca37ff5affadf9eabffe694474d18be96c5402dc897  aiworkstation-topic-intelligence-0.2.0-creator-topic-opportunity-research.zip
9c90adccd61966321201c8c05b0fad963e18ea412bd3112c694a4fe0cea9dab8  aiworkstation-topic-intelligence-0.2.0-evidence-backed-content-brief.zip
```

Do not upload a random checkout snapshot when testing the released package.

## What this smoke must answer

For ChatGPT, record these separately:

1. package upload/scan accepted;
2. Skill can be discovered or explicitly selected;
3. bundled runtime/code can execute, if the host supports that execution path;
4. live `https://aiworkstation.cn` Topic Radar access works, or the host reports it unavailable;
5. both Skills compose Opportunity → `ati.topic-opportunity-handoff.v1` → Brief.

## Shape A — Creator only

Install/upload only:

```text
creator-topic-opportunity-research
```

Prompt:

```text
今天有哪些 AI 题材值得中国科技内容创作者继续研究？先检查当前 Radar 的新鲜度和来源覆盖，再给最值得看的 3 个。
```

Record:

- upload status;
- scan/review status;
- Skill discovery;
- live Radar reachable yes/no;
- if blocked, whether the Skill refuses memory/local fallback;
- whether it falsely claims the Brief Skill ran.

## Shape B — Brief only

Install/upload only:

```text
evidence-backed-content-brief
```

Prompt:

```text
只用当前安装的 Skill，从当前 AI 热点里挑一个最适合做 2-3 分钟中文解释视频的题材，并直接给我研究型内容简报。
```

Record:

- upload/discovery status;
- live Radar reachable yes/no;
- bounded selection behavior;
- at most one selected topic;
- whether Insight is called only after selection when observable;
- no invented score;
- safe blocked/degraded behavior.

## Shape C — Both Skills

Install/upload both published v0.2.0 Skills.

Prompt:

```text
从当前 AI 热点里挑一个最适合做 2-3 分钟中文解释视频的题材，然后直接把它做成研究就绪的内容简报。我要受众收益、最强角度、前三秒、叙事结构、must_verify、avoid_claims 和素材建议。
```

Expected conceptual path:

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

Record:

- whether both Skills are discoverable;
- whether the host composes them automatically;
- selected topic identity when observable;
- handoff identity continuity when observable;
- live Radar/Insight accessibility;
- required Brief sections;
- any ChatGPT-specific scan, permission, runtime, or networking limitation.

## Decision

After the three shapes, classify ChatGPT as one of:

```text
SKILLS_ONLY_PASS
HOST_NETWORK_BLOCKED
PACKAGE_OR_RUNTIME_INCOMPATIBLE
COMPOSITION_BLOCKED
WORKSPACE_NOT_ELIGIBLE
UNOBSERVABLE
```

Interpretation:

- `SKILLS_ONLY_PASS`: do not add Hosted MCP merely for transport.
- `HOST_NETWORK_BLOCKED`: evaluate a thin approved Hosted MCP/App connection to the existing Topic Radar API.
- `PACKAGE_OR_RUNTIME_INCOMPATIBLE`: handle as host compatibility before changing business logic.
- `COMPOSITION_BLOCKED`: determine whether host orchestration or Skill contract changes are required.
- `WORKSPACE_NOT_ELIGIBLE`: no technical conclusion about ChatGPT Skill execution can be made from that workspace.

Never move or replace the immutable v0.2.0 tag based on this smoke.

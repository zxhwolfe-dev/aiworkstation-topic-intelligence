# ChatGPT Skill installation

Last verified against official OpenAI documentation: **2026-08-09**.

Topic Intelligence ships as two Agent Skills:

- `creator-topic-opportunity-research`
- `evidence-backed-content-brief`

Latest public release: **v0.2.0**.

v0.2.0 is the current public standalone Skill release. Each published Skill archive is self-contained and includes its own runtime helper plus the formal Topic Opportunity handoff reference.

## Current ChatGPT availability

OpenAI's current Help Center says Personal Skills are generally available for ChatGPT Business, Enterprise, Healthcare, and Edu users. Workspace permissions can further control whether users may create, upload, share, publish, or install Skills.

Do not market Topic Intelligence as a one-click install for every ChatGPT plan.

Official source:

- https://help.openai.com/en/articles/20001066

## Upload path

For an eligible ChatGPT account/workspace:

1. Open the ChatGPT sidebar.
2. Select **Plugins**.
3. Open the **Skills** tab in the Plugin Directory.
4. Select **Create**.
5. Choose **Upload from your computer**.
6. Upload the Skill using the format currently accepted by the product UI. The GitHub Release ZIP is the canonical checksummed distribution artifact; unpack it first if the UI expects the contained Skill directory/files rather than the ZIP container.
7. Let ChatGPT finish its Skill scan/review before use.

Uploaded Skills may be available immediately after scanning, may require review, or may be blocked by the product's safety scan.

## Standalone package boundary

In v0.2.0, each Skill package contains:

```text
SKILL.md
agents/openai.yaml
scripts/topic_radar_client.py
references/handoff-contract.md
LICENSE
```

This removes the previous package gap where a standalone archive could describe the repository-root helper without carrying that helper itself.

The package being self-contained does **not** guarantee that every ChatGPT workspace/surface grants arbitrary live network execution to the bundled helper. If the host cannot reach the current Topic Radar public contract, the Skill must report live evidence as unavailable and must not fall back to model memory/local artifacts.

If ChatGPT exposes a native approved live connection/tool path instead, the Skill may use the same public Topic Radar contract through that host capability rather than executing the helper directly.

## Surface synchronization

OpenAI currently documents that Personal Skills must be added separately on desktop and web/mobile; they do not automatically sync across those surfaces.

Treat each ChatGPT surface installation as an independent installation unless current product documentation says otherwise.

## First-use prompts

### Find creator/editorial opportunities

```text
过去24小时有哪些正在升温、值得中国科技内容创作者提前研究的 AI 题材？先告诉我 Radar 新鲜度和来源覆盖，再给候选。
```

Expected Skill:

```text
creator-topic-opportunity-research
```

### Turn one live topic into a brief

```text
从当前 AI 热点中挑一个适合 2–3 分钟内容的题材，给我受众收益、最强角度、前三秒、必须核验的事实和素材建议。
```

Preferred workflow when both are installed:

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

When the handoff is produced and consumed inside the same task, the exact selected feed `id` should remain the history/insight `topic_id`; Brief should not rediscover the topic by title.

When only `evidence-backed-content-brief` is installed, it may resolve a supplied topic directly or use its bounded single-topic fallback. It must not invent a new score or call insight for a broad feed.

## Important product boundary

A normal factual request such as:

```text
OpenAI今天发布了什么新消息？
```

is **not** a Topic Intelligence task by itself. It should use normal current-information lookup unless the user also asks for creator/editorial topic prioritization or content-opportunity analysis.

Likewise, rewriting supplied material, translation, generic title writing, and platform-style comparison should not invoke Topic Intelligence unless a live-topic decision is requested.

## Manual ChatGPT package smoke (when eligible)

Codex acceptance cannot prove ChatGPT UI/package behavior. If an eligible workspace is available, manually test the published v0.2.0 standalone packages:

1. creator-only standalone package;
2. brief-only standalone package;
3. both packages with one composed Opportunity → handoff → Brief prompt;
4. live Radar reachable or explicit blocked-live-data state;
5. no repository-root file requirement.

This is a separate product-surface smoke, not a reason to reinterpret Codex/runtime acceptance or move the immutable v0.2.0 tag. Record any ChatGPT-specific limitation separately from Skill code defects.

# ChatGPT Skill installation

Last verified against official OpenAI documentation: **2026-08-09**.

Topic Intelligence ships as two Agent Skills:

- `creator-topic-opportunity-research`
- `evidence-backed-content-brief`

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

Expected workflow:

```text
creator-topic-opportunity-research
  -> evidence-backed-content-brief
```

## Important product boundary

A normal factual request such as:

```text
OpenAI今天发布了什么新消息？
```

is **not** a Topic Intelligence task by itself. It should use normal current-information lookup unless the user also asks for creator/editorial topic prioritization or content-opportunity analysis.

Likewise, rewriting supplied material, translation, generic title writing, and platform-style comparison should not invoke Topic Intelligence unless a live-topic decision is requested.

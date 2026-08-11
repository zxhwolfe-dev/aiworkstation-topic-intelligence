# ChatGPT Skill installation

Last verified against official OpenAI documentation: **2026-08-09**.

Topic Intelligence ships as two Agent Skills:

- `creator-topic-opportunity-research`
- `evidence-backed-content-brief`

Current package version: **v0.2.2**.

## Current ChatGPT availability

OpenAI's current Help Center says Personal Skills are generally available for ChatGPT Business, Enterprise, Healthcare, and Edu users. Workspace permissions can further control whether users may create, upload, share, publish, or install Skills.

Do not market Topic Intelligence as a one-click install for every ChatGPT plan.

Official source:

- https://help.openai.com/en/articles/20001066

## Upload path

For an eligible ChatGPT account/workspace:

1. Open the ChatGPT sidebar.
2. Select **Plugins**.
3. Open **Skills**.
4. Select **Create**.
5. Choose **Upload from your computer**.
6. Upload the checksummed Skill artifact (or its contained Skill directory if the UI requires unpacked files).
7. Let ChatGPT finish scan/review before use.

## Package boundary

v0.2.x Skill archives are self-contained and include:

```text
SKILL.md
agents/openai.yaml
scripts/topic_radar_client.py
references/handoff-contract.md
references/quality-contract.md
LICENSE
```

v0.2.2 changes the bundled helper into a **public no-cost read transport** with deterministic `python3` invocation and bounded scans. It exposes only:

```text
feed
sources
history
```

It intentionally does not expose anonymous server-side Topic Insight.

## Cost boundary in ChatGPT

Normal public ChatGPT use should work as:

```text
ChatGPT Skill
  -> live AI Workstation feed/sources/history
  -> current ChatGPT model performs the editorial reasoning
```

This is the normal path, not a fallback.

The public Skill must not:

- call anonymous AI Workstation `/insight`;
- embed a server API key/shared bearer token;
- ask the user to paste a private credential into chat;
- silently consume the website's free/member model quota.

A future **authenticated** AI Workstation App/Plugin/OAuth connection may expose Premium Topic Insight separately. That native connection must identify the user and enforce membership/quota/credits. The portable Skill ZIP is not the authentication layer.

## Real ChatGPT validation

The published v0.2.0 packages were manually tested in ChatGPT web:

- Creator-only upload/discovery/runtime/live Radar: PASS;
- Brief-only bounded selection/live Radar: PASS;
- both-Skills behavioral composition: PASS;
- raw internal handoff serialization: not exposed by UI, so not overclaimed.

See [`chatgpt-v0.2.0-smoke-result-2026-08-09.md`](chatgpt-v0.2.0-smoke-result-2026-08-09.md).

v0.2.1 additionally addresses issues found in that smoke:

- short-video/duration/language constraints are not Radar platforms;
- explicit `AI` topic scope is preserved from the first bounded query;
- Radar facts are separated from host editorial analysis;
- no second selection after a valid handoff;
- public Brief uses host reasoning with zero AI Workstation server-model spend.

The v0.2.1 and v0.2.2 candidates were accepted through strict isolated Codex Host Eval, including live Radar evidence, neutral workspaces, Skill fixture isolation, manual review, and persistent verifier checks. This is Host/runtime evidence; it does **not** claim that the v0.2.2 ZIP upload UI was re-tested in ChatGPT. The last real ChatGPT Web upload evidence remains v0.2.0. See [`v0.2.1-non-ui-host-acceptance-2026-08-10.md`](v0.2.1-non-ui-host-acceptance-2026-08-10.md).

## First-use prompts

### Creator

```text
过去24小时有哪些正在升温、值得中国科技内容创作者提前研究的 AI 题材？先告诉我 Radar 新鲜度和来源覆盖，再给候选。
```

### Brief

```text
从当前 AI 热点中挑一个适合 2–3 分钟内容的题材，给我受众收益、最强角度、前三秒、必须核验的事实和素材建议。
```

With both Skills installed:

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

The exact selected feed `id` should remain stable through the current-task handoff. Brief may query finalist history when needed, but in normal public mode it should then use the ChatGPT model itself to create the editorial plan.

## Product boundary

A factual lookup such as:

```text
OpenAI今天发布了什么新消息？
```

is not automatically a Topic Intelligence task. Rewriting supplied material, translation, generic titles, and generic platform-style comparison also should not invoke these Skills unless a live-topic creator/editorial decision is requested.

## Surface synchronization

Treat each ChatGPT surface installation independently unless current OpenAI product documentation says otherwise.

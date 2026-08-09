# AI Workstation Topic Intelligence

**先找出今天真正值得研究的题，再把一个当前热点变成研究就绪的内容简报。**

[English](README.md)

最新公开版本：**v0.1.0 public preview**

Topic Intelligence 建在现有 AI Workstation「全球热点选题雷达」之上。它不重新做爬虫、聚类、评分、数据库或 GPT 后端，而是把实时 Radar 证据转成更可靠的创作者/编辑决策。

## 你可以直接拿它做什么？

### 1. 今天什么 AI 题材值得研究？

```text
今天有哪些 AI 题材值得我继续研究或做内容？先检查 Radar 是否足够新，再给我最值得看的 3 个。
```

预期 Skill：

```text
creator-topic-opportunity-research
```

目标不是再给几十条新闻，而是给少量候选，并明确：数据新鲜度、来源覆盖、机会分/阶段、观察到的趋势、事实与推断、下一步核验什么。

### 2. 海外有没有值得中文内容提前跟的机会？

```text
海外现在有哪些科技话题正在升温、可能值得中文内容创作者提前研究？中文区是否已经做烂如果没有直接证据就明确说不知道。
```

Skill 可以比较平台/地区的当前信号，但如果 Radar 没有直接测量“中文区内容饱和度”，就必须把它标成未知或假设，不能把猜测包装成数据。

### 3. 把当前热点变成研究/制作可直接接手的简报

```text
从当前 AI 热点里挑一个适合 2–3 分钟解释型内容的题材，给我受众收益、最强角度、前三秒、叙事结构、必须核验的事实、不能乱说的内容和素材建议。
```

预期工作流：

```text
creator-topic-opportunity-research
  -> evidence-backed-content-brief
```

完整 M3 场景和采用指标见 [`docs/m3-user-scenarios.md`](docs/m3-user-scenarios.md)。

## 选择你的入口

### Codex / 开发者

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

默认安装到：

```text
$HOME/.agents/skills/
```

显式调用：

```text
$creator-topic-opportunity-research
$evidence-backed-content-brief
```

安装器幂等、安全，不覆盖无关路径；如果你用过 pre-0.1.0 的旧名 `cross-market-trend-research`，只有在确认旧 symlink 属于当前 checkout 时才会安全迁移。

### ChatGPT

OpenAI 当前 Help Center 说明：Personal Skills 一般面向 ChatGPT Business、Enterprise、Healthcare、Edu 用户，工作区权限还可以进一步限制 Skill 的创建、上传和安装；Personal Skills 当前也需要在 desktop 与 web/mobile 分别添加，不会自动跨界面同步。

符合条件的用户目前可以在 ChatGPT：**Plugins → Skills → Create → Upload from your computer** 上传 Skill。

当前安装说明见 [`docs/chatgpt-install.md`](docs/chatgpt-install.md)。

官方参考：https://help.openai.com/en/articles/20001066

M3 不把 ChatGPT Skill 安装当成唯一入口。普通用户不应该先理解 Agent Skill 才能获得价值，因此我们同时设计 AI Workstation 直接用户入口，首屏/CTA 文案见 [`docs/website-entry-copy.zh-CN.md`](docs/website-entry-copy.zh-CN.md)。

## 两个正式 Skill

### `creator-topic-opportunity-research`

用于为创作者/编辑决策比较和排序实时 Radar 候选，包括：

- 当前升温/早期机会；
- freshness 与 source coverage；
- 多来源 evidence；
- 平台/地区差异；
- 跨市场传播时差假设。

### `evidence-backed-content-brief`

把一个**已由实时 Radar 确认的当前 Topic**转成可执行内容简报，包括：

- 一个优先角度；
- 受众收益和平台/形式适配；
- hook / 前三秒 / narrative beats；
- research questions / search handoff；
- `must_verify`；
- `avoid_claims`；
- `fact_basis` / unsupported assumptions；
- visual/material needs。

## 证据硬边界

**实时请求失败时，绝不能去本地文件找“替代实时数据”。**

以下内容不能替代当前 live evidence：

- `../akaiagents` 中的旧快照或本地数据；
- SQLite；
- fixtures / test captures；
- cached/exported JSON；
- logs / generated reports；
- 模型记忆冒充当前 Radar 事实。

同时必须区分五层：

1. **Radar 事实**；
2. **分析**；
3. **建议**；
4. **未知**；
5. **风险**。

## 产品边界

```text
akaiagents / 全球热点选题雷达
公开数据源 -> 聚合 -> 聚类 -> opportunity_score
-> trend/history -> source health -> GPT topic insight
                         |
                         | 公开 API
                         v
aiworkstation-topic-intelligence
Skills -> 证据检查 -> 跨市场解释
-> 选题机会判断 -> 内容简报编排
```

本仓库不重复实现 crawler、Topic 聚类、`opportunity_score`、趋势历史、数据库、来源健康或 GPT Topic Insight 后端。

## 已有 Topic Radar API

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`

默认生产地址：`https://aiworkstation.cn`。

Feed 卡片稳定身份字段是 `id`；传给 history/insight 时使用同一个值作为 `topic_id`。

当 `refreshing=true` 时，连续请求不是原子快照，应结合时间戳和刷新状态解释两次请求之间的变化。

## 发行 / 本地 helper

构建独立 Skill 包：

```bash
python3 scripts/build_release.py --output dist
```

v0.1.0 发行包含两个确定性 Apache-2.0 ZIP，以及 `release-manifest.json` 和 `SHA256SUMS`。

可选只读 API helper：

```bash
python3 scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history TOPIC_ID
python3 scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

helper 只使用 Python 标准库，不实现新的评分、抓取、持久化或模型逻辑。

## 测试与 M3 场景

```bash
python3 -m unittest discover -s tests -v
```

现有 trigger eval 有 20 条正/负例；M3 另外增加 [`evals/m3-scenarios.json`](evals/m3-scenarios.json)，把用户任务、Skill 链、必须展示/禁止行为和 activation event 独立出来。

M3 优先观察：

- `scan_to_followup_rate`；
- `scan_to_brief_rate`；
- `next_day_return_rate`；
- `blocked_live_data_rate`；
- `no_useful_candidate_rate`。

这些是产品采用指标，不是新的 Radar 评分。

## 更多文档

- ChatGPT 当前安装/资格说明：[`docs/chatgpt-install.md`](docs/chatgpt-install.md)
- M3 三个真实用户场景：[`docs/m3-user-scenarios.md`](docs/m3-user-scenarios.md)
- AI Workstation 首屏/CTA 文案：[`docs/website-entry-copy.zh-CN.md`](docs/website-entry-copy.zh-CN.md)
- 分发：[`docs/distribution.md`](docs/distribution.md)
- 发布清单：[`docs/release-checklist.md`](docs/release-checklist.md)
- 架构：[`docs/architecture.md`](docs/architecture.md)

## 环境

- Python 3.10+
- helper / installer / release builder 均无第三方运行时依赖
- 不依赖 `../akaiagents/.venv`
- 不导入 `akaiagents` 私有模块

## 当前状态

- **M0 已完成：** Skill-first 基础与生产 API contract。
- **M1 已完成：** Codex 安装/发现、trigger eval、证据边界、真实 Insight E2E。
- **M2 已完成：** v0.1.0 public preview、确定性发行、release 自动化、最终 Skill 命名与边界收敛。
- **M3 进行中：** 用户入口、安装理解、三个真实产品场景，以及是否值得进入 v0.2.0 工程的采用/回访验证。

# AI Workstation Topic Intelligence

**先找出今天真正值得研究的题，再把一个当前热点变成研究就绪的内容简报。**

[English](README.md)

最新公开版本：**v0.1.0 public preview**

当前开发线：**v0.2.0 未发布** —— 重点是 standalone Skill 真正自包含、Opportunity → Brief 正式 handoff、单 Skill fallback，以及真实任务质量验收。只有 fresh-session 验收通过后才考虑 `v0.2.0` tag/release；现有 `v0.1.0` 保持不变。

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

### 3. 选一个当前 Topic，并直接做成简报

```text
从当前 AI 热点里挑一个适合 2–3 分钟解释型内容的题材，给我受众收益、最强角度、前三秒、叙事结构、必须核验的事实、不能乱说的内容和素材建议。
```

两个 Skill 都安装时，优先工作流：

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

第一个 Skill 只选一个 finalist，把**同一个 live feed `id`**、快照 freshness、观察信号、未知、风险以及用户的平台/形式约束交给 Brief。当前任务里的有效 handoff 不再让 Brief 通过标题重新猜 Topic。

如果只安装 `evidence-backed-content-brief`，它也能独立使用：用户给 Topic 名称/ID 时直接实时解析；如果用户让它“自己挑一个”，只做一次 bounded feed selection（默认通常不超过 5 个候选），用 Radar 已有 `opportunity_score`、stage、freshness、evidence 和用户约束选最多 1 个，再只对这个 Topic 调 insight。不会另造评分，也允许明确“当前没有合适候选”。

## 两个 Skill

### `creator-topic-opportunity-research`

用于为创作者/编辑决策比较和排序实时 Radar 候选，包括：

- 当前升温/早期机会；
- freshness 与 source coverage；
- 多来源 evidence；
- 平台/地区差异；
- 跨市场传播时差假设；
- 选中 finalist 后生成一个正式 current-task handoff。

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

它可以消费当前任务里的 `ati.topic-opportunity-handoff.v1`、实时解析用户指定 Topic，或在 Opportunity Skill 不可用时使用 bounded standalone fallback。

## v0.2 开发线：真正 self-contained 的 Skill

每个 Skill 目录现在都设计成完整可分发单元：

```text
skill-name/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/handoff-contract.md
  LICENSE   # release ZIP 中注入
```

因此 standalone ZIP 不再依赖仓库根目录的 `scripts/topic_radar_client.py`，也不依赖 `../akaiagents`。

两个 Skill 内的 helper 与根目录开发 helper 由测试强制逐字节一致；如果 helper 或 handoff contract 缺失，release builder 会拒绝构建。

## 安装方式

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

`doctor` 现在不只检查 `SKILL.md` / `agents/openai.yaml`，也检查 bundled helper 和 handoff contract。

### Standalone ZIP

```bash
python3 scripts/build_release.py --output dist
```

每个 ZIP 只包含一个 Skill 根目录，以及它自己需要的 runtime/helper/reference 和 Apache-2.0 license。详见 [`docs/distribution.md`](docs/distribution.md)。

### ChatGPT

符合条件的 ChatGPT 工作区可以使用当前官方支持的 Skill 上传流程；具体资格、工作区权限和不同界面的同步行为可能变化，见 [`docs/chatgpt-install.md`](docs/chatgpt-install.md)。

ChatGPT UI 上传是单独的人工验收面，Codex 通过并不能证明 ChatGPT UI 上传一定可用。

## 证据硬边界

**实时请求失败时，绝不能去本地文件找“替代实时数据”。**

以下内容不能替代当前 live evidence：

- `../akaiagents` 中的旧快照或本地数据；
- SQLite；
- fixtures / test captures；
- cached/exported JSON；
- logs / generated reports；
- 之前保存的 Topic Opportunity handoff；
- 模型记忆冒充当前 Radar 事实。

当前任务里的 handoff 只是**工作流上下文**，不是新的持久化证据层。换了任务/时间后，需要重新读取 live Radar。

同时必须区分：

1. **Radar 事实**；
2. **分析**；
3. **建议**；
4. **未知**；
5. **风险**；
6. **Topic Insight**：已知 Topic 上的模型分析，不是独立 verified fact。

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
-> 选题机会判断 -> current-task handoff
-> 内容简报编排
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

## 验证

离线测试：

```bash
python3 -m unittest discover -s tests -v
```

现在除了原来的 trigger/evidence/release 测试，还会验证：

- Skill-local helper 与根 helper 一致；
- release ZIP 确实包含完整 runtime；
- ZIP 解压到仓库之外后，用包内 helper 对本地假 Radar 发真实 feed 请求；
- handoff 两边协议一致；
- Brief bounded fallback 规则；
- 24 条 M3.1 真实任务/故障态质量矩阵。

质量场景：

- [`evals/m3-skill-quality.json`](evals/m3-skill-quality.json)
- [`docs/m3-skill-quality-acceptance.md`](docs/m3-skill-quality-acceptance.md)

在决定发布 v0.2.0 之前，还必须做真实 fresh Codex / live network 验收。

## 更多文档

- M3.1 Skill 质量验收：[`docs/m3-skill-quality-acceptance.md`](docs/m3-skill-quality-acceptance.md)
- 分发：[`docs/distribution.md`](docs/distribution.md)
- 发布清单：[`docs/release-checklist.md`](docs/release-checklist.md)
- 架构：[`docs/architecture.md`](docs/architecture.md)
- ChatGPT 当前安装/资格说明：[`docs/chatgpt-install.md`](docs/chatgpt-install.md)
- M3 用户场景：[`docs/m3-user-scenarios.md`](docs/m3-user-scenarios.md)

## 环境

- Python 3.10+
- helper / installer / release builder 均无第三方运行时依赖
- 不依赖 `../akaiagents/.venv`
- 不导入 `akaiagents` 私有模块

## 当前状态

- **M0 已完成：** Skill-first 基础与生产 API contract。
- **M1 已完成：** Codex 安装/发现、trigger eval、证据边界、真实 Insight E2E。
- **M2 已完成：** v0.1.0 public preview、确定性发行、release 自动化、最终 Skill 命名与边界收敛。
- **M3 adoption baseline 已完成：** 用户入口文档和三个产品场景。
- **M3.1 进行中：** self-contained standalone Skills、正式 Opportunity → Brief handoff、Brief-only fallback、ZIP E2E、任务质量与 fresh-session 验收，作为未发布 0.2 开发线。

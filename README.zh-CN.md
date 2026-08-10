# AI Workstation Topic Intelligence

**先找出今天真正值得研究的题，再把一个当前热点变成研究就绪的内容简报。**

[English](README.md)

最新公开版本：**v0.2.1**

v0.2.0 已经证明：两个 standalone Skill 可以在 ChatGPT 上传/发现/执行，能直接访问实时 AI Workstation Topic Radar，也能完成 Creator → Brief 组合流程。

v0.2.1 继续优化真实 ChatGPT 使用中发现的问题，并新增一个非常重要的商业/成本边界：

> **公开 Skill 的正常使用，不再消耗 AI Workstation 服务器端大模型 Token。**

Topic Intelligence 继续建立在 AI Workstation「全球热点选题雷达」之上，不重新做爬虫、聚类、评分或持久化。

## 你可以拿它做什么？

### 1. 今天什么 AI 题材值得研究？

```text
今天有哪些 AI 题材值得我继续研究或做内容？先检查 Radar 是否足够新，再给我最值得看的 3 个。
```

预期 Skill：

```text
creator-topic-opportunity-research
```

Skill 从实时 Radar 获取事实，由**当前 ChatGPT / Codex / Agent 自己的大模型**完成比较、解释和推荐。

### 2. 海外有没有值得提前跟的机会？

```text
海外现在有哪些科技话题正在升温、可能值得中文内容创作者提前研究？中文区是否已经做烂如果没有直接证据就明确说不知道。
```

如果 Radar 没有直接测量中文区饱和度或传播时差，就必须标成未知/假设，不能当作数据事实。

### 3. 选一个当前 Topic，并直接做成研究简报

```text
从当前 AI 热点里挑一个适合 2–3 分钟解释型内容的题材，给我受众收益、最强角度、前三秒、叙事结构、必须核验的事实、不能乱说的内容和素材建议。
```

两个 Skill 都安装时：

```text
creator-topic-opportunity-research
  -> ati.topic-opportunity-handoff.v1
  -> evidence-backed-content-brief
```

Creator 只选一个 finalist，并把同一个 live `id` 交给 Brief。Brief 不再重新选题。

如果只装 Brief，它会做一次 bounded live selection（通常最多 5 个候选），选最多一个，再按需要查 history，然后由**当前宿主模型**直接生成研究就绪的内容简报。

## v0.2.1：公开 Skill 的成本边界

公开 Skill 应该可以放心传播，而不是每有一个人调用，就消耗你网站服务器的大模型额度。

### 公开 bundled helper 只允许读取无模型成本的 Radar 数据

```text
GET /api/v1/ai/topic-radar/feed
GET /api/v1/ai/topic-radar/sources
GET /api/v1/ai/topic-radar/history?topic_id=...
```

正常公开 Skill 流程：

```text
AI Workstation 实时 Radar 事实
            ↓
用户当前的 ChatGPT / Codex / Agent 模型
            ↓
选题 / 解释 / 角度 / hook / must_verify / avoid_claims / 素材建议
```

因此：

> **正常公开 Skill 使用 = 0 次 AI Workstation 服务器端 LLM 调用。**

公开 ZIP 不会：

- 暴露匿名 `insight` CLI 命令；
- 内置 AI Workstation API Key；
- 放一个所有人共用的 bearer token；
- 让用户把私人 Secret 粘贴到聊天里；
- 偷偷扣网站免费用户/会员的大模型额度。

### 未来 Premium 能力仍然可以保留

服务器端 Topic Insight 并不是永久删除，而是改成**账号绑定的 Premium 能力**。

未来如果 ChatGPT/其他宿主通过 AI Workstation App / Plugin / OAuth 等方式建立原生认证连接：

```text
用户连接 AI Workstation 账号
      ↓
识别 user_id / plan / quota
      ↓
由连接层扣会员/额度
      ↓
可选调用 Premium Topic Insight
```

这种情况下 `/insight` 可以作为增强能力。

但 bundled public Skill **不是认证层**，不能自己带共享 Key 去调用收费模型。

没有 Premium 连接也完全不影响公开 Skill 正常完成选题和 Brief；宿主模型直接做分析即可。

## 两个 Skill

### `creator-topic-opportunity-research`

负责：

- 当前升温 / early opportunity；
- freshness / source coverage；
- 平台和地区差异；
- evidence breadth；
- 跨市场假设；
- 选中一个 finalist 后生成 handoff。

### `evidence-backed-content-brief`

把实时 Radar Topic 变成：

- make / conditional / watch 判断；
- 受众收益；
- 最强角度；
- 前三秒 / hook；
- 2–3 分钟叙事结构；
- research questions / search queries；
- `must_verify`；
- `avoid_claims`；
- 素材需求；
- 未知与风险。

在公开模式下，这些编辑策划内容由**用户当前宿主模型**生成，不再由 AI Workstation 服务器模型生成。

## v0.2.1 真实 ChatGPT 实测后修掉的问题

1. **内容形式不等于 Radar 平台**

   `短视频 / 2–3 分钟 / 中文 / 普通用户` 不允许误当成 `platform/source` 过滤条件。

2. **用户明确说 AI，第一轮就查 AI**

   不能：

   ```text
   AI
   → 先查 generic technology
   → 得到手机/二维码/数据库
   → 第二次再收窄 AI
   ```

3. **Radar 事实和 AI 编辑判断分开**

   “受众更大”“更适合中国用户”“更容易传播”等默认属于宿主分析，不是 Radar 测量事实。

4. **handoff 后不再二次选题**

   ```text
   Creator 选 A
   → handoff A
   → Brief 继续 A
   ```

5. **公开 Brief 不再调用服务器模型**

   由宿主模型直接完成内容策划。

统一规则在：

```text
references/topic-intelligence-quality-contract.md
```

每个 Skill 包内也自带：

```text
references/quality-contract.md
```

## Standalone Skill 结构

```text
skill-name/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/handoff-contract.md
  references/quality-contract.md
  LICENSE
```

release builder 会强制检查这些 portable 文件与 canonical source 一致。

## 安装

### Codex

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

默认：

```text
$HOME/.agents/skills/
```

### Standalone ZIP

```bash
python3 scripts/build_release.py --output dist
```

### ChatGPT

v0.2.0 已经在 ChatGPT Web 做过真实 Creator-only / Brief-only / Both-Skills smoke：

- ZIP 上传：PASS
- Skill discovery：PASS
- bundled runtime：PASS
- live Radar：PASS
- 双 Skill 组合：行为验证 PASS

v0.2.1 候选包另外完成了不依赖 ChatGPT 登录的三条隔离新代理验收（Creator-only / Brief-only / Both-Skills）、解压包执行、实时 `feed` / `sources` / `history`、断网无本地回退和零 `/insight` 检查。这属于宿主/运行时验收，不声称重新测试了 v0.2.1 的 ChatGPT ZIP 上传界面。

详见：

- [`docs/chatgpt-install.md`](docs/chatgpt-install.md)
- [`docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md`](docs/chatgpt-v0.2.0-smoke-result-2026-08-09.md)
- [`docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md`](docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md)

## 证据硬边界

当前热点事实只能来自当前任务里的 live Radar 数据，不能用：

- `../akaiagents` 本地旧快照；
- SQLite；
- fixtures；
- cached/exported JSON；
- logs / reports；
- 旧 handoff；
- 模型记忆冒充当前事实。

最终输出要区分：

1. **Radar 事实**；
2. **宿主编辑分析**；
3. **未知 / must_verify**；
4. **可选 Premium Topic Insight**：只有已认证账号连接明确提供时才可使用，而且仍属于模型分析，不是独立事实来源。

## 产品边界

```text
AI Workstation Global Topic Radar
公开源 -> 聚合 -> 聚类 -> opportunity_score
-> trend/history -> source health
                 |
                 | public read API
                 v
Topic Intelligence Public Skills
证据检查 -> 选题 -> handoff -> 宿主模型生成 Brief

未来可选 Premium 连接
用户认证 -> 会员/额度校验 -> Server Topic Insight
```

本仓库不负责网站账户、计费、会员数据库或服务器模型后端。

## 验证

```bash
python3 scripts/sync_skill_runtime.py --check
python3 -m unittest discover -s tests -v
```

测试会验证：

- helper 三份一致；
- ZIP 确定性；
- 解压后 standalone runtime 可执行；
- handoff identity；
- Brief bounded fallback；
- v0.2.1 ChatGPT-derived quality cases；
- 公共 helper 没有 `insight` 命令；
- 公共 helper 只发 GET 请求。

## 当前状态

- **v0.2.1**：当前最新公开不可变版本；公开模式由宿主模型完成 Brief，不消耗 AI Workstation 服务器端 LLM Token。
- **v0.2.0**：上一公开不可变版本，也是最近一次在 ChatGPT Web 手工上传验证的版本。

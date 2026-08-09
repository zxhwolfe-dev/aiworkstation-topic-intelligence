# AI Workstation Topic Intelligence

**基于 AI Workstation「全球热点选题雷达」实时数据的趋势研究与内容策划 Skills。**

[English](README.md)

当前可分发版本：**0.1.0 public preview**

这个仓库**不重新开发热点雷达**。热点采集、聚合、聚类、机会分、趋势历史、来源健康和已有 GPT 选题分析继续由 `akaiagents` 中的全球热点选题雷达负责。

本仓库只负责把这些已有能力变成 ChatGPT、Codex 等支持 Skill 的 AI Host 可以正确执行的工作流，并严格区分实时事实、分析、建议、未知项和风险。

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

本项目明确不重复实现 crawler、Topic 聚类、`opportunity_score`、趋势历史、数据库、来源健康或 GPT Topic Insight 后端。

## 两个核心 Skill

### `creator-topic-opportunity-research`

用于为创作者/编辑决策比较和排序实时 Topic Radar 候选，包括加速题材、早期机会、平台/地区差异、数据新鲜度，以及需要进一步验证的跨市场时间差。

典型请求：

> 过去24小时海外有哪些正在升温、值得中国科技博主提前关注的 AI 选题？

### `evidence-backed-content-brief`

把一个**已经由实时 Topic Radar 确认的当前 Topic**转成可执行内容简报，包括 angle、hook、前三秒、受众、平台适配、研究问题、`must_verify` 和 `avoid_claims`。

典型请求：

> 从当前 AI 热点里挑一个适合 2–3 分钟内容的题材，给我研究就绪的选题简报。

## 证据硬边界

**实时请求失败时，绝不能去本地文件找“替代实时数据”。**

以下内容永远不能替代当前 live evidence：

- `../akaiagents` 中的旧快照或本地数据；
- SQLite 数据库；
- fixtures / test captures；
- cached/exported JSON；
- 日志、生成报告或其他历史持久化数据。

网络受限的 sandbox 只代表当前无法获取 live data，不代表可以使用模型记忆或本地旧数据补位。

## Codex 快速安装

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

默认安装到：

```text
$HOME/.agents/skills/
```

安装器使用 symlink，不复制 Skill；重复安装安全，并拒绝覆盖无关目录。pre-0.1.0 阶段曾使用旧名 `cross-market-trend-research`；升级执行 `install` 时，仅当旧 symlink 确认指向当前 checkout 的旧路径时才会安全删除，并替换为 `creator-topic-opportunity-research`。

常用命令：

```bash
python3 scripts/install_codex_skills.py version
python3 scripts/install_codex_skills.py status
python3 scripts/install_codex_skills.py doctor
python3 scripts/install_codex_skills.py uninstall
```

交互式 Codex 可在支持时用 `/skills` 检查发现状态。显式调用使用 `$creator-topic-opportunity-research` 或 `$evidence-backed-content-brief`；隐式触发由 eval 持续验证。

## 构建独立 Skill 发行包

```bash
python3 scripts/build_release.py --output dist
```

输出：

```text
dist/
  aiworkstation-topic-intelligence-0.1.0-creator-topic-opportunity-research.zip
  aiworkstation-topic-intelligence-0.1.0-evidence-backed-content-brief.zip
  release-manifest.json
  SHA256SUMS
```

每个 ZIP 只包含一个自包含 Skill，并带有 `SKILL.md`、`agents/openai.yaml` 和 Apache-2.0 `LICENSE`。构建是确定性的；Skill 目录里如果存在 symlink，发行构建会直接拒绝，避免包意外引用外部文件。

完整分发、升级、ChatGPT 上传、GitHub Release、未来 Plugin/Hosted MCP 边界见 [`docs/distribution.md`](docs/distribution.md)。

## ChatGPT 分发

当前 OpenAI 产品文档支持 ChatGPT 中的可复用 Skills，并允许符合条件的账号/工作区从本机上传 Skill。OpenAI Skills 遵循 Agent Skills 开放标准。

GitHub Release 中的 ZIP 是每个 Skill 的便携、可校验发行资产。实际安装时使用当时 ChatGPT 产品支持的 Skill 上传流程；如果界面要求上传解包后的 Skill 文件/目录而不是 ZIP 容器本身，就先解包再上传。具体可用性取决于当前 ChatGPT 套餐、工作区权限和使用界面。

不要假设某一个 ChatGPT 界面安装后的 Skill 会自动覆盖或同步所有其他界面的安装。

## 已有 Topic Radar API

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`

默认生产地址：`https://aiworkstation.cn`。

### Topic ID

- Feed 卡片稳定 ID 字段是 `id`；
- history / insight 请求把这个值原样作为 `topic_id`；
- history / insight 响应再以 `topic_id` 返回同一身份。

### 刷新一致性

当 `refreshing=true` 时，连续请求不是同一个原子快照；两次请求之间出现 history 点数变化，应结合时间戳和刷新状态判断。

## 本地 API helper

`scripts/topic_radar_client.py` 只使用 Python 标准库，不做评分、聚类、数据库、抓取或新模型逻辑。

```bash
python3 scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history TOPIC_ID
python3 scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

普通读取使用较短 timeout；模型型 `/insight` 使用独立、更长的 timeout。

## 测试与 Eval

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions 在 Python 3.10 / 3.12 上运行同一套离线测试。

当前 eval 已扩展到 **20 条真实边界用例**，包括：

- 当前热点/加速/早期机会；
- 平台和跨市场比较；
- 内容简报和高验证要求简报；
- stale / partial / source coverage；
- 普通写作、翻译、已有素材写脚本、代码任务、公司新闻查询、平台风格分析等**不应该触发 Topic Intelligence** 的请求。

M1 原始 12 条真实 Codex 验收中观察到 false positive = 0、false negative = 0；M2 在首个 public preview tag 前继续扩大边界覆盖。

## Codex 两道验收门

### Gate A：发现 / 触发 / 证据行为

可以用安全、网络受限、read-only 的 Codex sandbox 验证 Skill 选择、负例、安全降级以及禁止本地旧快照 fallback。

### Gate B：真实 Topic Radar E2E

真实联网验收必须使用明确允许访问 Topic Radar 的执行路径。不要为了联网把文件系统权限扩大到危险模式。

详细流程见 [`docs/codex-m1-acceptance.md`](docs/codex-m1-acceptance.md)。

## Release

- 版本：[`VERSION`](VERSION)
- 变更记录：[`CHANGELOG.md`](CHANGELOG.md)
- 许可证：[`LICENSE`](LICENSE) — Apache-2.0
- 分发说明：[`docs/distribution.md`](docs/distribution.md)
- 发布清单：[`docs/release-checklist.md`](docs/release-checklist.md)

当 `vX.Y.Z` Git tag 与 `VERSION` 一致时，release workflow 会运行测试、构建确定性 ZIP，并把两个 Skill 包、manifest、checksum 发布到 GitHub Release。

普通分支和 PR 不会自动创建 tag，也不会自动发布版本。

## Plugin / Hosted MCP

OpenAI 当前把 Plugin 定位为可以组合 Skills，并可选组合 Apps / app templates 的更高层容器。

M2 **不猜测、不照搬社区格式来造未经官方确认的 Plugin manifest**。等官方 builder/schema/submission 路径公开且可验证后，再增加正式 Plugin 包装。

Hosted MCP 同样暂缓。如果未来因为 Host 网络限制确实需要，它只能做薄的 transport/auth/tool exposure，不得复制 Topic Radar 的采集、聚类、评分、历史、数据库或 GPT insight。

## 环境

- Python 3.10+
- helper / installer / release builder 均无第三方运行时依赖
- 不依赖 `../akaiagents/.venv`
- 不导入 `akaiagents` 私有模块

## 当前状态

- **M0 已完成：** Skill-first 基础与生产 API contract。
- **M1 已完成：** Codex 安装/发现、触发 eval、证据边界、真实 insight E2E。
- **M2 进行中：** 版本化 public preview、确定性发行包、release 自动化、doctor 和更强真实边界 eval。

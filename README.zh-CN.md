# AI Workstation Topic Intelligence

**基于 AI Workstation「全球热点选题雷达」现有实时数据的选题研究与内容简报 Skills。**

这个仓库**不重新开发热点雷达**。热点采集、聚合、聚类、机会分、趋势历史、来源健康和已有 GPT 选题分析都继续由 `akaiagents` 中的全球热点选题雷达负责。

本仓库只负责把这些已经存在的能力变成可被 ChatGPT、Codex 等 AI Host 正确使用的工作流。

## 边界

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

本项目明确不重复实现 crawler、Topic 聚类、`opportunity_score`、趋势历史、数据库或 GPT Topic Insight 后端。

## 两个核心 Skill

### `cross-market-trend-research`

用于发现当前热点、加速题材、早期机会、平台/地区差异和需要进一步验证的跨市场时间差。

### `evidence-backed-content-brief`

用于把一个**当前、已由 Topic Radar 确认的 Topic**转成可执行内容简报，包括 angle、hook、前三秒、受众、视觉素材、研究问题、`must_verify` 与 `avoid_claims`。

## 已有公开 API

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`

默认生产地址：`https://aiworkstation.cn`。

### Topic ID 命名

- Feed 卡片稳定 ID 字段是 `id`；
- history / insight 请求把这个值原样作为 `topic_id`；
- history / insight 响应再以 `topic_id` 返回同一身份。

### 刷新中的一致性

当 `refreshing=true` 时，连续请求并不是同一个原子快照；history 点数在两次请求之间增加是正常现象，应结合时间戳判断。

## 证据硬边界

**实时请求失败时，绝不能去本地文件找“替代实时数据”。**

两个 Skill 都明确禁止把以下内容当作当前证据：

- `../akaiagents` 中的旧快照或本地数据；
- SQLite 数据库；
- fixtures / test captures；
- cached JSON / 导出文件；
- 日志、生成报告或其他持久化历史数据。

这些材料可以用于开发/测试，但不能支撑“现在正在发生什么”的结论。

如果 live Topic Radar 不可达，Skill 必须安全降级：说明实时证据不可用，而不是用模型记忆或本地旧数据补位。

## Codex 安装

M1 提供安全的 symlink 安装器：

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py status
```

默认安装到：

```text
$HOME/.agents/skills/
```

不会复制 Skill，也不会覆盖已存在的无关目录。

## Codex 验收分两道门

### Gate A：Skill 触发/证据边界

可以使用 `codex exec --ephemeral --sandbox read-only` 之类的安全隔离模式测试：

- Skill 是否正确触发；
- 负例是否不误触；
- 无网络时是否安全拒绝；
- 是否禁止本地旧快照 fallback。

### Gate B：真实网络 E2E

Codex sandbox 可能限制网络。网络受限时出现 DNS/连接失败，不应直接解释为 Topic Radar 生产故障。

真实 API 验收必须使用**明确允许访问 Topic Radar 的执行路径**，例如普通 shell 直接运行本仓库的只读 helper，或由宿主提供网络能力。

不要为了获得网络访问而把文件系统权限扩大到危险模式。

## 本地辅助脚本

`scripts/topic_radar_client.py` 只使用 Python 标准库，不做评分、聚类、数据库、抓取或新的 AI 推理。

```bash
python3 scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python3 scripts/topic_radar_client.py sources
python3 scripts/topic_radar_client.py history TOPIC_ID
python3 scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

`insight` 会调用现有 Topic Radar GPT 分析能力。

## 环境与依赖

- Python 3.10+
- 当前 helper 无第三方运行时依赖
- 不依赖 `../akaiagents/.venv`
- 不导入 `akaiagents` 私有模块

## 测试

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions 在 Python 3.10 和 3.12 上运行同一套离线测试。

## 当前状态

- M0：Skill-first 基础版本已合入 main。
- M1：Codex 安装、触发 eval 和证据边界加固正在 PR #2 验收。

暂不增加 crawler、数据库、新评分引擎、OAuth、Billing 或 Hosted MCP。

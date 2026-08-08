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
                         | 公开只读 API
                         v
aiworkstation-topic-intelligence
Skills -> 证据检查 -> 跨市场解释
-> 选题机会判断 -> 内容简报编排
```

本项目明确不重复实现：

- NewsNow、TrendRadar、MediaCrawler、TikTok、YouTube、Hacker News、RSS 采集器；
- Topic 聚类、去重；
- `opportunity_score`、`trend_stage`、历史趋势算法；
- 来源健康、缓存、stale、持久化；
- 已有 GPT Topic Insight 后端。

## M0 两个核心 Skill

### `cross-market-trend-research`

用于回答：

- 最近 24 小时全球有哪些值得关注的 AI/科技选题？
- 哪些题材正在加速？
- 哪些属于早期机会？
- 不同地区、平台的信号有什么差异？
- 是否存在值得进一步验证的跨市场时间差？

它必须基于实时 Topic Radar 数据，不允许用模型记忆冒充“当前热点”。

### `evidence-backed-content-brief`

用于把一个已经存在于 Topic Radar 中的 Topic 转成可执行内容简报，包括：

- 为什么现在值得做；
- 目标受众和适合平台；
- 推荐形式；
- 3 个已有内容角度及推荐角度；
- hook、前三秒、核心冲突、叙事节奏；
- 视觉素材需求；
- 后续研究问题、搜索词；
- `must_verify` 与 `avoid_claims`。

它优先复用现有 `/insight`，不重新实现一套 GPT 选题分析。

## 已有公开 API

- `GET /api/v1/ai/topic-radar/feed`
- `GET /api/v1/ai/topic-radar/sources`
- `GET /api/v1/ai/topic-radar/history?topic_id=...`
- `POST /api/v1/ai/topic-radar/insight?locale=zh|en`

默认生产地址：

```text
https://aiworkstation.cn
```

本地/测试环境可以设置：

```bash
export AIWORKSTATION_TOPIC_RADAR_BASE_URL=http://127.0.0.1:8000
```

## 本地辅助脚本

`scripts/topic_radar_client.py` 只是一个非常薄的只读 API client，只使用 Python 标准库。

它不做：

- 评分；
- 聚类；
- 数据库；
- 抓取；
- AI 推理。

示例：

```bash
python scripts/topic_radar_client.py feed --category technology --max-age-hours 24 --limit 12
python scripts/topic_radar_client.py sources
python scripts/topic_radar_client.py history TOPIC_ID
python scripts/topic_radar_client.py insight TOPIC_ID --locale zh
```

## 环境与依赖

这个项目**不要长期共用** `../akaiagents/.venv`。

建议：

- Python 3.10+
- 当前 helper 无第三方运行时依赖
- 不导入 `akaiagents` 私有模块
- 两个兄弟项目仅用于参考 contract、版本和工程规范

需要本地测试时，本仓库可以自己建立 `.venv`；没必要为了 M0 先建环境。

## 测试

```bash
python -m unittest discover -s tests -v
```

测试全部离线，不依赖实时公网。

## 核心原则

必须区分：

1. **Source facts**：Topic Radar 当前返回的事实字段；
2. **Analysis**：对信号的解释；
3. **Recommendations**：针对用户目标的建议；
4. **Unknowns**：当前数据无法证明的内容；
5. **Risks**：partial、stale、来源故障、证据不足、推断过强等风险。

`/insight` 是现有 GPT 对 Topic 的分析结果，不应当被提升为新的 verified fact。

## 当前状态

M0：Skill-first 基础版本。

暂不增加 crawler、数据库、新评分引擎、OAuth、Billing 或 Hosted MCP。

# AI Workstation Topic Intelligence

**从实时 Radar 找到值得研究的题，再把当前题材变成研究就绪的内容简报。**

[English](README.md)

当前包版本：**v0.3.0**

v0.3.0 对外只提供一个公开 Skill、一个安装包和一个官网入口。Skill 会根据自然语言自动识别三种模式：只选题、围绕用户给定题材做 Brief、先选题再基于同一个 finalist 做 Brief。

它继续使用 AI Workstation 全球热点选题 Radar 的公开读取接口。正常公开使用由用户当前的 ChatGPT、Codex 或其他宿主模型完成编辑分析，不消耗 AI Workstation 服务器端 LLM quota。

## 三种自动模式

### 只选题

```text
今天有哪些 AI 题材值得继续研究或做内容？先检查 Radar 新鲜度，再给我最值得看的 3 个，不要写完整简报。
```

Skill 做一次 bounded feed，返回候选、Radar 事实、选择理由和未知项，不主动追加 Brief。

### 用户已经给出题材，生成 Brief

```text
请基于我刚贴出的当前 Radar 卡片和精确 topic ID 写一份研究就绪的内容简报。只有在确实需要判断走势时才查这个题目的 history，不要重新选题。
```

Skill 保留用户给定的 topic identity。没有足够的当前快照时，会说明证据缺口，不会静默替换成另一个题材。

### 先选题，再生成 Brief

```text
从当前 AI 热点中挑一个适合中国科技用户研究的题材，然后直接生成研究简报。只允许一次 bounded feed，Brief 必须继续使用同一个 finalist。
```

Skill 只执行一次选题 feed，保留精确 Radar `id`，再基于同一题材完成 Brief，不进行第二次 broad/bounded 选题。

## 输出中的证据边界

每个当前性结论都必须来自本次 live Radar 响应、当前宿主的等价原生连接，或用户明确提供的当前 Radar 响应。不能用模型记忆、旧 JSON、缓存、日志、fixture、数据库或兄弟仓库快照冒充当前事实。

最终回答应区分：

1. **Radar 事实**：题目 ID、时间、新鲜度、来源、趋势字段和公开证据；
2. **宿主编辑分析**：选题理由、受众收益、角度、Hook、叙事和建议；
3. **未知与核验**：`must_verify`、风险和证据缺口；
4. **可选 Premium Insight**：只有用户明确连接了账号绑定的原生 Premium 能力时才存在，仍属于模型分析，不是独立事实来源。

当结论涉及受众、普通科技用户、中国市场适配度或传播潜力时，必须直接说明：Radar 未测量实际受众规模、内容/题材饱和度和未来传播量/virality。“适合中国用户”“受众可能更广”等是宿主模型的 editorial judgment，不是 Radar fact。

## 安装

正式安装包只从 GitHub Release 获取：

<https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/latest>

下载后安装 `topic-intelligence` ZIP。Codex 开发者也可以从源码执行：

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

默认安装到 `$HOME/.agents/skills/topic-intelligence/`。helper 必须从当前加载的 Skill 根目录调用，规范形式是：

```text
python3 <skill-local-helper> --timeout 30 feed --q AI --limit 12
python3 <skill-local-helper> --timeout 30 sources
python3 <skill-local-helper> --timeout 30 history <exact-feed-id>
```

不得使用 `python`、仓库根 `scripts/topic_radar_client.py`、`history --topic-id`、管道、重定向、命令组合或自定义 Radar origin。

## 官网入口

AI Workstation 的“全球热点选题雷达”页面右侧栏中，“本次来源覆盖”模块上方提供唯一产品入口。这个入口只负责获取 Skill，不把三种模式拆成三个按钮；用户直接用自然语言描述目标即可。

## 成本与安全边界

公开 helper 只允许调用：

```text
GET /api/v1/ai/topic-radar/feed
GET /api/v1/ai/topic-radar/sources
GET /api/v1/ai/topic-radar/history?topic_id=...
```

公开 Skill 不调用匿名 `/insight`，不内置共享 API key 或 bearer token，也不要求用户把私密凭据粘贴到聊天中。正常公开路径为：

```text
live Radar facts -> 用户当前宿主模型 -> 选题或研究 Brief
```

因此正常公开使用不会消耗 AI Workstation 服务器端 LLM quota。未来如提供 Premium Insight，必须通过账号绑定、明确认证且执行 quota 的原生连接。

## 适合的实际案例

- 内容团队早会：每天只选三个值得继续研究的 AI 题材；
- 中文创作者追踪海外早期机会：比较当前信号，但把跨市场时差标为 hypothesis；
- 编辑拿到一个 Radar topic ID 后：只查该 finalist 的 history，整理研究问题和核验清单；
- 研究人员准备视频或文章：一次选题后直接生成角度、Hook、叙事结构、素材需求和 `must_verify`；
- 不触发场景：翻译、改写、摘要、普通事实问答和用户已给完整材料的标题润色。

## 发布和运营

GitHub Release 是唯一正式下载源；每次发布同时提供 ZIP、`release-manifest.json` 和 `SHA256SUMS`。发布前必须通过完整 live Host Eval、逐 case semantic grader、人工 `must_show/must_not` 审核和 persistent evidence verifier。

运营上建议只记录匿名指标：Release 下载、安装成功、首次成功 Radar 调用、三种模式比例、helper 失败率、Radar stale/partial 比例、Brief 完成率和回访率。不要收集 topic 内容、对话正文、凭据、token 或 session。

遇到问题时先区分：helper 参数/路径错误、Radar 外部网络故障、宿主生命周期中断和语义工作流失败。未恢复断流、超时、缺少终态或非法 helper 调用都不能进入发布证据。

## 历史版本边界

- **v0.3.0**：当前已发布的单 Skill 产品线，具备独立的完整 live Host Eval evidence 和 verifier 通过记录；
- **v0.2.2 / v0.2.1**：不可变的双 Skill 历史线，其 Codex/Host Eval 不代表 ChatGPT Web UI 验证；
- **v0.2.0**：最后一次真实 ChatGPT Web ZIP 上传、发现和运行验证版本。

## 本地验证

```bash
python3 scripts/sync_skill_runtime.py --check
python3 -m unittest discover -s tests -v
python3 scripts/run_host_evals.py --suite v0.3.0 --dry-run
```

统一质量契约在 `references/topic-intelligence-quality-contract.md`，安装包中同步为 `references/quality-contract.md`。

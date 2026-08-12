# AI Workstation Topic Intelligence

**从实时 Radar 找到值得研究的题，再把一个当前题材变成研究就绪的内容简报。**

[English](README.md)

[![下载 v0.3.0](https://img.shields.io/badge/download-v0.3.0-2859dc)](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/tag/v0.3.0)
[![ChatGPT Web 验证](https://img.shields.io/badge/ChatGPT_Web-三模式_PASS-0b7a53)](docs/chatgpt-v0.3.0-smoke-result-2026-08-12.md)

当前稳定版本：**v0.3.0**。2026-08-12，最终 Release ZIP 已在真实 ChatGPT Web 中使用自然用户提示词完成三种用户可见模式 Smoke，并全部通过。

![AI Workstation 全球热点选题 Radar 与 Topic Intelligence Skill 入口](docs/assets/ai-topic-intelligence-showcase.png)

## 60 秒上手

1. 下载 [`topic-intelligence-0.3.0.zip`](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/tag/v0.3.0)。
2. ChatGPT：进入 **Plugins → Skills → Create**，上传 ZIP 并等待扫描完成；Codex 开发者可使用下方仓库安装器。
3. 直接用自然语言提需求。一个 Skill 会自动识别只选题、围绕给定当前题材做 Brief、先选题再做同一题材 Brief。
4. 首次可直接复制：

```text
从当前 AI 热点里挑一个最适合做 2–3 分钟中文解释视频的题材，然后直接把它做成研究型内容简报。给我受众收益、最强角度、前三秒、叙事结构、must_verify、avoid_claims 和素材建议。
```

ChatGPT Personal Skills 是否可用取决于当前套餐和工作区权限，详见 [ChatGPT 安装说明](docs/chatgpt-install.md)。

## 三个真实验证场景

以下是用户可见验收摘要，不是伪造的会话逐字稿或截图。

### `AI 题材研究推荐`——只选题

用户要求检查当前 Radar 与新鲜度，只返回最值得继续研究的三个 AI 题材，不生成完整 Brief。Skill 使用了当前 Radar，披露新鲜度和来源覆盖，正好返回三个题材后停止。

### `AI 产业对韩国影响`——用户给定题材直接做 Brief

在一个没有前置上下文的新会话中，用户给出当前题材“AI 产业究竟给韩国普通人带来了什么？”，要求生成适合 2–3 分钟中文解释视频的研究型简报。Skill 保留该题材，直接给出受众收益、最强角度、前三秒、叙事结构、研究问题、`must_verify`、`avoid_claims` 和素材建议。普通用户不需要先跨会话取得并复制 Radar ID。

### `本地AI智能体解析`——先选题，再直接做 Brief

用户要求从当前 AI 热点中选择一个题材，并在同一轮完成 Brief。Skill 选择一个题材后继续使用同一个 finalist，完成全部要求字段，没有停在候选列表，也没有要求用户再回复“继续”。

完整记录见 [v0.3.0 ChatGPT Web Smoke](docs/chatgpt-v0.3.0-smoke-result-2026-08-12.md)。

## 一个 Skill，三种自动模式

```text
只选题
用户给定当前题材 -> Brief
一次 bounded 选题 -> 同一 finalist 的 Brief
```

Topic Intelligence 从 [AI Workstation 全球热点选题 Radar](https://aiworkstation.cn/topic-radar/) 读取当前公开信号，由 ChatGPT、Codex 或其他兼容 Agent Skills Host 的当前宿主模型完成编辑分析。

官网产品页提供按域名自动本地化的安装与反馈说明：

- 中文：<https://aiworkstation.cn/topic-intelligence/>
- English：<https://useaistation.com/topic-intelligence/>

## 安装

### ChatGPT

使用具备 Personal Skills 上传能力的账号与工作区，上传正式 Release ZIP，不要自行重新打包。完整步骤与可用性边界见 [`docs/chatgpt-install.md`](docs/chatgpt-install.md)。

### Codex / 开发者

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

默认安装位置为 `$HOME/.agents/skills/topic-intelligence/`。

### 兼容 Agent Skills Host

Host 需要能够读取 `SKILL.md`、执行安装包内的 Python helper，并访问公开 Radar HTTP 接口。不同 Host 的入口、生命周期、权限和 Skill 发现机制可能不同。

## Brief 会包含什么

- 推荐结论与受众收益；
- 最强角度和前三秒；
- 叙事节奏与研究问题；
- `must_verify` 与 `avoid_claims`；
- 素材需求；
- 已知未知项和证据风险。

这些编辑字段由当前**宿主模型**生成，不由 AI Workstation 服务器模型生成。

## 证据与限制边界

当前性结论必须来自本次 live Radar 响应、当前宿主的等价原生连接，或用户明确提供的当前响应。不能用模型记忆、fixture、旧 JSON、日志、SQLite 或兄弟仓库快照冒充当前证据。

必须区分四层：

1. **Radar 事实**：当前 ID、时间、新鲜度、来源覆盖、分数、阶段和 history；
2. **宿主编辑分析**：选择、受众、角度、Hook、叙事和建议；
3. **未知与核验**：当前证据尚未建立的主张；
4. **可选认证 Premium Insight**：未来账号绑定的模型分析，仍不是独立事实证据。

重要限制：

- `partial` 或 `stale` Radar 响应必须披露；
- Radar 不测量实际受众规模或内容饱和度；
- Topic Intelligence 不预测未来传播量或 virality；
- 数据源可用性和 Host 的 Skill 支持会有差异；
- 用户可见 UI Smoke 不会展示每条底层命令或完整 raw trace。

本次 ChatGPT Web 人工验证确认了三种模式的用户可见行为。底层命令次数和原始运行 trace 仍由独立的 Codex Host Eval 与 release-evidence 门禁覆盖，而不是由 Web UI Smoke 直接证明。

## 公开 runtime 与成本边界

安装包内 helper 只提供：

```text
GET /api/v1/ai/topic-radar/feed
GET /api/v1/ai/topic-radar/sources
GET /api/v1/ai/topic-radar/history?topic_id=...
```

正常公开路径：

```text
live Radar facts -> 用户当前宿主模型 -> 选题 / Brief
```

因此正常使用不会产生 AI Workstation 服务器端 LLM 调用。公开 ZIP 不提供匿名 `/insight`，不内置共享 API key 或 bearer token，也不要求用户粘贴私密凭据。未来 Premium Insight 必须通过明确认证、账号绑定且执行 quota 的原生连接。

## 独立安装包

```text
topic-intelligence/
  SKILL.md
  agents/openai.yaml
  scripts/topic_radar_client.py
  references/quality-contract.md
  references/selection-workflow.md
  references/brief-workflow.md
  LICENSE
```

v0.3.0 ZIP SHA256：

```text
935bab465811a3efabd50ee46c3166c702ad719d19fd66ade718d871b69b066e
```

GitHub Release 是唯一正式下载源，同时提供 `release-manifest.json` 和 `SHA256SUMS`。

## 开发与验证

```bash
python3 scripts/sync_skill_runtime.py --check
python3 scripts/sync_plugin_candidate.py --check
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts skills
python3 scripts/run_host_evals.py --suite v0.3.0 --dry-run
```

统一质量契约位于 [`references/topic-intelligence-quality-contract.md`](references/topic-intelligence-quality-contract.md)，版本绑定的 Host Eval evidence 位于 [`release-evidence/v0.3.0/`](release-evidence/v0.3.0/)。

## 反馈与分发状态

安装失败、结果质量和功能建议可使用仓库的结构化 Issue Form。不要在公开 Issue 粘贴密钥、完整对话、客户资料或其他敏感信息。

OpenAI Developer Showcase 当前状态仅为 **submitted**，不代表 accepted 或 endorsed。Plugin 候选包已准备并通过仓库侧验证；公开 Plugin Directory 提交目前因 OpenAI Platform 付款方式和开发者身份验证前置条件暂时阻塞。这是外部分发条件，不是 Skill 缺陷，也不是 v0.3.0 发布 blocker。

## License

Apache-2.0，见 [`LICENSE`](LICENSE)。

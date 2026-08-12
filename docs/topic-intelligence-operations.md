# Topic Intelligence 使用与运营

## 产品形态

对外只维护一个官网入口、一个 `topic-intelligence` Skill、一个 GitHub Release ZIP。三种模式由用户的自然语言自动识别，不做三个产品入口。

官网入口位于 AI Workstation 全球热点选题雷达页面右侧栏“本次来源覆盖”模块上方。按钮统一指向：

<https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/latest>

## 用户使用

用户下载并安装 ZIP 后，直接提出目标即可：

```text
只选题：今天哪些 AI 题材值得继续研究？给我前三名，不要写 Brief。
```

```text
指定题材：基于我刚贴出的当前 Radar 卡片和其中的精确 topic ID 写研究就绪 Brief，不要重新 feed。
```

```text
组合任务：从当前 AI 热点挑一个题材，然后直接生成 Brief，只允许一次 bounded feed。
```

Skill 通过 `python3 <skill-local-helper> --timeout 30 feed|sources|history ...` 获取公开证据，宿主模型负责编辑判断。`history` 只在 finalist 需要趋势变化判断时使用。

## 结果如何阅读

要求回答明确分成：

- Radar facts：当前响应中的 ID、时间、新鲜度、来源和趋势字段；
- Host editorial analysis：选择理由、角度、受众收益、Hook 和叙事建议；
- Unknowns / must_verify：Radar 没有测量或原始来源仍需核验的内容；
- Recommendation：建议做、补资料后做或暂缓。

Radar 不测量实际受众规模、内容/题材饱和度和未来传播量/virality。中国用户适配、受众更广、传播潜力等表达必须标成宿主模型判断，不能写成 Radar 事实。

## 内容团队案例

### 每日选题会

每天只请求三个 finalist，审阅 freshness/source coverage，再由编辑决定是否进入研究。选题模式不自动扩写 Brief，避免把扫描结果变成未经核验的成稿。

### 海外早期机会

明确地区和领域后请求跨市场比较。Radar 只提供当前公开信号；“中国市场尚未饱和”只有存在直接证据时才能说，否则放入 unknowns。

### 研究简报交接

组合模式必须保留同一个 topic ID。Brief 不重复 feed，不通过重复调用 Radar 制造“使用过 Brief”的假象；只有趋势确实影响判断时才对 finalist 查 history。

## 发布位置

GitHub Release 是唯一正式分发渠道，包含：

- `topic-intelligence-<version>.zip`；
- `release-manifest.json`；
- `SHA256SUMS`。

官网、README 和安装文档都指向 Release 页面，不从服务器临时目录、分支构建产物或人工附件分发。

## 运营指标与隐私

建议只记录匿名产品指标：下载量、安装成功率、首次成功 helper 调用、三种模式比例、helper 失败率、Radar stale/partial 比例、Brief 完成率和回访率。

不收集 topic 内容、用户对话、凭据、token、session、原始 Radar 响应或可识别个人信息。故障分析只保留不含秘密的命令形状、状态码和生命周期摘要。

每次版本发布前重新运行完整 live Host Eval、authoritative grader、逐 case must_show/must_not 人工审核和 verifier。任何非法 helper、非零退出、无效 JSON、未完成 turn、终止性断流或 server-side anonymous LLM 调用都阻塞发布。

## 版本迁移

v0.2.0 是最后一次真实 ChatGPT Web ZIP 上传验证。v0.2.1、v0.2.2 是不可变的双 Skill 历史线，其 Host Eval 不代表 ChatGPT Web UI 验证。v0.3.0 使用单 Skill和新的完整 evidence，不能复用旧 evidence 或拼接旧 case。

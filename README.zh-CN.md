# AI Workstation Topic Intelligence

**从当前热点中找到值得研究的题，再把一个题材变成清晰、可执行的内容简报。**

[English](README.md)

[![下载 v0.3.0](https://img.shields.io/badge/download-v0.3.0-2859dc)](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/tag/v0.3.0)

![AI Workstation 全球热点选题雷达与 Topic Intelligence](docs/assets/ai-topic-intelligence-showcase.png)

Topic Intelligence 使用 [AI Workstation 全球热点选题雷达](https://aiworkstation.cn/topic-radar/) 的当前公开信号，帮助创作者、研究者和编辑：

- 筛选值得深入研究的题材；
- 把一个给定的当前题材整理成研究型简报；
- 选出一个题材，并继续为同一题材生成简报。

Radar 提供当前证据；ChatGPT、Codex 或其他兼容 Agent Skills Host 负责分析与表达。

## 开始使用

1. 下载 [`topic-intelligence-0.3.0.zip`](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/tag/v0.3.0)。
2. 在支持 Personal Skills 的 ChatGPT 工作区上传 ZIP，或使用下方 Codex 安装方式。
3. 直接说明你要选题、做简报，或两者一次完成。

首次可以这样问：

```text
从当前 AI 热点中挑一个适合做 2–3 分钟中文解释视频的题材，然后生成研究型内容简报。请包含受众收益、最强角度、开场、叙事结构、must_verify、avoid_claims 和素材建议。
```

## 安装

### ChatGPT

在支持 Personal Skills 的工作区上传正式 Release ZIP。是否可用取决于当前套餐和工作区权限，详见 [ChatGPT 安装说明](docs/chatgpt-install.md)。

### Codex

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

### 其他 Agent Skills Host

导入正式 Release ZIP 或 `topic-intelligence` 目录。Host 需要能读取 `SKILL.md`、运行安装包内的 Python helper，并访问公开 Radar API。

产品页：[中文](https://aiworkstation.cn/topic-intelligence/) · [English](https://useaistation.com/topic-intelligence/)

## 简报包含什么

- 受众收益与内容角度；
- 开场和叙事结构；
- 研究问题与来源优先级；
- `must_verify` 与 `avoid_claims`；
- 素材和画面需求。

## 证据与隐私

- 当前性结论必须来自当前 Radar 响应，不能用模型记忆或旧快照代替。
- 来源不完整或数据较旧时必须明确说明。
- Radar 不测量实际受众规模、内容饱和度或未来传播效果。
- 公开 Skill 只使用只读 Radar 接口，不需要 AI Workstation API key。
- 不要在公开 Issue 中提交密钥、完整对话、客户资料或其他敏感信息。

## 开发

```bash
python3 scripts/sync_skill_runtime.py --check
python3 scripts/sync_plugin_candidate.py --check
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts skills
```

贡献要求见 [CONTRIBUTING.md](CONTRIBUTING.md)，使用问题和建议请提交到 [GitHub Issues](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/issues)。

## License

Apache-2.0，见 [LICENSE](LICENSE)。

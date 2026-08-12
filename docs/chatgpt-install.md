# ChatGPT Skill installation

Last verified against official OpenAI documentation: **2026-08-09**.

Topic Intelligence v0.3.0 is one public Skill and one install archive:

- `topic-intelligence`
- Current package version: **v0.3.0**

The three user modes are inferred from the request. Users do not need to install or select separate Creator and Brief Skills.

## Availability

OpenAI's current Help Center says Personal Skills are generally available for ChatGPT Business, Enterprise, Healthcare, and Edu users. Workspace permissions can further control whether users may create, upload, share, publish, or install Skills.

Do not market Topic Intelligence as a one-click install for every ChatGPT plan.

Official source: <https://help.openai.com/en/articles/20001066>

## Upload path

For an eligible account/workspace:

1. Open the ChatGPT sidebar.
2. Select **Plugins**.
3. Open **Skills**.
4. Select **Create**.
5. Choose **Upload from your computer**.
6. Upload the `topic-intelligence` ZIP from the official GitHub Release.
7. Let ChatGPT finish its scan/review before using it.

Surface availability and installation state are independent. Confirm the Skill is visible in the current workspace before testing.

## First-use examples

Selection only:

```text
今天有哪些 AI 题材值得继续研究或做内容？只给我最值得看的三个，不要写完整简报。
```

Brief for a supplied topic:

```text
请基于当前 Radar 题目 topic:ai-example 写研究就绪的内容简报；只有在确实需要判断走势时才查 history，不要重新 feed 选题。
```

Selection followed by brief:

```text
从当前 AI 热点挑一个题材，然后直接生成研究简报。只允许一次 bounded feed，并保留同一个 finalist 的 Radar id。
```

翻译、改写、摘要、普通事实问答和完整材料润色不应触发 Topic Intelligence。

## Package and evidence boundary

The archive includes the Skill-local helper and references needed for standalone execution. The helper uses only public `feed`, `sources`, and `history` reads with `python3`; it does not expose anonymous `/insight`, shared credentials, or a custom Radar origin.

Normal v0.3.0 usage is validated by strict Codex Host Eval and persistent release evidence. That evidence covers lifecycle, runtime commands, Radar contracts, semantic grading, and manual review. It does **not** claim that v0.3.0 has been re-uploaded and re-tested in the ChatGPT Web UI.

The v0.2.0 package line remains the last real ChatGPT Web ZIP upload validation. v0.2.1 and v0.2.2 Host Eval records must not be presented as ChatGPT UI tests.

## Cost boundary

Normal public usage follows:

```text
public Radar feed/sources/history -> current ChatGPT host model -> answer
```

It must not call anonymous AI Workstation `/insight`, embed a shared API key, or ask the user to paste private credentials. Normal public use should not consume AI Workstation server-side LLM quota. Any future Premium Insight requires an explicitly authenticated native account connection with quota enforcement.

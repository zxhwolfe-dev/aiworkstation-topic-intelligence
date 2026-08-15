# Install Topic Intelligence in ChatGPT

Topic Intelligence is distributed as one ZIP containing one Skill. The Skill understands three requests: select topics, brief a supplied current topic, or select one topic and continue into a brief.

## Availability

Personal Skills availability depends on the current ChatGPT plan and workspace permissions. OpenAI currently documents availability for Business, Enterprise, Healthcare, and Edu workspaces; administrators may further control who can create, upload, share, publish, or install Skills.

Do not assume every ChatGPT account has the upload entry. Check the current [OpenAI Skills documentation](https://help.openai.com/en/articles/20001066) for authoritative availability.

## Install

1. Download `topic-intelligence-0.3.0.zip` from the official [GitHub Release](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/tag/v0.3.0).
2. Open **Plugins → Skills → Create** in ChatGPT.
3. Choose **Upload from your computer** and select the ZIP.
4. Wait for ChatGPT to finish its review, then confirm Topic Intelligence appears in the workspace.

Use the official ZIP without repackaging it.

## Try it

Topic selection:

```text
Find three current AI topics worth researching. Check freshness first and do not write a full brief.
```

Brief a topic:

```text
Turn this current Radar topic into a research-ready content brief without selecting a different topic.
```

Selection and brief:

```text
Choose one current AI topic, then build a research-ready brief for that same topic.
```

## Important limits

- Current claims require current Radar evidence.
- Incomplete or older source coverage should be disclosed.
- Radar does not measure actual audience size, topic saturation, or future reach.
- Topic Intelligence requires no AI Workstation API key. Never paste credentials or private conversations into prompts or public issues.

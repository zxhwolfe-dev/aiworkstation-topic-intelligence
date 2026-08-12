# ChatGPT Web v0.3.0 three-mode smoke result — 2026-08-12

## Result

- Validation date: **2026-08-12**
- Environment: **ChatGPT Web**
- Validation type: **user-visible UI smoke with natural user prompts**
- Final GitHub Release package: **`topic-intelligence-0.3.0.zip`**
- ZIP SHA256: **`935bab465811a3efabd50ee46c3166c702ad719d19fd66ade718d871b69b066e`**
- Mode 1: **PASS**
- Mode 2: **PASS**
- Mode 3: **PASS**
- Overall ChatGPT Web three-mode smoke: **PASS**

The installed package was the final published v0.3.0 Release ZIP. This record summarizes the publisher-confirmed user-visible acceptance result. It does not fabricate a verbatim transcript, screenshots, hidden logs, or raw internal traces.

## Mode 1 — selection only

Conversation name: **AI 题材研究推荐**

Natural user intent:

- inspect the current Radar;
- assess freshness;
- return the three AI topics most worth further research;
- do not produce a complete brief.

User-visible acceptance:

- Topic Intelligence triggered successfully;
- it used the current Radar;
- it disclosed freshness and source coverage;
- it returned exactly three topics;
- it did not append an unsolicited full research brief;
- Radar facts, host editorial judgment, and unknowns retained reasonable boundaries.

Result: **Mode 1 user-visible smoke PASS**.

## Mode 2 — supplied current topic to brief

Conversation name: **AI 产业对韩国影响**

This was a new conversation with no dependency on prior conversation context. The user supplied the current topic:

> AI 产业究竟给韩国普通人带来了什么？

The natural intent was to create a research-oriented brief for a two-to-three-minute Chinese explainer, without selecting a different topic; history could be checked only when trend evidence was needed.

User-visible acceptance:

- the supplied topic was preserved;
- the Skill did not reselect a different topic or return a new candidate list;
- it directly produced the research-oriented content brief;
- the result included audience payoff, strongest angle, opening three seconds, narrative structure, research questions, `must_verify`, `avoid_claims`, and material suggestions;
- evidence gaps, source boundaries, and unknowns were disclosed;
- audience size, content saturation, and future reach were not presented as measured Radar facts;
- the task was completed normally even though the user did not proactively provide an exact Radar ID.

An ordinary Mode 2 user does **not** need to obtain a Radar ID in another conversation and copy it into a new one. The Radar ID remains a traceability and evidence field, not a mandatory cross-conversation interaction step. The fact that an ID is not explicitly displayed in the UI is not, by itself, a user-visible functional failure.

Result: **Mode 2 user-visible smoke PASS**.

## Mode 3 — selection followed by a brief

Conversation name: **本地AI智能体解析**

Natural user intent:

- select one topic from current AI hotspots that suits a two-to-three-minute Chinese explainer;
- continue immediately into a research-oriented brief;
- include audience payoff, strongest angle, opening three seconds, narrative structure, `must_verify`, `avoid_claims`, and material suggestions.

User-visible acceptance:

- the Skill selected one topic from current AI hotspots;
- it did not stop at a candidate list;
- it completed the brief in the same response;
- the selected topic and final brief remained consistent;
- it did not ask the user to reply “continue”;
- all requested brief fields were present;
- it did not select a different topic while writing the brief.

Result: **Mode 3 user-visible smoke PASS**.

## Evidence boundary

All three user-facing modes passed a real ChatGPT Web smoke test using natural user prompts.

The manual ChatGPT Web validation confirms user-visible behavior for all three modes. Internal command counts and raw runtime traces remain covered by the separate Codex Host Eval and release-evidence gates rather than by the Web UI smoke.

This UI smoke does not claim that:

- ChatGPT Web displayed a complete raw tool-call trace;
- the publisher directly observed exact underlying feed call counts;
- every internal helper command was visible in the UI;
- the Web smoke replaces Codex Host Eval, semantic grading, manual review, or persistent release evidence;
- every Radar internal field appeared in the UI;
- every possible input combination was exhaustively tested.

## Public references

- [GitHub Release v0.3.0](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/tag/v0.3.0)
- [English README](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence#readme)
- [中文 README](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/blob/main/README.zh-CN.md)
- [ChatGPT installation guide](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/blob/main/docs/chatgpt-install.md)
- [Codex Host Eval evidence](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/blob/main/release-evidence/v0.3.0/host-evidence.json)

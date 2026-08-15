# OpenAI Developer Showcase submission archive — 2026-08-12

> Historical submission record. The setup steps below describe the surface used
> on 2026-08-12; for current installation and availability, use
> [`docs/install.md`](../install.md).

## Public submission summary

- Status: **submitted**
- Submission date: **2026-08-12**
- Project title: **AI Workstation Topic Intelligence**
- Tagline: **Find the current topics worth researching — then turn one into a research-ready content brief.**
- Author display name: **AI Workstation**
- GitHub repository: <https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence>
- Hosted URL: <https://aiworkstation.cn/topic-radar/>
- Cover image repository path: `docs/assets/ai-topic-intelligence-showcase.png`
- Cover image public URL: <https://raw.githubusercontent.com/zxhwolfe-dev/aiworkstation-topic-intelligence/main/docs/assets/ai-topic-intelligence-showcase.png>

## Project description

AI Workstation Topic Intelligence is one public Agent Skill for creators, researchers, and editors. It reads current public signals from AI Workstation Global Topic Radar, then uses the user’s current ChatGPT, Codex, or compatible host model to shortlist research opportunities or produce an evidence-aware content brief. Radar observations, host editorial judgment, and unknowns remain separate, and normal public use makes no AI Workstation server-side LLM call.

## Tech stack

- OpenAI Agent Skills format with `SKILL.md` and host metadata;
- Python 3.10+ standard-library Radar helper;
- public read-only Radar `feed`, `sources`, and `history` HTTP APIs;
- ChatGPT, Codex, or another compatible Agent Skills host model for editorial reasoning;
- deterministic release builder, GitHub Actions, Codex Host Eval, semantic grading, manual review, and persistent release evidence.

## Use cases

1. Select the strongest three current topics worth researching, without producing an unsolicited brief.
2. Turn a user-supplied current topic directly into a research-ready brief without changing the topic.
3. Select one current topic and continue in the same response with a brief for that same finalist.

## How Codex is used

Codex is a supported Agent Skills host and the release-validation environment. The project uses isolated, neutral Host workspaces to validate Skill triggering, bundled helper execution, live Radar contracts, topic-identity preservation, evidence boundaries, and complete host-model briefs. Persistent evidence is bound to the v0.3.0 release commit and kept separate from the manual ChatGPT Web UI smoke.

## Setup steps

1. Download `topic-intelligence-0.3.0.zip` from the official GitHub Release.
2. On that date, upload it through the eligible ChatGPT workspace Skill surface, or install it into a compatible Agent Skills host.
3. Ask naturally for a shortlist, a brief for a supplied current topic, or selection followed by a brief.
4. Keep `partial`/`stale` status and unknown claims visible in the result.

## Validation and distribution status

The final v0.3.0 Release ZIP completed a real ChatGPT Web smoke on 2026-08-12. Mode 1, Mode 2, Mode 3, and Overall all passed at the user-visible level. Internal command counts and raw traces remain covered by separate Codex Host Eval and release-evidence gates.

## Status boundary

**Submitted does not mean accepted, featured, endorsed, certified, or approved by OpenAI.** This archive does not claim Showcase inclusion, an official OpenAI recommendation, certification, approval, partnership, or any other endorsement.

This public archive intentionally omits real names, private email addresses, identity documents, payment information, agreement-checkbox data, and all other non-public personal information.

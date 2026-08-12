# AI Topic Intelligence

> Status: candidate prepared and validation-ready. Public Plugin Directory submission is temporarily blocked by the OpenAI Platform payment-method and developer-identity verification prerequisite. This external prerequisite is not a Skill defect or a v0.3.0 release blocker, and no v0.3.1 is required.

## Short description

Find live topic opportunities and build research-ready content briefs.

## Long description

AI Topic Intelligence is a skills-only workflow for creators, researchers, and editors. It reads current public signals from the AI Workstation Global Topic Radar, keeps Radar facts separate from host-model editorial judgment, and automatically chooses the smallest useful workflow:

- shortlist current topics worth researching;
- turn a supplied current Radar topic into a research-ready brief;
- select one topic and continue into a brief for the same finalist.

The public Skill requires no AI Workstation API key and does not consume AI Workstation server-side LLM quota. It exposes only public read-only Radar `feed`, `sources`, and `history` operations. Actual audience size, topic saturation, and future virality remain unknown unless separate evidence establishes them.

## Listing fields

- Name: `AI Topic Intelligence`
- Developer: `AI Workstation`
- Category: `Productivity`
- Website: `https://aiworkstation.cn/topic-intelligence/`
- Support: `https://aiworkstation.cn/support/`
- Privacy: `https://aiworkstation.cn/privacy/`
- Terms: `https://aiworkstation.cn/terms/`
- Repository: `https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence`
- License: `Apache-2.0`

## Starter prompts

1. `Find three current AI topics worth researching. Do not write a full brief.`
2. `Turn this current Radar topic into a research-ready content brief.`
3. `Select one current AI topic, then build a brief for the same finalist.`

This listing is retained for future submission after the external prerequisite is satisfied. It does not claim current public Plugin Directory availability or approval.

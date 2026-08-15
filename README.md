# AI Workstation Topic Intelligence

**Find current topics worth researching, then turn one into a clear, actionable content brief.**

[简体中文](README.zh-CN.md)

[![Latest Release](https://img.shields.io/github/v/release/zxhwolfe-dev/aiworkstation-topic-intelligence)](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/latest)

![AI Workstation Global Topic Radar with Topic Intelligence](docs/assets/ai-topic-intelligence-showcase.png)

Topic Intelligence is an installable Agent Skill. It uses current public signals from the [AI Workstation Global Topic Radar](https://aiworkstation.cn/topic-radar/) to help creators, researchers, and editors:

- shortlist topics worth deeper research;
- turn a supplied current topic into a research-ready brief;
- select one topic and continue directly into a brief for that same topic.

The Radar supplies current signal metadata and source links. Your Codex or
compatible Agent Skills host performs the analysis; material external claims
still require primary-source verification.

## Get started

1. Open the [latest GitHub Release](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/latest) for the standalone Skill archive, or clone this repository for the Codex installer.
2. Install the Skill using the host-specific workflow below.
3. Describe whether you want topic selection, a brief, or both.

Try:

```text
Choose one current AI topic for a two-to-three-minute explainer, then turn it into a research-ready content brief. Include the audience payoff, strongest angle, opening, narrative structure, must_verify, avoid_claims, and suggested visuals.
```

## Installation

### Codex

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

### Other Agent Skills hosts

Import the Release ZIP or `topic-intelligence` directory. The host must be able to read `SKILL.md`, run the bundled Python helper, and access the public Radar API.

See the [installation guide](docs/install.md) for detailed steps and
first-use prompts.

Product pages: [English](https://useaistation.com/topic-intelligence/) · [中文](https://aiworkstation.cn/topic-intelligence/)

## What the brief includes

- audience payoff and editorial angle;
- opening and narrative structure;
- research questions and source priorities;
- `must_verify` and `avoid_claims`;
- visual and material requirements.

## Evidence and privacy

- Current claims must come from a current Radar response, not model memory or saved snapshots.
- Radar observations and evidence links are research leads, not independent verification of external claims.
- Incomplete or older source coverage must be disclosed.
- Radar does not measure actual audience size, content saturation, or future reach.
- The public Skill uses read-only Radar endpoints and requires no AI Workstation API key.
- Do not include credentials, private conversations, or client data in public issues.

## Development

```bash
python3 scripts/sync_skill_runtime.py --check
python3 scripts/sync_plugin_candidate.py --check
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts skills
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution requirements and [GitHub Issues](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/issues) for support and feedback.

## License

Apache-2.0. See [LICENSE](LICENSE).

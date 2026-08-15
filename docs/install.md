# Install Topic Intelligence

Topic Intelligence is distributed as one standalone Agent Skill. Open the
[latest GitHub Release](https://github.com/zxhwolfe-dev/aiworkstation-topic-intelligence/releases/latest)
for the current archive, or clone the repository.

## Codex

Choose one installation path.

From the latest Release, extract the archive so the included
`topic-intelligence/` directory is located at
`~/.agents/skills/topic-intelligence/`. Start a new Codex session and confirm
that `topic-intelligence` appears in the available Skills list.

For a repository checkout, run from the repository root:

```bash
python3 scripts/install_codex_skills.py install
python3 scripts/install_codex_skills.py doctor
```

`doctor.ok=true` confirms that the Skill, metadata, helper, and workflow
references are available to Codex. The `doctor` command applies to the repository
installer path; Release installs can verify the helper with:

```bash
python3 ~/.agents/skills/topic-intelligence/scripts/topic_radar_client.py --help
```

## Compatible Agent Skills hosts

Import the Release ZIP or the `topic-intelligence` directory using the host's
documented Agent Skills workflow. The host must be able to read `SKILL.md`, run
the bundled Python helper, and access `https://aiworkstation.cn`.

## First requests

```text
Find three current AI topics worth researching. Check freshness first and do not write a full brief.
```

```text
Turn this current Radar card into a research-ready brief. Keep its exact ID and list what still needs verification.
```

```text
Select one current AI topic, then build a brief for that same topic without selecting again.
```

The Skill does not need an AI Workstation API key. Never paste credentials or
private conversations into installation feedback.

# AI Topic Intelligence Plugin Candidate

This directory is a validation-ready, skills-only Plugin candidate for a future directory submission. It contains no MCP server, App, authentication layer, or server-side model tool.

The bundled `topic-intelligence` Skill remains the source of runtime behavior. Update the canonical Skill first, then run:

```bash
python3 scripts/sync_plugin_candidate.py
python3 scripts/sync_plugin_candidate.py --check
python3 /home/zxhwolfe/.codex/auth-yinhe/skills/.system/plugin-creator/scripts/validate_plugin.py plugin-candidate/ai-topic-intelligence
```

Public submission is intentionally separate from repository validation. Developer/business identity verification, organization permissions, regional availability, listing fields, and review submission must be confirmed in the current OpenAI Platform UI by the publisher.

# Security Policy

## Supported version

Security fixes are applied to the current package line, presently v0.3.x. Historical v0.2.x packages are immutable release records.

## Report a vulnerability

Do not open a public issue for a vulnerability that could expose credentials, private data, or service access. Email `zxhwolfe@gmail.com` with:

- the affected version and component;
- clear reproduction steps;
- the expected and observed security impact;
- any suggested mitigation;
- whether the report can be acknowledged publicly.

Do not include API keys, tokens, private conversations, or unnecessary personal data. Allow a reasonable remediation window before public disclosure.

## Security boundary

The public Skill contains no AI Workstation API key or shared bearer token. Its bundled helper permits only public read-only Radar `feed`, `sources`, and `history` requests. Reports about the host product, GitHub, ChatGPT, Codex, or unrelated third-party sources should be sent to the responsible provider.

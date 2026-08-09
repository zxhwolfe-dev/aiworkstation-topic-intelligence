# v0.2.0 Expected Release Artifacts

The standalone Skill payload is unchanged by release metadata finalization, so the expected deterministic artifact hashes remain those validated during M3.1 acceptance.

Creator Skill:

```text
aiworkstation-topic-intelligence-0.2.0-creator-topic-opportunity-research.zip
SHA256 7d7ca0266abd55df374e4ca37ff5affadf9eabffe694474d18be96c5402dc897
```

Brief Skill:

```text
aiworkstation-topic-intelligence-0.2.0-evidence-backed-content-brief.zip
SHA256 9c90adccd61966321201c8c05b0fad963e18ea412bd3112c694a4fe0cea9dab8
```

The GitHub release workflow must also publish:

```text
release-manifest.json
SHA256SUMS
```

Post-release verification must compare the published assets to these expected hashes. A mismatch is a release blocker and must not be repaired by moving the public tag.
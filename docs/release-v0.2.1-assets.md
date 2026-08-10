# v0.2.1 Expected Release Artifacts

The release-prep changes are documentation/test-only, so the deterministic Skill payload hashes remain those validated from the v0.2.1 release candidate.

Creator Skill:

```text
aiworkstation-topic-intelligence-0.2.1-creator-topic-opportunity-research.zip
bytes 44621
SHA256 3381d798c29cc8f67b1bca3f1f6da8a34a34ab78e64b6af7bd48aff95b663bb6
```

Brief Skill:

```text
aiworkstation-topic-intelligence-0.2.1-evidence-backed-content-brief.zip
bytes 45043
SHA256 81d6aac45b42c27b8f24c27ac18b6a268509fb9a8a88a0813b96feab8f034d5e
```

The GitHub release workflow must also publish:

```text
release-manifest.json
SHA256SUMS
```

Post-release verification must compare all four published assets with the workflow build and the expected hashes above. A mismatch is a release failure and must not be repaired by moving the public tag.

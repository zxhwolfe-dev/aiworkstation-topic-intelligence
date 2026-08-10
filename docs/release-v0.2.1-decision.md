# v0.2.1 Release Decision

Date: 2026-08-10

Decision:

```text
RELEASE_ELIGIBLE
```

The v0.2.1 quality, public-cost-boundary, runtime, live-data, package, and non-UI fresh-host gates passed. See `docs/v0.2.1-non-ui-host-acceptance-2026-08-10.md`.

## Approved acceptance substitution

The release owner explicitly directed that final acceptance must not depend on a ChatGPT login and should use other testing methods to complete the release. The substituted gate uses three isolated fresh-agent runs over the installed v0.2.1 RC, not assumptions about ChatGPT behavior.

This decision preserves the product-surface boundary:

- it accepts the portable Skill/runtime release;
- it does not claim that the v0.2.1 ZIP upload UI was tested;
- it preserves the separate v0.2.0 manual ChatGPT web evidence;
- a future ChatGPT-specific regression may still be tested independently without moving or rewriting this release tag.

## Release constraints

- Tag only the validated release-prep commit after CI is green.
- The tag must be exactly `v0.2.1` and match `VERSION=0.2.1`.
- Never move, delete, or reuse `v0.1.0`, `v0.2.0`, or `v0.2.1` after publication.
- Do not tag a feature branch.
- The GitHub release workflow must rebuild, test, and publish both Skill ZIPs, `release-manifest.json`, and `SHA256SUMS`.
- Post-release verification must compare the published asset metadata and hashes with `docs/release-v0.2.1-assets.md`.

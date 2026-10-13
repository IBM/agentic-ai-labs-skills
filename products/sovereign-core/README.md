<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# IBM Sovereign Core

Skills for IBM Sovereign Core, IBM's customer-operated sovereign cloud
platform built on Red Hat OpenShift and Red Hat AI.

| Skill | What it covers |
|---|---|
| [`sovereign-core-ops`](skills/sovereign-core-ops/SKILL.md) | Planning, pre-flight checks, installation (Red Hat Enclave-based bare metal or customer-provided OpenShift), post-install steps, the two-step upgrade, backup, observability, and troubleshooting with must-gather. |

The skill is written against the public
[IBM Sovereign Core documentation](https://www.ibm.com/docs/en/sovereign-core/1.2.0)
for version 1.2.x. It tells the agent to confirm your version and use the
matching documentation, because commands and image tags change between
releases.

## Requirements

- Shell access to the Sovereign Core landing zone (RHEL 10.1), as a non-root
  user with sudo.
- IBM entitlement key and Red Hat entitlements (see the prerequisites
  reference).
- After installation: the `oc` CLI and the `sov-core-platform` CLI.

The skill asks for confirmation before every command that changes your
environment.

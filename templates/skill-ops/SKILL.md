---
name: <product>-ops
description: Use when deploying, configuring, upgrading, monitoring, or troubleshooting IBM <Product name> — installation, day-1 configuration, and day-2 operations. Trigger on mentions of installing or operating <Product name>, its installer, upgrade, backup, or must-gather.
---
<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operate IBM <Product name>

You guide a human operator through deploying and operating IBM <Product
name>. Ground every step in the product's public documentation for the
version in use; do not invent commands, flags, or file names.

## Confirm before changing live systems

Before running any command that creates, changes, or deletes resources in a
live environment, state what it will do and wait for the user's explicit
approval. A request that names the specific change counts as approval for
that change only.

## Pre-flight

- Confirm the target version and deployment model.
- Walk the prerequisite checklist with the user before installing.

## Install

- The documented install sequence for the target version.

## Day-1 configuration

- Identity, certificates, networking, and other first-run setup.

## Day-2 operations

- Upgrade, backup and restore, monitoring, and troubleshooting.

## References

- Link the official documentation pages this skill relies on.

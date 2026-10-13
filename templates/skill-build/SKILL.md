---
name: <product>-build
description: Use when building applications against IBM <Product name> — connecting, authenticating, using its client libraries or APIs, and following its patterns. Trigger on mentions of <Product name>, its CLI, SDKs, or configuration files.
---
<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Build with IBM <Product name>

You help developers build applications against IBM <Product name>. Ground
every command, API call, and configuration key in the product's public
documentation; do not invent flags or fields.

## Before you start

- Confirm which version of <Product name> the user targets and where it runs.
- Check which tools are available (CLI, SDK, MCP server) and how the user
  authenticates. Reference secrets by environment-variable name; never ask
  the user to paste credentials into the conversation or into files.

## Workflow

1. Understand what the application needs from <Product name>.
2. Set up connection and authentication.
3. Implement using the recommended client library or API.
4. Test against a non-production instance.

## Pitfalls

- List the mistakes developers commonly make with <Product name>.

## References

- Link the official documentation pages this skill relies on.

<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus, Claude Sonnet) -->

# wxo-agent-architect

A Claude Code skill for building, editing, testing, and publishing IBM watsonx Orchestrate (WXO) agents, tools, toolkits, knowledge bases, models, and connections.

## What it does

Activates automatically when you mention watsonx Orchestrate, the orchestrate ADK, `agent.yaml`, `toolkit-config.yaml`, or the `orchestrate` CLI. Guides you through:

- Searching current ADK docs before writing anything
- Discovering existing tools/agents to reuse or compose
- Choosing the right WXO primitive for your task
- Testing locally or against IBM Cloud
- Deploying and promoting through the `orchestrate` CLI (the default path)

See [`WORKFLOW.md`](./WORKFLOW.md) for the end-to-end deployment flow (plan →
build → deploy → test → iterate → promote) and how it fits with a platform
team's architecture-review gate.

## Install

In Claude Code, add the marketplace and install the plugin (the
`@agentic-ai-labs` suffix is the marketplace name from the manifest, not the
repository name):

```
/plugin marketplace add IBM/agentic-ai-labs-skills
/plugin install wxo-agent-architect@agentic-ai-labs
```

Run `/reload-plugins` to load the skill into the running session (restart Claude
Code if it still doesn't appear). Verify with `/plugin list`. Once loaded, the
skill activates automatically when you mention watsonx Orchestrate, and can also
be invoked directly as `/wxo-agent-architect:wxo-agent-architect`.

To pick up newer content later:

```
/plugin marketplace update agentic-ai-labs
/plugin update wxo-agent-architect
```

## Requirements

- **`watsonx-orchestrate-adk-docs` MCP server** (required, credential-free HTTP
  docs server):
  `claude mcp add --transport http watsonx-orchestrate-adk-docs https://developer.watson-orchestrate.ibm.com/mcp`
- **The `orchestrate` ADK/CLI** — the skill walks you through installing it
  (`uv pip install ibm-watsonx-orchestrate`) into a project-local virtualenv, so
  have `uv` installed (`brew install uv`).
- **WXO credentials in your shell** — `WO_API_KEY` + `WO_INSTANCE` for IBM Cloud,
  or the `WO_DEVELOPER_EDITION_*` set for a local Developer Edition. Keep them in
  an untracked `.env`; never commit them.
- *Optional:* the credentialed `watsonx-orchestrate-adk` MCP server, only for
  headless or no-shell automation. See
  [`reference/cli_vs_mcp.md`](./skills/wxo-agent-architect/reference/cli_vs_mcp.md).

<!-- Copyright contributors to the Agent Skills project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# wxo-agent-architect

A Claude Code skill for building, editing, testing, and publishing IBM watsonx Orchestrate (WXO) agents, tools, toolkits, knowledge bases, models, and connections.

## What it does

Activates automatically when you mention watsonx Orchestrate, the orchestrate ADK, `agent.yaml`, `toolkit-config.yaml`, or the `orchestrate` CLI. Guides you through:

- Searching current ADK docs before writing anything
- Discovering existing tools/agents to reuse or compose
- Choosing the right WXO primitive for your task
- Testing locally or against IBM Cloud
- Deploying via the `watsonx-orchestrate-adk` MCP server

See [`WORKFLOW.md`](./WORKFLOW.md) for the end-to-end deployment flow (plan →
build → deploy → test → iterate → promote) and how it fits with a platform
team's architecture-review gate.

## Install

> **Offline install (current).** This plugin ships as a zip archive and is
> installed from a local path. A hosted marketplace install will replace these
> steps once the plugin is published to a public repository.

1. Unzip the archive. It expands to a `wxo-agent-architect/` folder containing
   the marketplace (e.g. `~/Downloads/wxo-agent-architect`).
2. In Claude Code, add that folder as a local marketplace, then install the
   plugin (the `@agentic-ai-labs` suffix is the marketplace name, not a remote
   location). Use the path where you unzipped it:

   ```
   /plugin marketplace add ~/Downloads/wxo-agent-architect
   /plugin install wxo-agent-architect@agentic-ai-labs
   ```
3. Run `/reload-plugins` to load the skill into the running session (this also
   loads the skill — no separate reload needed). If it still doesn't appear,
   restart Claude Code.

Verify with `/plugin list`. Once loaded, the skill activates automatically
when you mention watsonx Orchestrate (see *What it does* above) — there is no
separate enable step.

To pick up a newer archive later, re-run the unzip, then:

```
/plugin marketplace update agentic-ai-labs
/plugin update wxo-agent-architect
```

## Requirements

- `uv` installed: `brew install uv`
- `.mcp.json` in the project root with `watsonx-orchestrate-adk` and `watsonx-orchestrate-adk-docs` servers configured
- WXO credentials in your shell (`WO_API_KEY` + `WO_INSTANCE` for IBM Cloud, or the `WO_DEVELOPER_EDITION_*` set for local)

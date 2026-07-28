# Agentic AI Labs — Claude Code plugins & skills

Shared [Claude Code](https://claude.com/claude-code) plugins and skills from the
IBM **Agentic AI Labs** team. This repository is a **plugin marketplace**: add it
once, then install any skill it publishes.

## Scope

A curated set of Claude Code skills for building on IBM's agentic platforms. The
marketplace manifest lives at [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json);
each skill is a plugin under [`plugins/`](plugins/).

## Available skills

| Skill | Description |
|-------|-------------|
| [`wxo-agent-architect`](plugins/wxo-agent-architect) | Build, edit, test, and publish IBM watsonx Orchestrate (WXO) agents, tools, toolkits, knowledge bases, models, and connections using the orchestrate ADK and CLI. |

## Install

In Claude Code:

```
/plugin marketplace add IBM/agentic-ai-labs-skills
/plugin install wxo-agent-architect@agentic-ai-labs
```

- `/plugin marketplace add` takes the **repository** (`IBM/agentic-ai-labs-skills`).
- `/plugin install` takes `<plugin>@<marketplace>` — the marketplace name is
  `agentic-ai-labs` (from the manifest), independent of the repo name.

Once installed, the skill activates automatically when you work with watsonx
Orchestrate, or you can invoke it directly.

## Requirements

- **Claude Code** with plugin support.
- For `wxo-agent-architect`: the `orchestrate` ADK/CLI and, for documentation
  lookups, the credential-free `watsonx-orchestrate-adk-docs` MCP server. See the
  skill's own `SKILL.md` and `reference/` for setup, credential handling, and the
  CLI-first workflow.

## Contributing

Contributions are welcome. Please review [CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). This repository enforces the
[Developer Certificate of Origin (DCO)](https://developercertificate.org/) — sign
your commits with `git commit -s`.

Source files carry an SPDX header:

```text
# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
```

## Security

To report a vulnerability, follow [SECURITY.md](SECURITY.md). Do not open a public
issue for security reports.

## Maintainers

See [MAINTAINERS.md](MAINTAINERS.md).

## License

Apache-2.0 — see [LICENSE](LICENSE).

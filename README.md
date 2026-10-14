<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Agentic AI Labs: agent skills for IBM products

Agent skills that teach coding agents to build on, deploy, and operate IBM
software. They come from the IBM **Agentic AI Labs** team and from upstream
projects across IBM, credited to their authors.

One repository serves every major coding agent. Each skill is a portable
[Agent Skills](https://agentskills.io) folder, and each product folder is a
plugin package. Supported agents:

- Claude Code
- OpenAI Codex
- GitHub Copilot
- Cursor
- IBM Bob
- Kiro, Cline, and others

## What's inside

| Product | Plugin | What the skills help with |
|---------|--------|---------------------------|
| [IBM Sovereign Core](products/sovereign-core) | [`sovereign-core`](products/sovereign-core) | Plan, install, upgrade, back up, and troubleshoot Sovereign Core on bare metal or customer-provided OpenShift, with confirmation before every change. |
| [IBM watsonx Orchestrate](products/watsonx-orchestrate) | [`wxo-agent-architect`](products/watsonx-orchestrate) | Build, test, deploy, and promote WXO agents, tools, toolkits, knowledge bases, models, and connections using the orchestrate ADK and CLI. |

**[CATALOG.md](CATALOG.md)** lists every skill. For each one it shows:

- whether the skill is maintained here or imported from upstream;
- which agents it has been verified in;
- where it came from.

Skills that we list but can't redistribute are linked there too.

## Install

Pick your agent. In every command, replace `<plugin>` with a plugin name
from the table above (for example `wxo-agent-architect`), and `<skill>` with
a skill name from [CATALOG.md](CATALOG.md).

### Claude Code

```text
/plugin marketplace add IBM/agentic-ai-labs-skills
/plugin install <plugin>@agentic-ai-labs
```

`/plugin marketplace add` takes the repository. `/plugin install` takes
`<plugin>@<marketplace>`, and the marketplace is called `agentic-ai-labs`.

### GitHub Copilot CLI

```text
copilot plugin marketplace add IBM/agentic-ai-labs-skills
copilot plugin install <plugin>@agentic-ai-labs
```

### OpenAI Codex

```text
codex plugin marketplace add IBM/agentic-ai-labs-skills
```

Then open `/plugins` in Codex and install the product you want.

### IBM Bob, Cursor, Kiro, Cline, and other agents

These agents read skill folders from disk. You can put the skills there in
two ways.

**Option A: the GitHub CLI.** `gh skill` is in preview. It knows each agent's
skills folder:

```text
gh skill install IBM/agentic-ai-labs-skills <skill> --agent bob
gh skill install IBM/agentic-ai-labs-skills --all --agent cursor
```

Run `gh skill install --help` for the full agent list. It includes `bob`,
`cursor`, `kiro-cli`, `cline`, `windsurf`, `opencode`, and `goose`.

**Option B: the installer in this repository.** It needs only standard
Python 3.9+, run from a clone:

```text
git clone https://github.com/IBM/agentic-ai-labs-skills.git
python3 agentic-ai-labs-skills/scripts/install_skills.py --list
python3 agentic-ai-labs-skills/scripts/install_skills.py --agent bob --product watsonx-orchestrate
```

Choose your agent with `--agent`:

| Value | Installs into |
|---|---|
| `bob` | `.bob/skills` |
| `kiro` | `.kiro/skills` |
| `cline` | `.cline/skills` |
| `claude` | `.claude/skills` |
| `agents` | `.agents/skills`, the shared folder read by Codex, Copilot, Cursor, opencode, Goose, Amp and others |

Other options:

- `--scope user` installs into your home directory instead of the current project.
- `--all` installs every product.
- `--dest DIR` installs into any other skills folder.

Re-running the installer upgrades skills you haven't edited. Skills you
changed locally are left alone unless you pass `--force`, which keeps a
backup first.

**Manual copy.** You can also copy folders by hand: copy
`products/<product>/skills/<skill>/` into your agent's skills folder.

## Requirements

- An agent that supports [Agent Skills](https://agentskills.io).
- Each product's tools, as described in its skill. For example,
  `wxo-agent-architect` needs the `orchestrate` ADK/CLI and the credential-free
  `watsonx-orchestrate-adk-docs` MCP server.

## Safety

Skills are instructions your agent follows with your permissions. This
catalog guards that in three ways:

- **Confirmation before live changes.** Any skill that can change a live
  system must tell the agent to stop and ask before creating, changing or
  deleting resources.
- **Reviewed imports.** Every imported skill is security-reviewed and pinned
  to an upstream commit.
- **Detected edits.** Any edit to an imported skill is caught by a content
  hash.

The catalog's provenance is in each skill's `catalog-entry.json`. Still,
review what a skill does before you use it against production systems.

## Contributing

Contributions are welcome, especially from IBM product teams who want to
publish or consolidate their skills here. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md).

- **Sign-off:** commits need a DCO sign-off (`git commit -s`).
- **Importing a skill from another project:** follow
  [docs/importing-skills.md](docs/importing-skills.md).
- **Known upstream sources:** listed in [UPSTREAMS.md](UPSTREAMS.md).

## Security

To report a vulnerability, follow [SECURITY.md](SECURITY.md). Do not open a public
issue for security reports.

## Maintainers

See [MAINTAINERS.md](MAINTAINERS.md).

## License

Apache-2.0, see [LICENSE](LICENSE). Imported skills keep their upstream
licenses, listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

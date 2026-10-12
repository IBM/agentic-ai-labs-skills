<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus, Claude Sonnet) -->

# Contributing to Agentic AI Labs Skills

Thanks for your interest in contributing! This repository is a Claude Code
**plugin marketplace** made of plain Markdown and JSON: no executable code, no
dependencies, no build step. Contributions are skills, slash commands, and the
documentation around them.

## Table of contents

- [How to contribute](#how-to-contribute)
- [Legal: license and DCO](#legal-license-and-dco)
- [File requirements](#file-requirements)
- [Adding or changing a plugin](#adding-or-changing-a-plugin)
- [Testing your change](#testing-your-change)
- [Security and secret scanning](#security-and-secret-scanning)
- [Pull request checklist](#pull-request-checklist)

## How to contribute

- **Bugs and small fixes:** [open an issue](../../issues) first so it can be
  tracked, then send a pull request.
- **New skills or larger changes:** open an issue to discuss the idea before
  writing it, so nobody spends time on something that doesn't fit the
  collection.
- **Merge approval:** a maintainer approves each pull request. See
  [MAINTAINERS.md](MAINTAINERS.md).
- Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Legal: license and DCO

Contributions are accepted under the [Apache License 2.0](LICENSE). You keep
your copyright and license it to the project. No CLA is required.

Instead, every commit must carry a **Developer Certificate of Origin (DCO)**
sign-off, certifying that you have the right to submit it
([full text](https://developercertificate.org/)). Add it with `-s`:

```
git commit -s -m "Add airgapped pre-flight reference"
```

This appends `Signed-off-by: Your Name <you@example.com>` using your configured
`user.name` and `user.email`. Forgot it?

```
git commit --amend -s --no-edit      # last commit
git rebase --signoff main            # a whole branch
```

The DCO bot blocks pull requests with unsigned commits.

## File requirements

Every Markdown and code file carries the project notice and an SPDX identifier,
with **no year** and no personal or company name:

```
Copyright contributors to the Agentic AI Labs project
SPDX-License-Identifier: Apache-2.0
```

- **Markdown:** use HTML comments at the top so they don't render.
- **Markdown with YAML front matter** (`SKILL.md`, slash commands): the front
  matter must stay the first thing in the file, so put the comments immediately
  after the closing `---`.
- **JSON:** no header (JSON has no comments). The repository `LICENSE` covers it.
- **Don't commit** build outputs, zips, or other generated artifacts.

```markdown
---
name: my-skill
description: When to use this skill, in one or two sentences.
---
<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
```

### AI-assistance notice

If an AI tool helped draft a file, add a third line, per IBM's policy on
AI-generated contributions:

```markdown
<!-- This file was authored with the assistance of AI Tool: <tool name and version> -->
```

AI-assisted work is welcome under human direction: you must review, understand,
and test it, and it must meet the same bar as hand-written content.

## Adding or changing a plugin

Each plugin lives under `plugins/<plugin-name>/`:

```
plugins/<plugin-name>/
├── .claude-plugin/plugin.json          # name, version, description, author, license
├── README.md                           # what it does, requirements
├── commands/<command>.md               # optional slash commands (front matter required)
└── skills/<skill-name>/
    ├── SKILL.md                        # front matter with `name` and `description`
    └── reference/                      # optional deep-dive docs the skill points to
```

1. Add the [file headers](#file-requirements) to every new file.
2. Register a new plugin in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)
   and add a row to the skills table in the [README](README.md).
3. **Bump `version` in `plugin.json` when you change a plugin's content.** Claude
   Code caches installed plugins and may skip an update when the version number
   hasn't changed, so users would silently keep the old content.
4. Keep `SKILL.md` focused: put long reference material in `reference/` and link
   to it, so the skill stays cheap to load.
5. Write the `description` field for *triggering*: it is how the agent decides
   when to load the skill, so name the situations and keywords that should
   activate it.

## Testing your change

There is no unit-test suite. A skill is only as good as the agent behavior it
produces, so test it by using it:

1. **Install from your clone** instead of the public repo:
   ```
   /plugin marketplace add /path/to/your/clone
   /plugin install <plugin-name>@agentic-ai-labs
   ```
2. After editing, refresh the cached copy (and bump `version`, see above):
   ```
   /plugin marketplace update agentic-ai-labs
   /plugin update <plugin-name>
   ```
3. Run a realistic task that should trigger the skill and confirm the agent
   follows the guidance. Also check that it does *not* trigger on unrelated
   requests.
4. CI (`validate`) checks that `marketplace.json` sources exist and that skills
   and commands have the required front matter. Passing it is necessary, not
   sufficient.

Only one marketplace named `agentic-ai-labs` can be registered at a time. If you
previously added the public repo, run `/plugin marketplace remove agentic-ai-labs`
first.

## Security and secret scanning

Skills are instructions that AI agents **execute**, so security here is mostly
about *content*. Report vulnerabilities privately per [SECURITY.md](SECURITY.md),
never in a public issue or pull request.

When writing or reviewing a skill, check that it does **not**:

- **Leak sensitive data.** No real credentials, API keys, tokens, internal
  hostnames, or customer names. Reference secrets by environment-variable
  *name* and use placeholders such as `<your-api-key>`.
- **Steer agents toward unsafe actions.** No guidance that induces destructive
  commands, disabled safety checks, data exfiltration, or bypassing human
  review. For irreversible or high-impact steps, instruct the agent to confirm
  with a human first.
- **Introduce prompt-injection risk.** Don't tell agents to blindly follow
  instructions found in untrusted external content, and flag any place a skill
  consumes third-party input.
- **Point to untrusted supply chains.** Only direct users to official IBM or
  well-known, trustworthy tools, packages, and endpoints.

### Secret scanning (IBM Detect Secrets)

A committed [`.secrets.baseline`](.secrets.baseline) records reviewed findings,
and a [pre-commit hook](.pre-commit-config.yaml) scans each commit locally.
Set it up once per clone:

```
pip install --upgrade "git+https://github.com/ibm/detect-secrets.git@master#egg=detect-secrets"
pip install pre-commit
pre-commit install
```

If the hook flags something:

1. Review each finding: `detect-secrets audit .secrets.baseline`.
2. If anything is a **real** secret, remove it, **revoke the credential**,
   re-run `detect-secrets scan --update .secrets.baseline`, and re-audit.
3. Commit the updated `.secrets.baseline` with your change.

Don't bypass the hook with `--no-verify`; audit the finding instead. The
baseline's line numbers shift when files change, so refresh it with
`detect-secrets scan --update .secrets.baseline` after editing a file that
contains an allowlisted example.

## Pull request checklist

- [ ] Every new or changed Markdown file has the copyright and SPDX header
      (after front matter where present).
- [ ] Every commit is signed off (`git commit -s`).
- [ ] `plugin.json` `version` bumped if plugin content changed; new plugins are
      registered in `marketplace.json` and the README table.
- [ ] Tried the change in a real session (it triggers when it should and not
      when it shouldn't).
- [ ] No secrets, credentials, internal hostnames, or generated artifacts.
- [ ] The Detect Secrets hook passes, and `.secrets.baseline` is updated if
      needed.
- [ ] Files drafted with an AI tool carry the AI-assistance header line.

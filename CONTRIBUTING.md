<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus, Claude Sonnet) -->

# Contributing to Agentic AI Labs Skills

Thanks for your interest in contributing! This repository is an agent-neutral
catalog of skills for IBM products, packaged for Claude Code, Codex, GitHub
Copilot, Cursor, IBM Bob, and other coding agents. Contributions are skills
(authored here or imported from upstream projects), optional agent-specific
add-ons, and the documentation around them.

**Skill content contains no executable code.** Maintainer tooling (validator,
catalog generator, drift check, installer) lives in `scripts/`, and its tests
live in `tests/`.

## Table of contents

- [How to contribute](#how-to-contribute)
- [Legal: license and DCO](#legal-license-and-dco)
- [File requirements](#file-requirements)
- [Adding or changing a product or skill](#adding-or-changing-a-product-or-skill)
- [Importing a skill from another project](#importing-a-skill-from-another-project)
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
- **Imported skills** keep their upstream license and headers. Don't add this
  project's header to them; see [importing skills](#importing-a-skill-from-another-project).
- **Generated files** (`.claude-plugin/marketplace.json`,
  `.agents/plugins/marketplace.json`, `CATALOG.md`, `THIRD_PARTY_NOTICES.md`,
  `UPSTREAMS.md`) are written by `scripts/build_catalog.py`. Never edit them
  by hand.
- **Don't commit** build outputs, zips, or other artifacts.

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

## Adding or changing a product or skill

Each product is one folder, and that folder is also its plugin package. The
full contract is in [docs/catalog-metadata.md](docs/catalog-metadata.md).

```
products/<product>/
├── plugin.json                    # Agent Plugins manifest: name, version, description, license
├── README.md                      # what the skills cover, requirements
├── commands/<command>.md          # optional, Claude Code-only add-ons
└── skills/<skill-name>/
    ├── SKILL.md                   # Agent Skills front matter only (name, description, ...)
    ├── catalog-entry.json         # status, live-system flag, verification
    └── references/                # optional deep-dive material
```

1. **Start from a template.** Use [`templates/skill-build`](templates/skill-build)
   for building applications against a product, or
   [`templates/skill-ops`](templates/skill-ops) for deploying, configuring and
   operating it. Name skills `<product>-build` and `<product>-ops`.
2. **Keep front matter portable.** SKILL.md may only use the
   [Agent Skills spec](https://agentskills.io/specification) keys. Put
   agent-specific behaviour, such as Claude Code commands, in optional add-ons.
3. **Guard live systems.** If following a skill can create, change or delete
   resources in a live environment, set `"changes_live_systems": true` and
   include the `## Confirm before changing live systems` section. Every
   `*-ops` skill needs that section.
4. **Bump `version` in the product's `plugin.json`** whenever anything in the
   product folder changes. CI enforces this. Agents cache installed plugins
   and skip updates when the version hasn't changed.
5. **Regenerate the catalog** with `uv run scripts/build_catalog.py`. For a new
   product, also add a row to the product table in the [README](README.md).
6. **Keep `SKILL.md` focused.** Stay under about 500 lines and move depth
   into `references/`. Write the `description` for *triggering*: name the
   situations and keywords that should activate the skill.
7. **Target the real IBM products.** Use public documentation only: nothing
   internal-only, no customer names, no internal hostnames.

## Importing a skill from another project

Skills from other IBM teams and the community are welcome, credited to their
authors. Follow [docs/importing-skills.md](docs/importing-skills.md). In short:

- **License:** only MIT, Apache-2.0, BSD and ISC content is copied. Anything
  else becomes a link-only entry in `catalog/pointers.json`.
- **Pinning:** every import is pinned to an upstream commit, keeps its
  upstream LICENSE file, and records its authors.
- **Security review:** a maintainer reviews every import before it merges.
  The review covers hidden instructions, credential handling, scripts, and
  live-system changes.
- **Edits:** copies stay byte-identical to upstream unless portability
  requires an edit. Any edit is recorded, and a content hash catches
  unrecorded ones.

## Testing your change

**Tooling checks.** Run the same checks as CI. They need
[uv](https://docs.astral.sh/uv/):

```
uv sync
uv run scripts/validate.py
uv run scripts/build_catalog.py --check
uv run pytest
```

**Behaviour checks.** Passing CI is necessary but not sufficient: a skill is
only as good as the agent behaviour it produces, so test it by using it.
[docs/verifying-skills.md](docs/verifying-skills.md) explains how to verify
a skill and record the verification. For Claude Code:

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

For other agents, install from your clone with
`python3 scripts/install_skills.py --agent <agent> --product <product>`.

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
The [`Detect Secrets` workflow](.github/workflows/detect-secrets.yml) repeats
the scan in CI on every pull request using IBM's `git-defenders` container, and
fails on any unaudited, live, or audited-as-real finding. Set up the local hook
once per clone:

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
- [ ] `plugin.json` `version` bumped if product content changed; catalog files
      regenerated (`uv run scripts/build_catalog.py`); new products added to the
      README table.
- [ ] Live-system skills set `changes_live_systems` and include the
      confirmation section.
- [ ] Imports follow [docs/importing-skills.md](docs/importing-skills.md),
      including the recorded security review.
- [ ] Tried the change in a real session (it triggers when it should and not
      when it shouldn't).
- [ ] No secrets, credentials, internal hostnames, or generated artifacts.
- [ ] The Detect Secrets hook passes, and `.secrets.baseline` is updated if
      needed.
- [ ] Files drafted with an AI tool carry the AI-assistance header line.

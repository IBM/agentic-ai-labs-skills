<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Catalog metadata contract

This page defines the files that describe a product and its skills. The
validator (`scripts/validate.py`) enforces every rule here, and CI runs it on
every pull request.

## Layout

```text
products/<product>/
├── plugin.json                  # product manifest (Agent Plugins format)
├── README.md
├── commands/                    # optional, Claude Code-only add-ons
└── skills/<skill-name>/
    ├── SKILL.md                 # the skill (Agent Skills format)
    ├── catalog-entry.json       # provenance and status (this page)
    ├── LICENSE                  # imported skills only: the upstream license
    └── references/ ...          # optional deep-dive material
```

A product folder is a complete plugin package:

- **Codex, GitHub Copilot and Cursor** read the root `plugin.json` natively.
- **Claude Code** loads the same folder through `.claude-plugin/marketplace.json`.
- **Agents without a catalog** receive the `skills/` folders through the installer or a manual copy.

## `plugin.json` (product manifest)

The manifest uses the
[Agent Plugins](https://agent-plugins.org/plugin-authors/manifest) format.

| Field | Rule |
|---|---|
| `$schema` | `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json` |
| `name` | Lowercase letters, digits and hyphens. Usually the product slug. |
| `version` | SemVer. Bump it whenever anything in the product folder changes; CI enforces this on pull requests. |
| `description` | Required. |
| `license` | SPDX expression, for example `Apache-2.0` or `Apache-2.0 AND MIT` when imported skills are included. |
| `extensions["com.ibm.agentic-ai-labs"]` | Catalog-only fields: `displayName`, `category`. |

## `SKILL.md` front matter

SKILL.md front matter may only use the
[Agent Skills spec](https://agentskills.io/specification) keys:

- `name`
- `description`
- `license`
- `compatibility`
- `metadata`
- `allowed-tools`

Agent-specific keys break portability, and some Claude surfaces reject unknown keys outright. Keys affected include Claude Code's
`disable-model-invocation` and `argument-hint`. Put that behaviour in an
optional add-on instead, such as a Claude Code command in `commands/`.

The other front-matter rules:

- **`name`:** 1–64 characters of lowercase letters, digits and single hyphens. It must equal the skill's directory name.
- **`description`:** 1–1024 characters. Write it for triggering: name the situations and keywords that should activate the skill.
- **`metadata`:** values must be strings, so quote them.
- **Length:** keep the body under about 500 lines and move depth into `references/`.

## `catalog-entry.json` (per skill)

Every skill has a catalog entry. It travels with the installed skill, and
agents ignore it.

### Common fields

| Field | Rule |
|---|---|
| `status` | `"maintained"` (authored here) or `"imported"` (copied from upstream). |
| `changes_live_systems` | `true` if following the skill can create, change or delete resources in a live environment. Classify by behaviour, not by name. |
| `guardrail_exception` | Optional. A reviewed explanation for why a live-system skill doesn't need the guardrail section, for example because the upstream skill already asks before every change. |
| `verified` | Object mapping agent to `"YYYY-MM-DD@<product version>"`. Agents: `claude-code`, `codex`, `bob`, `copilot`, `cursor`. See [verifying-skills.md](verifying-skills.md). |

A verification is shown as **stale** once the product's version moves past
the version recorded with it.

### Imported-skill fields

| Field | Rule |
|---|---|
| `upstream` | `{ "url": "https://github.com/<owner>/<repo>", "path": "<dir in upstream>", "ref": "<40-char commit SHA>" }` |
| `license` | SPDX ID. It must be one of MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC or 0BSD. Anything else becomes a pointer entry; see below. |
| `authors` | List of upstream authors or organizations. |
| `content_sha256` | Hash of the skill's files, excluding `catalog-entry.json`, computed by `scripts/catalog_lib.py`. |
| `modified` | `false` if the files are byte-identical to upstream at `ref`. Otherwise `true`. |
| `modifications` | Required when `modified` is true. One line per change and why, for example "Removed Claude-only `disable-model-invocation` key for portability." |
| `security_review` | `{ "reviewer", "date", "notes" }`, recorded after the checklist in [importing-skills.md](importing-skills.md). |
| `security_allowlist` | Relative paths of files the reviewer checked and accepted despite a validator flag: non-Markdown files, executable bits, or fetch-and-run commands. |

Imported files keep their upstream license and headers. The project's SPDX
header rule applies only to maintained files.

## The live-system guardrail

These skills must contain the guardrail section:

- every maintained skill named `*-ops`;
- every skill with `"changes_live_systems": true`, unless the skill records a `guardrail_exception`.

The heading must be exactly:

```markdown
## Confirm before changing live systems
```

It must be followed by this standard sentence, plus any product-specific
specifics:

> Before running any command that creates, changes, or deletes resources in
> a live environment, state what it will do and wait for the user's explicit
> approval. A request that names the specific change counts as approval for
> that change only.

## `catalog/pointers.json`

Pointer entries list upstream skills we cannot copy, usually because of
their license (for example MPL-2.0 or BUSL-1.1), or because a question is
unresolved. Pointers are **link-only**. They appear in `CATALOG.md` and
`UPSTREAMS.md`, never in an installable catalog.

```json
{
  "pointers": [
    {
      "name": "terraform-module-authoring",
      "url": "https://github.com/<owner>/<repo>",
      "path": "<dir in upstream>",
      "ref": "<40-char commit SHA>",
      "license": "MPL-2.0",
      "reason": "MPL-2.0 is not on the permissive list",
      "products": ["terraform"]
    }
  ]
}
```

If a pointer has a permissive license, its `reason` must start with
"unresolved", for example when the upstream's copyright notice conflicts
with its LICENSE file.

## Names

Skill names must be unique across every product and every pointer entry.
When two upstream skills share a name, import the one that fits its
product better and list the other as a pointer. Don't rename either of them:
renaming is a modification, and it breaks the link to upstream.

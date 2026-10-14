<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Importing a skill from another project

This catalog brings IBM-related skills from other teams and the community
together, credited to their authors. A maintainer does every import by
hand, following this checklist. CI (`scripts/validate.py`) enforces the
mechanical parts. The review steps need a human.

The field reference for `catalog-entry.json` is in
[catalog-metadata.md](catalog-metadata.md).

## 1. Decide: import, pointer, or skip

| Situation | Action |
|---|---|
| License is MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC or 0BSD | Import it (copy it here). |
| Any other license (MPL-2.0, BUSL-1.1, GPL, none, …) | Add a **pointer** entry to `catalog/pointers.json`. Pointers are link-only. |
| License is permissive but something is unresolved, for example the README's copyright notice conflicts with LICENSE | Add a pointer whose `reason` starts with "unresolved". |
| The skill needs other unpublished skills or private services to work | Skip it, or add a pointer that explains why. |
| Same name as a skill already in the catalog | Import the one that better fits its product and add a pointer for the other. Don't rename either one. |

Check the license **at the exact commit you will pin**, using the LICENSE file
in the repository and any license in the skill folder itself. Licenses
reported by inventories, search results or GitHub's sidebar are leads, not
facts. A permissive subtree inside a differently licensed repository counts
only if that subtree has its own LICENSE file.

## 2. Copy the skill at a pinned commit

1. **Pick the commit.** Use the full 40-character SHA of the upstream commit
   you reviewed, not a branch or tag.
2. **Copy the folder unchanged.** Copy the upstream skill folder, containing
   `SKILL.md` and its supporting files, to
   `products/<product>/skills/<upstream-skill-name>/`. Choose the product the
   skill targets. Portfolio-wide skills go in a collection folder; ask a
   maintainer which one.
3. **Add the license.** Copy the upstream LICENSE file into the skill folder
   if it isn't there already.
4. **Stage the files** with `git add`. The validator hashes tracked files only.

## 3. Security review

Skills are instructions that agents execute with the user's permissions,
and this catalog puts IBM's name on them. Read **every file** in the skill
and check for:

- [ ] **Hidden or injected instructions:** text addressed to the agent that
      the user wouldn't expect, such as "ignore previous instructions",
      instructions in HTML comments or zero-width characters, or a request to
      fetch and follow remote instructions.
- [ ] **Credential handling:** the skill must never ask the user to paste
      secrets into the chat or into files. Secrets go in environment
      variables or the product's secret store. Nothing may send credentials
      anywhere except the product itself.
- [ ] **Remote fetch:** URLs the skill tells the agent to download from or
      execute. They must be official IBM, Red Hat, HashiCorp or other
      well-known trustworthy sources, and must never be fetch-and-run
      (`curl … | sh`).
- [ ] **Bundled code:** scripts, binaries, notebooks and executables.
      Understand what each one does. The validator flags every non-Markdown
      file, every executable bit and every fetch-and-run command. After
      reviewing a flagged file, add its path to `security_allowlist`.
- [ ] **Live-system changes:** classify the skill. If following it can
      create, change or delete resources in a live environment, set
      `"changes_live_systems": true`. Then do one of these:
      - add the `## Confirm before changing live systems` section. This
        counts as a modification; record it.
      - record a `guardrail_exception` explaining why the upstream skill is
        already safe, for example because it asks before every change.

If anything fails review and can't be fixed with a small recorded edit, don't
import the skill. Add a pointer instead, or skip it.

## 4. Portability edits (only if required)

Keep upstream files byte-identical whenever possible. Edit only when the
skill wouldn't otherwise work across agents. The usual case is a top-level
front-matter key that isn't in the Agent Skills spec, such as
`disable-model-invocation`. Record every edit in `modifications`.

## 5. Write `catalog-entry.json`

```json
{
  "status": "imported",
  "upstream": {
    "url": "https://github.com/<owner>/<repo>",
    "path": "<path to the skill folder in upstream>",
    "ref": "<40-char commit SHA>"
  },
  "license": "MIT",
  "authors": ["<upstream author or organization>"],
  "content_sha256": "<see below>",
  "modified": false,
  "modifications": [],
  "security_review": {"reviewer": "<github handle>", "date": "YYYY-MM-DD", "notes": "<what you checked>"},
  "security_allowlist": [],
  "changes_live_systems": false,
  "verified": {}
}
```

Compute `content_sha256` **before** making any modification, so it
describes the upstream copy:

```text
uv run scripts/catalog_lib.py hash products/<product>/skills/<skill>
```

If you then make portability edits, leave `content_sha256` as the upstream
hash. Set `"modified": true` and list each change in `modifications`.

## 6. Register and regenerate

1. **Product manifest.** If the product folder is new, create its
   `plugin.json` and `README.md`, using an existing product as the model, and
   add a row to the README product table. Otherwise bump the product's
   `version`.
2. **Owners.** Add or update the upstream's owner and tracker link in
   `catalog/owners.json`, keyed by `<owner>/<repo>`.
3. **Regenerate and check:**
   ```text
   uv run scripts/build_catalog.py
   uv run scripts/validate.py
   ```
   `CATALOG.md`, `THIRD_PARTY_NOTICES.md` and `UPSTREAMS.md` now credit
   the upstream.

## When upstream changes (drift)

A weekly workflow (`.github/workflows/upstream-drift.yml`) keeps one issue
labelled `upstream-drift` up to date. For each drifted skill:

1. Review the upstream changes using the compare link in the issue.
2. Re-run the security review on the changed files.
3. Re-copy the folder at the new commit, re-apply any recorded
   modifications, and update `ref` and `content_sha256`. Bump the product's
   version.
4. If upstream moved or deleted the skill ("path missing"), or rewrote
   history ("pin missing"), decide case by case: re-pin, convert the skill
   to a pointer, or keep the current copy and note why.

## When an upstream team joins

When an upstream team agrees to consolidate, its skills can go one of two
ways:

- **Contributed here.** The team becomes the owner in
  `.github/CODEOWNERS`, and the skill's `status` becomes `maintained`,
  maintained in this repository.
- **Kept upstream.** The skill becomes a pointer.

Note the transition in `CHANGELOG.md`. People who installed the earlier
copy keep working, and they pick up the new copy, or the pointer's
instructions, on their next update.

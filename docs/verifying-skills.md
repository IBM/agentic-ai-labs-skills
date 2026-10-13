<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Verifying a skill in an agent

`CATALOG.md` shows which agents each skill has been verified in. A
verification records that a person checked the skill in a real session with
that agent. It is a claim made by a person, so make it only after doing the
checks below.

## What counts as verified

Install the skill the way a user would, then check all three:

1. **It triggers when it should.** Give the agent a realistic task in the
   skill's domain. Phrase it the way a user would, without naming the
   skill. The agent loads the skill.
2. **It stays quiet when it shouldn't.** Give the agent a related request
   for a different IBM product, or a generic coding task. The skill doesn't
   load.
3. **The guidance works.** The agent follows the skill and the result is
   correct: commands exist, flags are right, and the steps succeed against
   a real or test environment. For skills with
   `"changes_live_systems": true`, the agent also stops for confirmation
   before the first change to a live system.

If any check fails, fix the skill, or open an issue, instead of recording a
verification.

## Recording it

Add the agent to `verified` in the skill's `catalog-entry.json`, with the
date and the product's **current** version from its `plugin.json`:

```json
"verified": {
  "claude-code": "2026-10-12@1.2.0",
  "bob": "2026-10-14@1.2.0"
}
```

Agent keys are `claude-code`, `codex`, `bob`, `copilot` and `cursor`.

Then regenerate the catalog (`uv run scripts/build_catalog.py`). When the
product's version later moves past the recorded version, `CATALOG.md`
shows the verification as *stale*, because the skill changed since someone
last checked it.

A change that only adds or updates `verified` entries doesn't need a
version bump. CI exempts it, because a bump would immediately mark the new
verification stale.

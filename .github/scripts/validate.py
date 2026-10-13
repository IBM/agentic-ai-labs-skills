#!/usr/bin/env python3
# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Validate the plugin marketplace against the rules in CONTRIBUTING.md.

Run from the repository root:  python3 .github/scripts/validate.py
Set BASE_SHA to also enforce the "bump plugin.json version when content
changes" rule against that commit (CI sets it on pull requests).
"""
import glob
import json
import os
import re
import subprocess
import sys

COPYRIGHT = "Copyright contributors to the Agentic AI Labs project"
SPDX = "SPDX-License-Identifier: Apache-2.0"
LICENSE_ID = "Apache-2.0"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
# Third-party / template files that are intentionally left as-is.
HEADER_EXEMPT = {"CODE_OF_CONDUCT.md", "CHANGELOG.md", "MAINTAINERS.md"}
LEGACY_NAME = "Agent Skills project"

errors = []


def err(msg):
    errors.append(msg)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def front_matter(path):
    """Return the front-matter text of a Markdown file, or None if absent."""
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", read(path), re.S)
    return m.group(1) if m else None


def fm_field(fm, key):
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def check_header(path):
    """Markdown must carry the copyright + SPDX comments near the top."""
    text = read(path)
    text = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, count=1, flags=re.S)
    top = "\n".join(text.splitlines()[:8])
    if COPYRIGHT not in top or SPDX not in top:
        err(f"{path}: missing copyright/SPDX header (see CONTRIBUTING.md)")


def git(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )


# --- marketplace manifest ----------------------------------------------------
try:
    market = json.loads(read(".claude-plugin/marketplace.json"))
except (OSError, ValueError) as exc:
    sys.exit(f"ERROR: cannot load .claude-plugin/marketplace.json: {exc}")

registered = {}
for p in market.get("plugins", []):
    name, src = p.get("name"), p.get("source", "")
    if not name or not src or not os.path.isdir(src):
        err(f"marketplace.json: plugin '{name}': source missing -> {src}")
        continue
    if name in registered:
        err(f"marketplace.json: duplicate plugin name '{name}'")
    registered[name] = os.path.normpath(src)

# Every directory under products/ must be registered.
for d in sorted(glob.glob("products/*/")):
    d = os.path.normpath(d)
    if d not in registered.values():
        err(f"{d}: plugin directory is not registered in marketplace.json")

# README skills table must list every registered plugin.
readme = read("README.md")
for name in registered:
    if f"[`{name}`]" not in readme:
        err(f"README.md: plugin '{name}' missing from the skills table")

# --- per-plugin checks -------------------------------------------------------
for name, src in registered.items():
    manifest = os.path.join(src, "plugin.json")
    try:
        meta = json.loads(read(manifest))
    except (OSError, ValueError) as exc:
        err(f"{manifest}: cannot load: {exc}")
        meta = {}
    if meta:
        if meta.get("name") != name:
            err(f"{manifest}: name '{meta.get('name')}' != marketplace name '{name}'")
        if not SEMVER.match(str(meta.get("version", ""))):
            err(f"{manifest}: 'version' missing or not semver")
        if meta.get("license") != LICENSE_ID:
            err(f"{manifest}: license must be {LICENSE_ID}, got {meta.get('license')!r}")
        if not meta.get("description"):
            err(f"{manifest}: 'description' missing")

    if not os.path.isfile(os.path.join(src, "README.md")):
        err(f"{src}: README.md missing")

    skills = glob.glob(f"{src}/skills/*/SKILL.md")
    if not skills:
        err(f"{src}: no skills/*/SKILL.md found")
    for sk in skills:
        fm = front_matter(sk)
        if fm is None:
            err(f"{sk}: missing YAML front matter")
            continue
        sk_name = fm_field(fm, "name")
        if sk_name != os.path.basename(os.path.dirname(sk)):
            err(f"{sk}: front-matter name '{sk_name}' != directory name")
        if len(fm_field(fm, "description")) < 40:
            err(f"{sk}: description missing or too short to trigger on")

    for cmd in glob.glob(f"{src}/commands/*.md"):
        fm = front_matter(cmd)
        if fm is None or not fm_field(fm, "description"):
            err(f"{cmd}: command needs front matter with a description")

# --- headers and legacy naming on all Markdown ------------------------------
tracked = git("ls-files", "*.md").stdout.split()
for path in sorted(tracked):
    if path in HEADER_EXEMPT or not (
        "/" not in path or path.startswith("products/")
    ):
        continue
    if path in HEADER_EXEMPT:
        continue
    check_header(path)
    if LEGACY_NAME in read(path):
        err(f"{path}: contains legacy name '{LEGACY_NAME}'")

# --- version bump on pull requests ------------------------------------------
base = os.environ.get("BASE_SHA", "").strip()
if base:
    for name, src in registered.items():
        changed = git("diff", "--name-only", f"{base}...HEAD", "--", src).stdout.split()
        manifest = os.path.join(src, "plugin.json")
        # Only the manifest itself changing does not count as content.
        content = [c for c in changed if c != manifest]
        if not content:
            continue
        old = git("show", f"{base}:{manifest}")
        if old.returncode != 0:
            continue  # new plugin: nothing to compare against
        try:
            old_v = json.loads(old.stdout).get("version")
            new_v = json.loads(read(manifest)).get("version")
        except ValueError:
            continue
        if old_v == new_v:
            err(f"{manifest}: content changed but version is still {new_v}; bump it")

if errors:
    print("\n".join(f"ERROR: {e}" for e in errors))
    sys.exit(1)
print(f"OK: {len(registered)} plugin(s) validated")

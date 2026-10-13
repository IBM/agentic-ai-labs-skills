#!/usr/bin/env python3
# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Report upstream drift for imported skills and pointer entries.

    GITHUB_TOKEN=... uv run scripts/check_drift.py --output drift-report.md

For each pinned upstream (imported skill or pointer entry) this asks GitHub:

1. Does the pinned commit still exist?            -> otherwise "pin missing"
2. Does the path still exist on the default branch? -> otherwise "path missing"
3. Is the latest default-branch commit touching the path already contained in
   the pin (equal, or an ancestor of it)?          -> "current", else "drifted"

Step 3 deliberately does not compare the pin with the latest commit by
equality: pins are taken at whatever commit the license was verified at,
which is usually newer than the last change to the skill's own path.

Exit status: 0 when every check ran (drifted items are reported, not
errors); 1 when any check failed (network, rate limit, unexpected response),
so a failed check is never mistaken for "current".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import catalog_lib as cl

API = "https://api.github.com"
CATEGORIES = ("drifted", "path missing", "pin missing", "unsupported host", "check failed", "current")

# fetch(url) -> (http status, parsed JSON or None)
Fetch = Callable[[str], "tuple[int, object]"]


@dataclass
class Item:
    label: str  # e.g. "products/db2/skills/x" or "pointer x"
    url: str
    path: str
    ref: str


@dataclass
class Outcome:
    item: Item
    category: str
    detail: str = ""
    latest: str = ""


def github_fetch(token: str | None) -> Fetch:
    def fetch(url: str):
        if not url.startswith(API + "/"):
            raise ValueError(f"refusing to call non-GitHub API URL {url}")
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agentic-ai-labs-drift-check",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode() or "null")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            try:
                return exc.code, json.loads(body)
            except ValueError:
                return exc.code, None
    return fetch


def collect(root: Path) -> list[Item]:
    items = []
    for product in cl.discover(root):
        for s in product.skills:
            entry = s.entry or {}
            if entry.get("status") == "imported":
                up = entry.get("upstream") or {}
                items.append(Item(s.path.relative_to(root).as_posix(), up.get("url", ""), up.get("path", ""), up.get("ref", "")))
    for p in cl.load_pointers(root):
        items.append(Item(f"pointer {p.get('name', '?')}", p.get("url", ""), p.get("path", ""), p.get("ref", "")))
    return items


class CheckFailed(Exception):
    pass


def _get(fetch: Fetch, url: str, ok=(200,)):
    status, data = fetch(url)
    if status in ok:
        return status, data
    if status == 404:
        return status, data
    msg = (data or {}).get("message", "") if isinstance(data, dict) else ""
    raise CheckFailed(f"HTTP {status} from GitHub{': ' + msg if msg else ''}")


def check_item(item: Item, fetch: Fetch, branches: dict) -> Outcome:
    owner_repo = cl.parse_github_url(item.url)
    if not owner_repo or not cl.SHA_RE.match(item.ref or ""):
        return Outcome(item, "unsupported host", "upstream is not a pinned https://github.com repository")
    owner, repo = owner_repo
    base = f"{API}/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
    path = item.path.strip("/")
    qpath = urllib.parse.quote(path)
    try:
        key = f"{owner}/{repo}"
        if key not in branches:
            status, data = _get(fetch, base)
            if status == 404:
                return Outcome(item, "pin missing", "upstream repository not found")
            branches[key] = data["default_branch"]
        branch = branches[key]
        qbranch = urllib.parse.quote(branch)

        status, _ = _get(fetch, f"{base}/commits/{item.ref}")
        if status == 404:
            return Outcome(item, "pin missing", "pinned commit no longer exists upstream")

        status, _ = _get(fetch, f"{base}/contents/{qpath}?ref={qbranch}")
        if status == 404:
            return Outcome(item, "path missing", f"path no longer exists on {branch}")

        status, commits = _get(fetch, f"{base}/commits?sha={qbranch}&path={qpath}&per_page=1")
        if status == 404 or not commits:
            return Outcome(item, "path missing", f"no commits touch the path on {branch}")
        latest = commits[0]["sha"]
        if latest == item.ref:
            return Outcome(item, "current", latest=latest)

        status, cmp = _get(fetch, f"{base}/compare/{item.ref}...{latest}")
        if status == 404:
            return Outcome(item, "check failed", "compare API returned 404")
        # base=pin, head=latest path commit: "behind"/"identical" means the
        # latest path change is already contained in the pin.
        if cmp.get("status") in ("identical", "behind"):
            return Outcome(item, "current", latest=latest)
        return Outcome(item, "drifted", f"{cmp.get('ahead_by', '?')} newer commit(s) on {branch}", latest)
    except (CheckFailed, KeyError, TypeError, ValueError, OSError) as exc:
        return Outcome(item, "check failed", str(exc))


def _code(text: str) -> str:
    """Render untrusted upstream text inert: code span, no backticks, no mentions."""
    clean = re.sub(r"[`\r\n]", " ", str(text)).replace("@", "@​")
    return f"`{clean}`"


def report(outcomes: list[Outcome]) -> str:
    by_cat = {c: [o for o in outcomes if o.category == c] for c in CATEGORIES}
    lines = ["# Upstream drift report", ""]
    summary = ", ".join(f"{len(by_cat[c])} {c}" for c in CATEGORIES if by_cat[c])
    lines.append(f"Checked {len(outcomes)} pinned upstream(s): {summary or 'nothing to check'}.")
    lines.append("")
    for cat in CATEGORIES:
        if not by_cat[cat] or cat == "current":
            continue
        lines += [f"## {cat.capitalize()}", ""]
        for o in by_cat[cat]:
            owner_repo = cl.parse_github_url(o.item.url)
            line = f"- {_code(o.item.label)}: {_code(o.item.url)} path {_code(o.item.path)}"
            if o.detail:
                line += f" ({_code(o.detail)})"
            if cat == "drifted" and owner_repo and cl.SHA_RE.match(o.latest or ""):
                line += f" [compare](https://github.com/{owner_repo[0]}/{owner_repo[1]}/compare/{o.item.ref}...{o.latest})"
            lines.append(line)
        lines.append("")
    if by_cat["current"]:
        lines += ["## Current", ""] + [f"- {_code(o.item.label)}" for o in by_cat["current"]] + [""]
    lines.append("To act on drift, follow docs/importing-skills.md (re-review, re-pin, update the hash).")
    return "\n".join(lines) + "\n"


def run(root: Path, fetch: Fetch) -> list[Outcome]:
    branches: dict = {}
    return [check_item(i, fetch, branches) for i in collect(root)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Report upstream drift for imported skills and pointers.")
    ap.add_argument("--output", help="write the markdown report to this file")
    args = ap.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    outcomes = run(root, github_fetch(os.environ.get("GITHUB_TOKEN")))
    text = report(outcomes)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text)
    attention = any(o.category != "current" for o in outcomes)
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"needs_attention={'true' if attention else 'false'}\n")
    return 1 if any(o.category == "check failed" for o in outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())

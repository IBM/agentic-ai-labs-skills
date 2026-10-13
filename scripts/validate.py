#!/usr/bin/env python3
# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Validate the skills catalog against the rules in CONTRIBUTING.md.

Run from anywhere:  uv run scripts/validate.py
Set BASE_SHA to also enforce the "bump plugin.json version when a product's
content changes" rule against that commit (CI sets it on pull requests).

The catalog contract is documented in docs/catalog-metadata.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import catalog_lib as cl

COPYRIGHT = "Copyright contributors to the Agentic AI Labs project"
SPDX = "SPDX-License-Identifier: Apache-2.0"
LEGACY_NAME = "Agent Skills project"
# Third-party / template files that are intentionally left as-is.
HEADER_EXEMPT = {"CODE_OF_CONDUCT.md", "CHANGELOG.md", "MAINTAINERS.md"}
# Markdown is scanned for headers at the repo root and under these folders.
HEADER_DIRS = ("products/", "docs/", "templates/")

# Files in an imported skill that need no security allow-list entry.
BENIGN_FILE_RE = re.compile(r"(?i)(\.md|\.markdown|\.txt)$|(^|/)(LICENSE|LICENCE|NOTICE|COPYING)[^/]*$")
# Patterns that download and execute remote code in one step.
FETCH_AND_RUN_RES = [
    re.compile(r"(?i)\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|k)?sh\b"),
    re.compile(r"(?i)\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?python[0-9.]*\b"),
    re.compile(r"(?i)\b(ba|z)?sh\s+<\(\s*(curl|wget)\b"),
    re.compile(r"(?i)\$\(\s*(curl|wget)\b"),
    re.compile(r"(?i)\biex\b.*\b(DownloadString|Invoke-WebRequest|iwr|irm|Invoke-RestMethod)\b"),
]
SKILL_BODY_WARN_LINES = 500


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def check_frontmatter(root: Path, skill: cl.Skill, res: Result) -> None:
    where = _rel(root, skill.path / "SKILL.md")
    fm = skill.frontmatter
    if fm is None:
        return
    extra = sorted(set(fm) - cl.SPEC_FRONTMATTER_KEYS)
    if extra:
        res.errors.append(
            f"{where}: front matter keys not in the Agent Skills spec: {', '.join(extra)} "
            "(move agent-specific behaviour to an add-on, see docs/catalog-metadata.md)"
        )
    name = fm.get("name")
    if not isinstance(name, str) or not cl.NAME_RE.match(name) or len(name) > 64:
        res.errors.append(
            f"{where}: name {name!r} must be 1-64 chars of lowercase letters, digits and single hyphens"
        )
    elif name != skill.name:
        res.errors.append(f"{where}: name {name!r} does not match directory {skill.name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip() or len(desc) > 1024:
        res.errors.append(f"{where}: description must be a non-empty string of at most 1024 chars")
    meta = fm.get("metadata")
    if meta is not None:
        if not isinstance(meta, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in meta.items()
        ):
            res.errors.append(f"{where}: metadata must map string keys to string values (quote them)")
    lines = skill.body.count("\n")
    if lines > SKILL_BODY_WARN_LINES:
        res.warnings.append(f"{where}: body is {lines} lines; keep SKILL.md under ~500 and move depth to references/")


def has_guardrail(skill: cl.Skill) -> bool:
    """True if the guardrail heading appears as a real heading (not inside a code fence)."""
    in_fence = False
    for line in skill.body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence and line.rstrip() == cl.GUARDRAIL_HEADING:
            return True
    return False


def check_verified(root: Path, skill: cl.Skill, entry: dict, res: Result) -> None:
    where = _rel(root, skill.path / cl.ENTRY_FILE)
    verified = entry.get("verified", {})
    if not isinstance(verified, dict):
        res.errors.append(f"{where}: verified must be an object of agent -> 'YYYY-MM-DD@<version>'")
        return
    current = cl.parse_semver(skill.product.version or "")
    for agent, value in verified.items():
        if agent not in cl.AGENTS:
            res.errors.append(f"{where}: unknown verification agent {agent!r} (known: {', '.join(cl.AGENTS)})")
            continue
        m = cl.VERIFIED_RE.match(value) if isinstance(value, str) else None
        if not m or not re.match(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$", m.group(1)):
            res.errors.append(f"{where}: verified.{agent} must look like 'YYYY-MM-DD@<version>', got {value!r}")
            continue
        version = cl.parse_semver(m.group(2))
        if version is None:
            res.errors.append(f"{where}: verified.{agent} version {m.group(2)!r} is not SemVer")
        elif current and version > current:
            res.errors.append(
                f"{where}: verified.{agent} records version {m.group(2)} above the product version {skill.product.version}"
            )


def check_upstream(where: str, upstream, res: Result, label: str = "upstream") -> None:
    if not isinstance(upstream, dict):
        res.errors.append(f"{where}: {label} must be an object with url, path and ref")
        return
    if not cl.parse_github_url(upstream.get("url", "")):
        res.errors.append(f"{where}: {label}.url must be an https://github.com/<owner>/<repo> URL")
    if not upstream.get("path"):
        res.errors.append(f"{where}: {label}.path is required")
    if not cl.SHA_RE.match(upstream.get("ref", "")):
        res.errors.append(f"{where}: {label}.ref must be a full 40-character commit SHA")


def check_security_flags(root: Path, skill: cl.Skill, entry: dict, res: Result) -> None:
    where = _rel(root, skill.path)
    allow = set(entry.get("security_allowlist") or [])
    for f in cl.tracked_files(root, skill.path):
        rel = f.relative_to(skill.path).as_posix()
        if rel == cl.ENTRY_FILE or not f.is_file():
            continue
        reasons = []
        if not BENIGN_FILE_RE.search(rel):
            reasons.append("non-Markdown file")
        if os.access(f, os.X_OK):
            reasons.append("executable bit")
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = ""
        if any(rx.search(text) for rx in FETCH_AND_RUN_RES):
            reasons.append("fetch-and-run pattern")
        if reasons and rel not in allow:
            res.errors.append(
                f"{where}/{rel}: {', '.join(reasons)} in an imported skill; review it and add "
                f"{rel!r} to security_allowlist (see docs/importing-skills.md)"
            )


def check_no_symlinks(root: Path, skill: cl.Skill, res: Result) -> None:
    for dirpath, dirnames, filenames in os.walk(skill.path):
        for n in dirnames + filenames:
            p = Path(dirpath) / n
            if p.is_symlink():
                res.errors.append(f"{_rel(root, p)}: symlinks are not allowed inside skills")


def check_entry(root: Path, skill: cl.Skill, res: Result) -> None:
    where = _rel(root, skill.path / cl.ENTRY_FILE)
    entry = skill.entry
    if entry is None:
        res.errors.append(f"{where}: missing (every skill needs a catalog entry; see docs/catalog-metadata.md)")
        return
    status = entry.get("status")
    if status not in ("maintained", "imported"):
        res.errors.append(f"{where}: status must be 'maintained' or 'imported', got {status!r}")
        return
    live = entry.get("changes_live_systems")
    if not isinstance(live, bool):
        res.errors.append(f"{where}: changes_live_systems must be true or false")
    check_verified(root, skill, entry, res)

    guarded = has_guardrail(skill)
    exception = entry.get("guardrail_exception")
    if status == "maintained" and skill.name.endswith("-ops") and not guarded:
        res.errors.append(
            f"{_rel(root, skill.path / 'SKILL.md')}: ops skills must contain the section "
            f"'{cl.GUARDRAIL_HEADING}'"
        )
    if live is True and not guarded and not (isinstance(exception, str) and exception.strip()):
        res.errors.append(
            f"{where}: changes_live_systems is true, so SKILL.md needs the section "
            f"'{cl.GUARDRAIL_HEADING}' or a recorded guardrail_exception"
        )

    if status == "imported":
        check_upstream(where, entry.get("upstream"), res)
        license_id = entry.get("license")
        if license_id not in cl.PERMISSIVE_LICENSES:
            res.errors.append(
                f"{where}: license {license_id!r} may not be copied here; use a pointer entry "
                f"in catalog/pointers.json instead (permissive: {', '.join(sorted(cl.PERMISSIVE_LICENSES))})"
            )
        if not any((skill.path / n).is_file() for n in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE")):
            res.errors.append(f"{_rel(root, skill.path)}: imported skills must bundle the upstream LICENSE file")
        if not entry.get("authors"):
            res.errors.append(f"{where}: authors is required for imported skills")
        review = entry.get("security_review")
        if not (isinstance(review, dict) and review.get("reviewer") and review.get("date")):
            res.errors.append(f"{where}: security_review with reviewer and date is required for imported skills")
        actual = cl.content_sha256(root, skill.path)
        modified = entry.get("modified")
        if modified is True:
            if not entry.get("modifications"):
                res.errors.append(f"{where}: modified is true, so modifications must describe each change")
        elif actual != entry.get("content_sha256"):
            res.errors.append(
                f"{where}: content_sha256 does not match the skill's files; either the copy was edited "
                "(set modified: true and record the change in modifications) or the hash is stale"
            )
        check_security_flags(root, skill, entry, res)


def check_product(root: Path, product: cl.Product, market_by_source: dict, res: Result) -> None:
    where = _rel(root, product.path / "plugin.json")
    for e in product.errors:
        res.errors.append(f"{where}: {e}")
    m = product.manifest
    if not m:
        return
    if m.get("$schema") != cl.AGENT_PLUGINS_SCHEMA:
        res.errors.append(f"{where}: $schema must be {cl.AGENT_PLUGINS_SCHEMA}")
    if not isinstance(m.get("name"), str) or not cl.NAME_RE.match(m["name"]):
        res.errors.append(f"{where}: name must be lowercase letters, digits and hyphens")
    if cl.parse_semver(m.get("version", "")) is None:
        res.errors.append(f"{where}: version must be SemVer (e.g. 1.0.0)")
    if not m.get("description"):
        res.errors.append(f"{where}: description is required")
    if not re.match(r"^[A-Za-z0-9.+-]+( (AND|OR) [A-Za-z0-9.+-]+)*$", m.get("license", "")):
        res.errors.append(f"{where}: license must be an SPDX license expression")
    if not product.skills:
        res.errors.append(f"{_rel(root, product.path)}: product has no skills (skills/<name>/SKILL.md)")

    entry = market_by_source.get(f"./products/{product.slug}")
    if entry is None:
        res.errors.append(f"{_rel(root, product.path)}: product is not registered in .claude-plugin/marketplace.json")
    else:
        if entry.get("name") != m.get("name"):
            res.errors.append(
                f".claude-plugin/marketplace.json: entry name {entry.get('name')!r} != plugin name {m.get('name')!r}"
            )
        if entry.get("version") != m.get("version"):
            res.errors.append(
                f".claude-plugin/marketplace.json: {m.get('name')} version {entry.get('version')} "
                f"!= plugin.json version {m.get('version')}"
            )


def check_pointers(root: Path, pointers: list[dict], res: Result) -> None:
    for i, p in enumerate(pointers):
        where = f"catalog/pointers.json[{i}] ({p.get('name', '?')})"
        if not isinstance(p.get("name"), str) or not cl.NAME_RE.match(p["name"]):
            res.errors.append(f"{where}: pointer name must be lowercase letters, digits and hyphens")
        check_upstream(where, p, res, label="pointer")
        if not p.get("products"):
            res.errors.append(f"{where}: pointer must list the products it relates to")
        reason = (p.get("reason") or "").strip()
        if not reason:
            res.errors.append(f"{where}: pointer needs a reason")
        if p.get("license") in cl.PERMISSIVE_LICENSES and "unresolved" not in reason.lower():
            res.errors.append(
                f"{where}: pointer license {p.get('license')} is permissive; import it instead, "
                "or explain why in a reason that starts with 'unresolved'"
            )


def check_names_unique(root: Path, products, pointers, res: Result) -> None:
    seen: dict[str, str] = {}
    for product in products:
        for s in product.skills:
            loc = _rel(root, s.path)
            if s.name in seen:
                res.errors.append(f"{loc}: duplicate skill name {s.name!r} (also at {seen[s.name]})")
            seen.setdefault(s.name, loc)
    for p in pointers:
        name = p.get("name")
        if name in seen:
            res.errors.append(f"catalog/pointers.json: duplicate skill name {name!r} (also at {seen[name]})")
        seen.setdefault(name, "catalog/pointers.json")


def check_markdown_headers(root: Path, products, res: Result) -> None:
    imported_dirs = [
        s.path for p in products for s in p.skills if (s.entry or {}).get("status") == "imported"
    ]
    for f in cl.tracked_files(root):
        rel = _rel(root, f)
        if not rel.endswith(".md") or rel in HEADER_EXEMPT:
            continue
        if "/" in rel and not rel.startswith(HEADER_DIRS):
            continue
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        if LEGACY_NAME in text:
            res.errors.append(f"{rel}: contains legacy name '{LEGACY_NAME}'")
        if any(d == f.parent or d in f.parents for d in imported_dirs):
            continue  # imported content keeps its upstream headers
        _, body = cl.split_frontmatter(text)
        top = "\n".join(body.lstrip("\n").splitlines()[:8])
        if COPYRIGHT not in top or SPDX not in top:
            res.errors.append(f"{rel}: missing copyright/SPDX header (see CONTRIBUTING.md)")


def check_readme(root: Path, products, res: Result) -> None:
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    for p in products:
        if p.name and f"[`{p.name}`]" not in text:
            res.errors.append(f"README.md: plugin '{p.name}' missing from the skills table")


def check_version_bumps(root: Path, products, base: str, res: Result) -> None:
    for p in products:
        manifest = _rel(root, p.path / "plugin.json")
        changed = cl.git(root, "diff", "--name-only", f"{base}...HEAD", "--", _rel(root, p.path)).stdout.split()
        if not [c for c in changed if c != manifest]:
            continue
        old = cl.git(root, "show", f"{base}:{manifest}")
        if old.returncode != 0:
            continue  # new product (or newly moved): nothing to compare against
        try:
            old_v = json.loads(old.stdout).get("version")
        except ValueError:
            continue
        if old_v == p.version:
            res.errors.append(f"{manifest}: product content changed but version is still {p.version}; bump it")


def run(root: Path, base_sha: str | None = None) -> Result:
    root = Path(root).resolve()
    res = Result()
    products = cl.discover(root)
    try:
        pointers = cl.load_pointers(root)
    except ValueError as exc:
        res.errors.append(f"catalog/pointers.json: not valid JSON: {exc}")
        pointers = []
    try:
        market = cl.load_json(root / ".claude-plugin" / "marketplace.json")
    except (OSError, ValueError) as exc:
        res.errors.append(f".claude-plugin/marketplace.json: cannot load: {exc}")
        market = {}
    market_by_source = {e.get("source"): e for e in market.get("plugins", []) if isinstance(e, dict)}
    product_sources = {f"./products/{p.slug}" for p in products}
    for source, entry in market_by_source.items():
        if source not in product_sources:
            res.errors.append(
                f".claude-plugin/marketplace.json: entry {entry.get('name')!r} source {source!r} is not a product folder"
            )

    for product in products:
        check_product(root, product, market_by_source, res)
        for skill in product.skills:
            for e in skill.errors:
                res.errors.append(f"{_rel(root, skill.path)}: {e}")
            check_frontmatter(root, skill, res)
            check_no_symlinks(root, skill, res)
            check_entry(root, skill, res)
    check_names_unique(root, products, pointers, res)
    check_pointers(root, pointers, res)
    check_markdown_headers(root, products, res)
    check_readme(root, products, res)
    if base_sha:
        check_version_bumps(root, products, base_sha, res)
    return res


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    res = run(root, os.environ.get("BASE_SHA", "").strip() or None)
    for w in res.warnings:
        print(f"WARNING: {w}")
    for e in res.errors:
        print(f"ERROR: {e}")
    if res.errors:
        return 1
    n = len(cl.discover(root))
    print(f"OK: {n} product(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

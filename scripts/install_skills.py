#!/usr/bin/env python3
# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Install IBM product skills from this repository into a coding agent.

Run from a clone of the repository (standard-library Python 3.9+, no setup):

    git clone https://github.com/IBM/agentic-ai-labs-skills.git
    python3 agentic-ai-labs-skills/scripts/install_skills.py --list
    python3 agentic-ai-labs-skills/scripts/install_skills.py --agent bob --product sovereign-core

Agents (project scope paths; --scope user installs under your home directory):
    bob     .bob/skills          kiro    .kiro/skills       cline  .cline/skills
    claude  .claude/skills       agents  .agents/skills (shared folder read by
                                         Codex, Copilot, Cursor, opencode, ...)
or --dest DIR for any other skills folder.

Safety rules:
- Only the selected skill folders are ever written; nothing else is touched.
- A copy this installer put there and you have not edited is upgraded in place.
- A copy you edited, or one it did not install, is skipped with a warning
  unless you pass --force; then the old copy is backed up first.
- Bookkeeping and backups live in a sibling folder (e.g. .bob/.agentic-ai-labs/),
  never inside the skills folder, so agents never load them as skills.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_WARNINGS = 2

AGENT_DIRS = {
    "bob": ".bob/skills",
    "kiro": ".kiro/skills",
    "cline": ".cline/skills",
    "claude": ".claude/skills",
    "agents": ".agents/skills",
}
STATE_DIR = ".agentic-ai-labs"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class InstallError(Exception):
    pass


# --- source discovery (stdlib only; mirrors scripts/catalog_lib.py) ----------

def load_catalog(source_root: Path):
    products = {}
    for pdir in sorted((source_root / "products").glob("*/")):
        manifest_path = pdir / "plugin.json"
        if not manifest_path.is_file():
            continue
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        skills = []
        for sdir in sorted((pdir / "skills").glob("*/")):
            if (sdir / "SKILL.md").is_file():
                skills.append(sdir)
        products[pdir.name] = {
            "name": manifest.get("name", pdir.name),
            "version": manifest.get("version", "0.0.0"),
            "skills": skills,
        }
    pointers = []
    ptr_path = source_root / "catalog" / "pointers.json"
    if ptr_path.is_file():
        with open(ptr_path, encoding="utf-8") as fh:
            data = json.load(fh)
        pointers = data.get("pointers", []) if isinstance(data, dict) else data
    return products, pointers


def dir_sha256(path: Path) -> str:
    """Hash every file in a skill directory (relative path, exec bit, bytes)."""
    h = hashlib.sha256()
    for f in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = f.relative_to(path).as_posix()
        mode = "x" if os.access(f, os.X_OK) else "-"
        h.update(f"{rel}\0{mode}\0{hashlib.sha256(f.read_bytes()).hexdigest()}\n".encode())
    return h.hexdigest()


def check_source_skill(sdir: Path) -> None:
    if not NAME_RE.match(sdir.name):
        raise InstallError(f"refusing skill with unsafe name {sdir.name!r} in {sdir.parent}")
    for dirpath, dirnames, filenames in os.walk(sdir):
        for n in dirnames + filenames:
            p = Path(dirpath) / n
            if p.is_symlink():
                raise InstallError(f"refusing to install {sdir.name}: source contains a symlink ({p})")


# --- install record ---------------------------------------------------------------

def record_path(dest: Path) -> Path:
    return dest.parent / STATE_DIR / f"{dest.name}.install.json"


def load_record(dest: Path) -> tuple[dict, list[str]]:
    path = record_path(dest)
    if not path.is_file():
        return {}, []
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        skills = data.get("skills", {})
        if not isinstance(skills, dict):
            raise ValueError("skills is not an object")
        return skills, []
    except (ValueError, OSError) as exc:
        return {}, [f"install record {path} is unreadable ({exc}); treating existing skills as user-owned"]


def save_record(dest: Path, skills: dict) -> None:
    path = record_path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"version": 1, "skills": skills}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# --- planning ---------------------------------------------------------------------

def resolve_dest(args) -> Path:
    if args.dest:
        return Path(args.dest).expanduser()
    base = Path.home() if args.scope == "user" else Path(args.project_dir)
    return base / AGENT_DIRS[args.agent]


def select(products: dict, pointers: list, wanted: list[str], all_: bool):
    """Return (skill dirs with their product, pointer entries to print)."""
    if all_:
        chosen = list(products)
        ptrs = []
    else:
        by_name = {info["name"]: slug for slug, info in products.items()}
        chosen, ptrs, unknown = [], [], []
        for w in wanted:
            slug = w if w in products else by_name.get(w)
            matched_ptrs = [p for p in pointers if w == p.get("name") or w in p.get("products", [])]
            if slug:
                chosen.append(slug)
            elif matched_ptrs:
                ptrs.extend(matched_ptrs)
            else:
                unknown.append(w)
        if unknown:
            known = ", ".join(sorted(products)) or "(none)"
            raise InstallError(f"unknown product(s): {', '.join(unknown)}. Known products: {known}")
    skills = []
    for slug in dict.fromkeys(chosen):
        for sdir in products[slug]["skills"]:
            skills.append((slug, products[slug]["version"], sdir))
    return skills, ptrs


def check_dest(dest: Path, source_root: Path) -> None:
    resolved = dest.resolve()
    products = (source_root / "products").resolve()
    if resolved == products or products in resolved.parents:
        raise InstallError(f"refusing to install into the catalog's own products/ folder ({dest})")
    if dest.is_symlink():
        raise InstallError(f"refusing to write through symlinked skills folder {dest}")
    if dest.exists() and not dest.is_dir():
        raise InstallError(f"{dest} exists and is not a directory")


# --- actions ----------------------------------------------------------------------

def _copy_in(src: Path, dest: Path, name: str) -> None:
    """Copy src to dest/name atomically (temp dir in the state folder, then rename)."""
    staging = dest.parent / STATE_DIR / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f"{name}-", dir=staging))
    try:
        shutil.copytree(src, tmp / name, symlinks=True)
        target = dest / name
        if target.exists():
            old = Path(tempfile.mkdtemp(prefix=f"{name}-old-", dir=staging))
            os.replace(target, old / name)
            os.replace(tmp / name, target)
            shutil.rmtree(old)
        else:
            os.replace(tmp / name, target)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _backup(dest: Path, name: str, stamp: str) -> Path:
    backups = dest.parent / STATE_DIR / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    # Unique per run and skill, even for two runs within the same second.
    backup_root = Path(tempfile.mkdtemp(prefix=f"{stamp}-{name}-", dir=backups))
    target = backup_root / name
    shutil.copytree(dest / name, target, symlinks=True)
    return target


def install(args) -> int:
    source_root = Path(args.source_root).resolve()
    products, pointers = load_catalog(source_root)

    if args.list:
        for slug, info in products.items():
            print(f"{slug} ({info['name']} v{info['version']}): " + ", ".join(s.name for s in info["skills"]))
        for p in pointers:
            print(f"[pointer] {p.get('name')} ({', '.join(p.get('products', []))}): {p.get('url')} ({p.get('license')})")
        return EXIT_OK

    if not args.all and not args.product:
        raise InstallError("choose --product NAME (repeatable) or --all; use --list to see products")
    if not args.dest and not args.agent:
        raise InstallError("choose --agent or --dest")

    selected, ptrs = select(products, pointers, args.product or [], args.all)
    # Validate everything before writing anything.
    for _, _, sdir in selected:
        check_source_skill(sdir)
    dest = resolve_dest(args)
    check_dest(dest, source_root)
    for _, _, sdir in selected:
        target = dest / sdir.name
        if target.is_symlink():
            raise InstallError(f"refusing to write through symlinked skill folder {target}")

    for p in ptrs:
        print(f"{p.get('name')}: not redistributed here ({p.get('license')}); install it from "
              f"{p.get('url')} (path {p.get('path')})")
    if not selected:
        return EXIT_OK

    record, warnings = load_record(dest)
    for w in warnings:
        print(f"WARNING: {w}")
    stamp = _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    exit_code = EXIT_OK
    changed = False
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    for slug, version, sdir in selected:
        name = sdir.name
        target = dest / name
        src_hash = dir_sha256(sdir)
        entry = {"product": slug, "product_version": version, "sha256": src_hash}
        if not target.exists():
            action = "install"
        else:
            installed_hash = dir_sha256(target)
            rec = record.get(name)
            if rec and rec.get("sha256") == installed_hash:
                action = "skip" if installed_hash == src_hash else "upgrade"
            elif installed_hash == src_hash:
                action = "adopt"
            elif args.force:
                action = "replace"
            else:
                print(f"WARNING: {target} differs from the catalog copy and was edited locally or not "
                      f"installed by this tool; left untouched (use --force to back it up and replace it)")
                exit_code = EXIT_WARNINGS
                continue

        verb = {"install": "installed", "upgrade": "upgraded", "skip": "up to date",
                "adopt": "already identical; now tracked", "replace": "replaced (backup kept)"}[action]
        if args.dry_run:
            print(f"[dry-run] {name}: would be {verb.split(' (')[0]}")
            continue
        if action == "replace":
            backup = _backup(dest, name, stamp)
            print(f"{name}: backed up to {backup}")
        if action in ("install", "upgrade", "replace"):
            _copy_in(sdir, dest, name)
        if action != "skip" or record.get(name, {}).get("product_version") != version:
            record[name] = entry
            changed = True
        print(f"{name}: {verb}")

    if changed and not args.dry_run:
        save_record(dest, record)
    staging = dest.parent / STATE_DIR / "staging"
    if staging.is_dir() and not any(staging.iterdir()):
        staging.rmdir()
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Install IBM product skills from this repository into a coding agent.",
        epilog="Run from a clone of the repository. See the module docstring for safety rules.",
    )
    target = ap.add_mutually_exclusive_group()
    target.add_argument("--agent", choices=sorted(AGENT_DIRS), help="target agent")
    target.add_argument("--dest", help="explicit skills folder to install into")
    ap.add_argument("--scope", choices=("project", "user"), default="project",
                    help="project (default, under --project-dir) or user (under your home directory)")
    ap.add_argument("--project-dir", default=os.getcwd(), help="project folder for project scope (default: cwd)")
    ap.add_argument("--product", action="append", help="product folder or plugin name (repeatable)")
    ap.add_argument("--all", action="store_true", help="install every product")
    ap.add_argument("--list", action="store_true", help="list products, skills and pointer entries")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen without writing")
    ap.add_argument("--force", action="store_true", help="replace edited or untracked copies (after backup)")
    ap.add_argument("--source-root", default=str(Path(__file__).resolve().parent.parent),
                    help=argparse.SUPPRESS)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return install(args)
    except (InstallError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())

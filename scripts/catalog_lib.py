# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Shared discovery and parsing for the skills catalog.

The catalog contract is documented in docs/catalog-metadata.md. In short:

- products/<slug>/plugin.json     Agent Plugins manifest (one per product)
- products/<slug>/skills/<name>/  one skill: SKILL.md + catalog-entry.json
- catalog/pointers.json           link-only upstream entries (never copied)
- catalog/owners.json             hand-maintained upstream owners/trackers

Used by the maintainer tools (validate, build_catalog, check_drift). The
installer deliberately does NOT import this module: it must run on a bare
python3 without PyYAML.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
EXTENSION_KEY = "com.ibm.agentic-ai-labs"
MARKETPLACE_NAME = "agentic-ai-labs"

# Agents a verification can be recorded for.
AGENTS = ("claude-code", "codex", "bob", "copilot", "cursor")

# Licenses whose content may be copied into this repository (R10).
PERMISSIVE_LICENSES = frozenset(
    {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD"}
)

# Top-level SKILL.md frontmatter keys allowed by the Agent Skills spec.
SPEC_FRONTMATTER_KEYS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)

# The fixed live-system guardrail heading (R6). Matched as a whole line.
GUARDRAIL_HEADING = "## Confirm before changing live systems"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
GITHUB_URL_RE = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")
VERIFIED_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})@(.+)$")

ENTRY_FILE = "catalog-entry.json"


@dataclass
class Skill:
    product: "Product"
    name: str  # directory name
    path: Path  # skill directory
    frontmatter: dict | None = None
    body: str = ""
    entry: dict | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def rel(self) -> str:
        return self.path.relative_to(self.product.root).as_posix()

    @property
    def status(self) -> str | None:
        return (self.entry or {}).get("status")


@dataclass
class Product:
    root: Path  # repository root
    slug: str
    path: Path
    manifest: dict | None = None
    skills: list[Skill] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def name(self) -> str | None:
        return (self.manifest or {}).get("name")

    @property
    def version(self) -> str | None:
        return (self.manifest or {}).get("version")

    @property
    def extension(self) -> dict:
        return ((self.manifest or {}).get("extensions") or {}).get(EXTENSION_KEY) or {}


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_text, body). frontmatter_text is None if absent."""
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def parse_semver(v: str) -> tuple[int, int, int] | None:
    m = SEMVER_RE.match(v or "")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_skill(product: Product, skill_dir: Path) -> Skill:
    skill = Skill(product=product, name=skill_dir.name, path=skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    fm_text, skill.body = split_frontmatter(text)
    if fm_text is None:
        skill.errors.append("SKILL.md has no YAML front matter")
    else:
        try:
            fm = yaml.safe_load(fm_text)
        except yaml.YAMLError as exc:
            skill.errors.append(f"SKILL.md front matter is not valid YAML: {exc}")
            fm = None
        if fm is not None and not isinstance(fm, dict):
            skill.errors.append("SKILL.md front matter must be a mapping")
            fm = None
        skill.frontmatter = fm
    entry_path = skill_dir / ENTRY_FILE
    if entry_path.is_file():
        try:
            skill.entry = load_json(entry_path)
        except ValueError as exc:
            skill.errors.append(f"{ENTRY_FILE} is not valid JSON: {exc}")
    return skill


def discover(root: Path) -> list[Product]:
    """Load every product folder and its skills under root/products."""
    products = []
    for pdir in sorted((root / "products").glob("*/")):
        product = Product(root=root, slug=pdir.name, path=pdir)
        manifest_path = pdir / "plugin.json"
        if manifest_path.is_file():
            try:
                product.manifest = load_json(manifest_path)
            except ValueError as exc:
                product.errors.append(f"plugin.json is not valid JSON: {exc}")
        else:
            product.errors.append("missing plugin.json")
        for sdir in sorted((pdir / "skills").glob("*/")):
            # Only immediate children with a SKILL.md are skills (Agent
            # Plugins discovery rule); anything else (e.g. local eval
            # workspaces) is ignored.
            if (sdir / "SKILL.md").is_file():
                product.skills.append(load_skill(product, sdir))
        products.append(product)
    return products


def load_pointers(root: Path) -> list[dict]:
    path = root / "catalog" / "pointers.json"
    if not path.is_file():
        return []
    data = load_json(path)
    return data.get("pointers", []) if isinstance(data, dict) else data


def load_owners(root: Path) -> dict:
    path = root / "catalog" / "owners.json"
    if not path.is_file():
        return {}
    data = load_json(path)
    return data.get("upstreams", {}) if isinstance(data, dict) else {}


def is_git_repo(root: Path) -> bool:
    return (root / ".git").exists()


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def tracked_files(root: Path, under: Path | None = None) -> list[Path]:
    """Files tracked by git (or every file, when root is not a git repo).

    Restricting to tracked files keeps local-only artifacts (eval workspaces,
    caches) out of validation and hashing.
    """
    base = under or root
    if is_git_repo(root):
        rel = base.relative_to(root).as_posix() if base != root else "."
        out = git(root, "ls-files", "-z", "--", rel).stdout
        return sorted(root / p for p in out.split("\0") if p)
    files = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.startswith(".git")]
        files.extend(Path(dirpath) / f for f in filenames)
    return sorted(files)


def content_sha256(root: Path, skill_dir: Path) -> str:
    """Hash a skill directory's content, excluding its catalog entry.

    Covers each file's relative path, executable bit, and bytes, so renames,
    chmod +x, and edits all change the hash.
    """
    h = hashlib.sha256()
    for f in tracked_files(root, skill_dir):
        rel = f.relative_to(skill_dir).as_posix()
        if rel == ENTRY_FILE or f.is_symlink() or not f.is_file():
            continue
        mode = "x" if os.access(f, os.X_OK) else "-"
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        h.update(f"{rel}\0{mode}\0{digest}\n".encode())
    return h.hexdigest()


def parse_github_url(url: str) -> tuple[str, str] | None:
    m = GITHUB_URL_RE.match(url or "")
    return (m.group(1), m.group(2)) if m else None


def _main(argv: list[str]) -> int:
    """`uv run scripts/catalog_lib.py hash <skill dir>` prints content_sha256."""
    if len(argv) != 2 or argv[0] != "hash":
        print("usage: catalog_lib.py hash <skill directory>")
        return 2
    root = Path(__file__).resolve().parent.parent
    skill_dir = Path(argv[1]).resolve()
    print(content_sha256(root, skill_dir))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(_main(sys.argv[1:]))

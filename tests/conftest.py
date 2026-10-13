# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Shared fixtures: build small catalog trees on disk for tooling tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

HEADER = (
    "<!-- Copyright contributors to the Agentic AI Labs project -->\n"
    "<!-- SPDX-License-Identifier: Apache-2.0 -->\n"
)
GUARDRAIL = (
    "## Confirm before changing live systems\n\n"
    "Before running any command that creates, changes, or deletes resources "
    "in a live environment, state what it will do and wait for the user's "
    "explicit approval.\n"
)
MIT_TEXT = "MIT License\n\nPermission is hereby granted, free of charge...\n"


class Repo:
    """Builder for a minimal catalog repository rooted at `root`."""

    def __init__(self, root: Path):
        self.root = root
        (root / ".claude-plugin").mkdir(parents=True)
        self.market = {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "agentic-ai-labs",
            "owner": {"name": "Agentic AI Labs"},
            "plugins": [],
        }
        self.readme_rows: list[str] = []
        self._flush()

    # -- low level -----------------------------------------------------
    def write(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def write_json(self, rel: str, data) -> Path:
        return self.write(rel, json.dumps(data, indent=2) + "\n")

    def _flush(self):
        self.write_json(".claude-plugin/marketplace.json", self.market)
        rows = "\n".join(self.readme_rows)
        self.write("README.md", f"{HEADER}\n# Catalog\n\n| Skill | Description |\n|---|---|\n{rows}\n")

    # -- products and skills --------------------------------------------
    def product(self, slug: str, name: str | None = None, version: str = "1.0.0",
                license: str = "Apache-2.0", register: bool = True, **extra) -> Path:
        name = name or slug
        manifest = {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": name,
            "version": version,
            "description": f"IBM {slug} skills for coding agents.",
            "license": license,
            "extensions": {"com.ibm.agentic-ai-labs": {"displayName": slug.title(), "category": "Data"}},
        }
        manifest.update(extra)
        self.write_json(f"products/{slug}/plugin.json", manifest)
        self.write(f"products/{slug}/README.md", f"{HEADER}\n# {slug}\n")
        if register:
            self.market["plugins"].append(
                {"name": name, "description": manifest["description"],
                 "source": f"./products/{slug}", "version": version}
            )
            self.readme_rows.append(f"| [`{name}`](products/{slug}) | {slug} |")
            self._flush()
        return self.root / "products" / slug

    def skill(self, product: str, name: str, *, description: str | None = None,
              frontmatter_extra: str = "", body: str = "Do the thing.\n",
              header: bool = True, entry: dict | None = None) -> Path:
        description = description or f"Use when building applications against IBM {product} ({name})."
        fm = f"---\nname: {name}\ndescription: {description}\n{frontmatter_extra}---\n"
        text = fm + (HEADER if header else "") + f"\n# {name}\n\n" + body
        sdir = self.root / "products" / product / "skills" / name
        self.write(f"products/{product}/skills/{name}/SKILL.md", text)
        if entry is None:
            entry = {"status": "maintained", "changes_live_systems": False, "verified": {}}
        if entry is not False:
            self.write_json(f"products/{product}/skills/{name}/catalog-entry.json", entry)
        return sdir

    def imported_skill(self, product: str, name: str, *, license: str = "MIT",
                       files: dict[str, str] | None = None, entry_overrides: dict | None = None,
                       body: str = "Upstream instructions.\n", license_file: bool = True) -> Path:
        """Create an imported skill whose content hash matches its entry."""
        import catalog_lib

        sdir = self.skill(product, name, header=False, body=body, entry=False)
        if license_file:
            self.write(f"products/{product}/skills/{name}/LICENSE", MIT_TEXT)
        for rel, text in (files or {}).items():
            self.write(f"products/{product}/skills/{name}/{rel}", text)
        entry = {
            "status": "imported",
            "upstream": {
                "url": "https://github.com/example-org/example-skills",
                "path": f"skills/{name}",
                "ref": "a" * 40,
            },
            "license": license,
            "authors": ["Example Org"],
            "content_sha256": catalog_lib.content_sha256(self.root, sdir),
            "modified": False,
            "modifications": [],
            "security_review": {"reviewer": "maintainer", "date": "2026-10-12", "notes": "ok"},
            "security_allowlist": [],
            "changes_live_systems": False,
            "verified": {},
        }
        entry.update(entry_overrides or {})
        self.write_json(f"products/{product}/skills/{name}/catalog-entry.json", entry)
        return sdir

    def pointers(self, entries: list[dict]):
        self.write_json("catalog/pointers.json", {"pointers": entries})


@pytest.fixture
def repo(tmp_path) -> Repo:
    return Repo(tmp_path / "repo")


@pytest.fixture
def guardrail() -> str:
    return GUARDRAIL

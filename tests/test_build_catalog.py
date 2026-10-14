# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Catalog generator: golden outputs, status rendering, pointers, --check."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import build_catalog

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "golden"
REPO_ROOT = Path(__file__).resolve().parent.parent

POINTER = {
    "name": "terraform-module-authoring",
    "url": "https://github.com/example-org/terraform-skills",
    "path": "skills/module-authoring",
    "ref": "c" * 40,
    "license": "MPL-2.0",
    "reason": "MPL-2.0 is not on the permissive list",
    "products": ["terraform"],
}


def sample(repo):
    """Two products, one maintained skill each, one import, one pointer."""
    repo.product("db2", version="1.2.0", author={"name": "Agentic AI Labs"})
    repo.skill("db2", "db2-build", entry={
        "status": "maintained", "changes_live_systems": False,
        "verified": {"bob": "2026-10-10@1.2.0", "claude-code": "2026-09-01@1.1.0"},
    })
    repo.product("confluent", version="1.0.0")
    repo.imported_skill("confluent", "kafka-streams")
    repo.pointers([POINTER])
    repo.write_json("catalog/owners.json", {"upstreams": {
        "example-org/example-skills": {"maintainer": "Example Org", "tracker": "https://github.com/example-org/example-skills/issues"},
    }})
    return repo


def test_golden_outputs(repo):
    files = build_catalog.build(sample(repo).root)
    if os.environ.get("UPDATE_GOLDEN"):
        for rel, content in files.items():
            p = GOLDEN / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
    for rel, content in files.items():
        expected = (GOLDEN / rel).read_text(encoding="utf-8")
        assert content == expected, f"{rel} differs from golden (UPDATE_GOLDEN=1 to refresh after review)"


def test_output_is_deterministic(repo):
    root = sample(repo).root
    assert build_catalog.build(root) == build_catalog.build(root)


def test_ae3_verified_in_bob_only_shows_codex_unverified(repo):
    repo.product("db2")
    repo.skill("db2", "db2-build", entry={"status": "maintained", "changes_live_systems": False,
                                          "verified": {"bob": "2026-10-10@1.0.0"}})
    md = build_catalog.build(repo.root)["CATALOG.md"]
    row = next(line for line in md.splitlines() if "`db2-build`" in line)
    assert "Bob ✓" in row and "Codex" not in row


def test_stale_verification_is_marked(repo):
    sample(repo)
    md = build_catalog.build(repo.root)["CATALOG.md"]
    row = next(line for line in md.splitlines() if "`db2-build`" in line)
    assert "Claude Code (stale: 1.1.0)" in row and "Bob ✓" in row


def test_ae1_pointer_is_listed_but_never_installable(repo):
    files = build_catalog.build(sample(repo).root)
    assert "terraform-module-authoring" in files["CATALOG.md"]
    assert "terraform-module-authoring" not in files["THIRD_PARTY_NOTICES.md"]
    assert "terraform-module-authoring" not in files[".claude-plugin/marketplace.json"]
    assert "terraform-module-authoring" not in files[".agents/plugins/marketplace.json"]
    assert "example-org/terraform-skills" in files["UPSTREAMS.md"]


def test_import_appears_in_notices_with_license_and_authors(repo):
    notices = build_catalog.build(sample(repo).root)["THIRD_PARTY_NOTICES.md"]
    row = next(line for line in notices.splitlines() if "kafka-streams" in line)
    assert "MIT" in row and "Example Org" in row and "aaaaaaaaaaaa" in row


def test_codex_entries_include_required_fields(repo):
    market = json.loads(build_catalog.build(sample(repo).root)[".agents/plugins/marketplace.json"])
    assert market["name"] == "agentic-ai-labs" and market["interface"]["displayName"]
    for entry in market["plugins"]:
        assert entry["source"]["source"] == "local" and entry["source"]["path"].startswith("./products/")
        assert entry["policy"]["installation"] and entry["policy"]["authentication"]
        assert entry["category"]


def test_plugin_names_identical_across_catalogs(repo):
    files = build_catalog.build(sample(repo).root)
    claude = {e["name"] for e in json.loads(files[".claude-plugin/marketplace.json"])["plugins"]}
    codex = {e["name"] for e in json.loads(files[".agents/plugins/marketplace.json"])["plugins"]}
    assert claude == codex == {"db2", "confluent"}


def test_product_without_skills_fails(repo):
    repo.product("db2")
    with pytest.raises(build_catalog.BuildError, match="no skills"):
        build_catalog.build(repo.root)


def test_check_detects_hand_edited_marketplace(repo):
    root = sample(repo).root
    build_catalog.write(root)
    assert build_catalog.stale_files(root) == []
    path = root / ".claude-plugin" / "marketplace.json"
    path.write_text(path.read_text().replace("Agentic AI Labs", "Someone Else"))
    assert build_catalog.stale_files(root) == [".claude-plugin/marketplace.json"]


def test_generated_markdown_has_headers(repo):
    files = build_catalog.build(sample(repo).root)
    for rel in ("CATALOG.md", "THIRD_PARTY_NOTICES.md", "UPSTREAMS.md"):
        assert "SPDX-License-Identifier: Apache-2.0" in files[rel].splitlines()[1]


def test_real_repository_catalog_is_current():
    assert build_catalog.stale_files(REPO_ROOT) == []

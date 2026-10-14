# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Installer: install, upgrade, user edits, safety refusals, pointers."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import install_skills as inst


@pytest.fixture
def src(repo):
    """A source catalog: db2 (two skills), sovereign-core (one), one pointer."""
    repo.product("db2", version="1.0.0")
    repo.skill("db2", "db2-build")
    repo.skill("db2", "db2-ops", body="## Confirm before changing live systems\n\nAsk first.\n",
               entry={"status": "maintained", "changes_live_systems": True, "verified": {}})
    repo.product("sovereign-core", version="1.0.0")
    repo.skill("sovereign-core", "sovereign-core-ops")
    repo.pointers([{
        "name": "terraform-module-authoring", "url": "https://github.com/example-org/tf",
        "path": "skills/mod", "ref": "c" * 40, "license": "MPL-2.0",
        "reason": "MPL-2.0", "products": ["terraform"],
    }])
    return repo.root


@pytest.fixture
def project(tmp_path):
    p = tmp_path / "project"
    p.mkdir()
    return p


def run(src, project, *args):
    return inst.main(["--source-root", str(src), "--project-dir", str(project), *args])


def skills_in(d: Path) -> set[str]:
    return {c.name for c in d.iterdir()} if d.is_dir() else set()


# --- happy paths ---------------------------------------------------------------------

def test_install_one_product_into_bob_project(src, project):
    assert run(src, project, "--agent", "bob", "--product", "db2") == 0
    assert skills_in(project / ".bob" / "skills") == {"db2-build", "db2-ops"}
    assert (project / ".bob" / "skills" / "db2-build" / "SKILL.md").is_file()
    assert (project / ".bob" / "skills" / "db2-build" / "catalog-entry.json").is_file()
    record = json.loads((project / ".bob" / ".agentic-ai-labs" / "skills.install.json").read_text())
    assert set(record["skills"]) == {"db2-build", "db2-ops"}


def test_install_all_into_shared_agents_folder(src, project):
    assert run(src, project, "--agent", "agents", "--all") == 0
    assert skills_in(project / ".agents" / "skills") == {"db2-build", "db2-ops", "sovereign-core-ops"}


def test_product_selected_by_plugin_name_or_slug(src, project):
    assert run(src, project, "--agent", "kiro", "--product", "sovereign-core") == 0
    assert skills_in(project / ".kiro" / "skills") == {"sovereign-core-ops"}


def test_user_scope_resolves_under_home(src, project, tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    assert run(src, project, "--agent", "cline", "--scope", "user", "--product", "db2") == 0
    assert skills_in(home / ".cline" / "skills") == {"db2-build", "db2-ops"}
    assert not (project / ".cline").exists()


def test_explicit_dest_is_created(src, project, tmp_path):
    dest = tmp_path / "custom" / "skills"
    assert run(src, project, "--dest", str(dest), "--product", "db2") == 0
    assert skills_in(dest) == {"db2-build", "db2-ops"}


def test_dry_run_writes_nothing(src, project):
    assert run(src, project, "--agent", "bob", "--product", "db2", "--dry-run") == 0
    assert not (project / ".bob").exists()


# --- idempotency and upgrade -------------------------------------------------------------

def test_rerun_without_changes_writes_nothing(src, project):
    run(src, project, "--agent", "bob", "--product", "db2")
    skill_md = project / ".bob" / "skills" / "db2-build" / "SKILL.md"
    before = skill_md.stat().st_mtime_ns
    assert run(src, project, "--agent", "bob", "--product", "db2") == 0
    assert skill_md.stat().st_mtime_ns == before


def test_unmodified_copy_upgrades_silently(src, project):
    run(src, project, "--agent", "bob", "--product", "db2")
    (src / "products/db2/skills/db2-build/SKILL.md").write_text(
        (src / "products/db2/skills/db2-build/SKILL.md").read_text() + "\nNew guidance.\n")
    assert run(src, project, "--agent", "bob", "--product", "db2") == 0
    assert "New guidance." in (project / ".bob/skills/db2-build/SKILL.md").read_text()
    assert not (project / ".bob" / ".agentic-ai-labs" / "backups").exists()


# --- user edits and --force ---------------------------------------------------------------

def test_user_modified_copy_is_left_untouched(src, project):
    run(src, project, "--agent", "bob", "--product", "db2")
    installed = project / ".bob/skills/db2-build/SKILL.md"
    installed.write_text(installed.read_text() + "\nMy local tweak.\n")
    (src / "products/db2/skills/db2-build/SKILL.md").write_text("---\nname: db2-build\ndescription: v2\n---\nv2\n")
    assert run(src, project, "--agent", "bob", "--product", "db2") == inst.EXIT_WARNINGS
    assert "My local tweak." in installed.read_text()


def test_force_backs_up_outside_skills_folder(src, project):
    run(src, project, "--agent", "bob", "--product", "db2")
    installed = project / ".bob/skills/db2-build/SKILL.md"
    installed.write_text(installed.read_text() + "\nMy local tweak.\n")
    (src / "products/db2/skills/db2-build/SKILL.md").write_text("---\nname: db2-build\ndescription: v2\n---\nv2\n")
    assert run(src, project, "--agent", "bob", "--product", "db2", "--force") == 0
    assert installed.read_text().endswith("v2\n")
    assert skills_in(project / ".bob/skills") == {"db2-build", "db2-ops"}  # exactly one db2-build
    backups = list((project / ".bob/.agentic-ai-labs/backups").rglob("SKILL.md"))
    assert len(backups) == 1 and "My local tweak." in backups[0].read_text()


def test_preexisting_skill_without_record_is_user_owned(src, project):
    mine = project / ".bob/skills/db2-build"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("---\nname: db2-build\ndescription: mine\n---\nmine\n")
    assert run(src, project, "--agent", "bob", "--product", "db2") == inst.EXIT_WARNINGS
    assert (mine / "SKILL.md").read_text().endswith("mine\n")
    assert (project / ".bob/skills/db2-ops/SKILL.md").is_file()  # other skill still installed


def test_identical_preexisting_copy_is_adopted(src, project):
    run(src, project, "--agent", "bob", "--product", "db2")
    (project / ".bob/.agentic-ai-labs/skills.install.json").unlink()
    assert run(src, project, "--agent", "bob", "--product", "db2") == 0
    record = json.loads((project / ".bob/.agentic-ai-labs/skills.install.json").read_text())
    assert "db2-build" in record["skills"]


def test_corrupted_record_is_treated_as_unknown_origin(src, project):
    run(src, project, "--agent", "bob", "--product", "db2")
    installed = project / ".bob/skills/db2-build/SKILL.md"
    installed.write_text(installed.read_text() + "\nlocal\n")
    (project / ".bob/.agentic-ai-labs/skills.install.json").write_text("{not json")
    assert run(src, project, "--agent", "bob", "--product", "db2") == inst.EXIT_WARNINGS
    assert installed.read_text().endswith("local\n")


def test_other_user_skills_never_touched(src, project):
    other = project / ".bob/skills/my-own-skill"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("mine")
    (project / ".bob/skills/notes.txt").write_text("keep")
    run(src, project, "--agent", "bob", "--all", "--force")
    assert (other / "SKILL.md").read_text() == "mine"
    assert (project / ".bob/skills/notes.txt").read_text() == "keep"


# --- refusals: nothing is written ---------------------------------------------------------

def test_unknown_product_fails_before_writing(src, project):
    assert run(src, project, "--agent", "bob", "--product", "db2", "--product", "nope") == inst.EXIT_ERROR
    assert not (project / ".bob").exists()


def test_unknown_agent_fails(src, project):
    with pytest.raises(SystemExit):
        run(src, project, "--agent", "emacs", "--all")


def test_source_symlink_is_refused(src, project, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("do not copy")
    os.symlink(secret, src / "products/db2/skills/db2-build/link.txt")
    assert run(src, project, "--agent", "bob", "--product", "db2") == inst.EXIT_ERROR
    assert not (project / ".bob").exists()


def test_symlinked_destination_skill_dir_is_refused(src, project, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (project / ".bob/skills").mkdir(parents=True)
    os.symlink(elsewhere, project / ".bob/skills/db2-build")
    assert run(src, project, "--agent", "bob", "--product", "db2", "--force") == inst.EXIT_ERROR
    assert list(elsewhere.iterdir()) == []


def test_symlinked_skills_folder_is_refused(src, project, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (project / ".bob").mkdir()
    os.symlink(elsewhere, project / ".bob/skills")
    assert run(src, project, "--agent", "bob", "--product", "db2") == inst.EXIT_ERROR
    assert list(elsewhere.iterdir()) == []


def test_skill_name_with_separator_is_refused(src, project):
    bad = src / "products/db2/skills/..evil"
    bad.mkdir()
    (bad / "SKILL.md").write_text("x")
    assert run(src, project, "--agent", "bob", "--product", "db2") == inst.EXIT_ERROR
    assert not (project / ".bob").exists()


def test_pointer_prints_link_and_copies_nothing(src, project, capsys):
    assert run(src, project, "--agent", "bob", "--product", "terraform") == 0
    out = capsys.readouterr().out
    assert "https://github.com/example-org/tf" in out
    assert not (project / ".bob").exists()


def test_list_mode(src, project, capsys):
    assert run(src, project, "--list") == 0
    out = capsys.readouterr().out
    assert "db2" in out and "sovereign-core-ops" in out and "terraform-module-authoring" in out

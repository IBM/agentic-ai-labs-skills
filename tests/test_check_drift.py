# Copyright contributors to the Agentic AI Labs project
# SPDX-License-Identifier: Apache-2.0
"""Drift checker against a mocked GitHub API."""
from __future__ import annotations

import check_drift as cd

PIN = "a" * 40
LATEST = "b" * 40
REPO_API = "https://api.github.com/repos/example-org/example-skills"


class FakeGitHub:
    """Minimal GitHub API: one repo, configurable commits/paths/compare."""

    def __init__(self, *, pin_exists=True, path_exists=True, latest=LATEST,
                 compare_status="ahead", fail_with=None, default_branch="main"):
        self.pin_exists, self.path_exists = pin_exists, path_exists
        self.latest, self.compare_status = latest, compare_status
        self.fail_with, self.default_branch = fail_with, default_branch
        self.calls: list[str] = []

    def __call__(self, url):
        self.calls.append(url)
        if self.fail_with:
            return self.fail_with, {"message": "API rate limit exceeded"}
        if url == REPO_API:
            return 200, {"default_branch": self.default_branch}
        if url.startswith(f"{REPO_API}/commits/"):
            return (200, {"sha": PIN}) if self.pin_exists else (404, {"message": "No commit found"})
        if url.startswith(f"{REPO_API}/contents/"):
            return (200, []) if self.path_exists else (404, {"message": "Not Found"})
        if url.startswith(f"{REPO_API}/commits?"):
            return 200, ([{"sha": self.latest}] if self.latest else [])
        if url.startswith(f"{REPO_API}/compare/"):
            return 200, {"status": self.compare_status, "ahead_by": 3}
        return 404, {"message": f"unexpected {url}"}


def imported(repo, **over):
    repo.product("confluent")
    repo.imported_skill("confluent", "kafka-streams", entry_overrides={
        "upstream": {"url": "https://github.com/example-org/example-skills", "path": "skills/kafka-streams", "ref": PIN},
        **over,
    })
    return repo.root


def only(outcomes):
    assert len(outcomes) == 1
    return outcomes[0]


def test_pin_equal_to_latest_path_commit_is_current(repo):
    o = only(cd.run(imported(repo), FakeGitHub(latest=PIN)))
    assert o.category == "current"


def test_pin_newer_than_last_path_change_is_current(repo):
    """Pin at repo HEAD (newer than the last commit touching the path): not drift."""
    o = only(cd.run(imported(repo), FakeGitHub(compare_status="behind")))
    assert o.category == "current"


def test_ae4_newer_commit_on_path_is_drifted_with_compare_link(repo):
    outcomes = cd.run(imported(repo), FakeGitHub(compare_status="ahead"))
    assert only(outcomes).category == "drifted"
    text = cd.report(outcomes)
    assert f"https://github.com/example-org/example-skills/compare/{PIN}...{LATEST}" in text


def test_diverged_history_counts_as_drift(repo):
    assert only(cd.run(imported(repo), FakeGitHub(compare_status="diverged"))).category == "drifted"


def test_pin_missing(repo):
    assert only(cd.run(imported(repo), FakeGitHub(pin_exists=False))).category == "pin missing"


def test_path_deleted_or_renamed_is_path_missing_not_current(repo):
    assert only(cd.run(imported(repo), FakeGitHub(path_exists=False))).category == "path missing"


def test_rate_limit_is_check_failed_never_current(repo):
    outcomes = cd.run(imported(repo), FakeGitHub(fail_with=403))
    assert only(outcomes).category == "check failed"
    assert "rate limit" in only(outcomes).detail


def test_server_error_is_check_failed(repo):
    assert only(cd.run(imported(repo), FakeGitHub(fail_with=502))).category == "check failed"


def test_pointer_entries_are_checked_too(repo):
    repo.product("db2")
    repo.skill("db2", "db2-build")
    repo.pointers([{"name": "tf", "url": "https://github.com/example-org/example-skills", "path": "skills/tf",
                    "ref": PIN, "license": "MPL-2.0", "reason": "MPL", "products": ["terraform"]}])
    o = only(cd.run(repo.root, FakeGitHub(compare_status="ahead")))
    assert o.item.label == "pointer tf" and o.category == "drifted"


def test_non_github_upstream_is_unsupported_and_makes_no_calls(repo):
    root = imported(repo, upstream={"url": "https://gitlab.com/a/b", "path": "p", "ref": PIN})
    gh = FakeGitHub()
    assert only(cd.run(root, gh)).category == "unsupported host"
    assert gh.calls == []


def test_only_api_github_com_is_ever_called(repo):
    gh = FakeGitHub()
    cd.run(imported(repo), gh)
    assert gh.calls and all(u.startswith("https://api.github.com/") for u in gh.calls)


def test_hostile_upstream_text_is_rendered_inert():
    item = cd.Item(label="products/x/skills/`evil`", url="https://github.com/a/b",
                   path="skills/@admin [click](https://phish.example)", ref=PIN)
    text = cd.report([cd.Outcome(item, "path missing", detail="<img src=x onerror=alert(1)> @team")])
    line = next(line for line in text.splitlines() if line.startswith("- "))
    assert "@admin" not in line and "@team" not in line  # mentions neutralised
    assert line.count("`") % 2 == 0  # no unbalanced code spans
    assert "[click](https://phish.example)" in line  # present only inside a code span
    assert "`skills/@​admin [click](https://phish.example)`" in line


def test_report_lists_every_category_with_items(repo):
    o1 = cd.Outcome(cd.Item("a", "https://github.com/a/b", "p", PIN), "drifted", latest=LATEST)
    o2 = cd.Outcome(cd.Item("b", "https://github.com/a/b", "p", PIN), "check failed", "HTTP 502")
    text = cd.report([o1, o2])
    assert "## Drifted" in text and "## Check failed" in text and "1 drifted, 1 check failed" in text

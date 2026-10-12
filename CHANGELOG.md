# Changelog

All notable changes to this project are documented in this file. Plugin
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-10-12

### Added
- `wxo-agent-architect`: slash-command wrapper (`/wxo-agent-architect`).
- IBM detect-secrets pre-commit hook and `.secrets.baseline`.
- Stricter CI validation (`.github/scripts/validate.py`): manifest and plugin
  consistency, license, front matter, file headers, README table, and the
  version-bump rule.

### Changed
- `wxo-agent-architect`: credential health check silently refreshes expired
  tokens and only warns on a dead or missing key.
- Copyright headers now read "Agentic AI Labs project".
- Rewrote `CONTRIBUTING.md`, `SECURITY.md`, and the plugin README for the
  public release.

### Fixed
- `plugin.json` declared the license as MIT; the project is Apache-2.0.

## [1.0.0]

### Added
- Initial release of the `wxo-agent-architect` plugin and the
  `agentic-ai-labs` marketplace.

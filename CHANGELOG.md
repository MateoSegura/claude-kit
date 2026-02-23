# Changelog

All notable changes to claude-kit will be documented in this file.

## [Unreleased]
<!-- Use /bump-plugin to add entries here -->

## [0.0.7] - 2026-02-23

### Added
- `claude-kit list` redesigned — plugins grouped by shared prefix, each group header shows the exact shortcut command (`claude-kit -k <prefix>`), plugin versions shown inline, redundant Shortcuts section removed

## [0.0.6] - 2026-02-23

### Added
- Pretty launch header when starting kits — plugins are grouped by team prefix with role names listed per line, kit/plugin counts shown, and consistent color styling throughout

## [0.0.5] - 2026-02-23

### Fixed
- `claude-kit version` now shows the nearest git tag (e.g. `v0.0.4`) instead of a raw commit hash when HEAD is not exactly on a tagged commit
- `claude-kit update` now shows the version tag after updating instead of the short commit hash
- `claude-kit update` "What's new" section now skips `[Unreleased]` and shows the latest versioned release entry instead of `vUnreleased`
- `install.sh` version display applies the same tag fallback fix
- `git pull` in update now passes `--tags` to ensure new tags are fetched alongside commits

## [0.0.4] - 2026-02-23

### Chore
- Removed `.claude/CLAUDE.md` and migrated all repo rules into `.claude/rules/plugin-conventions.md` for consistency with the modular rules layout

## [0.0.3] - 2026-02-23

### Added
- `.claude/rules/git-workflow.md` — modular rule file teaching Claude the branch → PR → CI → merge → release convention for this repo; loaded automatically by Claude Code alongside `CLAUDE.md`

## [0.0.2] - 2026-02-23

### Fixed
- `claude-kit version` now displays the git tag (e.g. `v0.0.1`) instead of a raw commit hash when HEAD is tagged
- `install.sh` version display likewise shows the tag on install/update

## [0.0.1] - 2026-02-23

### Fixed
- `install.sh` now exits with an error if Claude Code CLI (`claude`) is not found — previously installed silently and crashed at runtime
- `claude-kit --kit` now shows a clear error message instead of a Python traceback when `claude` is not in PATH

## [0.0.0] - 2026-02-23

### Plugins
- **coding-embedded-zephyr-tester** — Complete Zephyr RTOS test engineering plugin with 6 agents (unit-test-writer, integration-test-writer, coverage-analyzer, test-runner, mock-specialist, test-reviewer), 6 skills (ztest-patterns, twister-workflows, coverage-analysis, mock-strategies, test-design-patterns), and 3 commands (test, coverage, scaffold-tests)
- **Hardware communication skills** for Svelte knowledge plugin — 5 new skill directories covering USB/serial/HID, Bluetooth Low Energy, LAN/mDNS discovery, audio/MIDI devices, and hardware abstraction patterns for IoT device communication via Tauri desktop apps
- **system-maker** 0.1.0 — Added `/system-maker:validate` semantic Tier 2-4 plugin review command

### Fixed
- `.lsp.json` format corrected across all Zephyr plugins (server names as top-level keys, added `extensionToLanguage` mapping)
- Read-only agents now use `permissionMode: plan` instead of `default`
- Stop hooks that reference tool usage changed from `prompt` to `agent` type

### Tooling
- **validate-plugins.py** — Tier 1 structural validator (JSON syntax, field names, companion existence, hook script references)
- **CI/CD** — push.yml (fast branch + changed-plugin check), pr.yml (Tier 1 + Claude semantic review with PR comments), weekly.yml (full strict audit), release.yml (gate + GitHub Release)
- **Branch naming enforcement** — push.yml rejects branches that don't match `<type>/<description>`
- **.claude/CLAUDE.md** — Repo-level rules (plugin.json schema, frontmatter keys, script conventions, version strategy)
- **.claude/commands/** — `/validate-all`, `/bump-plugin`, `/release` developer workflow commands
- **docs/plugin-spec.md** — Human-readable plugin specification distilled from system-maker skills

### Plugin Teams
- **Zephyr RTOS** (4 plugins): knowledge, engineer, grader, tester — complete team
- **Svelte Frontend** (4 plugins): knowledge, engineer, grader, tester — complete team
- **System** (3 plugins): core-spec, system-maker, system-updater

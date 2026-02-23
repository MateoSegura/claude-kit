# Changelog

All notable changes to claude-kit will be documented in this file.

## [Unreleased]
<!-- Use /bump-plugin to add entries here -->

## [0.0.14] - 2026-02-23

### Added
- `nightly.yml` CI workflow — runs semantic review of all plugins at 02:00 UTC
  daily; if WARN or FATAL findings exist, Claude auto-fixes them, opens a PR,
  and enables auto-merge so it merges once Tier 1 validation passes
- Detailed version number documentation in `.claude/rules/git-workflow.md`:
  MAJOR/MINOR/PATCH semantics for plugin versions and repo release tags, with
  decision tables and examples

### Changed
- `pr.yml` — removed `claude-validate` job; semantic review (5–10 min, token-
  expensive) is now handled by the nightly workflow instead of every PR; required
  PR gates remain `fast-validate` and `validate-tier1` only

## [0.0.13] - 2026-02-23

### Added
- `README.md` added to all 11 plugins documenting agents (with exact descriptions
  from frontmatter), commands, skill inventories, companion auto-loading, and
  launch instructions
- `.claude/rules/documentation.md` — project rule requiring README updates
  whenever plugin agents, commands, or skills change
- `system-maker` identity skill Phase 11 now generates `README.md` in the staged
  build directory before copying to output — all new plugins ship with docs
- `system-updater` identity skill Phase 7 now regenerates `README.md` from the
  staged plugin's current state before replacing the live plugin

### Changed
- Main README plugins section replaced: verbose 4-column tables swapped for
  one-paragraph team blurbs and a links table pointing to each plugin README
- `claude-validate` CI job no longer uses `if:` condition — always runs and exits
  with success or failure (never skipped); non-plugin PRs exit 0 immediately with
  a "No plugin files changed" message, making the job safe to add as a required
  branch protection check

### Plugin versions
- `system-maker`: 0.1.0 → 0.1.1 (identity skill Phase 11 README generation)
- `system-updater`: 0.0.0 → 0.0.1 (identity skill Phase 7 README regeneration)
- All other plugins: 0.0.0 → 0.0.1 (README doc added)

## [0.0.12] - 2026-02-23

### Added
- Tier 1 validator check 10 (warn): `SKILL.md` files must not exceed 500 lines
- Tier 1 validator check 11 (fatal): agent files must use `tools:` not `allowed-tools:` — catches silent load failures
- Tier 1 validator check 12 (fatal): command files must use `allowed-tools:` not `tools:` — catches silent load failures
- Tier 1 validator check 13 (warn): `ctl.json` role must be a known value
- `push.yml` now prints Python version before syntax check for visibility
- Branch protection rules on `main` now require `fast-validate` and `validate-tier1` to pass before any PR can merge

## [0.0.11] - 2026-02-23

### Fixed
- `system-updater` plugin-structure skill was documenting `role`, `companions`, `author`, `keywords` etc. as valid `plugin.json` optional fields — these cause silent load failures; replaced with the correct CRITICAL warning and `ctl.json` section matching `system-maker`
- `core-spec` was missing `.claude-plugin/ctl.json`; created with `{"role": "system"}`
- `system-maker` and `system-updater` `ctl.json` were missing the `role` field; added `"role": "system"` to both

## [0.0.10] - 2026-02-23

### Fixed
- `claude-kit list` now groups all hyphenated plugin names under their prefix regardless of member count — `core-spec` now correctly appears under `core` instead of as a standalone entry

## [0.0.9] - 2026-02-23

### Added
- `scripts/test-cli.sh` — 20 smoke tests covering help, list, validate, version, and all error/unknown-flag cases; wired into `fast-validate` CI between syntax check and Tier 1 plugin validation

## [0.0.8] - 2026-02-23

### Fixed
- Changelog bullet lines in `claude-kit update` now wrap at 70 chars — no more single-line walls of text
- `SyntaxError` in `claude-kit list` on Python < 3.12 caused by backslash inside f-string expression; fixed by pre-computing the plural suffix
- CI (`fast-validate`) now runs `python3 -m py_compile` on the CLI script first, catching syntax errors on every push before plugin validation

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

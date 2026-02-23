# Changelog

All notable changes to claude-kit will be documented in this file.

## [Unreleased]
### Plugins Changed
- **system-maker** 0.0.0 → 0.1.0 — Added `/system-maker:validate` semantic review command

### Tooling Added
- **validate-plugins.py** — Tier 1 structural validator (JSON syntax, field names, companion existence, hook script references)
- **system-maker:validate** — Semantic Tier 2-4 plugin reviewer command
- **CI workflows** — push.yml (fast check), pr.yml (Tier 1 + Claude review), weekly.yml (full audit), release.yml (gate + GitHub Release)
- **.claude/CLAUDE.md** — Repo-level rules for working in claude-kit
- **.claude/commands/** — `/validate-all`, `/bump-plugin`, `/release` developer commands
- **docs/plugin-spec.md** — Human-readable plugin specification

## [0.0.0] - 2026-02-22

### Added
- **coding-embedded-zephyr-tester** — Complete Zephyr RTOS test engineering plugin with 6 agents (unit-test-writer, integration-test-writer, coverage-analyzer, test-runner, mock-specialist, test-reviewer), 6 skills (ztest-patterns, twister-workflows, coverage-analysis, mock-strategies, test-design-patterns), and 3 commands (test, coverage, scaffold-tests)
- **Hardware communication skills** for Svelte knowledge plugin — 5 new skill directories covering USB/serial/HID, Bluetooth Low Energy, LAN/mDNS discovery, audio/MIDI devices, and hardware abstraction patterns for IoT device communication via Tauri desktop apps
- **Changelog mechanism** — `claude-kit update` now displays a summary of what changed after pulling

### Fixed
- `.lsp.json` format corrected across all Zephyr plugins (server names as top-level keys, added `extensionToLanguage` mapping)
- Read-only agents now use `permissionMode: plan` instead of `default`
- Stop hooks that reference tool usage changed from `prompt` to `agent` type

### Teams
- **Zephyr RTOS** (4 plugins): knowledge, engineer, grader, tester — complete team
- **Svelte Frontend** (4 plugins): knowledge, engineer, grader, tester — complete team
- **System** (3 plugins): core-spec, system-maker, system-updater

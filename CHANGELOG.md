# Changelog

All notable changes to claude-kit will be documented in this file.

## [Unreleased]

## [0.3.4] - 2026-02-24

### Changed
- **Grader report output convention** — all 3 grader plugins now write reports
  to `reports/<YYYY-MM-DD_HH-MM-SS>/` (was `grade-reports/`) and zip all files
  into `contents.zip` for easy transfer to other machines
  - `coding-embedded-zephyr-grader`: 0.1.3 → 0.1.4
  - `coding-frontend-svelte-grader`: 0.0.5 → 0.0.6
  - `coding-cloud-python-grader`: 0.0.5 → 0.0.6
- **Grader report quality** — all 3 grader plugins now include git context
  (branch, commit hash, clean/dirty status) in report headers. Zephyr grader
  HTML template redesigned with professional typography, clean layout, and
  print-friendly CSS (replaces gradient-heavy design)
- **Python grader file output** — `grade` command now writes report.md and
  scorecard.json to disk (was terminal-only), matching zephyr/svelte behavior

### Added
- `.claude/rules/cross-team-consistency.md` — enforces checking all 3 teams
  when fixing bugs in any single team plugin, preventing silent drift

### Fixed
- `coding-embedded-zephyr-engineer`: 0.0.4 → 0.0.5
  - PostToolUse hook scripts (`validate-kconfig.sh`, `validate-dts-overlay.sh`)
    crashed on Edit operations — Edit tool provides `new_string` not `content`,
    causing `grep` to fail on empty input under `set -euo pipefail`
  - Stop hook JSON format prefix added
- Stop hook "JSON validation failed" errors across all 14 team plugins — prompt-type
  Stop hooks returned narrative text instead of valid JSON. Added explicit
  `RESPOND WITH ONLY A JSON OBJECT` prefix to every prompt-type and agent-type
  Stop hook across all 3 teams (zephyr, svelte, python)
  - `coding-cloud-python-debugger`: 0.0.4 → 0.0.5
  - `coding-cloud-python-engineer`: 0.0.4 → 0.0.5
  - `coding-cloud-python-grader`: 0.0.4 → 0.0.5
  - `coding-cloud-python-tester`: 0.0.4 → 0.0.5
  - `coding-embedded-zephyr-debugger`: 0.0.4 → 0.0.5
  - `coding-embedded-zephyr-grader`: 0.1.2 → 0.1.3
  - `coding-embedded-zephyr-knowledge`: 0.1.2 → 0.1.3
  - `coding-embedded-zephyr-tester`: 0.0.4 → 0.0.5
  - `coding-frontend-svelte-debugger`: 0.0.5 → 0.0.6
  - `coding-frontend-svelte-engineer`: 0.0.4 → 0.0.5
  - `coding-frontend-svelte-grader`: 0.0.4 → 0.0.5
  - `coding-frontend-svelte-knowledge`: 0.0.4 → 0.0.5
  - `coding-frontend-svelte-tester`: 0.0.4 → 0.0.5

## [0.3.3] - 2026-02-24

### Added
- **Plugin consistency checks** (`test-plugin-consistency.sh`): 5 deterministic
  checks on every push — version badge matching, agent skill cross-reference
  resolution, hook type safety (no prompt/agent in PreToolUse/PostToolUse),
  frontmatter field naming, and CHANGELOG version accuracy
- **Per-PR Claude semantic review** (`semantic-check` job in pr.yml): lightweight
  Claude Haiku review on every PR that changes plugins — checks identity
  coherence, domain specificity, content depth, cross-agent contradictions, and
  hook appropriateness. Posts informational PR comment, never blocks merge
- **Prompt builder** (`build-semantic-prompt.py`): generates focused review
  prompts from changed plugin metadata for the semantic-check CI job

### Fixed
- `claude-kit update` version diff baseline: compare against nearest git tag
  instead of HEAD, so version arrows match changelog entries even when
  intermediate commits were pulled between releases
- `_show_changelog` now shows ALL release entries since the user's last tag,
  not just the latest — users who skip releases see the full history
- `core-spec` README version badge (0.0.0 → 0.0.1)

## [0.3.2] - 2026-02-24

### Fixed
- **coding-frontend-svelte-debugger** (0.0.4 → 0.0.5): fix 7 agent files missing
  `coding-frontend-svelte-knowledge:` companion prefix on skill references — all
  companion skills (svelte5-runes, sveltekit-patterns, component-patterns,
  css-architecture, accessibility, desktop-targets, hardware-abstraction,
  usb-serial-hid, ble-communication, lan-discovery, audio-midi-devices) now
  resolve correctly at runtime

### Changed
- **Deterministic hooks for teams** — complete architectural overhaul of hook
  strategy across all 15 team plugins. Removed ALL prompt-type hooks from
  PreToolUse and PostToolUse events (41 prompt hooks eliminated). Only
  deterministic command scripts remain in the hot path. This eliminates hook
  cross-fire errors, "hook stopped continuation" blocking, and ~250-350
  unnecessary haiku LLM calls per session when team plugins are loaded together.
  Role-specific enforcement now uses the 5-layer defense model: permissionMode
  in agent frontmatter, system prompts, deterministic command scripts,
  acceptEdits UI, and Stop hooks for session-end verification.
- **System-maker hook reference updated** — `hooks-reference.md` now documents
  the "Deterministic Hooks for Teams" strategy including the 5-layer defense
  model, cross-fire problem explanation, and updated hook type selection guidance
- **Review checklist updated** — both system-maker and system-updater
  `review-checklist.md` now enforce H9 (no prompt/agent hooks in Pre/PostToolUse)
  and H15 (no role-specific restrictions in hot-path hooks), H17 (file-type-gating)

### Fixed
- `enforce-sysbuild.sh` now whitelists `/tmp/` builds, `--pristine`, and
  `--dry-run` flags to prevent cross-fire when grader runs analysis builds
- Deleted 3 orphaned `block-dangerous-commands.sh` scripts from debugger/grader
  plugins that were unreferenced by hooks.json

### Plugin versions
- `coding-cloud-python-debugger`: 0.0.3 → 0.0.4
- `coding-cloud-python-engineer`: 0.0.3 → 0.0.4
- `coding-cloud-python-grader`: 0.0.3 → 0.0.4
- `coding-cloud-python-knowledge`: 0.0.2 → 0.0.3
- `coding-cloud-python-tester`: 0.0.3 → 0.0.4
- `coding-embedded-zephyr-debugger`: 0.0.3 → 0.0.4
- `coding-embedded-zephyr-engineer`: 0.0.3 → 0.0.4
- `coding-embedded-zephyr-grader`: 0.1.1 → 0.1.2
- `coding-embedded-zephyr-knowledge`: 0.1.1 → 0.1.2
- `coding-embedded-zephyr-tester`: 0.0.3 → 0.0.4
- `coding-frontend-svelte-debugger`: 0.0.3 → 0.0.5
- `coding-frontend-svelte-engineer`: 0.0.3 → 0.0.4
- `coding-frontend-svelte-grader`: 0.0.3 → 0.0.4
- `coding-frontend-svelte-knowledge`: 0.0.3 → 0.0.4
- `coding-frontend-svelte-tester`: 0.0.3 → 0.0.4
- `system-maker`: 0.2.2 → 0.2.3
- `system-updater`: 0.0.2 → 0.0.3

## [0.3.1] - 2026-02-24

### Fixed
- Complete session-awareness coverage: added role-checking preambles to ALL
  remaining PostToolUse `Write|Edit` prompt hooks across 10 plugins — engineers,
  testers, knowledge editors, and system-maker all had PostToolUse hooks that
  would cross-fire when loaded in a team session (e.g., grader's report
  validation hook blocking engineer's code edits)
- Zephyr grader: converted PreToolUse `Write|Edit` from command type
  (`restrict-file-writes.sh`) to prompt type with session-awareness — the
  command hook hard-blocked engineers from writing `.c` files
- Zephyr grader: converted PreToolUse `Bash` from command type
  (`block-dangerous-commands.sh`) to prompt type with session-awareness
- Deleted 2 orphaned grader scripts replaced by prompt hooks

### Plugin versions
- `coding-cloud-python-engineer`: 0.0.2 → 0.0.3
- `coding-cloud-python-knowledge`: 0.0.1 → 0.0.2
- `coding-cloud-python-tester`: 0.0.2 → 0.0.3
- `coding-embedded-zephyr-engineer`: 0.0.2 → 0.0.3
- `coding-embedded-zephyr-grader`: 0.1.0 → 0.1.1
- `coding-embedded-zephyr-knowledge`: 0.1.0 → 0.1.1
- `coding-embedded-zephyr-tester`: 0.0.2 → 0.0.3
- `coding-frontend-svelte-engineer`: 0.0.2 → 0.0.3
- `coding-frontend-svelte-grader`: 0.0.2 → 0.0.3
- `coding-frontend-svelte-knowledge`: 0.0.2 → 0.0.3
- `coding-frontend-svelte-tester`: 0.0.2 → 0.0.3
- `system-maker`: 0.2.1 → 0.2.2

## [0.3.0] - 2026-02-24

### Added
- **Zephyr knowledge: deep hardware references** — `hardware-nordic/` (7 files)
  and `hardware-espressif/` (7 files) with comprehensive chip documentation
  covering families, peripherals, power modes, errata/gotchas, Zephyr support
  status, and tooling for all nRF52/53/54/91 and ESP32/S2/S3/C3/C6/H2 families
- **Session-awareness preamble pattern** across all 15 team plugin hook files —
  every role-specific restriction hook now checks "am I actually this role?"
  before enforcing, preventing hook cross-fire when plugins are loaded together

### Changed
- **Zephyr knowledge: hardware skill rename** — `esp32-hardware/` →
  `hardware-espressif/`, `nordic-hardware/` → `hardware-nordic/`,
  `nxp-hardware/` → `hardware-nxp/`, `stm32-hardware/` → `hardware-stm32/`
  (MINOR: breaking rename, but pre-1.0 so no major bump)
- **Zephyr grader: dynamic board targeting** — grader no longer defaults to
  `native_sim` or `qemu_cortex_m3`; instead detects actual hardware targets
  from CMakeLists.txt, prj.conf, board overlays, and west.yml; `board` (string)
  replaced with `boards` (array) throughout the entire grading pipeline
- **Zephyr grader: board-specific resource scoring** — resource analyzer now
  reads CONFIG_FLASH_SIZE/CONFIG_SRAM_SIZE for each target board instead of
  using hardcoded baselines; scoring formulas use 50/50 flash/RAM weighting
- **Zephyr engineer: cross-reference updates** — all 3 agents updated to
  reference renamed hardware skills (`hardware-nordic`, `hardware-espressif`,
  `hardware-nxp`, `hardware-stm32`)
- **system-maker**: hook-writer agent, hooks-reference.md, review-checklist.md,
  arch-designer, arch-reviewer, make-agent, and make-team updated with
  session-awareness documentation and enforcement rules
- **system-updater**: change-planner, change-writer, plugin-reviewer,
  plugin-structure SKILL.md, and review-checklist.md updated with
  session-awareness guidance

### Removed
- Orphaned shell scripts cleaned up from 7 plugins — scripts that were
  replaced by session-awareness prompt hooks but not deleted:
  `block-dangerous-commands.sh` (3 plugins), `restrict-file-writes.sh` (2),
  `check-test-file.sh`, `validate-submission-structure.sh`,
  `block-dangerous-test-commands.sh`, `check-safe-command.sh`

### Plugin versions
- `coding-embedded-zephyr-knowledge`: 0.0.1 → 0.1.0
- `coding-embedded-zephyr-grader`: 0.0.1 → 0.1.0
- `coding-embedded-zephyr-engineer`: 0.0.1 → 0.0.2
- `coding-embedded-zephyr-debugger`: 0.0.2 → 0.0.3
- `coding-embedded-zephyr-tester`: 0.0.1 → 0.0.2
- `coding-cloud-python-debugger`: 0.0.2 → 0.0.3
- `coding-cloud-python-engineer`: 0.0.1 → 0.0.2
- `coding-cloud-python-grader`: 0.0.2 → 0.0.3
- `coding-cloud-python-tester`: 0.0.1 → 0.0.2
- `coding-frontend-svelte-debugger`: 0.0.2 → 0.0.3
- `coding-frontend-svelte-engineer`: 0.0.1 → 0.0.2
- `coding-frontend-svelte-grader`: 0.0.1 → 0.0.2
- `coding-frontend-svelte-knowledge`: 0.0.1 → 0.0.2
- `coding-frontend-svelte-tester`: 0.0.1 → 0.0.2
- `system-maker`: 0.2.0 → 0.2.1
- `system-updater`: 0.0.1 → 0.0.2

## [0.2.5] - 2026-02-24

### Fixed
- Debugger hook collision when loading full teams: all three debugger plugins
  (`coding-embedded-zephyr-debugger`, `coding-frontend-svelte-debugger`,
  `coding-cloud-python-debugger`) converted Write|Edit PreToolUse hooks from
  hard-block `command` (exit 2) to soft `prompt` reminders — prevents debugger
  hooks from blocking legitimate writes by grader/engineer plugins loaded in
  the same session
- `coding-cloud-python-grader` write hook was unconditionally blocking ALL
  writes (including scorecard/report output); replaced with
  `restrict-file-writes.sh` that allows report formats (.md, .json, .html,
  .txt) matching the pattern used by the other two graders

### Plugin versions
- `coding-embedded-zephyr-debugger`: 0.0.1 → 0.0.2
- `coding-frontend-svelte-debugger`: 0.0.1 → 0.0.2
- `coding-cloud-python-debugger`: 0.0.1 → 0.0.2
- `coding-cloud-python-grader`: 0.0.1 → 0.0.2

## [0.2.4] - 2026-02-24

### Fixed
- CLI: debugger plugins now group with their team in the launch display instead
  of appearing as standalone entries; added `"debugger"` to `_ROLE_SUFFIXES`

## [0.2.3] - 2026-02-24

### Changed
- Statusline redesigned with dot gauge progress bar (`●●●●●○○○○○○○○○○○`),
  session cost display, token K/M suffixes, lines added/removed, and
  color-coded tiers (cyan/green/yellow/red by context usage)
- Single `jq` call replaces ~10 separate invocations for better performance
- Removed `bc` dependency — token formatting uses pure `awk`

### Added
- Mermaid markdown preview extension in devcontainer config

## [0.2.2] - 2026-02-24

### Changed
- All documentation consolidated into README — configuration hierarchy
  (with 7 Mermaid diagrams), agent team architecture, plugin structure,
  and developer workflow are now in one place
- Deleted `docs/` directory (research notes, plugin-spec, how-it-works,
  old working specs)

## [0.2.1] - 2026-02-24

### Added
- `docs/how-it-works.md` — configuration hierarchy guide with Mermaid diagrams
  explaining how Claude Code's 4-scope config (managed, user, project shared,
  project local) works for individuals and organizations, and how claude-kit
  plugins layer on top via `--plugin-dir`
- `install.sh` now auto-installs Claude Code CLI if `claude` is not found,
  using the official installer (`curl -fsSL https://claude.ai/install.sh | bash`)

### Fixed
- Removed duplicate Python Cloud Backend Team section in README

## [0.2.0] - 2026-02-24

### Added
- `coding-cloud-python-knowledge` v0.0.1 — shared domain reference for
  Python cloud-backend development (asyncio, FastAPI, gRPC, Docker, K8s)
- `coding-cloud-python-engineer` v0.0.1 — Python cloud-backend engineer
  (6 agents: feature-builder, api-designer, async-specialist, db-specialist,
  container-specialist, code-reviewer)
- `coding-cloud-python-grader` v0.0.1 — Python cloud-backend grader
  (10 agents covering 8 grading dimensions with quantitative scoring)
- `coding-cloud-python-tester` v0.0.1 — Python cloud-backend tester
  (5 agents: unit, integration, e2e, performance, coverage analysis)
- `coding-cloud-python-debugger` v0.0.1 — Python cloud-backend debugger
  (7 agents: triage + asyncio, profiler, trace, db-query, gRPC, container)
- `coding-embedded-zephyr-debugger` v0.0.1 — Zephyr RTOS debugger
  (7 agents: triage + fault-analyzer, kernel, peripheral, boot, network,
  postmortem; covers hard faults, stack overflow, kernel panic, MCUboot,
  BLE/LTE/Thread, and offline crash dump analysis)
- `coding-frontend-svelte-debugger` v0.0.1 — Svelte 5/SvelteKit debugger
  (9 agents: triage + compiler/TS, reactivity, SSR/routing, styling,
  accessibility, hardware/Tauri IPC, build/bundle, test failure)

### Changed
- `system-maker` v0.1.1 → v0.2.0 — removed `deployer` and `migrator`
  from standard coding team roles; coding teams now use 4 roles (engineer,
  grader, tester, debugger); deployment/migration concerns are operational
- Zephyr RTOS Team expanded from 4 to 5 plugins (added debugger)
- Svelte Frontend Team expanded from 4 to 5 plugins (added debugger)
- `scripts/validate-plugins.py` — removed `deployer` and `migrator`
  from VALID_ROLES

### Fixed
- Devcontainer: simplified devcontainer.json (#38)
- Devcontainer: Oh My Zsh with robbyrussell theme and plugins (#36, #37)
- Devcontainer: avoid wincred credential helper inside Linux container (#35)
- CLI: load .env via --env-file, move lifecycle to ctl.sh (#34)
- Devcontainer: add BuildKit registry cache (#33)
- Devcontainer: replace Docker-in-Docker with host socket mount (#32)

## [0.1.0] - 2026-02-23

### Added
- CLI flag passthrough: all unknown flags (--resume, --continue,
  --verbose, --print, --output-format, etc.) are now forwarded to
  `claude` instead of being rejected with "Unknown flag"
- `.devcontainer/.env.example` for GITHUB_TOKEN and IS_SANDBOX config
- `ctl.sh create/start` auto-authenticate gh and ghcr.io from .env

### Changed
- Devcontainer runs as root (removed `dev` user); IS_SANDBOX=1 baked
  in so Claude Code runs without restrictions
- Devcontainer uses native Claude Code installer instead of npm
- Tool versions: Go 1.26.0, yq 4.52.4, hyperfine 1.20.0, Node.js 24
- `ctl.sh push` uses GITHUB_TOKEN from .env instead of gh auth token
- Updated help text with passthrough examples and claude-kit flag docs

### Fixed
- Dockerfile GID 1000 collision on self-hosted runner (--force flag)
- publish-devcontainer workflow starts Docker daemon before build

## [0.0.18] - 2026-02-23

### Fixed
- `nightly.yml` — YAML parse error caused by unindented lines (`$PREVIEW`,
  `$FIXES`, `## Review Findings`) inside a `run: |` block; YAML parser
  treated them as top-level keys, producing "workflow file issue" failures
  on every push; fixed by moving PR body generation to
  `scripts/build-nightly-prompt.py` (new `pr-body` subcommand) and using
  `gh pr create --body-file` instead of a multi-line shell variable

## [0.0.17] - 2026-02-23

### Fixed
- `claude-kit update` no longer fails with "would clobber existing tag"
  errors when the user's local clone has stale tags (e.g. after an upstream
  history rewrite); now runs `git fetch --tags --force` before pulling so
  local tags are always synced to remote state
- `install.sh` update path has the same fix applied

## [0.0.16] - 2026-02-23

### Fixed
- `pr-autofix.yml` — replaced job-level `if:` condition with a `gate` job
  that always completes; `autofix` job depends on gate output; eliminates
  the 0-job workflow_run failure that flooded notifications on every
  successful `fast-validate` run on `main`
- `nightly.yml` — added `if: github.ref == 'refs/heads/main'` guard so the
  job does not run spuriously when the workflow file first appears on feature
  branches; moved inline Python heredocs to external scripts
- `scripts/build-autofix-prompt.py` — external script for pr-autofix prompt
  (eliminates heredoc-inside-`run:` YAML parsing failures)
- `scripts/build-nightly-prompt.py` — external script for nightly review
  prompt

## [0.0.15] - 2026-02-23

### Added
- `pr-autofix.yml` — when `fast-validate` fails on a PR branch, Claude reads
  the failure logs and pushes a fix commit automatically; CI re-runs and the
  loop continues until all checks pass or 3 attempts are exhausted (tracked
  via `autofix-attempt-N` PR labels); posts a comment if no changes could be made

### Fixed
- `push.yml` — changed to full history fetch (`fetch-depth: 0`) and added
  `git fetch --tags --force`; fixes `version shows tag format` smoke test
  failure on self-hosted runners with stale tag caches
- `nightly.yml` — replaced bash heredoc prompt construction with a Python
  inline script; previous heredoc caused the workflow to produce 0 jobs

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

# claude-kit

[![Stable](https://img.shields.io/github/v/release/MateoSegura/claude-kit?label=stable&color=blue)](https://github.com/MateoSegura/claude-kit/releases/latest)
[![CI](https://github.com/MateoSegura/claude-kit/actions/workflows/push.yml/badge.svg)](https://github.com/MateoSegura/claude-kit/actions/workflows/push.yml)
[![PR Validation](https://github.com/MateoSegura/claude-kit/actions/workflows/pr.yml/badge.svg)](https://github.com/MateoSegura/claude-kit/actions/workflows/pr.yml)

Specialized Claude Code plugins for your team. One command launches a domain expert — with companion knowledge and the right tools loaded automatically.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/MateoSegura/claude-kit/main/install.sh | bash
```

Requires: `git`, `python3`, `claude` (Claude Code CLI). `jq` is installed automatically if missing.

## Usage

```bash
# List available kits
claude-kit list

# Launch a full team by domain prefix (loads all related plugins)
claude-kit --kit coding-embedded-zephyr
claude-kit --kit coding-frontend-svelte

# Launch a specific plugin
claude-kit --kit coding-embedded-zephyr-engineer

# Combine kits in one session
claude-kit --kit coding-embedded-zephyr-engineer --kit core-spec

# Skip permission prompts
claude-kit --kit coding-embedded-zephyr --yolo

# Choose model (default: opus)
claude-kit --kit coding-embedded-zephyr --model sonnet

# Check current version and look for updates
claude-kit version

# Pull latest plugins
claude-kit update

# Set up Claude Code features (status line)
claude-kit setup

# Validate plugin structure (Tier 1: JSON, fields, hooks)
claude-kit validate --all
claude-kit validate coding-embedded-zephyr-engineer

# Undo setup changes
claude-kit restore

# Remove claude-kit from this machine
claude-kit uninstall
```

---

## Theory: Why Agent Teams?

Claude Code is a powerful single-agent system. But a single agent trying to be a firmware engineer, a code reviewer, a test writer, and a domain expert simultaneously hits a fundamental problem: **context dilution**. When you ask one agent to do everything, its instructions grow unbounded, its tool access is unrestricted, and there's no enforcement of what "good" looks like for each role.

claude-kit solves this with **specialized agent teams** — multiple Claude agents, each expert at one thing, working together in a single session.

### The Four-Role Team Model

Every domain team in claude-kit has exactly four roles:

```
Knowledge ──► Engineer
     └──────► Grader
     └──────► Tester
```

| Role | Responsibility | Key design principle |
|------|---------------|---------------------|
| **Knowledge** | Domain reference — APIs, patterns, hardware specs | No agents, no commands. Pure skill injection. |
| **Engineer** | Active implementation — writes, builds, debugs | Loads knowledge as companion. Hooks enforce hard constraints. |
| **Grader** | Blind quantitative review — scores code across weighted dimensions | Isolated from engineer context. Never writes code. |
| **Tester** | Test engineering — writes tests, runs coverage, validates CI | Own test knowledge. Never touches production code. |

**Why four?** Each role requires a different permission model, different tool access, and different hard constraints:

- The **engineer** needs write access and aggressive build-and-fix loops
- The **grader** needs read-only access and must be blind to who wrote the code
- The **tester** needs write access but only to test files, never source files
- The **knowledge** plugin provides shared domain context without polluting any role's instructions

### How Claude's Architecture Makes This Work

**Skills = context injection, not instructions.** A `skill` file in claude-kit is preloaded verbatim into an agent's context at launch. The knowledge plugin's skills — kernel API references, hardware specs, design patterns — are injected into the engineer's context automatically, giving it domain expertise without bloating the engineer's own instructions.

**Agents = focused subagents.** When you run `/coding-embedded-zephyr-engineer:develop`, the `develop` command spawns a set of specialized subagents (firmware-engineer, devicetree-specialist, code-reviewer) in parallel. Each subagent has:
- `tools:` restricted to exactly what it needs
- `skills:` preloaded with exactly the reference material it uses
- `permissionMode:` set to `plan` for read-only agents, `acceptEdits` for writers

**Hooks = behavioral enforcement, not guidelines.** Every plugin uses hooks to enforce hard constraints that Claude must never bypass:
- **PreToolUse `command` hooks** block dangerous shell commands before they run (exit 2 = block)
- **PostToolUse `prompt` hooks** review code changes for anti-patterns using a focused Claude evaluation
- **PostToolUse `agent` hooks** run multi-step verification that requires reading files (e.g., checking that DTS overlays are valid, not just that they were written)
- **Stop `agent` hooks** verify deliverable quality before Claude is allowed to stop — checking build success, error handling, and coverage thresholds

**Commands = orchestration, not implementation.** A `command` file coordinates a workflow by spawning agents. The command itself never writes code. It gathers requirements, launches specialized agents in parallel, synthesizes results, and presents output. This keeps the main conversation clean and the implementation in dedicated subagents.

---

## Plugins

### Zephyr RTOS Team

```bash
claude-kit --kit coding-embedded-zephyr  # loads all four
```

| Plugin | Role | What it does |
|--------|------|-------------|
| `coding-embedded-zephyr-knowledge` | Knowledge | Shared domain reference: kernel APIs, devicetree/Kconfig syntax, build system (west/sysbuild), Nordic/STM32/NXP/ESP32 hardware, networking, security, serialization. Auto-loaded by engineer and tester. |
| `coding-embedded-zephyr-engineer` | Engineer | Firmware development specialist. Agents: firmware-engineer, devicetree-specialist, build-debug-analyst, code-reviewer, test-engineer. Hooks enforce sysbuild usage, block destructive commands, validate DTS overlays and Kconfig, run async builds. |
| `coding-embedded-zephyr-grader` | Grader | Blind quantitative code review across 9 weighted dimensions (correctness, resource usage, style, Zephyr patterns, compilability, completeness, architecture, static analysis, testing). Agents run a full tool pipeline. |
| `coding-embedded-zephyr-tester` | Tester | Test engineering: ztest unit tests, Twister test runner, FFF mocking, gcov/lcov coverage, CI infrastructure. Agents: unit-test-writer, integration-test-writer, coverage-analyzer, test-runner, mock-specialist, test-reviewer. |

### Svelte Frontend Team

```bash
claude-kit --kit coding-frontend-svelte  # loads all four
```

| Plugin | Role | What it does |
|--------|------|-------------|
| `coding-frontend-svelte-knowledge` | Knowledge | Shared reference: Svelte 5 runes, SvelteKit patterns, CSS architecture, accessibility, hardware communication (USB/BLE/LAN/audio), Tauri desktop targets. Auto-loaded by engineer and tester. |
| `coding-frontend-svelte-engineer` | Engineer | Svelte 5 / SvelteKit specialist. Agents: component-writer, feature-builder, scaffold-writer, style-engineer, performance-analyst. Hooks enforce Svelte 5 rune patterns, block deprecated Svelte 4 syntax in real-time. |
| `coding-frontend-svelte-grader` | Grader | Blind code review across 8 dimensions (component quality, TypeScript, state management, styling, testing, accessibility, performance, UX). |
| `coding-frontend-svelte-tester` | Tester | Testing specialist: Vitest, vitest-browser-svelte component testing, Playwright E2E, axe accessibility audits. Agents cover unit, component, E2E, and coverage analysis. |

### System Plugins

| Plugin | What it does |
|--------|-------------|
| `core-spec` | Spec-driven development for long-running sessions — write the spec first, derive implementation phases from it, track progress via file-based state, recover full context after compaction through hooks and agents |
| `system-maker` | Build new domain plugins via a guided 11-phase workflow with parallel subagent execution. Includes the `/system-maker:validate` semantic reviewer. |
| `system-updater` | Enhance existing plugins via a structured 6-phase workflow with surgical change planning — reads current state, plans changes, implements with reviewer verification |

---

## Plugin Structure

Every plugin is a directory of markdown files and JSON configs:

```
plugins/<name>/
├── .claude-plugin/
│   ├── plugin.json    # { name, description, version } — parsed by Claude Code
│   └── ctl.json       # { role, companions } — read by claude-kit
├── agents/            # subagent definitions (tools:, permissionMode:, skills:)
├── commands/          # user-invocable slash commands (allowed-tools:)
├── skills/            # domain knowledge preloaded into agent context
│   └── <skill-name>/
│       ├── SKILL.md   # entry point (max 500 lines)
│       └── reference.md
├── hooks/
│   └── hooks.json     # PreToolUse / PostToolUse / Stop handlers
└── scripts/           # shell scripts called by command hooks
```

**Critical distinction:** Agents use `tools:` in frontmatter. Commands and skills use `allowed-tools:`. Using the wrong key is a silent failure.

**Companion auto-loading:** A plugin declares companions in `ctl.json`. claude-kit loads them first, before the requesting plugin. The engineer always gets the knowledge plugin's skills injected before its own agents launch.

See [`docs/plugin-spec.md`](docs/plugin-spec.md) for the complete specification.

---

## For Plugin Developers

```bash
# Create a new plugin (guided 11-phase workflow)
claude-kit --kit system-maker
# → /system-maker:make-agent

# Enhance an existing plugin (6-phase workflow)
claude-kit --kit system-updater
# → /system-updater:update-agent

# Validate your plugin before committing
claude-kit validate --all          # Tier 1: JSON, fields, hooks
claude-kit validate --changed      # only files changed since last commit
# → /system-maker:validate         # Tier 2-4: semantic review
```

**Branch naming is enforced by CI:** `<type>/<description>`
Valid types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `style`, `release`, `hotfix`

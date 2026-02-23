# claude-kit

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

# Validate a plugin's structure
claude-kit validate coding-embedded-zephyr-engineer

# Undo setup changes
claude-kit restore

# Remove claude-kit from this machine
claude-kit uninstall
```

## How It Works

`claude-kit --kit <name>` launches Claude Code with `--plugin-dir` pointing at the right plugin(s). Your working directory and `CLAUDE.md` are preserved — claude-kit doesn't touch them.

**Smart loading:**
- **Domain shortcuts** — `coding-embedded-zephyr` loads all four plugins: `engineer`, `grader`, `knowledge`, `tester`
- **Companion auto-load** — a plugin can declare companions in `.claude-plugin/ctl.json`; claude-kit loads them automatically. The `engineer` and `tester` plugins always pull in `knowledge`.

## Plugins

### Zephyr RTOS Team

| Plugin | What it does |
|--------|-------------|
| `coding-embedded-zephyr-engineer` | Firmware development specialist — Zephyr RTOS, devicetree, Kconfig, west builds, secure boot |
| `coding-embedded-zephyr-knowledge` | Shared domain reference — kernel APIs, hardware targets, design patterns (auto-loaded) |
| `coding-embedded-zephyr-grader` | Blind quantitative code review across 9 weighted dimensions with automated tooling |
| `coding-embedded-zephyr-tester` | Test engineering — ztest, twister, FFF mocking, gcov/lcov coverage, CI infrastructure |

### Svelte Frontend Team

| Plugin | What it does |
|--------|-------------|
| `coding-frontend-svelte-engineer` | Svelte 5 / SvelteKit specialist — runes, TypeScript strict, Tailwind, Tauri desktop targets |
| `coding-frontend-svelte-knowledge` | Shared domain reference — runes, CSS architecture, accessibility, hardware comms (auto-loaded) |
| `coding-frontend-svelte-grader` | Blind quantitative code review across 8 weighted dimensions |
| `coding-frontend-svelte-tester` | Testing specialist — Vitest, vitest-browser-svelte, Playwright E2E, axe accessibility audits |

### System Plugins

| Plugin | What it does |
|--------|-------------|
| `core-spec` | Spec-driven development — write the spec first, track phases via file-based state, recover after context compaction |
| `system-maker` | Build new domain plugins via a guided multi-phase workflow with parallel subagent execution |
| `system-updater` | Enhance existing plugins via a structured 6-phase workflow with surgical change planning |

## Plugin Structure

```
plugins/<name>/
├── .claude-plugin/
│   ├── plugin.json    # manifest (name, version, description)
│   └── ctl.json       # companions, role (optional)
├── agents/            # subagent definitions
├── commands/          # slash commands
├── skills/            # domain knowledge (auto-loaded into context)
├── hooks/
│   └── hooks.json
└── scripts/           # hook scripts
```

To create a new plugin: `claude-kit --kit system-maker` then `/system-maker:make-agent`

To update an existing plugin: `claude-kit --kit system-updater` then `/system-updater:update-agent`

## For Plugin Developers

See `docs/` for architecture research and `templates/` for plugin format reference.

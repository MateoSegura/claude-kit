# claude-forge

Specialized Claude Code plugins for your team. One command launches a domain expert — with companion knowledge and the right tools loaded automatically.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/MateoSegura/claude-forge/main/install.sh | bash
```

Requires: `git`, `claude` (Claude Code CLI), `jq`

## Usage

```bash
# List available domains
forge list

# Launch by domain (loads all related plugins automatically)
forge run coding-embedded-zephyr

# Launch a specific plugin
forge run coding-embedded-zephyr-engineer

# Skip permission prompts (yolo mode)
forge run --yolo coding-embedded-zephyr

# Keep up to date
forge update

# Validate a plugin's structure
forge validate coding-embedded-zephyr-engineer
```

## How It Works

`forge run <name>` launches Claude Code with `--plugin-dir` pointing at the right plugin(s). Your working directory and `CLAUDE.md` are preserved — forge doesn't touch them.

**Smart loading:**
- **Domain shortcuts** — `coding-embedded-zephyr` loads all three: `engineer`, `grader`, `knowledge`
- **Companion auto-load** — a plugin can declare companions in `.claude-plugin/ctl.json`; forge loads them automatically. The `engineer` plugin always pulls in `knowledge`.
- **Aliases** — named bundles in `config.json` (e.g., `zephyr-planned` = planner + knowledge + engineer)

## Plugins

| Plugin | What it does |
|--------|-------------|
| `coding-embedded-zephyr-engineer` | Zephyr RTOS firmware specialist |
| `coding-embedded-zephyr-knowledge` | Zephyr domain knowledge base (auto-loaded with engineer) |
| `coding-embedded-zephyr-grader` | Firmware code review and grading |
| `system-maker` | Build new domain plugins via guided workflow |
| `system-updater` | Enhance existing plugins |
| `system-planner` | Deterministic planning with plan files |

## Update

```bash
forge update
```

Pulls the latest plugins from this repo. No reinstall needed.

## For Plugin Developers

See `docs/` for research notes and `templates/` for plugin format reference.

Plugin structure:
```
plugins/<name>/
├── .claude-plugin/
│   ├── plugin.json    # manifest
│   └── ctl.json       # companions, role (optional)
├── agents/            # subagent definitions
├── commands/          # slash commands
├── skills/            # domain knowledge (auto-loaded)
├── hooks/
│   └── hooks.json
└── scripts/           # hook scripts
```

To create a new plugin: `forge run system-maker` then `/system-maker:make-agent`

To update an existing plugin: `forge run system-updater` then `/system-updater:update-agent`

# Claude Code Plugin Specification

> **Source of truth:** `plugins/system-maker/skills/plugin-structure/`
>
> This document is a human-readable summary distilled from those skill files.
> When in doubt, consult the skills directly — they are the canonical reference.

---

## Directory Layout

```
plugin-name/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest (REQUIRED)
│   └── ctl.json             # Orchestration metadata (optional)
├── agents/                  # Subagent definitions
│   └── agent-name.md
├── commands/                # Slash commands
│   └── command-name.md
├── skills/                  # Reference knowledge
│   └── skill-name/
│       ├── SKILL.md         # Entry point (REQUIRED, max 500 lines)
│       ├── reference.md     # Detailed docs (loaded on demand)
│       └── examples.md      # Usage examples (loaded on demand)
├── hooks/
│   └── hooks.json           # Hook definitions
├── scripts/                 # Shell scripts used by hooks
│   └── validate.sh
├── .lsp.json                # Language server config (optional)
└── .mcp.json                # MCP server config (optional)
```

---

## `plugin.json` — Required

Located at `.claude-plugin/plugin.json`. Parsed by Claude Code's plugin loader.

**CRITICAL: Only use these three fields.** Any other field (e.g. `author`,
`role`, `companions`, `keywords`) causes the plugin to **silently fail to load**.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Plugin identifier, kebab-case. Must match directory name exactly. |
| `description` | string | yes | Human-readable description. Minimum 20 characters. |
| `version` | string | no | Semantic version: `x.y.z` |

```json
{
  "name": "my-plugin",
  "description": "Domain-expert coding agent for ...",
  "version": "0.1.0"
}
```

---

## `ctl.json` — Orchestration Metadata

Located at `.claude-plugin/ctl.json` (alongside `plugin.json`). Read by
`claude-kit`, NOT by Claude Code. This is where `role` and `companions` go.

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | Plugin archetype: `engineer`, `grader`, `tester`, `debugger`, `deployer`, `migrator`, `knowledge` |
| `companions` | string[] | Companion plugins to auto-load. Must exist in `plugins/`. |

```json
{
  "role": "engineer",
  "companions": ["my-knowledge-plugin"]
}
```

**Knowledge plugins** use `"role": "knowledge"` and must NOT have `agents/` or
`commands/` directories. They contain skills and optionally hooks only.

---

## Agent Files — `agents/*.md`

Subagents launched from commands or other agents via the `Task` tool.

### Frontmatter

```yaml
---
name: agent-name          # REQUIRED. Must match filename (without .md)
description: What this agent does and when to use it  # REQUIRED
model: opus               # opus | sonnet | haiku (default: sonnet)
tools: Read, Glob, Write  # REQUIRED field name — NOT 'allowed-tools:'
disallowedTools: Bash     # Tools to explicitly deny
skills: skill-name-1      # Skills to preload (full SKILL.md injected)
permissionMode: default   # default | plan | bypassPermissions
maxTurns: 20              # Max API round-trips before agent stops
color: "#4A90D9"          # Hex color for CLI status line
---
```

### Critical Rules

- **`tools:` not `allowed-tools:`** — Using the wrong key causes silent failure
  (agent launches with no tool access)
- Both `name` and `description` are REQUIRED
- Subagents cannot spawn other subagents — hierarchy is flat
- Skills listed in `skills:` are injected in full at launch
- Subagents do NOT inherit skills from parent — list every skill explicitly

---

## Command Files — `commands/*.md`

User-invocable via `/plugin-name:command-name`. Run in the main conversation
context. Best for interactive workflows and orchestration.

### Frontmatter

```yaml
---
description: Brief description of what this command does  # REQUIRED
allowed-tools: Task, Read, Write, Bash  # NOT 'tools:' (that's for agents)
---
```

### Critical Rules

- **`allowed-tools:` not `tools:`** — opposite of agents
- `description` is required (shown in `/` command menu)
- Commands orchestrate by spawning agents — they do not do heavy lifting
  themselves

---

## Skill Files — `skills/<skill-name>/SKILL.md`

Reference knowledge preloaded into agents. Claude auto-invokes skills when a
task matches the skill's description. Max 500 lines for `SKILL.md` — move
detail into `reference.md`, `examples.md`, etc.

### Frontmatter

```yaml
---
name: plugin-name:skill-name  # REQUIRED. Format: plugin:dir-name
description: What knowledge this skill provides  # REQUIRED
user-invocable: false         # Hide from user menu (identity/background skills)
allowed-tools: Read, Grep     # NOT 'tools:'
---
```

### Key Patterns

| Pattern | Frontmatter |
|---------|-------------|
| Normal skill (user + Claude can invoke) | `name`, `description` |
| Background knowledge (Claude-only, hidden) | `+ user-invocable: false` |
| User-only (explicit invocation only) | `+ disable-model-invocation: true` |
| Heavy skill in subagent | `+ context: fork`, `agent: Explore` |
| Identity skill | `user-invocable: false`, content describes agent's persona |

---

## `hooks/hooks.json`

Hooks run handlers in response to lifecycle events. Uses **event names as
top-level keys** — NOT a flat array.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh",
            "description": "Validate before bash runs"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review the change. Context: $ARGUMENTS. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}."
          },
          {
            "type": "agent",
            "prompt": "Verify output quality. Context: $ARGUMENTS.",
            "timeout": 120
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify deliverable quality. Use Read/Glob/Grep to check. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

### Three Hook Types

| Type | Description | Decision |
|------|-------------|----------|
| `command` | Shell script. Exit 0 = allow, exit 2 = block | Via exit code |
| `prompt` | LLM evaluates inline prompt against context | Via `{"ok": true/false}` |
| `agent` | Spawns agentic verifier with tool access | Via `{"ok": true/false}` |

### Common Events

| Event | When |
|-------|------|
| `PreToolUse` | Before a tool executes (can block) |
| `PostToolUse` | After a tool succeeds |
| `Stop` | When agent stops |
| `SessionStart` | Session begins |

### Script Path Convention

Always use `${CLAUDE_PLUGIN_ROOT}` — never hardcode absolute paths:

```bash
# Correct
"command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"

# Wrong
"command": "/home/user/plugins/my-plugin/scripts/validate.sh"
```

---

## Frontmatter Quick Reference

| Component | Tool restriction field | Wrong field |
|-----------|----------------------|-------------|
| `agents/*.md` | `tools:` | ~~allowed-tools:~~ |
| `commands/*.md` | `allowed-tools:` | ~~tools:~~ |
| `skills/*/SKILL.md` | `allowed-tools:` | ~~tools:~~ |

---

## Validation

Tier 1 (structural, fast):
```bash
claude-kit validate --all           # all plugins
claude-kit validate <plugin-name>   # single plugin
claude-kit validate --changed       # changed since HEAD~1
```

Tier 2-4 (semantic, requires system-maker):
```bash
claude-kit --kit system-maker
# then: /system-maker:validate <plugin-name>
```

---

## Version Strategy

Plugin versions in `plugin.json` follow semver independently:

| Bump | When |
|------|------|
| `patch` | Doc/content improvement, hook tweak, script fix |
| `minor` | New agent, command, or skill added |
| `major` | Breaking change — renamed command, removed agent, changed skill API |

Use `/bump-plugin` to bump a version and update CHANGELOG.
Use `/release` to finalize a release, tag, and push.

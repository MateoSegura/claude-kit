---
name: plugin-structure
description: Canonical reference specification for Claude Code plugin file formats, frontmatter fields, hooks schema, and component conventions. Preloaded by the plugin-reviewer agent to audit plugins for correctness and completeness.
user-invocable: false
---

# Claude Code Plugin Structure Reference

This is the single source of truth for plugin file formats. Every file in a Claude Code plugin MUST conform to the schemas documented here.

## Plugin Directory Layout

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (REQUIRED)
├── commands/                 # Slash commands (legacy but supported)
│   └── command-name.md
├── agents/                   # Subagent definitions
│   └── agent-name.md
├── skills/                   # Knowledge/reference skills
│   └── skill-name/
│       ├── SKILL.md          # Entry point (REQUIRED, max 500 lines)
│       ├── reference.md      # Detailed docs (loaded on demand)
│       └── examples.md       # Usage examples (loaded on demand)
├── hooks/
│   └── hooks.json            # Hook definitions
├── scripts/                  # Shell scripts used by hooks
│   └── script-name.sh
├── .lsp.json                 # Language server config (optional)
└── .mcp.json                 # MCP server config (optional)
```

### Important: ${CLAUDE_PLUGIN_ROOT}

The environment variable `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's absolute path at runtime. Use it in hooks, MCP server configurations, and shell scripts to reference files within the plugin directory without hardcoding paths.

Example: `${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh`

## plugin.json (Required)

Located at `.claude-plugin/plugin.json`. This is the ONLY file that goes inside `.claude-plugin/`.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier, kebab-case format `<type>-<domain>-<tech>-<role>` (e.g., "coding-embedded-zephyr-engineer") |
| `description` | string | Human-readable plugin description |
| `version` | string | Semantic version (e.g., "1.0.0") |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Author name or handle |
| `homepage` | string | URL to plugin homepage |
| `repository` | string | URL to source repository |
| `license` | string | SPDX license identifier |
| `keywords` | string[] | Searchable tags |
| `commands` | object | Command configuration overrides |
| `agents` | object | Agent configuration overrides |
| `skills` | object | Skill configuration overrides |
| `hooks` | object | Hook definitions (alternative to hooks.json) |
| `mcpServers` | object | MCP server definitions (alternative to .mcp.json) |
| `companions` | string[] | List of companion plugin names to load alongside this plugin. Example: `["coding-embedded-zephyr-knowledge"]`. At runtime, `ctl.sh` resolves companions and passes multiple `--plugin-dir` arguments to Claude. |
| `role` | string | Plugin archetype. Standard values: `engineer`, `grader`, `tester`, `debugger`, `deployer`, `migrator`, `knowledge`. Knowledge plugins must NOT have agents/ or commands/ directories. |

### Example

```json
{
  "name": "coding-embedded-zephyr-engineer",
  "description": "Domain-expert coding agent for Zephyr RTOS embedded systems",
  "version": "1.0.0",
  "author": "mateo",
  "keywords": ["embedded", "zephyr", "rtos", "firmware"],
  "license": "MIT"
}
```

### Knowledge Plugins

Knowledge plugins have `role: "knowledge"` and provide shared domain reference material (API references, hardware targets, design patterns, build system docs, safety hooks). They are loaded as companions by role plugins via the `companions` field. Knowledge plugins must NOT contain `agents/` or `commands/` directories — they only provide skills and hooks.

## Agent Files (agents/*.md)

Subagent definitions launched via the `Task` tool. Every agent MUST have both `name` and `description` in its frontmatter — these are the only two required fields.

### Frontmatter Format

```yaml
---
name: agent-name                    # REQUIRED
description: "What this agent does" # REQUIRED
model: opus | sonnet | haiku
tools: Tool1, Tool2, Tool3          # NOT allowed-tools
skills: skill-name-1, skill-name-2
permissionMode: default | plan | acceptEdits
color: "#hexcolor"
---
```

### Critical Rule: tools NOT allowed-tools

Agent frontmatter uses `tools:` to restrict tool access. Using `allowed-tools:` in an agent file is an ERROR.

```yaml
# CORRECT — agent gets these tools
tools: Read, Glob, Grep, Write, Edit, Bash

# WRONG — field name not recognized, agent gets NO tools
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **yes** | Agent identifier, kebab-case. Must match filename (without .md). |
| `description` | string | **yes** | What this agent does. Used in Task tool spawning. |
| `model` | string | no | Model to use: `opus`, `sonnet`, or `haiku` (default: sonnet) |
| `tools` | string | no | Comma-separated tool list to restrict access. Omit to inherit all tools. |
| `disallowedTools` | string | no | Comma-separated tools to deny (opposite of `tools`). |
| `skills` | string | no | Comma-separated skill names to preload at agent launch. |
| `permissionMode` | string | no | Permission behavior: `default`, `plan`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions` |
| `color` | string | no | Hex color for CLI status line (e.g., "#4A90D9") |
| `maxTurns` | number | no | Maximum conversation turns for this agent |
| `memory` | string | no | Persistent memory scope: `user`, `project`, or `local` |

## Command Files (commands/*.md)

Commands are user-invocable via `/plugin-name:command-name`. They run in the main conversation context.

### Frontmatter Format

```yaml
---
allowed-tools: Tool1, Tool2, Tool3   # NOT tools
description: "What this command does"
---
```

### Critical Rule: allowed-tools NOT tools

Command frontmatter uses `allowed-tools:` to restrict tool access. Using `tools:` in a command file follows agent convention incorrectly.

```yaml
# CORRECT — command can use these tools
allowed-tools: Task, AskUserQuestion, Read, Bash

# WRONG — using agent field name in command
tools: Task, AskUserQuestion, Read, Bash
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | Shown in command listings. Describes what the command does. |
| `allowed-tools` | string | no | Comma-separated list of tools this command can use. Inherits all tools if omitted. |

## Skill Files (skills/*/SKILL.md)

Skills are knowledge files that get preloaded into agents. They contain reference information, specifications, and examples.

### Frontmatter Format

```yaml
---
name: skill-name                     # REQUIRED
description: "What knowledge this skill provides" # REQUIRED
user-invocable: true | false
allowed-tools: Tool1, Tool2          # NOT tools (same as commands)
---
```

### Multi-File Structure

Skills can span multiple files. SKILL.md is the entry point (max 500 lines). Detailed content goes in reference files alongside SKILL.md:

```
skill-name/
├── SKILL.md              # Entry point (auto-loaded)
├── coding-standards.md   # Detailed standards
├── workflow-patterns.md  # Common patterns
└── api-reference.md      # API specifications
```

SKILL.md should link to reference files:

```markdown
## Additional Resources

For detailed coding standards, see [coding-standards.md](coding-standards.md).
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **yes** | Skill identifier, kebab-case. Must match directory name. |
| `description` | string | **yes** | What knowledge this skill provides. Claude uses this for auto-invocation. |
| `user-invocable` | boolean | no | Set to `false` to hide from user's command menu (for identity skills). Default: true. |
| `allowed-tools` | string | no | Comma-separated tools the skill can use (same pattern as commands). |

## hooks.json Format

Located at `hooks/hooks.json`. Hooks run handlers in response to lifecycle events.

### Critical Format: Event-Based Keys

The hooks format uses **event names as top-level keys** with arrays of matcher/hook pairs under each event.

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolNamePattern",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/script.sh"
          }
        ]
      }
    ]
  }
}
```

### Three Hook Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `command` | Runs shell command. Exit 0 = pass, exit 2 = block. | `type`, `command` |
| `prompt` | Evaluates LLM prompt. Returns `{"ok": true/false}`. | `type`, `prompt`, `model` |
| `agent` | Spawns agentic verifier with tool access. Returns `{"ok": true/false}`. | `type`, `prompt`, `timeout` |

### Example

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review this file for naming conventions: $ARGUMENTS. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
            "model": "haiku"
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
            "prompt": "Verify all required deliverables exist. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### Common Hook Events

| Event | When it fires | Matcher matches |
|-------|--------------|-----------------|
| `PreToolUse` | Before a tool executes | Tool name (Write, Bash, Edit) |
| `PostToolUse` | After a tool executes successfully | Tool name |
| `Stop` | When the agent is about to stop | — |
| `SessionStart` | When a session begins | — |
| `SessionEnd` | When a session ends | — |

## Best Practices

1. **Naming**: Use kebab-case for all file and directory names
2. **Tool restrictions**: Agents use `tools:`, commands/skills use `allowed-tools:`
3. **Required fields**: Agents and skills MUST have both `name` and `description`
4. **Skill structure**: Keep SKILL.md under 500 lines, split detailed content into reference files
5. **Identity as skill**: Use `user-invocable: false` skills for agent identity/methodology
6. **Hook scripts**: Always use `${CLAUDE_PLUGIN_ROOT}` for script paths, never hardcode
7. **Model selection**: Use `opus` for complex reasoning, `sonnet` for generation, `haiku` for validation
8. **Flat hierarchy**: Subagents cannot spawn other subagents — design accordingly

## Common Format Errors

| Component | Error | Correct |
|-----------|-------|---------|
| Agent | `allowed-tools: Read, Write` | `tools: Read, Write` |
| Command | `tools: Read, Write` | `allowed-tools: Read, Write` |
| Skill | `tools: Read` | `allowed-tools: Read` |
| Agent | Missing `description` field | Add `description: "..."` |
| Skill | Missing `name` field | Add `name: skill-name` |
| hooks.json | Flat array instead of event keys | Use event-based structure |
| Hook script | Missing shebang | Add `#!/bin/bash` |
| Hook script | Hardcoded paths | Use `${CLAUDE_PLUGIN_ROOT}/...` |

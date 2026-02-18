---
name: system-maker:plugin-structure
description: Canonical reference specification for Claude Code plugin file formats, frontmatter fields, hooks schema, and component conventions. Preloaded by Phase 8 implementation agents to ensure correct file generation.
---

# Claude Code Plugin Structure Reference

This is the single source of truth for plugin file formats. Every file you generate for a plugin MUST conform to the schemas documented here. When in doubt, follow this spec exactly.

## Additional resources

For detailed specifications beyond what's covered in this entry point, see:

- [agent-reference.md](agent-reference.md) — Complete agent frontmatter specification, permission modes, tool restrictions, model selection, spawning, skills preloading, memory, color assignments
- [hooks-reference.md](hooks-reference.md) — Complete hooks specification with all 3 types (command, prompt, agent), 14 event types, decision control, async hooks, patterns, environment variables
- [skills-reference.md](skills-reference.md) — Multi-file skill structure, identity-as-skill pattern, frontmatter reference, loading behavior, content guidelines
- [lsp-mcp-reference.md](lsp-mcp-reference.md) — LSP server configuration (.lsp.json), MCP server configuration (.mcp.json), multi-server examples

<directory-layout>

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
│   └── format-code.sh
├── .lsp.json                 # Language server config (optional)
└── .mcp.json                 # MCP server config (optional)
```

### Important: ${CLAUDE_PLUGIN_ROOT}

The environment variable `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's absolute path at runtime. Use it in hooks, MCP server configurations, and shell scripts to reference files within the plugin directory without hardcoding paths.

Example: `${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh`

</directory-layout>

<plugin-json>

## plugin.json (Required)

The plugin manifest. Located at `.claude-plugin/plugin.json`. This is the ONLY file that goes inside `.claude-plugin/` (along with the optional `ctl.json`).

**CRITICAL: plugin.json is parsed by Claude Code's plugin loader. Only use the fields listed below. Adding unrecognized fields (e.g., `role`, `keywords`, `companions`) will cause the plugin to SILENTLY FAIL TO LOAD. Put orchestration metadata in `ctl.json` instead.**

### plugin.json — Supported Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Plugin identifier, kebab-case |
| `description` | string | yes | Human-readable plugin description |
| `version` | string | no | Semantic version (e.g., "1.0.0") |

Only these three fields are safe. Do NOT add `role`, `keywords`, `companions`, `author`, `license`, or any other fields to plugin.json.

### plugin.json Example

```json
{
  "name": "coding-embedded-zephyr-engineer",
  "description": "Domain-expert coding agent for Zephyr RTOS embedded systems",
  "version": "1.0.0"
}
```

### ctl.json — Orchestration Metadata

Located at `.claude-plugin/ctl.json` (alongside plugin.json). Read by `ctl.sh`, NOT by Claude Code. This is where `role` and `companions` go.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | no | Plugin archetype. Standard values: `engineer`, `grader`, `tester`, `debugger`, `deployer`, `migrator`, `knowledge` |
| `companions` | string[] | no | Companion plugin names to auto-load. Example: `["coding-embedded-zephyr-knowledge"]` |

### ctl.json Example

```json
{
  "role": "engineer",
  "companions": ["coding-embedded-zephyr-knowledge"]
}
```

**Note on knowledge plugins**: Knowledge plugins use `"role": "knowledge"` in ctl.json and must NOT contain `agents/` or `commands/` directories. They serve as companion reference material loaded alongside role plugins.

</plugin-json>

<command-files>

## Command Files (commands/*.md)

Commands are user-invocable via `/plugin-name:command-name`. They are markdown files with YAML frontmatter. Commands run in the main conversation context and are the LEGACY pattern (still fully supported).

### Distinction: Commands vs Skills

- **Commands** (`commands/*.md`): User-invoked explicitly via `/plugin:command`. They run in the main conversation. Legacy pattern, still works. Best for: interactive workflows, orchestration, guided processes.
- **Skills** (`skills/*/SKILL.md`): Auto-invoked by Claude when the task matches the skill's description. Context-efficient — loaded only when relevant. Newer pattern. Best for: reference knowledge, domain expertise, specifications.

### Format

```markdown
---
allowed-tools: Tool1, Tool2, Tool3
description: Brief description of what this command does
---

# Command Title

Instructions for Claude when this command is invoked.
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allowed-tools` | string | no | Comma-separated list of tools this command can use. Inherits all tools if omitted. **Note: Commands use `allowed-tools:`, NOT `tools:`.** |
| `description` | string | yes | Shown in command listings. Describes what the command does. |

### Example: Orchestrator Command

```markdown
---
allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Write, Edit, Bash
description: Create a new component through a guided multi-step workflow.
---

# Create Component

You orchestrate component creation by gathering requirements, then spawning
specialized subagents to do the implementation work.

## Workflow

### Step 1: Gather Requirements
Use AskUserQuestion to understand what the user needs.

### Step 2: Launch Implementation
Spawn the implementation agent using Task:
- subagent_type: component-writer
- Pass requirements as input

### Step 3: Validate
Review the output and present to the user.
```

</command-files>

<agent-files-summary>

## Agent Files (agents/*.md)

Subagent definitions launched via the `Task` tool from commands or other agents. Every agent MUST have both `name` and `description` in its frontmatter — these are the only two required fields.

### Essential Frontmatter

```yaml
---
name: agent-name
description: What this agent does (REQUIRED)
model: opus | sonnet | haiku
tools: Tool1, Tool2, Tool3
skills: skill-name-1, skill-name-2
permissionMode: default
color: "#hexcolor"
---
```

### Critical Rules

- The correct field name is `tools:` — NOT `allowed-tools:`
- Subagents CANNOT spawn other subagents — keep hierarchy flat
- Skills listed in `skills:` are injected in FULL into the agent's context at launch
- Subagents do NOT inherit skills from the parent — list every skill explicitly

For the complete agent specification including all 12 frontmatter fields, permission modes, tool restriction guidelines, model selection, spawning syntax, memory, and color assignments, see [agent-reference.md](agent-reference.md).

</agent-files-summary>

<skill-files-summary>

## Skill Files (skills/skill-name/SKILL.md)

Skills are knowledge files that get preloaded into agents. They contain reference information, specifications, and examples. Claude auto-invokes skills when a task matches the skill's description.

### Essential Frontmatter

```yaml
---
name: plugin-name:skill-name
description: What knowledge this skill provides
---
```

### Key Rules

- **Max 500 lines** for SKILL.md — move detailed content to reference files
- Multi-file structure: `SKILL.md` + `reference.md`, `examples.md`, etc.
- Use `user-invocable: false` for background knowledge (identity skills)
- Skills are REFERENCE material, not executable instructions

For the complete skill specification including multi-file structure, identity-as-skill pattern, all frontmatter fields, loading behavior, and content guidelines, see [skills-reference.md](skills-reference.md).

</skill-files-summary>

<hooks-summary>

## hooks.json

Hooks run handlers in response to lifecycle events during a Claude Code session. The format uses **event names as top-level keys** with arrays of matcher/hook pairs.

### Essential Format

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
    ]
  }
}
```

### Three Hook Types

| Type | Description | Use for |
|------|-------------|---------|
| `command` | Runs shell command. Exit code 0 = pass, exit 2 = block. | File validation, path protection, format checking |
| `prompt` | Evaluates LLM prompt against context. Returns `{"ok": true/false}`. | Code review, convention checking, naming validation |
| `agent` | Spawns agentic verifier with tool access. Returns `{"ok": true/false}`. | Complex validation requiring file reads and multi-step reasoning |

### Key Events

| Event | When | Matcher |
|-------|------|---------|
| `PreToolUse` | Before tool executes | Tool name |
| `PostToolUse` | After tool succeeds | Tool name |
| `Stop` | Agent stops | — |
| `SessionStart` | Session begins | — |

For the complete hooks specification including all 14 events, decision control, async hooks, environment variables, prompt/agent hook details, and common patterns, see [hooks-reference.md](hooks-reference.md).

</hooks-summary>

<external-config-summary>

## .lsp.json and .mcp.json

Optional configuration files at the plugin root for language server and MCP server integration.

### .lsp.json (Language Servers)

Provides Claude with IDE-level language intelligence (diagnostics, go-to-definition, completions).

```json
{
  "clangd": {
    "command": "clangd",
    "args": ["--background-index"],
    "extensionToLanguage": { ".c": "c", ".h": "c" }
  }
}
```

### .mcp.json (MCP Servers)

Connects Claude to external tool servers via Model Context Protocol.

```json
{
  "mcpServers": {
    "custom-tools": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.js"]
    }
  }
}
```

For complete LSP and MCP specifications including all fields, multi-server examples, initialization options, and transport configuration, see [lsp-mcp-reference.md](lsp-mcp-reference.md).

</external-config-summary>

<best-practices>

## Best Practices

1. **Naming**: Use kebab-case for all file and directory names.
2. **Tool restrictions**: Agents use `tools:` in frontmatter. Commands and skills use `allowed-tools:`. Never mix these up.
3. **Model selection**: Use `opus` for complex reasoning, `sonnet` for generation, `haiku` for simple validation.
4. **Structured output**: Every agent should define its exact output format with examples.
5. **Skills for shared knowledge**: If multiple agents need the same reference info, put it in a skill.
6. **Hooks for enforcement**: Use hooks to validate outputs and enforce hard constraints — not for things Claude handles well already.
7. **Commands as orchestrators**: Commands coordinate workflows, spawning agents for the heavy lifting.
8. **Use ${CLAUDE_PLUGIN_ROOT}**: Always use this variable in hooks and MCP/LSP configs instead of hardcoding paths.
9. **Flat agent hierarchy**: Subagents cannot spawn other subagents. Design accordingly.
10. **Required fields matter**: Agents require both `name` and `description`. Skills require both `name` and `description`.
11. **Identity as a skill**: Use `user-invocable: false` skills for agent identity/methodology. Plugins do NOT read their own CLAUDE.md — only skills, agents, hooks, commands, and config files are loaded.
12. **Multi-file skills**: Keep SKILL.md under 500 lines. Split into reference files for depth.
13. **Rich hooks**: Use all 3 hook types (command, prompt, agent) — not just command hooks.
14. **LSP for language intelligence**: Always include `.lsp.json` when the domain has a language server available.

</best-practices>

<quick-reference>

## Quick Reference: Frontmatter Field Names

| Component | Field | Correct | Common Mistake |
|-----------|-------|---------|----------------|
| Agent | Tool restrictions | `tools:` | ~~allowed-tools:~~ |
| Command | Tool restrictions | `allowed-tools:` | ~~tools:~~ |
| Agent | Tool denials | `disallowedTools:` | — |
| Agent | Name | `name:` (required) | — |
| Agent | Description | `description:` (required) | Treating as optional |
| Agent | Permission level | `permissionMode:` | — |
| Agent | Turn limit | `maxTurns:` | — |
| Agent | Persistent memory | `memory:` | — |
| Agent | Spawn restrictions | `tools: Task(agent-type)` | — |
| Skill/Command | Tool restrictions | `allowed-tools:` | ~~tools:~~ |
| Skill | Hide from menu | `user-invocable: false` | — |
| Skill | User-only invoke | `disable-model-invocation: true` | — |
| Skill | Run in subagent | `context: fork` | — |
| Skill | Subagent type | `agent: Explore` | — |
| Skill | Autocomplete hint | `argument-hint:` | — |
| Hooks | Event keys | `PreToolUse`, `PostToolUse`, etc. | ~~`before`/`after` types~~ |
| Hooks | Hook type | `command`, `prompt`, `agent` | ~~`before`/`after`~~ |
| Hooks | Background exec | `async: true` | — |
| Hooks | Decision control | `permissionDecision`, `decision` | — |

</quick-reference>

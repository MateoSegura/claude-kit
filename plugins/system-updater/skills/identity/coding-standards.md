# System Updater — Coding Standards for Plugin Files

This document defines the coding standards and format conventions for Claude Code plugin files. These standards ensure consistency, correctness, and compatibility across all plugins.

## Plugin File Format Conventions

### Agent Files (`agents/*.md`)

Agent files define subagents spawned via the Task tool. Critical format rules:

**Frontmatter Structure:**

```yaml
---
name: agent-name
description: "What this agent does" # REQUIRED
model: opus | sonnet | haiku
tools: Tool1, Tool2, Tool3          # NOT allowed-tools
skills: identity, skill-name
permissionMode: plan | acceptEdits | default
color: "#hexcolor"
---
```

**Critical Field Rule**: Agent frontmatter uses `tools:` — NEVER `allowed-tools:`.

The `name` and `description` fields are REQUIRED. All other fields are optional.

Tool restrictions are specified via `tools:` (restricts to the listed tools) or `disallowedTools:` (denies specific tools while allowing all others).

### Command Files (`commands/*.md`)

Command files define user-invocable workflows triggered via `/plugin:command`. Format rules:

**Frontmatter Structure:**

```yaml
---
allowed-tools: Tool1, Tool2, Tool3    # NOT tools
description: "What this command does"
---
```

**Critical Field Rule**: Command frontmatter uses `allowed-tools:` — NEVER `tools:`.

### Skill Files (`skills/*/SKILL.md`)

Skill files provide reference knowledge preloaded into agents. Format rules:

**Frontmatter Structure:**

```yaml
---
name: skill-name
description: "What knowledge this skill provides" # REQUIRED
user-invocable: true | false
---
```

The `name` and `description` fields are REQUIRED.

Skills use `allowed-tools:` if they restrict tools — same pattern as commands, NOT `tools:`.

Identity skills should set `user-invocable: false` to hide them from the user's command menu.

**File Structure Rule**: SKILL.md is the entry point (max 500 lines). Detailed content goes in reference files (`coding-standards.md`, `workflow-patterns.md`, `api-reference.md`, etc.) alongside SKILL.md.

## JSON Structure Rules

### plugin.json

Located at `.claude-plugin/plugin.json`. Required fields:

```json
{
  "name": "plugin-name",
  "description": "Human-readable plugin description",
  "version": "1.0.0"
}
```

**Required fields**: `name`, `description`, `version`

Optional fields include `author`, `keywords`, `homepage`, `repository`, `license`.

### hooks.json

Located at `hooks/hooks.json`. Uses **event-based keys** format:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
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

**Critical Format Rule**: The top-level `hooks` object has event names as keys (e.g., `PreToolUse`, `PostToolUse`, `Stop`). Each event key maps to an ARRAY of matcher/hook objects. Each matcher object has a `hooks` array containing the actual hook definitions.

**Common mistake**: Forgetting the outer array under each event key. The structure is `hooks → EventName → array → object with matcher and hooks`.

## Frontmatter Field Ordering Conventions

While field order is technically flexible, follow these conventions for consistency:

### Agent Frontmatter Order

1. `name`
2. `description`
3. `model`
4. `tools` or `disallowedTools`
5. `skills`
6. `permissionMode`
7. `maxTurns`
8. `memory`
9. `color`

### Command/Skill Frontmatter Order

1. `name` (skills only)
2. `description`
3. `allowed-tools`
4. `user-invocable` (skills only)
5. `disable-model-invocation` (skills only)

## Hook Script Requirements

Shell scripts referenced by hooks must follow these conventions:

### Shebang

Every shell script MUST start with:

```bash
#!/bin/bash
```

or

```bash
#!/usr/bin/env bash
```

### Exit Codes

Hook scripts communicate results via exit codes:

- **Exit 0**: Success, allow the operation (for PreToolUse hooks)
- **Exit 2**: Block the operation (for PreToolUse hooks — convention for explicit blocking)
- **Non-zero exit**: Generic failure

For PreToolUse hooks that need to block a tool, exit with code 2 and write an error message to stderr:

```bash
echo "BLOCKED: Cannot write to production config" >&2
exit 2
```

### Permission Decision Control

PreToolUse command hooks can output structured JSON to control permission prompts:

```bash
echo '{"hookSpecificOutput":{"permissionDecision":"allow"}}'
exit 0
```

Permission decision values:
- `"allow"` — Skip permission prompt, proceed with the tool
- `"deny"` — Block the tool silently
- `"ask"` — Show normal permission prompt (default behavior)

### Environment Variables

Hook scripts have access to these environment variables:

- `$CLAUDE_PLUGIN_ROOT` — Plugin's absolute directory path
- `$TOOL_INPUT_FILE_PATH` — File being written/edited (Write/Edit tools)
- `$TOOL_INPUT_COMMAND` — Bash command being executed (Bash tool)
- `$TOOL_INPUT` — Full tool input as JSON string

Always use `${CLAUDE_PLUGIN_ROOT}` when referencing scripts or files within the plugin:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh
```

## Naming Conventions

### File Names

All file and directory names use **kebab-case**:

- `plugin-analyzer.md` ✓
- `coding-standards.md` ✓
- `plugin_analyzer.md` ✗
- `CodingStandards.md` ✗

### Name Field Matching

The `name:` field in frontmatter MUST match the file/directory name:

```yaml
# agents/plugin-analyzer.md
---
name: plugin-analyzer  # Matches filename
---
```

```yaml
# skills/identity/SKILL.md
---
name: identity  # Matches directory name
---
```

### Agent/Skill Identifiers

When referencing agents in Task tool calls or skills in agent frontmatter, use the exact name from the `name:` field:

```yaml
# Agent frontmatter
skills: identity, plugin-structure
```

```
# Task tool call
subagent_type: "plugin-analyzer"
```

## Skill File Structure

### Multi-File Pattern

For skills exceeding 500 lines or covering multiple sub-topics:

```
skill-name/
├── SKILL.md              # Entry point (REQUIRED, max 500 lines)
├── coding-standards.md   # Detailed standards
├── workflow-patterns.md  # Common patterns
└── api-reference.md      # API specifications
```

### SKILL.md Content Guidelines

SKILL.md should contain:
- Overview and purpose
- Essential concepts (must-know)
- Quick reference tables
- Format summaries with examples
- Links to reference files

Reference files contain:
- Exhaustive field specifications
- Complete examples with commentary
- Edge cases and troubleshooting
- API signatures and type definitions

### Linking to Reference Files

Use relative markdown links from SKILL.md:

```markdown
## Additional Resources

For detailed coding standards, see [coding-standards.md](coding-standards.md).

For workflow patterns, see [workflow-patterns.md](workflow-patterns.md).
```

## Common Format Errors to Avoid

### Frontmatter Field Name Errors

| Component | CORRECT | WRONG |
|-----------|---------|-------|
| Agent | `tools: Read, Write` | ~~`allowed-tools: Read, Write`~~ |
| Command | `allowed-tools: Read, Write` | ~~`tools: Read, Write`~~ |
| Skill | `allowed-tools: Read` | ~~`tools: Read`~~ |

### Hooks.json Structure Errors

```json
// WRONG — flat array
{
  "hooks": [
    { "matcher": "Write", "type": "command", "command": "..." }
  ]
}

// WRONG — missing array under event key
{
  "hooks": {
    "PreToolUse": {
      "matcher": "Write",
      "hooks": [...]
    }
  }
}

// CORRECT — event key → array → matcher/hooks objects
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          { "type": "command", "command": "..." }
        ]
      }
    ]
  }
}
```

### Missing Required Fields

- Agent files missing `name` or `description` will fail to load
- Skill files missing `name` or `description` will fail to load
- plugin.json missing `name`, `description`, or `version` causes plugin validation errors

## File Permissions

Shell scripts must be executable:

```bash
chmod +x scripts/validate.sh
```

The change-writer agent should make all scripts executable after creating them.

## JSON Validation

All JSON files must be valid. Validate with:

```bash
python3 -m json.tool file.json > /dev/null
```

Exit code 0 = valid, non-zero = invalid.

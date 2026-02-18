# Plugin File Coding Standards

This document defines the exact formatting conventions for all plugin component files that system-maker generates. Every file type has specific frontmatter requirements, structure patterns, and common mistakes to avoid.

## Agent Files (agents/*.md)

### Frontmatter Format

```yaml
---
name: agent-name
description: "What this agent does (REQUIRED)"
model: opus | sonnet | haiku
tools: Tool1, Tool2, Tool3
skills: identity, skill-1, skill-2
permissionMode: default | acceptEdits | plan
color: "#hexcolor"
---
```

### Critical Rules

**REQUIRED FIELDS:**
- `name:` — Must match filename without .md extension
- `description:` — Clear, specific description of the agent's role

**TOOLS FIELD:**
- Field name is `tools:` — NOT `allowed-tools:`
- Common mistake: Using `allowed-tools:` (wrong field name causes silent failure — agent gets no tools)
- Comma-separated list: `tools: Read, Write, Edit, Bash`
- If omitted, agent inherits ALL available tools

**SKILLS FIELD:**
- MUST include `identity` as the first skill: `skills: identity, other-skill`
- Without identity, agent operates as generic assistant with no domain knowledge
- Comma-separated list of skill directory names

**MODEL FIELD:**
- Options: `opus` (complex reasoning), `sonnet` (general work), `haiku` (simple validation)
- Default: `sonnet` if omitted
- Use `opus` for architecture, identity writing, complex review
- Use `haiku` only for mechanical validation

**COLOR FIELD:**
- Hex color for CLI status line: `color: "#4A90D9"`
- Must be distinct from other agents' colors
- Avoid pastels — use saturated, visible colors

### Body Structure

```markdown
# Agent Name

<role>
## Role
Precise description of what this agent does.
</role>

<input>
## Input
What this agent receives and how to parse it.
</input>

<process>
## Process

1. Step-by-step instructions
2. Each step concrete and actionable
3. Use numbered lists for sequential work
</process>

<output-format>
## Output Format

Exact structure with examples:

```json
{
  "field": "value",
  "example": "concrete data"
}
```
</output-format>

<constraints>
## Constraints

- Hard rules the agent must follow
- Things the agent must NOT do
</constraints>
```

### Common Mistakes

```yaml
# WRONG — using allowed-tools instead of tools
---
name: writer
description: "Writes code"
allowed-tools: Read, Write, Edit
---

# CORRECT
---
name: writer
description: "Writes code"
tools: Read, Write, Edit
---
```

```yaml
# WRONG — missing identity skill
---
name: writer
skills: domain-api, examples
---

# CORRECT
---
name: writer
skills: identity, domain-api, examples
---
```

## Command Files (commands/*.md)

### Frontmatter Format

```yaml
---
allowed-tools: Tool1, Tool2, Tool3
description: "Brief description of what this command does"
---
```

### Critical Rules

**ALLOWED-TOOLS FIELD:**
- Field name is `allowed-tools:` — NOT `tools:`
- Commands and skills use `allowed-tools:`, agents use `tools:`
- Comma-separated: `allowed-tools: Task, AskUserQuestion, Read, Write`

**DESCRIPTION FIELD:**
- Required
- Shown in command listings
- Be specific about what the command orchestrates

### Body Structure

```markdown
# Command Title

Brief overview of what this command does.

<workflow>
## Workflow

### Step 1: Phase Name
Description of first step.

### Step 2: Phase Name
Description of second step.

Use numbered steps for sequential phases.
</workflow>
```

## Skill Files (skills/*/SKILL.md)

### Frontmatter Format

```yaml
---
name: plugin-name:skill-name
description: "What knowledge this skill provides"
user-invocable: true | false
allowed-tools: Tool1, Tool2, Tool3
---
```

### Critical Rules

**REQUIRED FIELDS:**
- `name:` — Format: `plugin-name:skill-name`. The `skill-name` portion must match the directory name.
- `description:` — Specific description of the knowledge domain

**USER-INVOCABLE FIELD:**
- `user-invocable: false` for identity skills (hidden from menu, Claude can still auto-load)
- Default: `true` if omitted

**MAX 500 LINES:**
- SKILL.md is the entry point — it gets auto-loaded into agent context
- Keep it under 500 lines ALWAYS
- Move detailed content to reference files

**ALLOWED-TOOLS FIELD:**
- Field name is `allowed-tools:` — NOT `tools:`
- Only needed if the skill uses tools (rare)

### Multi-File Structure

```
skill-name/
├── SKILL.md              # Entry point (REQUIRED, max 500 lines)
├── reference.md          # Detailed specification
├── examples.md           # Code examples
└── api-reference.md      # API docs
```

**SKILL.md** contains:
- Overview and purpose
- Key concepts
- Quick reference tables
- Links to reference files

**Reference files** contain:
- Exhaustive specifications
- Complete examples
- Edge cases and troubleshooting
- Anything that would make SKILL.md exceed 500 lines

### Body Structure

```markdown
# Skill Name

Overview of what this skill contains.

<key-concepts>
## Key Concepts

- Concept 1 with brief explanation
- Concept 2 with brief explanation
</key-concepts>

<quick-reference>
## Quick Reference

| Item | Value | Notes |
|------|-------|-------|
| ... | ... | ... |

</quick-reference>

<additional-resources>
## Additional Resources

For detailed specifications, see [reference.md](reference.md).
For code examples, see [examples.md](examples.md).
</additional-resources>
```

### Identity Skill Specifics

The identity skill (`skills/identity/`) has a special 3-file structure:

```
skills/identity/
├── SKILL.md              # Core identity, methodology, non-negotiables
├── coding-standards.md   # Frontmatter formats, file structure rules
└── workflow-patterns.md  # Step-by-step workflow patterns
```

Frontmatter:
```yaml
---
name: identity
description: "Core identity and methodology for <domain>"
user-invocable: false
---
```

## Hooks (hooks/hooks.json)

### Correct Format

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
            "prompt": "Review this code: $ARGUMENTS. Check for domain-specific anti-patterns. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
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
            "prompt": "Verify all deliverables exist and tests pass. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### Critical Rules

**EVENT-BASED STRUCTURE:**
- Top-level keys are event names: `PreToolUse`, `PostToolUse`, `Stop`, etc.
- Each event contains an ARRAY of matcher groups
- Each matcher group has `matcher` and `hooks` fields

**WRONG FORMAT (flat array):**
```json
// NEVER generate this old format
{
  "hooks": [
    { "matcher": "Write", "type": "command", "command": "..." }
  ]
}
```

**HOOK TYPES:**

1. **command** — Shell script execution
   ```json
   {
     "type": "command",
     "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check.sh"
   }
   ```

2. **prompt** — LLM-based validation
   ```json
   {
     "type": "prompt",
     "prompt": "Check this code: $ARGUMENTS. Respond {\"ok\": true/false}.",
     "model": "haiku"
   }
   ```

3. **agent** — Full agent with tools
   ```json
   {
     "type": "agent",
     "prompt": "Verify deliverables. Respond {\"ok\": true/false}.",
     "timeout": 60
   }
   ```

**SCRIPT PATHS:**
- Always use `${CLAUDE_PLUGIN_ROOT}/scripts/filename.sh`
- Never hardcode absolute paths
- Make scripts executable: `chmod +x scripts/*.sh`

**MATCHER FIELD:**
- For tool-based events: pipe-separated tool names `"Write|Edit|Bash"`
- For non-tool events (Stop, SessionStart): empty string `""`

### Required Hooks for Quality Plugins

Every plugin should have:

1. **PreToolUse (command)**: Block dangerous operations
2. **PostToolUse (prompt)**: Domain-specific linting
3. **Stop (agent)**: Verify work completed

Example:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/block-dangerous-commands.sh"
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
            "prompt": "Check the written code for domain-specific anti-patterns and deprecated APIs: $ARGUMENTS. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"specific issue\"}.",
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
            "prompt": "Verify all required files exist, code compiles, and tests pass. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
            "timeout": 90
          }
        ]
      }
    ]
  }
}
```

## Plugin Manifest (plugin.json)

### Format

```json
{
  "name": "plugin-name",
  "description": "One-line description of what this plugin does",
  "version": "1.0.0"
}
```

**CRITICAL**: `plugin.json` must contain ONLY `name`, `description`, and `version`. Extra fields (`role`, `keywords`, `companions`) cause Claude Code to silently fail to load the plugin. Use `ctl.json` for role and companions metadata.

### Rules

- File location: `.claude-plugin/plugin.json`
- `name` field must match plugin directory name
- `name` must match regex: `^[a-z]+-[a-z][-a-z]*$` (format: `<type>-<domain>-<tech>-<role>`)
- `version` uses semantic versioning: `major.minor.patch`
- **Only 3 fields allowed**: `name`, `description`, `version` — nothing else

## LSP Configuration (.lsp.json)

### Single Language Example

```json
{
  "lsp": {
    "c": {
      "command": "clangd",
      "args": ["--background-index", "--compile-commands-dir=build"]
    }
  }
}
```

### Multi-Language Example

```json
{
  "lsp": {
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"]
    },
    "python": {
      "command": "pylsp",
      "args": []
    }
  }
}
```

### When to Include

Include .lsp.json when the domain uses:
- C/C++ → clangd
- Go → gopls
- Rust → rust-analyzer
- TypeScript → typescript-language-server
- Python → pylsp
- Java → jdtls

Skip for shell scripts, simple scripting languages without LSP servers.

## MCP Configuration (.mcp.json)

### Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.js"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

### Rules

- Only create .mcp.json if MCP servers actually EXIST
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- If MCP servers are "needed but don't exist", mark as TODO in architecture — do NOT create the file

## Common Cross-File Mistakes

### 1. Inconsistent Skill References

```yaml
# Agent references skill that doesn't exist
# agents/writer.md
skills: identity, zephyr-api, devicetree

# But skills directory only has:
# skills/identity/
# skills/zephyr-apis/    <-- name mismatch (apis vs api)
```

Fix: Skill names in agent frontmatter must EXACTLY match skill directory names.

### 2. Missing Identity Preload

```yaml
# agents/code-writer.md
skills: domain-api, examples   # WRONG — missing identity
```

Fix: Every agent must include `identity` in skills list.

### 3. Script Referenced But Not Executable

```json
// hooks.json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
}
```

But the script doesn't have execute permissions. Fix:
```bash
chmod +x scripts/validate.sh
```

### 4. Wrong Frontmatter Field Names

Most common mistake — mixing up `tools:` vs `allowed-tools:`:

| Component | Correct Field | Wrong Field |
|-----------|--------------|-------------|
| Agent | `tools:` | ~~allowed-tools:~~ |
| Command | `allowed-tools:` | ~~tools:~~ |
| Skill | `allowed-tools:` | ~~tools:~~ |

## Markdown Structure Conventions

### Use XML Tags for Determinism

```markdown
<section-name>
## Section Title

Content here.
</section-name>
```

Benefits:
- Unambiguous section boundaries
- Prevents content bleeding between sections
- Easier for Claude to parse and follow instructions

### Code Blocks with Language Tags

Always specify language:
```markdown
```json
{ "valid": "json" }
```

```yaml
name: example
```

```bash
#!/bin/bash
echo "example"
```
```

### Tables for Specifications

Use tables for field definitions, option lists, comparisons:

```markdown
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Identifier |
```

### Examples After Every Rule

Every specification should include a concrete example:

```markdown
// BAD
"Use proper frontmatter format."

// GOOD
"Use proper frontmatter format:
```yaml
---
name: agent-name
description: "What it does"
---
```"
```

## JSON Formatting

### Indentation
- 2 spaces (not tabs)
- Consistent throughout file

### Valid JSON
- No trailing commas
- All strings double-quoted
- No comments (JSON doesn't support comments)

### Validation
Test all JSON files:
```bash
python3 -m json.tool plugin.json > /dev/null
python3 -m json.tool hooks.json > /dev/null
python3 -m json.tool .mcp.json > /dev/null
python3 -m json.tool .lsp.json > /dev/null
```

## File Naming Conventions

- **Directories**: `kebab-case` (e.g., `plugin-structure`, `zephyr-api`)
- **Agent files**: `kebab-case.md` (e.g., `code-writer.md`)
- **Command files**: `kebab-case.md` (e.g., `start-project.md`)
- **Skill directories**: `kebab-case` (e.g., `identity`, `domain-patterns`)
- **Scripts**: `kebab-case.sh` (e.g., `validate-code.sh`)
- **No spaces, no underscores, no uppercase** except in:
  - `SKILL.md` (always uppercase, special file)
  - Environment variables in scripts (`$TOOL_INPUT_FILE_PATH`)

## Shell Script Standards

### Shebang
Always start with:
```bash
#!/bin/bash
```

### Make Executable
```bash
chmod +x scripts/*.sh
```

### Use Environment Variables
Available in hooks:
- `$TOOL_INPUT_FILE_PATH` — file being written/edited
- `$TOOL_INPUT_COMMAND` — bash command being run
- `${CLAUDE_PLUGIN_ROOT}` — plugin directory path

### Exit Codes
- `exit 0` — success, allow operation
- `exit 2` — block operation (PreToolUse only)
- `exit 1` — general failure

### Example Script
```bash
#!/bin/bash
# Block writes to sensitive files

if echo "$TOOL_INPUT_FILE_PATH" | grep -qE '(\.env|credentials|secrets)'; then
  echo "BLOCKED: Cannot write to sensitive file" >&2
  exit 2
fi

exit 0
```

## Summary Checklist

When generating plugin files, verify:

- [ ] Agent files use `tools:`, not `allowed-tools:`
- [ ] Command/skill files use `allowed-tools:`, not `tools:`
- [ ] All agents include `identity` in skills list
- [ ] All agents have `name:` and `description:`
- [ ] SKILL.md files are under 500 lines
- [ ] Identity skill has 3 files (SKILL.md, coding-standards.md, workflow-patterns.md)
- [ ] Hooks.json uses event-based structure (not flat array)
- [ ] All three hook types are used (command, prompt, agent)
- [ ] Script paths use `${CLAUDE_PLUGIN_ROOT}/scripts/`
- [ ] All scripts are executable (chmod +x)
- [ ] All JSON files are valid (test with json.tool)
- [ ] Plugin name matches regex `^[a-z]+-[a-z][-a-z]*$` (format: `<type>-<domain>-<tech>-<role>`)
- [ ] No CLAUDE.md file exists in plugin
- [ ] Skill names in agent frontmatter match skill directory names exactly

## Knowledge vs Role File Placement

When a discipline has a knowledge plugin, file placement follows these rules:

### Goes in Knowledge Plugin
- Domain API reference skills (e.g., `zephyr-kernel/`, `devicetree-kconfig/`)
- Hardware target skills (e.g., `esp32-hardware/`, `nordic-hardware/`)
- Design pattern skills (e.g., `design-patterns/`)
- Build system reference skills (e.g., `build-system/`)
- Domain-wide safety scripts (e.g., `block-dangerous-commands.sh`, `check-environment.sh`)
- `.lsp.json` (duplicated in both — same language servers needed)

### Goes in Role Plugin
- `skills/identity/` — role-specific persona, methodology, non-negotiables
- `agents/` — all subagent definitions
- `commands/` — all workflow orchestration
- Role-specific skills (e.g., grader's `grading-rubrics/`, `scoring-engine/`)
- Role-specific hooks (e.g., engineer's anti-pattern linting, grader's report validation)
- Role-specific scripts (e.g., `enforce-sysbuild.sh`, `restrict-file-writes.sh`)

### Agent Skill References

Agents in role plugins can reference skills from the knowledge companion in their frontmatter `skills:` list. At runtime, the companion plugin is loaded via `--plugin-dir`, making its skills available to all agents.

Example agent frontmatter in the engineer plugin:
```
skills: identity, zephyr-kernel, devicetree-kconfig, build-system
```
Here, `identity` is from the role plugin, while `zephyr-kernel`, `devicetree-kconfig`, and `build-system` are from the knowledge companion.

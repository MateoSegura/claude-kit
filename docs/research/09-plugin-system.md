# Claude Code Plugin System - Distributing Agent Profiles

## Core Insight

A Claude Code plugin IS the agent profile. The plugin system provides:
- Installation (`claude plugin install`)
- Namespacing (no conflicts between plugins)
- Distribution (via marketplace or git)
- Updates (`claude plugin update`)
- Composition (multiple plugins coexist)
- Context efficiency (subagent skills only load when relevant)

## Plugin Directory Structure

```
embedded-zephyr-plugin/
├── .claude-plugin/
│   └── plugin.json              # Manifest (name, version, description)
├── commands/                     # User-invokable skills
│   ├── new-driver.md            #   /embedded-zephyr:new-driver
│   ├── ble-service.md           #   /embedded-zephyr:ble-service
│   └── review.md                #   /embedded-zephyr:review
├── skills/                       # Auto-invoked by Claude when task matches
│   ├── zephyr-api-lookup/
│   │   └── SKILL.md             # Claude auto-uses when writing Zephyr code
│   ├── datasheet-reader/
│   │   └── SKILL.md
│   └── vendor-search/
│       └── SKILL.md
├── agents/                       # Subagents with own context windows
│   ├── firmware-implementer.md   # Full write access, domain expert
│   └── firmware-reviewer.md      # Read-only reviewer
├── hooks/
│   └── hooks.json                # Plugin-scoped hooks
├── .mcp.json                     # MCP server configurations
├── .lsp.json                     # LSP server configurations (optional)
└── statusline.sh                 # Custom status bar display (optional)
```

**Important**: commands/, agents/, skills/, hooks/ go at the plugin ROOT, not inside .claude-plugin/. Only plugin.json goes inside .claude-plugin/.

## Plugin Manifest

```json
{
  "name": "embedded-zephyr",
  "description": "Zephyr RTOS embedded systems expert with drivers, BLE, networking, TLS, and hardware interfaces.",
  "version": "1.2.0",
  "author": {
    "name": "Your Org"
  },
  "repository": "https://github.com/your-org/claude-embedded-zephyr",
  "license": "MIT"
}
```

The `name` field becomes the namespace: `/embedded-zephyr:new-driver`, `/embedded-zephyr:ble-service`, etc.

## Commands vs Skills

| Type | Location | Invocation | Context |
|---|---|---|---|
| **Commands** | `commands/*.md` | User types `/plugin-name:command` | Runs in main conversation |
| **Skills** | `skills/*/SKILL.md` | Claude auto-invokes based on task | Injected when relevant |

Skills are context-efficient - they only load when Claude determines they're relevant based on the `description` field. Commands are explicit user actions.

## Subagent Definition (In Plugin)

```markdown
# agents/firmware-implementer.md
---
name: firmware-implementer
description: >
  Expert Zephyr RTOS firmware implementer. Use proactively for any
  embedded implementation task.
model: opus
tools: Read, Edit, Write, Bash, Glob, Grep
mcpServers:
  - zephyr-docs
  - datasheet-reader
  - github-vendor
skills:
  - zephyr-api-lookup
  - datasheet-reader
  - vendor-search
memory: user
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/hooks/verify-docs-read.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/hooks/check-zephyr-patterns.sh"
---

[Identity and instructions here...]
```

Key subagent frontmatter fields:
- `skills`: Preloaded into subagent context (NOT inherited from parent)
- `memory`: `user` | `project` | `local` - persistent cross-session learning
- `hooks`: Scoped to this subagent only
- `mcpServers`: Only loaded when this subagent is active
- `model`: Can use cheaper models for simple tasks
- `tools`: Restrict what the subagent can do
- `permissionMode`: Override permission behavior

## Plugin Hooks

```json
// hooks/hooks.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/hooks/check-patterns.sh",
          "statusMessage": "Checking patterns..."
        }]
      }
    ]
  }
}
```

Plugin hooks apply whenever the plugin is installed. Subagent hooks (in frontmatter) apply only when that specific subagent runs.

## MCP Servers (In Plugin)

```json
// .mcp.json
{
  "mcpServers": {
    "zephyr-docs": {
      "command": "npx",
      "args": ["-y", "@your-org/zephyr-docs-mcp"],
      "env": { "ZEPHYR_BASE": "${ZEPHYR_BASE:-/opt/zephyr}" }
    },
    "github-vendor": {
      "command": "npx",
      "args": ["-y", "@your-org/github-search-mcp"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

## Installation Methods

### From Marketplace
```bash
claude plugin install @your-org/embedded-zephyr
```

### From Local Directory (Development/Testing)
```bash
claude --plugin-dir ./embedded-zephyr-plugin
```

### Team Marketplace (Auto-Available)
```json
// .claude/settings.json (committed to repo)
{
  "pluginMarketplaces": [
    "https://github.com/your-org/claude-plugins"
  ]
}
```

## Updates
```bash
claude plugin update embedded-zephyr
```
Or if using `--plugin-dir` pointing to a local git checkout, `git pull` updates it.

## Multi-Profile (Multiple Plugins)

```bash
claude plugin install @your-org/embedded-zephyr
claude plugin install @your-org/cloud-k8s
```

Both coexist. Claude auto-delegates to the right subagent/skills based on task. No manual switching needed. For explicit profile forcing:

```bash
claude --agent firmware-implementer
```

## Transparency

The plugin layers ON TOP of existing user config. Installing a plugin does not modify:
- User's CLAUDE.md
- User's settings.json
- User's existing hooks
- Project configuration

Everything composes cleanly via namespacing.

## Status Bar Integration

The statusline JSON includes `agent.name` when running with `--agent` or when a subagent is active. Plugins can bundle a `statusline.sh` that shows the active profile.

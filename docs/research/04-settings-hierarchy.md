# Claude Code Settings Hierarchy

## Precedence Order (Highest to Lowest)

```
1. MANAGED SETTINGS        ← Cannot be overridden by anything below
   /etc/claude-code/managed-settings.json (Linux/WSL)
   /Library/Application Support/ClaudeCode/managed-settings.json (macOS)
   C:\Program Files\ClaudeCode\managed-settings.json (Windows)
   OR: Server-managed via Admin Console (takes precedence over file-based)

2. CLI ARGUMENTS           ← Temporary session overrides
   --model, --settings, --allowed-tools, --agent, --mcp-config, etc.

3. LOCAL SETTINGS          ← Personal per-project overrides (gitignored)
   .claude/settings.local.json

4. PROJECT SETTINGS        ← Shared team settings (committed to git)
   .claude/settings.json

5. USER SETTINGS           ← Personal defaults across all projects (lowest)
   ~/.claude/settings.json
```

## What Each Level Controls

### Managed (Organization)
- Permission rules (allow/deny/ask for tools)
- Hooks (org-wide enforcement)
- Environment variables
- Model selection
- MCP server restrictions
- Sandbox configuration
- **Managed-only keys** (see below)

### Project (Team)
- Project-specific hooks
- Project-specific permissions
- Shared MCP server configs (.mcp.json)
- Project CLAUDE.md and rules

### User (Personal)
- Personal preferences (model, language)
- Personal hooks and workflows
- User-level skills
- User-level MCP servers
- User CLAUDE.md

### Local (Temporary/Machine-Specific)
- Machine-specific overrides
- Sensitive local config
- Experimental features

## Settings File Locations

| Purpose | File |
|---|---|
| User settings | `~/.claude/settings.json` |
| User memory | `~/.claude/CLAUDE.md` |
| User agents | `~/.claude/agents/*.md` |
| Project settings | `.claude/settings.json` |
| Project local | `.claude/settings.local.json` |
| Project memory | `./CLAUDE.md` or `.claude/CLAUDE.md` |
| Project local memory | `./CLAUDE.local.md` |
| Project rules | `.claude/rules/*.md` |
| Project agents | `.claude/agents/*.md` |
| Project skills | `.claude/commands/*.md` or `.claude/skills/*/SKILL.md` |
| MCP config | `.mcp.json` (project) or in settings.json |
| Managed settings | `/etc/claude-code/managed-settings.json` |
| Managed memory | `/etc/claude-code/CLAUDE.md` |
| Managed MCP | `/etc/claude-code/managed-mcp.json` |
| Auth/preferences | `~/.claude.json` |
| Auto-learned memory | `~/.claude/projects/<project>/memory/MEMORY.md` |

## Key Architectural Point

When multiple settings define the same key, the highest-priority source wins.
Permission rules are evaluated in order: deny > ask > allow. The first matching rule wins.
Hooks from all applicable scopes run (they don't override each other - they accumulate).

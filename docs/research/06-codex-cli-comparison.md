# OpenAI Codex CLI - Full Comparison with Claude Code

## Config Structure Comparison

| Concept | Claude Code | Codex CLI |
|---|---|---|
| **Config format** | JSON | TOML |
| **User config** | `~/.claude/settings.json` | `~/.codex/config.toml` |
| **Project config** | `.claude/settings.json` | `.codex/config.toml` |
| **Local override** | `.claude/settings.local.json` | N/A (profiles instead) |
| **Instructions file** | `CLAUDE.md` | `AGENTS.md` |
| **Override instructions** | `CLAUDE.local.md` | `AGENTS.override.md` |
| **Global instructions** | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` |
| **Managed settings** | `/etc/claude-code/managed-settings.json` | `/etc/codex/managed_config.toml` |
| **Hard constraints** | Part of managed-settings.json | Separate `/etc/codex/requirements.toml` |
| **Rules dir** | `.claude/rules/*.md` | N/A |
| **Skills dir** | `.claude/commands/` or `.claude/skills/` | `.agents/skills/` |
| **MCP config** | `mcpServers` in settings.json or `.mcp.json` | `[mcp_servers.*]` in config.toml |
| **Non-interactive** | `claude -p "prompt"` | `codex exec "prompt"` |
| **Env var override** | `CLAUDE_CODE_CONFIG_DIR` | `CODEX_HOME` |

## Hooks Comparison (Critical Asymmetry)

| Feature | Claude Code | Codex CLI |
|---|---|---|
| Event types | **14 events** | **~1 event** (`agent-turn-complete`) |
| Can block actions | **Yes** (PreToolUse can deny) | **No** (notification-only) |
| Hook types | command, prompt, **agent** | External command only |
| Matchers | Regex on tool names | None |
| Async hooks | Yes | No |
| Per-subagent hooks | Yes (frontmatter) | No |

**This is the biggest asymmetry.** Claude Code's hook system enables deterministic enforcement. Codex hooks are notifications only - they cannot intercept, block, or inject context.

## Instructions File Behavior (Key Difference)

### Claude Code (CLAUDE.md)
- Root CLAUDE.md: auto-loaded at startup
- Subdirectory CLAUDE.md: **NOT auto-loaded** (empirically verified)
- Path-filtered rules: **NOT auto-injected**

### Codex CLI (AGENTS.md)
- Chains automatically from root down to CWD:
  ```
  ~/.codex/AGENTS.md → repo-root/AGENTS.md → src/AGENTS.md → src/lib/AGENTS.md
  ```
- `AGENTS.override.md` takes priority at each level
- Configurable: `project_doc_fallback_filenames`, `project_doc_max_bytes` (32 KiB default)
- **Codex handles subdirectory instructions better than Claude for this reason**

## Enterprise Comparison

| Feature | Claude Code Teams | Codex Business |
|---|---|---|
| Cloud-pushed settings | Yes (admin console) | Yes (ChatGPT admin) |
| Polling interval | Hourly | At startup + periodic |
| MDM support | Not documented | macOS `com.openai.codex` domain |
| RBAC | Not documented | Yes, via ChatGPT admin groups |
| Lock out user hooks | `allowManagedHooksOnly: true` | Via requirements.toml |
| Disable yolo mode | `disableBypassPermissionsMode` | requirements.toml blocks `danger-full-access` |
| Audit/compliance | Enterprise only (API) | Enterprise only (API) |
| SSO | Enterprise only | Enterprise (SAML) |

## What Codex Has That Claude Doesn't

| Feature | Codex | Claude Equivalent |
|---|---|---|
| Profiles | `[profiles.fast]` in config.toml | None (use CLI flags) |
| OS-level sandbox | Seatbelt/Landlock/seccomp | Trust-based permissions |
| Cloud execution | `codex cloud exec` | None |
| Run as MCP server | `codex mcp-server` | None |
| Output schema | `--output-schema schema.json` | `--json-schema` |
| Shell env policy | Fine-grained env var filtering | None |
| Open source | Yes (GitHub) | No |
| Fallback filenames | `project_doc_fallback_filenames` | None |
| AGENTS.md auto-chaining | Root to CWD | Root only |

## What Claude Has That Codex Doesn't

| Feature | Claude Code | Codex Equivalent |
|---|---|---|
| 14 hook events | Full lifecycle control | 1 notification event |
| Blocking hooks | PreToolUse can deny operations | Cannot block |
| Agent hooks | `type: "agent"` spawns full agents | N/A |
| Prompt hooks | `type: "prompt"` for LLM evaluation | N/A |
| Built-in TaskList | Persistent across compaction | No equivalent |
| Plugin system | Full plugin ecosystem | Skills only |
| Subagent memory | Persistent cross-session learning | N/A |
| Subagent hooks | Scoped to individual agents | N/A |
| Path-scoped rules | .claude/rules/ with frontmatter | N/A |

## Codex Skill System

```
my-skill/
  SKILL.md              # Required: name, description, instructions
  scripts/              # Optional: executable code
  references/           # Optional: documentation
  assets/               # Optional: templates
  agents/openai.yaml    # Optional: UI, policy, dependencies
```

Discovery locations (priority order):
1. `.agents/skills/` in CWD
2. Parent `.agents/skills/`
3. `$REPO_ROOT/.agents/skills/`
4. `$HOME/.agents/skills/` or `$HOME/.codex/skills/`
5. `/etc/codex/skills/`
6. Built-in

## Pricing Reference

| Codex Plan | Price | Local Messages/5hr |
|---|---|---|
| Free/Go | $0 | Limited |
| Plus | $20/mo | 45-225 |
| Pro | $200/mo | 300-1500 |
| Business | $30/user/mo | Same as Plus |
| Enterprise | Contact sales | Custom |

## Decision: Claude Code Selected

Claude Code was selected as the primary platform due to:
1. Superior hook system (14 events, blocking, agent hooks)
2. Plugin ecosystem for distribution
3. Subagent system with memory, hooks, and MCP per-agent
4. Better deterministic enforcement capabilities
5. Enterprise managed settings with `allowManagedHooksOnly`

Codex remains valuable for comparison benchmarks and specific use cases (cloud execution, open-source CI integration).

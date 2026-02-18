# Claude Code Hooks - Complete Reference

## Overview

Hooks are the only **deterministic** event-driven mechanism in Claude Code. They fire reliably at lifecycle events regardless of conversation state or compaction.

## All 14 Hook Events

| Event | When It Fires | Can Block? | Matcher Input |
|---|---|---|---|
| **SessionStart** | Session begins, resumes, or compacts | No | `startup`, `resume`, `clear`, `compact` |
| **UserPromptSubmit** | User submits a prompt | Yes | None |
| **PreToolUse** | Before any tool executes | Yes (can deny) | Tool name (e.g., `Bash`, `Edit\|Write`, `mcp__server__tool`) |
| **PermissionRequest** | Permission dialog appears | Yes | Tool name |
| **PostToolUse** | After a tool succeeds | No | Tool name |
| **PostToolUseFailure** | After a tool fails | No | Tool name |
| **Notification** | Claude needs attention | No | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |
| **SubagentStart** | A subagent begins execution | No | Agent type name |
| **SubagentStop** | A subagent completes | Yes | Agent type name |
| **Stop** | Claude finishes responding | Yes | None |
| **TeammateIdle** | Agent team member about to go idle | Yes | None |
| **TaskCompleted** | A task is marked complete | Yes | None |
| **PreCompact** | Before context compaction | No | `manual`, `auto` |
| **SessionEnd** | Session terminates | No | `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |

## Three Hook Types

### 1. Command Hook (Shell Script)
Runs a shell command. Receives JSON on stdin, communicates via exit codes and stdout.

```json
{
  "type": "command",
  "command": "/path/to/script.sh",
  "timeout": 600,
  "async": false,
  "statusMessage": "Running validation..."
}
```

### 2. Prompt Hook (LLM Evaluation)
Uses a small, fast LLM to evaluate a condition. Returns `{"ok": true}` or `{"ok": false, "reason": "..."}`.

```json
{
  "type": "prompt",
  "prompt": "Check if all tests are passing. $ARGUMENTS",
  "timeout": 30
}
```

### 3. Agent Hook (Full Agent with Tools)
Spins up a full agent that can read files, run tools, and do real work.

```json
{
  "type": "agent",
  "prompt": "Read plan/status.md and summarize current project state.",
  "timeout": 60
}
```

## Exit Code Behavior

| Exit Code | Behavior |
|---|---|
| **0** | Action proceeds. stdout added as context. |
| **2** | Blocking error. stderr fed back to Claude as feedback. |
| **Other** | Non-blocking. stderr shown in verbose mode only. |

## JSON Output Format (Exit 0)

```json
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "warning message to inject",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "explanation",
    "updatedInput": {},
    "additionalContext": "context text"
  }
}
```

## Common Input Fields (All Hooks Receive)

```json
{
  "session_id": "unique_session_id",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions",
  "hook_event_name": "EventName"
}
```

## Tool-Specific Input (PreToolUse/PostToolUse)

```json
{
  "tool_name": "Bash|Edit|Write|Read|Glob|Grep|WebFetch|WebSearch|Task",
  "tool_input": {
    "command": "...",
    "file_path": "...",
    "content": "..."
  },
  "tool_use_id": "toolu_..."
}
```

## Matchers

Matchers are **regex patterns** that filter when hooks fire:

- Tool hooks: match against tool name (`Bash`, `Edit|Write`, `mcp__server__tool`)
- SessionStart: match against source (`startup`, `resume`, `clear`, `compact`)
- PreCompact: match against trigger (`manual`, `auto`)
- MCP tools: `mcp__<server>__<tool>` pattern (e.g., `mcp__memory__.*`)

## Hook Configuration Locations

| Scope | File | Applies To |
|---|---|---|
| User | `~/.claude/settings.json` | All projects |
| Project | `.claude/settings.json` | This repo, all users |
| Local | `.claude/settings.local.json` | This repo, only you |
| Managed | `/etc/claude-code/managed-settings.json` | All users (org-enforced) |
| Plugin | `hooks/hooks.json` inside plugin | When plugin is enabled |
| Subagent | YAML frontmatter in agent .md file | While that subagent is active |

## Environment Variables Available in Hooks

- `$CLAUDE_PROJECT_DIR` - Project root directory
- `${CLAUDE_PLUGIN_ROOT}` - Plugin root (for plugin hooks)
- `$CLAUDE_ENV_FILE` - Environment file path (SessionStart only)

## Critical Architectural Note

Hooks **cannot** directly invoke skills or tools. They can only:
- Run shell commands
- Evaluate prompts via LLM
- Spawn agent instances that have tool access
- Inject context via stdout/systemMessage
- Block operations via exit code 2 or permissionDecision: "deny"

The `type: "agent"` hook is the closest to "trigger a skill" - it gets a full agent with tool access that can read/write files.

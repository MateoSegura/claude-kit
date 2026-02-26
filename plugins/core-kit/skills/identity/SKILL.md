---
name: core-kit:identity
description: "Auto-routing intelligence layer for claude-kit. Makes plugin capabilities accessible through natural language without explicit slash commands."
user-invocable: false
---

# core-kit — Auto-Routing Intelligence

core-kit is the transparent orchestration layer for claude-kit. It eliminates the need for users to memorize slash commands by automatically mapping natural language intents to loaded skills, commands, and agents.

## Why This Exists

claude-kit plugins inject domain knowledge, specialized agents, and behavioral hooks into Claude Code sessions. Without core-kit, accessing these capabilities requires knowing the exact slash command:

```
/embedded-zephyr-engineer:develop    ← user must know this exists
/system-maker:make-team              ← user must know this exists
/cloud-python-grader:grade           ← user must know this exists
```

With core-kit, the user just talks naturally:

```
"implement the BLE peripheral"       → auto-invokes engineer develop
"create a new plugin for React"      → auto-invokes system-maker:make-team
"review my code and score it"        → auto-invokes grader grade
```

## Theoretical Foundation

core-kit operates at the L1 cache layer of the context hierarchy (see `docs/theory-context-cache.md`). Its routing rules are loaded into every conversation via `~/.claude/rules/`, giving them the highest attention priority and binding authority.

The mechanism exploits three properties of transformer attention:

1. **Rules files have binding authority** — Claude Code treats `~/.claude/rules/*.md` as instructions that "OVERRIDE any default behavior." This is the strongest injection point available outside managed configuration.

2. **Contextual knowledge overrides parametric defaults** — Claude's default behavior is to wait for explicit slash commands. The routing rules override this with explicit instructions to scan and auto-invoke. Per Arora et al. (2025), contextual instructions reduce parametric uncertainty exponentially.

3. **The available skills list is already in context** — Every loaded skill appears in the system-reminder with its name and description. The routing rules simply tell Claude to USE this information proactively rather than passively.

## Architecture

core-kit has two components:

### 1. Rules File (Main Conversation — L1 Cache)
`~/.claude/rules/claude-kit-autoroute.md` — installed by `claude-kit setup`, removed by `claude-kit restore`. Contains the binding routing instructions that Claude must follow. This is the active mechanism that makes auto-routing work.

### 2. Skills (Agent Context — L2 Cache)
The `routing` skill provides comprehensive intent mapping reference for agents that need routing awareness. The `identity` skill (this file) provides context about what core-kit is and why it exists.

## What This Plugin Does NOT Contain

- No agents — routing happens in the main conversation, not in subagents
- No commands — the whole point is to avoid explicit commands
- No hooks — routing is instruction-based, not event-based
- No MCP servers — no external services needed

## Relationship to Other Plugins

core-kit is complementary to all other plugins. It does not modify, override, or conflict with any plugin's skills, agents, hooks, or commands. It adds a routing layer ON TOP of existing functionality:

```
User message → core-kit routing rules → Skill tool invocation → Plugin command
```

All plugin behavior remains unchanged. core-kit only affects HOW the user reaches that behavior (natural language vs slash commands).

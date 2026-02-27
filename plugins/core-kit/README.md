# core-kit

> **Role:** Knowledge companion · **Version:** 0.1.0

Dispatch intelligence for claude-kit — maps natural language intents to loaded skills and commands transparently.

This is a **universal knowledge plugin** that auto-loads with every team session. It provides dispatch intelligence that enables users to access claude-kit's full capabilities through natural conversation without memorizing slash commands.

---

## How It Works

core-kit operates through two components:

### 1. Rules File (installed by `claude-kit setup`)

A rules file at `~/.claude/rules/claude-kit.md` provides binding instructions that tell Claude to scan loaded skills for intent matches on every user message. This is the active mechanism — rules files have the highest non-managed authority in Claude Code's configuration hierarchy.

### 2. Skills (auto-loaded with every team)

The `routing` skill provides edge-case guidance for ambiguous, negative, and compound intent handling that supplements the dispatch algorithm.

### Before core-kit:
```
User: "review my code and tell me what's wrong"
Claude: "Sure, I can help review your code..."  ← generic response
```

### After core-kit:
```
User: "review my code and tell me what's wrong"
Claude: [invokes grader:grade]  ← full plugin workflow with rubrics, scoring, hooks
```

---

## Skills Inventory

| Skill | Purpose |
|-------|---------|
| `routing` | Edge-case guidance for intent dispatch — ambiguous, negative, and compound intent handling |

---

## Installation

core-kit auto-loads with every team via `domain: "universal"`. The rules file must be installed separately:

```bash
claude-kit setup    # installs rules file + statusline
claude-kit restore  # removes both
```

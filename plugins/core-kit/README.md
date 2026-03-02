# core-kit

> **Role:** Knowledge companion · **Version:** 0.2.0

Auto-routing intelligence for claude-kit — maps natural language intents to loaded skills and commands transparently.

This is a **universal knowledge plugin** that auto-loads with every team session. It provides routing intelligence that enables users to access claude-kit's full capabilities through natural conversation without memorizing slash commands.

---

## How It Works

core-kit operates through two components:

### 1. Rules File (installed by `claude-kit setup`)

A rules file at `~/.claude/rules/claude-kit-autoroute.md` provides binding instructions that tell Claude to scan loaded skills for intent matches on every user message. This is the active mechanism — rules files have the highest non-managed authority in Claude Code's configuration hierarchy.

### 2. Skills (auto-loaded with every team)

The `routing` skill provides comprehensive intent-to-skill mapping reference. The `identity` skill explains core-kit's role in the architecture.

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
| `routing` | Comprehensive intent-to-skill mapping patterns, team resolution logic, and routing theory. Reference: [intent-map.md](skills/routing/intent-map.md) |
| `identity` | What core-kit is, why it exists, and how it fits in the architecture |

---

## Installation

core-kit auto-loads with every team via `domain: "universal"`. The rules file must be installed separately:

```bash
claude-kit setup    # installs rules file + statusline
claude-kit restore  # removes both
```

---

## Theoretical Foundation

See [docs/theory-context-cache.md](../../docs/theory-context-cache.md) for the full theory. In summary:

- **Rules files are L1 cache** — always loaded, binding authority, every token attends to them
- **Skill descriptions are L2 cache** — listed in system-reminder, inform matching but lack binding authority
- **The combination** creates a transparent routing layer that exploits the transformer's preference for contextual over parametric knowledge

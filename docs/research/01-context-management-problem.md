# The Context Management Problem

## Core Thesis

Long-session degradation in AI coding agents is not primarily a "hallucination" problem - it is a **context management** problem. When conversations get long:

1. The high-level goal gets buried under implementation details
2. Context compaction loses critical architectural decisions
3. The model starts solving local problems that contradict global plans
4. There is no persistent "source of truth" outside the conversation window

## Root Causes

### Information Loss During Compaction
When Claude Code's context window fills up, it automatically compacts (summarizes) earlier messages. This process:
- Preserves the general gist but loses specific decisions
- Drops implementation details that matter for consistency
- Cannot distinguish between "important architectural decision" and "routine code change"

### No Persistent State Mechanism
The conversation itself is ephemeral. Without external state:
- The model has no way to "re-orient" after compaction
- Task progress lives only in the conversation, which gets summarized away
- Domain-specific rules that were discussed early get lost

### Context Pollution
In a monorepo with multiple domains (frontend, embedded, cloud), loading all domain context at once:
- Wastes context window space on irrelevant rules
- Increases the chance of the model conflating patterns from different domains
- Makes compaction more aggressive (more content to summarize)

## What Survives Compaction

Based on empirical testing, only these mechanisms reliably persist:

| Mechanism | Survives Compaction? | How? |
|---|---|---|
| Root CLAUDE.md | Yes | Re-injected into system prompt every turn |
| Global rules (.claude/rules/*.md without path filter) | Yes | Loaded at startup, re-injected every turn |
| Built-in TaskList (TaskCreate/TaskUpdate) | Yes | Stored separately from conversation |
| Hooks | Yes (deterministic) | Event-driven, independent of conversation |
| Files on disk (plan/status.md) | Yes (if re-read) | Persist on filesystem, but must be explicitly read |

| Mechanism | Survives Compaction? | Why Not? |
|---|---|---|
| Subdirectory CLAUDE.md files | No | NOT auto-loaded (empirically verified) |
| Path-filtered rules | No | NOT auto-injected when matching files are touched |
| Conversation instructions | No | Get summarized away during compaction |
| "Remember to do X" type instructions | No | Probabilistic, degrades over time |

## The Solution Framework

The fix requires making critical behaviors **deterministic** rather than relying on the model "remembering" to do things:

1. **Hooks** for enforcement - guaranteed to fire at lifecycle events
2. **Persistent file state** (plan/, status.log) - survives outside the conversation
3. **Minimal root CLAUDE.md** - always loaded, carries bootstrap instructions
4. **Plugin system** - packages domain expertise into installable, context-efficient units
5. **Subagents** - isolate domain context into separate context windows

See: [02-claude-code-hooks.md](./02-claude-code-hooks.md), [10-deterministic-workflow-patterns.md](./10-deterministic-workflow-patterns.md)

---
name: core-kit:routing
description: "Comprehensive intent-to-skill routing patterns for claude-kit. Maps natural language to loaded plugin commands with team resolution logic."
user-invocable: false
---

# Intent Routing — How Natural Language Maps to Skills

This skill provides the complete routing intelligence for mapping user intent to claude-kit plugin commands. It is the reference material behind the auto-routing rules installed at `~/.claude/rules/claude-kit-autoroute.md`.

## Routing Principles

### 1. Intent Extraction

Every user message contains an implicit or explicit ACTION. Extract it before responding:

- **Explicit actions**: "create", "build", "review", "test", "debug", "grade", "plan"
- **Implicit actions**: "what's wrong with this code" → debug/diagnose, "is this any good" → grade/evaluate
- **Non-actions**: "hello", "thanks", "what is X" → no routing needed (unless X maps to a knowledge skill)

### 2. Skill Resolution

Once the action is identified, match it against the available skills list (visible in the system-reminder). The system-reminder always contains every loaded skill with its description.

Resolution priority:
1. **Exact match** — user says the skill name → invoke it
2. **Description match** — user's intent matches a skill's description → invoke it
3. **Role match** — user's intent maps to a role pattern (e.g., "review code" → grader) → find loaded role skill
4. **Knowledge match** — user asks about a domain topic → find matching knowledge skill
5. **No match** — respond normally without routing

### 3. Team Resolution

Team-specific commands follow the pattern `<domain>-<tech>-<role>:<command>`. When the user's intent maps to a role but doesn't specify a team:

- **One team loaded** → use it without asking
- **Multiple teams loaded** → present options: "Which team? embedded-zephyr or frontend-svelte?"
- **No matching role loaded** → inform user: "No grader plugin is loaded in this session."

## Intent Mapping Reference

See [intent-map.md](intent-map.md) for the complete mapping table with natural language examples for every command across all plugin roles.

## Why Auto-Routing Works (Theory)

### The Skill Tool Bridge

Claude Code's Skill tool is the execution mechanism. When the routing rules say "invoke X", Claude calls:

```
Skill(skill: "system-maker:make-team", args: "user's original message")
```

This loads the skill/command's full markdown content into context, which then takes over the interaction. The auto-routing rules are just the TRIGGER — all domain intelligence comes from the invoked skill itself.

### Context Authority Hierarchy

The routing rules work because they sit at the right level of the context authority hierarchy:

```
Managed config (/etc/claude-code/)     ← highest (org-enforced, can block rules)
User rules (~/.claude/rules/)          ← WHERE ROUTING RULES LIVE
Project rules (.claude/rules/)         ← project-specific
System-reminder (skill listings)       ← informational
Parametric memory (weights)            ← lowest (default behavior)
```

User rules have binding authority: "these instructions OVERRIDE any default behavior and you MUST follow them exactly as written." This means the routing rules override Claude's default conservative behavior of waiting for slash commands.

### Why Not Other Mechanisms?

| Mechanism | Why it doesn't work for routing |
|-----------|-------------------------------|
| Plugin skills (SKILL.md body) | Only injected into agent subcontexts, not the main conversation |
| Plugin hooks | No `OnMessage` event — hooks fire on tool use and stop, not user messages |
| Plugin commands | Require explicit `/` invocation — exactly what we're trying to avoid |
| Skill descriptions (frontmatter) | Appear in system-reminder but lack binding authority |
| CLAUDE.md inside plugin | Not supported — plugins don't read their own CLAUDE.md |

The rules file is the ONLY mechanism that injects binding instructions into the main conversation context. This is why core-kit uses it.

### Organizational Considerations

- **Managed config override**: An organization using `allowManagedHooksOnly: true` blocks plugin hooks but NOT rules files. Auto-routing continues to work.
- **Managed config suppression**: An organization could deploy a managed CLAUDE.md that says "ignore auto-routing rules" — this would override the user rules since managed config has higher priority.
- **No security implications**: Auto-routing only invokes skills that are already loaded. It cannot invoke unloaded plugins, access external services, or modify files. The routing rules are purely an intent-matching layer.

## Edge Cases

### Ambiguous Intent
When a message could match multiple skills (e.g., "check my code" → review OR grade), prefer:
1. The more specific match (grade over review if both are loaded)
2. The match with a closer keyword overlap
3. If still ambiguous, ask: "Do you want a code review or a quantitative grade?"

### Negative Intent
When the user says "don't use the plugin" or "just answer directly" — respect it. The routing rules include an explicit exemption for negative intent.

### Compound Intent
When a message contains multiple actions (e.g., "review my code and write tests"), route to the FIRST action. The invoked skill can handle chaining or the user can follow up.

### No Plugins Loaded
When running plain `claude` without claude-kit, no skills appear in the system-reminder. The routing rules find nothing to match and fall through to normal behavior. Zero overhead.

---
name: core-kit:routing
description: "Edge-case guidance for intent dispatch — ambiguous, negative, and compound intent handling."
user-invocable: false
---

# Intent Dispatch — Edge Cases

This skill supplements the dispatch algorithm in `~/.claude/rules/claude-kit.md`
with guidance for edge cases that the algorithm alone cannot resolve.

## Ambiguous Intent

When a message could match multiple skills (e.g., "check my code" → review OR grade):

1. Prefer the more specific match (grade over review if both are loaded)
2. Prefer the match with closer keyword overlap to the user's phrasing
3. If still ambiguous, ask briefly: "Do you want a code review or a quantitative grade?"

## Negative Intent

When the user says "don't use the plugin", "just answer directly", or "without
the command" — respect it. The dispatch rules include an explicit exemption for
negative intent. Do not route.

## Compound Intent

When a message contains multiple actions (e.g., "review my code and write tests"),
route to the FIRST action. The invoked skill can handle chaining, or the user can
follow up with the second action.

## No Plugins Loaded

When running plain `claude` without claude-kit, no skills appear in the
system-reminder. The dispatch algorithm finds nothing to match and falls through
to normal behavior. Zero overhead.

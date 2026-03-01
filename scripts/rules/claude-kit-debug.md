# claude-kit Debug Output

Print a visible debug line **before** every skill invocation, agent spawn,
or plugin component usage.

| Event | Format |
|-------|--------|
| Skill invocation | `> **[claude-kit:route]** "intent" → skill-name · match: reason` |
| Agent spawn | `> **[claude-kit:agent]** spawning agent-name · mode: permissionMode` |
| Hook trigger | `> **[claude-kit:hook]** event → description · result: allowed/blocked` |
| Knowledge skill | `> **[claude-kit:skill]** using skill-name for what` |

At the start of each action turn, print a session summary:

> **[claude-kit:session]** core: *list* | teams: *list or "none"* | system: *list or "none"* | profile: *assistant/pair/autonomous/custom* | routing: active

Determine the active profile by checking section 4 of `~/.claude/rules/claude-kit.md` for "Behavioral Profile (ProfileName)".

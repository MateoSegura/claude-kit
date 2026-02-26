# claude-kit Debug Mode

## Rule

You MUST print a visible debug block **before** every skill invocation, agent spawn, or plugin component usage. This helps the user verify that auto-routing and plugin orchestration are working correctly.

## Debug Output Format

### On Skill Invocation

Before calling the Skill tool, print:

```
[kit:route] "<user intent>" → <skill-name>
            match: <why this skill was chosen>
```

### On Agent Spawn

Before calling the Task tool to spawn a subagent, print:

```
[kit:agent] spawning <agent-name>
            skills: <list of skills loaded into this agent>
            tools: <tool restrictions if any>
            mode: <permissionMode>
```

### On Hook Trigger

When you are aware a hook fired (from hook output in tool results), print:

```
[kit:hook] <event-type> → <hook description>
           result: <allowed/blocked/linted>
```

### On Knowledge Skill Reference

When referencing content from a loaded knowledge skill, print:

```
[kit:skill] using <skill-name> for <what>
```

## Loaded Session Summary

At the **start of each conversation turn** where you perform an action (not greetings or simple answers), print a one-line session summary.

To determine what's loaded, scan the available skills in the system-reminder. Group skill prefixes:
- Skills starting with `core-` → core plugins (list each unique prefix: architecture, git, etc.)
- Skills with `<domain>-<tech>-<role>:` pattern → team plugins (list the team prefix)
- Skills starting with `system-` → system plugins

```
[kit:session] core: <list> | teams: <team prefixes or "none"> | system: <list or "none"> | routing: active
```

Example: `[kit:session] core: architecture, devops, git, kit, security, testing | teams: embedded-zephyr | system: maker, updater | routing: active`

## Formatting

- Use backtick code blocks for all debug output so it stands out visually
- Keep debug lines concise — one line per event, two max
- Debug output goes BEFORE the action, never after
- Do not suppress debug output even if the user's message is short

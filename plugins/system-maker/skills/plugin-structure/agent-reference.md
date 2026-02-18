# Agent Files — Complete Reference

This is the exhaustive specification for Claude Code agent files (`agents/*.md`). Every field, mode, and pattern is documented here.

## File Location

Agent files live at `plugins/<name>/agents/<agent-name>.md`. They are launched via the `Task` tool from commands or parent agents using `subagent_type: agent-name`.

## Complete Frontmatter

```yaml
---
name: agent-name
description: What this agent does (REQUIRED — Claude uses this to understand the agent's purpose)
model: opus | sonnet | haiku
tools: Tool1, Tool2, Tool3
disallowedTools: ToolA, ToolB
skills: skill-name-1, skill-name-2
permissionMode: default
maxTurns: 10
memory: project
mcpServers: server-name
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "echo check"
color: "#4A90D9"
---
```

## All Frontmatter Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | **yes** | — | Agent identifier. Must match the filename (without .md). Used in Task tool's `subagent_type` parameter. Kebab-case. |
| `description` | string | **yes** | — | What this agent does. Claude uses this to understand when and how to use the agent. Be specific — vague descriptions cause misrouting. |
| `tools` | string | no | all tools | Comma-separated list restricting which tools the agent can use. When omitted, the agent inherits all available tools. When specified, the agent can ONLY use the listed tools. |
| `disallowedTools` | string | no | none | Comma-separated list of tools to explicitly deny. Use this when you want to inherit all tools EXCEPT specific ones. Opposite of `tools`. |
| `model` | string | no | sonnet | Which Claude model to use: `opus`, `sonnet`, or `haiku`. See Model Selection below. |
| `permissionMode` | string | no | default | Controls how the agent handles permission prompts. See Permission Modes below. |
| `maxTurns` | number | no | — | Maximum conversation turns (API round-trips) for this agent. When reached, the agent stops regardless of completion status. Use to prevent runaway agents. |
| `skills` | string | no | none | Comma-separated skill names to preload. The FULL content of each skill's SKILL.md is injected into the agent's context at launch. See Skills Preloading below. |
| `mcpServers` | string | no | none | MCP servers available to this agent. Comma-separated server names from the plugin's `.mcp.json`. |
| `hooks` | object | no | none | Agent-specific hook overrides. Same format as `hooks.json` but scoped to this agent only. |
| `memory` | string | no | none | Persistent memory scope. See Memory below. |
| `color` | string | no | — | Hex color code for CLI status line visibility. Helps distinguish agents visually during parallel execution. |

## CRITICAL: `tools:` NOT `allowed-tools:`

The correct frontmatter field name is `tools:`. This is the most common mistake in agent files. Using the wrong field name causes silent failure — the agent launches with no tool access.

```yaml
# CORRECT — agent gets these tools
tools: Read, Glob, Grep, Write, Edit, Bash

# WRONG — field name is not recognized, agent gets NO tools
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
```

## Permission Modes

| Mode | Behavior | Use for |
|------|----------|---------|
| `default` | Normal permission prompts for sensitive operations | Most agents — safe default |
| `acceptEdits` | Auto-accept file edits (Read, Write, Edit) without prompting | Trusted implementation agents writing to isolated build dirs |
| `delegate` | Delegate permission decisions to parent agent | Child agents in a hierarchy |
| `dontAsk` | Skip operations that would require permission (silently no-op) | Agents that should never block on permissions |
| `bypassPermissions` | Bypass ALL permission checks | Only for fully trusted agents in controlled environments |
| `plan` | Read-only planning mode — no write operations allowed | Architecture, analysis, review agents |

### When to Use Each Mode

- **Analysis/review agents**: Use `plan` — they should never write files
- **Implementation agents writing to /tmp build dirs**: Use `acceptEdits` — the build dir is isolated
- **Agents running user-facing commands**: Use `default` — let the user approve
- **Never use `bypassPermissions`** unless running with `--dangerously-skip-permissions` already

## Tool Restriction Guidelines

Assign the MINIMUM tools needed for the agent's role:

### Read-Only Agents (analysis, review, validation)

```yaml
tools: Read, Glob, Grep, Bash, WebSearch, WebFetch
```

These agents analyze but never modify. Giving them write tools is a design error — it means the agent's role is unclear.

### Write Agents (implementation, generation)

```yaml
tools: Read, Glob, Grep, Write, Edit, Bash
```

These agents create and modify files. They should NOT have `Task` (leaf nodes) or `WebSearch` (focused on local files).

### Orchestration Agents (coordinate other agents)

```yaml
tools: Task, AskUserQuestion, Read, Glob, Grep
```

These agents dispatch work to other agents. They typically don't need write tools because they delegate implementation.

### Specific Rules

- **NEVER** give write tools (`Write`, `Edit`) to analysis/review agents
- **NEVER** give `Task` to leaf-node agents — subagents cannot spawn other subagents
- **NEVER** give `AskUserQuestion` to subagents unless they genuinely need user input
- When an agent only needs to spawn SPECIFIC subagents, use `Task(agent-type)` syntax:

```yaml
# Can only spawn these two specific agent types
tools: Read, Write, Task(component-writer), Task(reviewer)

# Can spawn ANY agent type (less restrictive)
tools: Read, Write, Task
```

## Subagent Spawning

Agents are spawned from commands or parent agents using the `Task` tool:

```
Task tool call:
  subagent_type: "agent-name"    # matches the agent's `name:` field
  prompt: "Do this specific thing"
  model: "sonnet"                # optional override
```

### Hierarchy Rules

1. **Commands** can spawn agents via Task
2. **Agents** can spawn other agents via Task (if they have the Task tool)
3. **Subagents spawned by agents CANNOT spawn further subagents** — Claude Code enforces a flat hierarchy
4. Design your agent tree to be at most 2 levels deep: Command → Agent → (no further spawning)

### Parallel Spawning

Launch multiple agents in parallel by making multiple Task calls in a single response:

```
# These run concurrently:
Task(subagent_type: "analyzer", prompt: "Analyze component A")
Task(subagent_type: "analyzer", prompt: "Analyze component B")
Task(subagent_type: "analyzer", prompt: "Analyze component C")
```

This is the primary mechanism for parallelism in Claude Code plugins.

## Skills Preloading Behavior

When an agent lists skills in its frontmatter, the behavior is:

1. The FULL content of each skill's `SKILL.md` is injected into the subagent's context at launch
2. The content is not "available for invocation" — it is literally loaded into the agent's prompt
3. This means skills consume context window space — only preload skills the agent actually needs
4. Subagents do NOT inherit skills from the parent conversation — every agent must explicitly list its skills
5. If a skill has reference files (`reference.md`, `examples.md`), only SKILL.md is preloaded — the agent must use Read to access reference files

### Example

```yaml
# This agent gets the full content of both skills injected at launch
skills: plugin-structure, domain-patterns
```

### Context Efficiency

- Preloaded skills consume context proportional to their SKILL.md size
- This is why the 500-line limit on SKILL.md matters — a 2000-line skill would consume half an agent's context
- Put detailed reference material in separate files that the agent reads on demand
- Only preload skills that the agent needs for EVERY task — use auto-invocation for optional skills

## Model Selection

| Model | Speed | Reasoning | Cost | Use for |
|-------|-------|-----------|------|---------|
| `opus` | Slowest | Deepest | Highest | Architecture design, identity writing, code review, complex analysis, anything requiring nuanced judgment |
| `sonnet` | Medium | Good | Medium | Code generation, skill writing, implementation, most general-purpose work |
| `haiku` | Fastest | Basic | Lowest | Simple validation, format checking, linting, quick lookups, trivial transformations |

### Selection Guidelines

- **Default to `sonnet`** — it's the best balance of speed and capability
- Use `opus` when the agent needs to make architectural decisions, write identity/methodology, or review complex code
- Use `haiku` only for mechanical tasks with no ambiguity (JSON validation, format checking)
- When in doubt, use `sonnet` — using `opus` everywhere wastes time and money

## Memory Field

The `memory` field enables cross-session persistent learning:

| Scope | Persists across | Storage location | Use case |
|-------|----------------|-----------------|----------|
| `user` | All sessions for this user | User-level config | Personal preferences, coding style, common patterns |
| `project` | All sessions in this project | Project-level config | Project conventions, architecture decisions, team patterns |
| `local` | Sessions in this directory | Directory-level config | Directory-specific patterns, local overrides |

### When to Use Memory

- Use `project` for agents that learn project conventions over time
- Use `user` for agents that adapt to personal coding style
- Avoid memory for one-shot agents (builders, validators) — they don't benefit from persistence

## Color Assignments

Each agent gets a distinct color for CLI status line visibility during parallel execution:

### Suggested Palette

| Color | Hex | Best for |
|-------|-----|----------|
| Red | `#FF6347` | Error checking, validation, review agents |
| Blue | `#4A90D9` | Architecture, design, analysis agents |
| Green | `#32CD32` | Implementation, writing, generation agents |
| Amber | `#E8A838` | Orchestration, coordination agents |
| Purple | `#9370DB` | Identity, methodology, style agents |
| Teal | `#20B2AA` | Research, exploration, search agents |
| Pink | `#FF69B4` | Testing, QA agents |
| Gold | `#DAA520` | Configuration, setup agents |

### Rules

- Use saturated, distinguishable colors — avoid pastels that blend together
- Never assign the same color to two agents that might run in parallel
- Avoid pure white or black — they don't show well on most terminal backgrounds

## Agent Body Structure

The markdown body after the frontmatter should follow this structure for maximum determinism:

```markdown
# Agent Name

<role>
## Role
Precise description of what this agent does.
</role>

<input>
## Input
What this agent receives and how to parse it.
</input>

<process>
## Process
Step-by-step instructions with numbered steps.
Each step should be concrete and actionable.
</process>

<output-format>
## Output Format

Exact structure of what the agent must return.

### Example Output:

```json
{
  "field": "value",
  "nested": {
    "detail": "concrete example"
  }
}
```
</output-format>

<constraints>
## Constraints
- Hard rules the agent must follow
- Things the agent must NOT do
</constraints>
```

### Why XML Tags

XML tags in agent bodies increase determinism for Claude models:

- They create unambiguous section boundaries
- They prevent section content from bleeding into other sections
- They make it easier for Claude to find and follow specific instructions
- They improve structured output compliance

### Body Best Practices

1. **Be concrete**: Show example inputs AND outputs with realistic data
2. **Number steps**: Use numbered steps in the Process section for sequential work
3. **Define rejection**: Explain what "bad output" looks like so the agent can self-correct
4. **One role per agent**: If an agent does two things, split it into two agents
5. **Include edge cases**: Document what happens when the input is unusual or incomplete

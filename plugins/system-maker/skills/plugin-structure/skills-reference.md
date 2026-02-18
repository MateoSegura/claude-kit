# Skills — Complete Reference

This is the exhaustive specification for Claude Code skill files (`skills/skill-name/SKILL.md`). Covers single-file and multi-file structures, identity-as-skill pattern, all frontmatter fields, loading behavior, and content guidelines.

## File Location

Skills live at `plugins/<name>/skills/<skill-name>/SKILL.md`. The directory name is the skill identifier. Only `SKILL.md` is required — additional files are optional and loaded on demand.

## What Skills Are

Skills are **reference knowledge** that gets preloaded into agents. They contain specifications, patterns, examples, and domain expertise — NOT executable instructions or workflows (those are commands).

### Skills vs Commands

| Aspect | Skills | Commands |
|--------|--------|----------|
| Invocation | Auto-invoked by Claude when task matches description | Explicitly invoked by user via `/plugin:command` |
| Context | Loaded into agent's context (or forked) | Runs in main conversation |
| Purpose | Reference knowledge, specifications, patterns | Workflows, orchestration, interactive processes |
| Pattern | Newer, preferred | Legacy, still supported |
| Efficiency | Loaded only when relevant | Always available after invocation |

## Complete Frontmatter

```yaml
---
name: plugin-name:skill-name
description: What knowledge this skill provides
allowed-tools: Read, Grep, Glob
user-invocable: true
disable-model-invocation: false
context: fork
agent: Explore
argument-hint: "describe what arguments look like"
---
```

## All Frontmatter Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | **yes** | — | Skill identifier, format: `plugin-name:skill-name` (kebab-case). The `skill-name` portion must match the directory name. The `plugin-name:` prefix ensures skills are unambiguous when multiple plugins are loaded. |
| `description` | string | **yes** | — | What knowledge this skill provides. Claude uses this to decide when to auto-load the skill. Be specific — vague descriptions cause incorrect loading. |
| `user-invocable` | boolean | no | `true` | When `false`, hides the skill from the user's `/` command menu. Claude can still auto-load it based on description. Used for background knowledge like identity skills. |
| `disable-model-invocation` | boolean | no | `false` | When `true`, only the user can invoke this skill (via `/` menu). Claude will NOT auto-load it. Use for skills that should only run when explicitly requested. |
| `context` | string | no | — | Set to `"fork"` to run the skill in a subagent instead of the main conversation. Useful for heavy skills that shouldn't consume main context. |
| `agent` | string | no | — | Which subagent type to use when `context: fork` is set. For example: `"Explore"` for codebase exploration, or a custom agent name. |
| `allowed-tools` | string | no | — | Comma-separated list of tools the skill can use without permission prompts. Same field name as commands — NOT `tools:` (which is for agents only). Example: `Read, Grep, Glob` or `Bash(gh *)`. |
| `argument-hint` | string | no | — | Hint text shown in autocomplete when the user types `/plugin:skill`. Describes expected arguments (e.g., `"component name to analyze"`). |

### Frontmatter Combinations

| Scenario | Frontmatter |
|----------|-------------|
| Normal skill (user and Claude can invoke) | `name`, `description` |
| Background knowledge (Claude-only, hidden from menu) | `name`, `description`, `user-invocable: false` |
| User-only skill (explicit invocation required) | `name`, `description`, `disable-model-invocation: true` |
| Heavy skill in subagent | `name`, `description`, `context: fork`, `agent: Explore` |
| Identity skill | `name: identity`, `description: "Core identity..."`, `user-invocable: false` |

## How Skills Are Loaded

Skills enter an agent's context through two mechanisms:

### 1. Explicit Preloading (via agent `skills:` frontmatter)

When an agent lists a skill in its `skills:` field, the FULL content of the skill's `SKILL.md` is injected into the agent's context at launch.

```yaml
# In the agent's frontmatter:
skills: plugin-structure, domain-patterns
```

**Behavior:**
- The entire `SKILL.md` content becomes part of the agent's system prompt
- This happens at launch — before the agent receives any task
- Reference files (`reference.md`, `examples.md`) are NOT auto-loaded — the agent reads them on demand
- Skills consume context window space proportional to their SKILL.md size
- Subagents do NOT inherit skills from the parent — list every needed skill explicitly

### 2. Auto-Invocation (by Claude based on description)

Claude automatically loads a skill when the current task matches the skill's `description` field. This is the primary advantage of skills over commands.

**Behavior:**
- Claude evaluates skill descriptions against the current task
- If there's a match, the skill content is loaded into the conversation
- This is more context-efficient than preloading — skills are only loaded when needed
- Works for both user-invocable and non-user-invocable skills

### Loading Priority

1. Explicitly preloaded skills (via `skills:` frontmatter) load first
2. Auto-invoked skills load when Claude determines they're relevant
3. User-invoked skills (via `/plugin:skill`) load on user request

## Multi-File Skill Structure

For skills that exceed 500 lines or cover multiple sub-topics, split content across multiple files:

```
my-skill/
├── SKILL.md              # Entry point (REQUIRED, max 500 lines)
├── reference.md          # Detailed specification
├── examples.md           # Usage examples and patterns
├── api-reference.md      # API signatures and types
├── troubleshooting.md    # Common issues and solutions
└── scripts/
    └── helper.py         # Utility scripts
```

### Rules for Multi-File Skills

1. **SKILL.md is the entry point** — it's the only file that gets auto-loaded
2. **Max 500 lines for SKILL.md** — this is a hard limit, not a suggestion
3. **Reference files are loaded on demand** — Claude reads them when it follows the links
4. **Link from SKILL.md to reference files** using markdown links:

```markdown
## Additional resources

- For complete frontmatter specification, see [reference.md](reference.md)
- For usage examples and patterns, see [examples.md](examples.md)
- For API signatures, see [api-reference.md](api-reference.md)
```

5. **Each reference file should be self-contained** — it should make sense without reading SKILL.md first
6. **Name files descriptively** — `api-reference.md` is better than `details.md`

### What Goes in SKILL.md vs Reference Files

| Content type | Location |
|-------------|----------|
| Overview and purpose | SKILL.md |
| Essential concepts (must-know) | SKILL.md |
| Quick reference tables | SKILL.md |
| Format summaries with examples | SKILL.md |
| Links to reference files | SKILL.md |
| Exhaustive field specifications | Reference file |
| Complete examples with commentary | Reference file |
| Edge cases and troubleshooting | Reference file |
| API signatures and type definitions | Reference file |
| Pattern catalogs | Reference file |

### Context Efficiency

Multi-file skills are more context-efficient because:

- SKILL.md (preloaded) is concise — only essential info
- Reference files are loaded ONLY when the agent actually needs the detail
- An agent working on hooks only loads the hooks reference, not the agent or LSP references
- This is especially important for agents with multiple preloaded skills

### Example: Zephyr Kernel API Skill

```
zephyr-kernel-api/
├── SKILL.md                 # Overview, key concepts, quick reference (~200 lines)
├── api-reference.md         # Complete API signatures with params and return types (~400 lines)
├── examples.md              # Code examples for common patterns (~300 lines)
└── troubleshooting.md       # Common pitfalls and debugging (~150 lines)
```

**SKILL.md** would contain:
- Overview of Zephyr kernel subsystem
- Key concepts (threads, semaphores, message queues)
- Quick reference table of most-used functions
- Links to reference files for depth

**api-reference.md** would contain:
- Complete function signatures with all parameters
- Return type documentation
- Parameter constraints and valid ranges
- Thread safety notes

## Identity-as-Skill Pattern

A skill can serve as the agent's core identity, methodology, and decision-making framework. This is the recommended pattern for domain-expert plugins.

### Why a Skill, Not CLAUDE.md

Plugins do NOT read their own CLAUDE.md file. CLAUDE.md only loads based on the user's current working directory hierarchy — it is not a plugin component. A CLAUDE.md placed inside a plugin directory will never be automatically loaded.

Skills, on the other hand, are loaded via the plugin system regardless of cwd. By putting identity information in a skill with `user-invocable: false`, you guarantee it gets loaded when Claude needs it. **Do NOT create a CLAUDE.md inside plugins — use skills instead.**

### Identity Skill Structure

```
skills/identity/
├── SKILL.md              # Core identity, methodology, decision framework
├── coding-standards.md   # Language-specific coding conventions
└── workflow-patterns.md  # Common workflow patterns and best practices
```

### Identity SKILL.md Template

```yaml
---
name: identity
description: "Core identity and methodology for [domain] development. Auto-loaded for all domain tasks."
user-invocable: false
---
```

```markdown
# [Domain] Expert Identity

<methodology>
## Methodology

You are a [domain] development expert. Your approach:

1. [Core principle 1]
2. [Core principle 2]
3. [Core principle 3]
</methodology>

<conventions>
## Coding Conventions

- [Convention 1]
- [Convention 2]
- [Convention 3]

For complete coding standards, see [coding-standards.md](coding-standards.md).
</conventions>

<decision-framework>
## Decision Framework

When choosing between approaches:
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]
</decision-framework>

<workflow>
## Standard Workflow

For common workflow patterns, see [workflow-patterns.md](workflow-patterns.md).
</workflow>
```

### Identity Preloading

Every agent in the plugin should include the identity skill in its `skills:` field:

```yaml
# In every agent's frontmatter:
skills: identity, other-skill-1, other-skill-2
```

This ensures consistent methodology and conventions across all agents in the plugin.

## Content Guidelines for Skills

### Structure for Scanning

Skills are reference material — optimize for quick scanning:

- Use tables for field specifications and options
- Use code blocks for concrete examples
- Use bullet lists for rules and constraints
- Use headers to create clear sections
- Use XML tags for determinism in Claude models

### Concrete Over Abstract

```markdown
// BAD — too abstract
"Use appropriate naming conventions for your language"

// GOOD — concrete and actionable
"Functions: snake_case (e.g., `get_device_config`)
 Classes: PascalCase (e.g., `DeviceManager`)
 Constants: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`)
 Files: kebab-case (e.g., `device-manager.c`)"
```

### Example-Driven

Every specification should include at least one concrete example:

```markdown
// BAD — spec without example
"The matcher field accepts pipe-separated tool names"

// GOOD — spec with example
"The matcher field accepts pipe-separated tool names:
```json
"matcher": "Write|Edit|Bash"
```"
```

### Edge Cases

Document what happens in unusual situations:

```markdown
### Edge Cases

- If `tools:` is omitted, the agent inherits ALL tools (not zero tools)
- If `skills:` lists a non-existent skill, the agent launches without error but the skill is missing
- If two skills have the same name, the one in the plugin takes precedence
```

---

## Domain Generalization Strategy for Plugin Architecture

When designing a plugin architecture, decompose the domain into a hierarchy to avoid creating narrow, non-extensible plugins. This ensures the plugin ages well and can accommodate future growth without restructuring.

### The Domain Hierarchy

Every domain description contains layers:

1. **FRAMEWORK layer** (core domain) — The foundational framework or paradigm that defines the programming model. This becomes the agent's identity and name.
2. **TARGET layer** (instantiation) — A specific platform, runtime, or deployment target within the framework. This becomes an extension skill.
3. **TOOLING layer** (peripheral) — Specific tools, libraries, or integrations that support the workflow. These become additional skills or MCP servers.

### Decomposition Examples

| User says | Framework (core) | Target (extension) | Tooling (peripheral) |
|-----------|------------------|--------------------|-----------------------|
| "ESP32 Zephyr embedded" | Zephyr RTOS | ESP32 hardware | west, esptool |
| "React frontend with TypeScript" | React | TypeScript patterns | ESLint, Vite |
| "Go cloud with Kubernetes" | Go cloud services | Kubernetes orchestration | kubectl, Helm |
| "Rust embedded for ARM Cortex-M" | Rust embedded | ARM Cortex-M specifics | probe-rs, cargo-embed |
| "Python ML with PyTorch on AWS" | PyTorch ML | AWS deployment | SageMaker, boto3 |
| "Flutter mobile for iOS" | Flutter | iOS platform specifics | Xcode, CocoaPods |

### Naming Rule

The agent is named `<type>-<domain>-<tech>-<role>`. The domain is the broad discipline, the tech is the core framework, and targets become extension skills:
- `coding-embedded-zephyr-engineer` (domain=embedded, tech=zephyr — NOT `coding-embedded-zephyr-esp32-engineer`, ESP32 is a target)
- `coding-embedded-zephyr-grader` (same domain+tech, different role)
- `coding-embedded-linux-engineer` (same domain, different tech)
- `coding-frontend-react-engineer` (NOT `coding-frontend-react-nextjs-engineer` — Next.js is a target)
- `coding-cloud-golang-engineer` (NOT `coding-cloud-golang-kubernetes-engineer` — K8s is a target)

Standard domains: embedded, cloud, frontend, backend, mobile, ml, devops.
Standard roles: engineer, grader, tester, debugger, deployer, migrator. Both are ALWAYS explicit.

### Architecture Consequence

The core agent knows the framework deeply. Target-specific knowledge lives in extension skills that can be added without modifying the core:

```
coding-embedded-zephyr-engineer/
├── skills/
│   ├── identity/            # Core identity (user-invocable: false)
│   │   └── SKILL.md
│   ├── zephyr-kernel/       # Framework-level knowledge
│   │   ├── SKILL.md
│   │   ├── reference.md
│   │   └── examples.md
│   ├── esp32-hardware/      # Target extension (add more targets later)
│   │   ├── SKILL.md
│   │   ├── reference.md
│   │   └── examples.md
│   └── devicetree/          # Tooling knowledge
│       ├── SKILL.md
│       └── reference.md
```

To add nRF52 support later, you create `skills/nrf52-hardware/` — zero changes to the core agent.

### Generalization Checklist

Before finalizing a plugin architecture, verify:
- [ ] The agent name reflects the FRAMEWORK, not the target
- [ ] Core skills cover framework-level knowledge that applies to ALL targets
- [ ] Target-specific knowledge is isolated in its own extension skill
- [ ] Adding a new target requires ONLY adding a new skill directory — no modifications to existing agents, commands, or hooks
- [ ] The identity skill describes expertise in the framework, mentioning the current target as one example

## Knowledge Plugin Structure

Knowledge plugins are companion plugins that provide shared domain reference material. They have a reduced structure compared to role plugins:

```
coding-embedded-zephyr-knowledge/
├── .claude-plugin/
│   └── plugin.json          # role: "knowledge", no companions
├── .lsp.json                # Same LSP config as role plugins
├── skills/
│   ├── identity/
│   │   └── SKILL.md         # Minimal domain overview (~40 lines)
│   ├── zephyr-kernel/       # Domain API references
│   │   ├── SKILL.md
│   │   └── api-reference.md
│   ├── design-patterns/     # Domain patterns
│   │   ├── SKILL.md
│   │   ├── patterns-reference.md
│   │   └── anti-patterns.md
│   └── ...                  # More domain skills
├── hooks/
│   └── hooks.json           # Safety hooks only
└── scripts/
    ├── block-dangerous-commands.sh
    └── check-environment.sh
```

### Key Differences from Role Plugins

| Aspect | Knowledge Plugin | Role Plugin |
|--------|-----------------|-------------|
| agents/ | NOT PRESENT | Required |
| commands/ | NOT PRESENT | Required |
| Identity | Minimal domain overview | Full persona + methodology |
| Hooks | Safety only | Role-specific linting + verification |
| plugin.json role | `"knowledge"` | `"engineer"`, `"grader"`, etc. |
| plugin.json companions | None | References knowledge plugin |

### Companion Loading

Role plugins reference their knowledge companion via the `companions` field in plugin.json:
```json
{
  "companions": ["coding-embedded-zephyr-knowledge"]
}
```

At runtime, `ctl.sh` resolves companions and passes multiple `--plugin-dir` arguments to Claude, loading both plugins' skills, hooks, and configs.

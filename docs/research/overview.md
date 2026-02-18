# Agent Configuration Research - Overview

## Decision

**Claude Code** is the selected primary platform for building specialized AI coding agents. The decision is based on its superior hook system (14 deterministic events vs Codex's 1), plugin ecosystem for distribution, subagent system with persistent memory, and enterprise managed settings with enforcement capabilities. Codex CLI remains available for comparison benchmarks and specific use cases (cloud execution, CI integration).

## The Problem We're Solving

AI coding agents degrade during long sessions - not because they hallucinate, but because they lose context. The conversation gets compacted, architectural decisions get summarized away, and the model starts solving local problems that contradict global plans. The solution requires making critical behaviors **deterministic** (hook-driven) rather than relying on the model "remembering" to do things.

## Research Documents

### Core Architecture

| Document | What It Covers |
|---|---|
| [01-context-management-problem.md](./01-context-management-problem.md) | Why long sessions degrade, what survives compaction, the solution framework |
| [02-claude-code-hooks.md](./02-claude-code-hooks.md) | Complete hook reference: all 14 events, 3 hook types (command, prompt, agent), matchers, exit codes, input/output schemas |
| [03-claude-md-and-rules-behavior.md](./03-claude-md-and-rules-behavior.md) | **Empirically verified** behavior of CLAUDE.md and rules. Key finding: subdirectory CLAUDE.md files and path-filtered rules are NOT auto-loaded |
| [04-settings-hierarchy.md](./04-settings-hierarchy.md) | Full settings precedence: managed > CLI > local > project > user. All file locations. |

### Enterprise & Organization

| Document | What It Covers |
|---|---|
| [05-enterprise-managed-settings.md](./05-enterprise-managed-settings.md) | Server-managed vs endpoint-managed deployment, managed-only keys (allowManagedHooksOnly, etc.), Teams vs Enterprise features, authentication |

### Platform Comparison

| Document | What It Covers |
|---|---|
| [06-codex-cli-comparison.md](./06-codex-cli-comparison.md) | Full Claude Code vs Codex CLI comparison: config structure, hooks, enterprise, instructions behavior, what each has that the other doesn't |
| [07-cross-platform-architecture.md](./07-cross-platform-architecture.md) | How to structure a monorepo for both platforms: shared directory, sync script, friction assessment, workload tiering |

### Agent Design & Distribution

| Document | What It Covers |
|---|---|
| [08-agent-profile-architecture.md](./08-agent-profile-architecture.md) | What creates "taste" (consistent output), the identity file, measurement/benchmarking framework, profile composition model |
| [09-plugin-system.md](./09-plugin-system.md) | The plugin IS the agent: directory structure, manifest, commands vs skills, subagent definitions with hooks/MCP/memory, installation, updates, multi-profile coexistence |
| [10-deterministic-workflow-patterns.md](./10-deterministic-workflow-patterns.md) | Hook configurations for compaction recovery, domain detection, plan enforcement, status tracking. Includes all hook scripts. |
| [11-statusline-configuration.md](./11-statusline-configuration.md) | Status bar customization, available JSON data, agent-aware display, performance tips |

## Key Findings (Corrections Made Along the Way)

Several initial assumptions were corrected through empirical testing:

1. **Subdirectory CLAUDE.md files are NOT auto-loaded** when Claude reads files in that directory. They are just regular files. (Initially assumed they were auto-injected.)

2. **Path-filtered rules (.claude/rules/ with frontmatter) are NOT auto-injected** when Claude touches matching files. Only global rules (no path filter) are auto-loaded. (Initially assumed path filters triggered injection.)

3. **The first test showing all CLAUDE.md secrets** was misleading - Claude proactively used tools (5 turns) to search for CLAUDE.md files. It wasn't auto-injection.

4. **Codex CLI's AGENTS.md auto-chains from root to CWD** - this is actually better than Claude's subdirectory CLAUDE.md behavior for monorepo context.

5. **Hook `type: "agent"` is the closest to auto-triggering a skill** after compaction - it spins up a full agent with tool access that can read state files.

## Architecture Summary

```
Organization Layer (enforced, cannot be overridden)
├── /etc/claude-code/managed-settings.json  (hooks, permissions)
├── /etc/claude-code/CLAUDE.md              (org standards)
└── /etc/claude-code/managed-mcp.json       (approved MCP servers)

User Layer (personal defaults)
├── ~/.claude/settings.json                 (personal hooks, prefs)
├── ~/.claude/CLAUDE.md                     (personal instructions)
└── ~/.claude/agents/*.md                   (personal agents)

Plugin Layer (installable domain expertise)
├── embedded-zephyr/                        (hooks, skills, agents, MCP)
├── cloud-k8s/                              (hooks, skills, agents, MCP)
└── security-baseline/                      (shared rules)

Project Layer (repo-specific)
├── .claude/settings.json                   (project hooks)
├── .claude/rules/*.md                      (global rules - auto-loaded)
├── CLAUDE.md                               (minimal bootstrap)
└── plan/                                   (file-based state - hook-managed)
    ├── overview.md
    ├── status.log (append-only, hook-written)
    └── phases/
```

## Next Steps

1. Build the first plugin (embedded-zephyr) with identity, 3 rules, 1 MCP server, 1 hook, 2 examples
2. Create the activation script for testing with `--plugin-dir`
3. Write 3 benchmark prompts and run A/B tests
4. Iterate the profile based on results
5. Build second plugin (cloud-k8s) to prove the framework generalizes
6. Set up team marketplace for distribution
7. Configure managed settings for org-wide enforcement

# Product Architecture — claude-kit

**Status:** active
**Date:** 2026-02-28

## Overview

claude-kit is a context engineering framework that makes AI coding agents
domain-specific, verifiable, and transparent. It sits between the user and
Claude Code, constructing the right combination of knowledge, constraints,
and agent roles for each session.

The product architecture rests on three pillars, each addressing a different
layer of the value proposition.

## The Three Pillars

### Pillar 1 — Plugin System (Local, Core Value)

The plugin system is the foundation. It delivers value from the first session
without requiring accounts, cloud connectivity, or configuration beyond
installation.

```
User intent → claude-kit CLI → Plugin resolution → Claude Code session
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Knowledge        Role Agents      Enforcement
              (skills)      (engineer, grader,   (hooks)
                             tester, debugger)
```

**Components:**
- **Skills** — Curated domain knowledge injected into agent context windows.
  Each skill is a markdown file targeting a specific subsystem. Skills are
  the primary mechanism for narrowing LLM output toward domain-correct code
  (REQ-001, ADR-001).
- **Role agents** — Specialized agent definitions with role-appropriate tools,
  permissions, and behavioral constraints. Five roles per domain team
  (REQ-003, ADR-002).
- **Hooks** — Deterministic enforcement scripts that fire on tool-use events.
  PreToolUse blocks dangerous operations; PostToolUse validates output quality
  (REQ-004, ADR-003).
- **Companions** — Cross-plugin knowledge sharing via declared dependencies.
  All roles in a team share a single knowledge plugin (ADR-004).
- **Auto-routing** — Natural language intent mapping to skill invocations,
  eliminating the need to memorize slash commands.

### Pillar 2 — Transparency Layer (Local, Trust Building)

The transparency layer makes the plugin system observable. It transforms
claude-kit from a black box into a glass box.

```
Session runtime → Hook scripts → Structured logs (events.jsonl)
                → Debug mode  → Narrative traces ([kit:*] blocks)
                → Stop hook   → Grader evaluation (score + issues)
```

**Components:**
- **Session logging** — Every hook firing, tool use, and enforcement verdict
  recorded to structured files on disk. Ground truth for what happened
  (REQ-005, ADR-005).
- **Debug traces** — Human-readable `[kit:*]` blocks showing routing decisions,
  agent spawns, skill loading, and constraint checking. Approximate but
  intuition-building (ADR-005).
- **Grader evaluation** — Independent quality scoring at session end via the
  grader role. Structured output with numerical score, issue list, and file
  references (ADR-006).
- **Trend reporting** — Aggregated session data showing quality trends over
  time. The "feel" signal for whether the tool is helping (REQ-007).

### Pillar 3 — Platform and Ecosystem (Cloud, Growth)

The platform extends local value to organizational and community scales.

```
Local CLI ──upload──> Cloud Platform ──dashboard──> Team Leads
                          │
                    ┌─────┼─────┐
                    ▼     ▼     ▼
                 User   Session  Org
                 Accts  Analytics Config
                          │
Community ──publish──> Plugin Registry ──install──> Users
```

**Components:**
- **User accounts** — Authentication for plugin access and cloud features
  (REQ-009).
- **Session analytics** — Aggregated quality metrics across teams and time
  periods (REQ-009).
- **Configuration management** — Organization-level plugin and constraint
  definitions (REQ-009).
- **Plugin registry** — Community discovery, publication, and quality gating
  (REQ-010, ADR-008).

## The User Journey

### Individual Developer

1. Install claude-kit and update plugins
2. Launch a session: `claude-kit --kit cloud-python`
3. Experience domain-specific agent behavior immediately (Pillar 1)
4. Enable debug mode to see what's happening (Pillar 2)
5. Over time, review session trends to calibrate trust (Pillar 2)

### Team Lead

1. Define approved plugin configurations for the team
2. Deploy configurations to team members via cloud platform (Pillar 3)
3. Monitor team-wide quality metrics on the dashboard (Pillar 3)
4. Iterate on plugin configurations based on data

### Community Contributor

1. Create a plugin for a new domain using system-maker
2. Validate with built-in quality tooling
3. Publish to the registry (Pillar 3)
4. Maintain and update based on community feedback

## How the Pillars Connect

Each pillar depends on the previous:

- **Pillar 2 needs Pillar 1:** Transparency without a plugin system has
  nothing to observe.
- **Pillar 3 needs Pillar 2:** Platform analytics require session logging.
  Community quality gating requires the same validation tooling.
- **Pillar 1 is independently valuable:** The plugin system delivers value
  without transparency features or cloud connectivity.

This dependency chain determines the build order: plugin system first,
transparency second, platform third. Each pillar is independently shippable
and incrementally valuable.

## Architectural Constraints

- **Offline-first:** The CLI must function fully without cloud connectivity.
  Cloud features enhance but never gate core functionality.
- **Model-agnostic:** Context engineering works with any model that accepts a
  context window. The architecture does not depend on Claude-specific features.
- **Stdlib-only CLI:** The CLI has zero third-party runtime dependencies.
  All functionality is implemented with Python stdlib.
- **Composable loading:** Any combination of plugins can be loaded in a single
  session. No plugin assumes exclusive control of the session.

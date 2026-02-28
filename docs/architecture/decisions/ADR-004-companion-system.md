# ADR-004: Companion System for Cross-Role Knowledge Sharing

**Status:** accepted
**Date:** 2026-02-28

## Context

In a multi-agent team with five specialized roles (ADR-002), a critical design
question is how domain knowledge is shared across roles. Three approaches exist:

1. **Duplicated knowledge** — Each role carries its own copy of domain facts.
   Simple but creates drift: when a fact changes, all copies must be updated
   in lockstep. The multi-agent-architecture research identifies knowledge
   divergence between agents as a primary failure mode in multi-agent systems.

2. **Centralized knowledge service** — A knowledge API that agents query at
   runtime. Adds infrastructure complexity and latency. Requires the knowledge
   service to be available for every session.

3. **Shared knowledge substrate** — A passive knowledge plugin that all role
   plugins declare as a companion dependency. The knowledge is defined once
   and injected into each role's context at load time. Changes propagate to
   all roles automatically on the next session.

The theory-context-cache research frames this as cache coherence: when multiple
specialized cores (agents) share a cache (knowledge), a coherence protocol
ensures they work with consistent data. Without coherence, agents produce
contradictory outputs — the engineer uses API v2 while the tester validates
against API v1.

The memory-architecture research adds that knowledge should be versioned and
provenance-tracked. A companion system where knowledge lives in a single
plugin with a single version number provides natural versioning — the
knowledge plugin's version is the knowledge version.

## Decision

claude-kit implements cross-role knowledge sharing through a companion
declaration system:

1. Each team has exactly one knowledge plugin (e.g., `embedded-zephyr-knowledge`)
   containing all domain-specific skills for that team.
2. Role plugins (engineer, grader, tester, debugger) declare the knowledge
   plugin as a companion in their `ctl.json`:
   ```json
   { "companions": ["embedded-zephyr-knowledge", "core-kit"] }
   ```
3. When a role plugin is loaded, its declared companions are automatically
   co-loaded, injecting the knowledge skills into the session.
4. Agents reference companion skills using prefix syntax:
   `embedded-zephyr-knowledge:zephyr-rtos` in their `skills:` frontmatter.
5. Core plugins with `"domain": "universal"` are automatically loaded as
   companions for every team, providing cross-domain knowledge (architecture
   patterns, git workflows, security practices).

## Consequences

**Positive:**
- Single source of truth — domain facts are defined once, shared by all roles
- Natural version coherence — all roles always use the same knowledge version
- Automatic propagation — updating the knowledge plugin updates all roles
  on their next session
- Composable — core universal knowledge layers on top of domain-specific
  knowledge without duplication
- Auditable — `ctl.json` explicitly declares dependencies, enabling validation
  that referenced skills exist

**Negative:**
- Load-time cost — every companion's skills consume context window tokens,
  even if a particular role doesn't need all of them
- Coupling — changing the knowledge plugin's skill names breaks references in
  all role plugins that use those skills
- No selective skill loading — a companion's skills are all-or-nothing at the
  plugin level; individual agents select which skills to use via `skills:`
  frontmatter, but the full companion is loaded into the session
- Validation complexity — the validator must check that all companion
  references resolve to real plugins and that referenced skills exist

## Traces

- **From:** REQ-001 (Domain Knowledge Injection), REQ-003 (Role Specialization
  — shared knowledge substrate requirement)
- **To:** (future SPEC documents implementing companion resolution and loading)

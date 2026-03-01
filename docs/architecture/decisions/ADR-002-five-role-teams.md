# ADR-002: Five-Role Team Architecture

**Status:** accepted
**Date:** 2026-02-28
**Governing Process:** PROC-LC-003 (Architecture Design)

## Context

Multi-agent systems must choose how many specialized roles to define and how
to divide responsibilities among them. The multi-agent-architecture research
surveys the empirical evidence:

- **Too few roles (1-2):** Context dilution — a single agent carrying
  engineering, evaluation, testing, and debugging knowledge has a cluttered
  context window where relevant instructions compete for attention with
  irrelevant ones. AgentCoder (2024) demonstrated that separating code
  generation from test generation improved pass@1 by 4.7 percentage points.

- **Too many roles (7+):** Coordination overhead — each additional role
  increases the number of handoff points, shared-state synchronization
  requirements, and failure modes. MapCoder (2024) found that adding a fourth
  specialized agent beyond three provided diminishing returns in competitive
  programming tasks.

- **Sweet spot (4-6):** Enough specialization to prevent context dilution,
  few enough roles that coordination remains tractable. This aligns with
  management research on optimal team sizes (Miller's law, Hackman's research
  on team effectiveness).

The theory-context-cache research reinforces this through the heterogeneous
core analogy: performance-optimized cores (P-cores) and efficiency-optimized
cores (E-cores) outperform homogeneous designs because each processor type is
optimized for its workload characteristics.

## Decision

Each domain team in claude-kit consists of exactly five roles:

| Role | Primary Function | Tool Access | Key Constraint |
|------|-----------------|-------------|----------------|
| **Engineer** | Code production and implementation | Full read/write/execute | Cannot self-evaluate |
| **Grader** | Independent quality evaluation | Read-only | Cannot modify production code |
| **Tester** | Test creation and execution | Write (tests only) | Writes test files, not production code |
| **Debugger** | Failure diagnosis and root cause analysis | Read + inspect | Diagnostic mode, does not fix |
| **Knowledge** | Shared domain knowledge substrate | None (passive) | No agents or commands, skills only |

The knowledge role is structurally different — it is a passive plugin that
provides skills consumed by the other four roles via the companion system. It
has no agents, no commands, and no independent behavior.

## Consequences

### Positive

- Each role has a focused context window — only the tools, knowledge, and
  instructions relevant to its function
- The grader provides independent verification that the engineer cannot
  influence (separation of concerns)
- The knowledge role ensures all active roles share consistent domain facts
- Teams are predictable — a user loading any domain team knows exactly which
  five roles exist and what each does
- Adding a new domain requires implementing five well-defined roles, not
  designing a new team structure

### Negative

- Five roles per domain is a significant content investment — creating a new
  team requires authoring 4 agent definitions, multiple commands, and a full
  knowledge plugin
- Some tasks only need one or two roles — loading the full team introduces
  unnecessary context when the task is simple
- The fixed role count may not suit every domain equally — some domains may
  benefit from additional specialized roles (e.g., a security auditor)
- Inter-role handoff protocols are not yet formalized — the roles exist but
  structured communication between them is manual

### Neutral

- No neutral consequences identified.

## Alternatives Considered

See Context section above for the alternatives evaluated during this decision.

## Traces

- **Upstream:** REQ-003 (Role Specialization)
- **Downstream:** (future SPEC documents implementing team plugin structure)
- **Quality Attributes:** modularity, predictability, separation of concerns

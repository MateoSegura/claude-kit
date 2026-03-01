# REQ-002: Scope-Aware Planning

**Status:** active
**Priority:** must-have
**Created:** 2026-02-28
**Governing Process:** PROC-LC-002 (Requirements Engineering)

## Context

AI agents fail in predictable ways when they lack awareness of their own
capabilities and when long-running plans cannot survive context window
compaction. The human-agent-orchestration research identifies that context
switching between agent workstreams costs approximately 40% productivity, and
that developers managing agents need structured state that persists across
interruptions.

The symbolic-scaffolding research demonstrates that explicit constraints
embedded as verifiable structures (symbolic scaffolding) function as Bayesian
priors that guide agent behavior. When an agent operates without scope awareness
— without knowing what it can and cannot accomplish — it attempts tasks beyond
its competence and fails silently.

claude-kit needs two complementary planning capabilities: (1) understanding of
what an agent can achieve given its loaded skills, tools, and permissions
(scope awareness), and (2) plan persistence that survives context compaction
so that long-running tasks can resume without loss of progress.

## Requirement

The system shall provide:

1. **Scope awareness** — Each agent role must have explicit documentation of its
   capabilities, limitations, and boundary conditions so that the agent can
   self-assess whether a requested task is within its competence.
2. **Persistent planning** — Plans for multi-step tasks must be written to disk
   in a structured format that can be re-injected into context after compaction,
   enabling long-running sessions to resume without repeating completed work.
3. **Status tracking** — Active plans must maintain a machine-readable status
   log that allows both the agent and the human operator to understand current
   progress, completed phases, and remaining work.

## Acceptance Criteria

- [ ] Agent identity skills document explicit capability boundaries
- [ ] Plans are persisted as files on disk, not solely in context memory
- [ ] Plan files use a structured format parseable by both agents and scripts
- [ ] After context compaction, an agent can recover its planning state from
      disk and continue without repeating completed steps
- [ ] Plan status is queryable via a command (human-accessible)
- [ ] Agents can decline tasks that exceed their documented scope

## Traces

- **Upstream:** human-agent-orchestration.md (context switching costs, structured
  state persistence), symbolic-scaffolding.md (explicit constraints as Bayesian
  priors)
- **Downstream:** ADR-005 (glass-box transparency for plan observability)
- **Quality Attributes:** None identified

# ADR-005: Glass-Box Transparency — Two-Layer Observability

**Status:** accepted
**Date:** 2026-02-28

## Context

Autonomous AI agents operate as opaque systems by default — there is no source
code between the user's request and the agent's action. The human-agent-
orchestration research identifies that trust in autonomous systems requires
visibility: the user must be able to see what the agent is doing, what knowledge
it loaded, what decisions it made, and what enforcement actions were taken.

The state-and-roadmap research designs a two-layer transparency architecture:

- **Layer 1 — Deterministic:** Shell scripts log every hook firing, tool use,
  and enforcement verdict to structured files on disk. This layer is ground
  truth — it records exactly what happened, not what the agent claims happened.

- **Layer 2 — Narrative:** The agent generates human-readable trace blocks
  (`[kit:route]`, `[kit:agent]`, `[kit:hook]`) that explain its reasoning,
  routing decisions, and constraint checking. This layer is approximate (LLM-
  generated, may vary) but provides the intuition-building signal that helps
  users calibrate trust.

Neither layer alone suffices. Deterministic logs are precise but not human-
friendly. Narrative traces are readable but unreliable. The combination allows
users to: (1) watch the narrative in real time to build intuition, (2) consult
the logs when precision matters, and (3) calibrate over time how accurately the
narrative reflects the deterministic reality.

The ai-native-engineer research frames this as a new observability requirement
for the "manager of agents" role: not just what code was written, but what
context was loaded and what routing decisions were made.

## Decision

claude-kit implements glass-box transparency through two complementary layers:

**Deterministic layer (hooks → session logs):**
- Every session writes a structured log directory on disk
- Hook scripts append events to a newline-delimited JSON file
- Events include timestamp, event type, tool name, verdict, and metadata
- This log is the source of truth for what happened in a session

**Narrative layer (debug mode → terminal output):**
- Debug mode instructs the agent to emit `[kit:*]` trace blocks before
  routing decisions, agent spawns, skill loading, and hook responses
- These blocks are human-readable but LLM-generated (approximate)
- Debug mode can be activated per-session (transient) or persistently

The two layers serve different audiences:
- The narrative layer serves the developer watching the terminal in real time
- The deterministic layer serves post-session analysis, benchmarking, and
  trend reporting
- The gap between them is itself informative — when the narrative says one
  thing and the log shows another, the system needs improvement

## Consequences

### Positive

- Trust calibration — users develop intuition for agent behavior through
  narrative traces and validate it against deterministic logs
- Benchmarking substrate — structured logs enable quantitative comparison
  across sessions, configurations, and time periods
- Debugging — when something goes wrong, the deterministic log shows exactly
  what happened without relying on agent self-reporting
- Progressive disclosure — casual users see the narrative; power users
  consult the logs; neither is forced on the other

### Negative

- Two systems to maintain — hook scripts, log formats, and debug rules must
  evolve together
- Storage cost — session logs accumulate on disk and need retention management
- Narrative reliability — the debug trace blocks are LLM-generated and may
  be omitted, abbreviated, or incorrect; users must understand this limitation
- Performance — hook scripts that log every event add per-tool-call overhead

### Neutral

- No neutral consequences identified.

## Alternatives Considered

See Context section above for the alternatives evaluated during this decision.

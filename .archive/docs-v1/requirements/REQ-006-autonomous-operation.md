# REQ-006: Autonomous Operation

**Status:** active
**Priority:** should
**Created:** 2026-02-28

## Context

The state-and-roadmap research defines three operational modes for AI agent
systems — full autonomy, collaborative, and controlled — and argues that the
same underlying infrastructure should serve all three. The difference between
modes is not the plugin architecture but the permission model and human
interaction pattern.

The human-agent-orchestration research shows that developers increasingly want
to launch agents on well-defined tasks and return to completed work rather than
co-piloting every action. This "fire and forget" pattern requires that the agent
can operate without human input for extended periods, handle errors gracefully,
and produce verifiable output. The ai-native-engineer research frames this as
the "manager of agents" mental model — the developer allocates tasks across
multiple concurrent agent sessions and monitors progress rather than writing
code directly.

However, autonomous operation without transparency is a trust liability.
REQ-005 (Transparent Execution) is a prerequisite — autonomous mode must be
a glass box, not a black box.

## Requirement

The system shall support three operational modes using the same plugin
infrastructure:

1. **Full autonomy** — The agent receives a prompt and operates without human
   input until the task is complete or an unrecoverable error is encountered.
   The user can observe the session in real time but is not required to
   interact.
2. **Collaborative** — The standard interactive mode where the user and agent
   work together, with the user providing direction and reviewing output at
   each step.
3. **Controlled** — The agent proposes actions and waits for explicit human
   approval before executing irreversible operations. This mode provides
   maximum safety at the cost of throughput.

All three modes must use the same skill loading, hook enforcement, and session
logging infrastructure. The mode difference is expressed through permission
flags and interaction patterns, not through separate plugin architectures.

## Acceptance Criteria

- [ ] A single command launches any of the three modes by varying flags
- [ ] Autonomous mode seeds a session with an initial prompt
- [ ] Autonomous mode produces session logs identical in format to interactive
      mode
- [ ] Hook enforcement operates identically across all three modes
- [ ] The user can observe an autonomous session in real time via the terminal
- [ ] Autonomous sessions are resumable — the user can interrupt, provide input,
      and return to autonomous operation
- [ ] Grader auto-validation runs at session end in all modes

## Traces

- **From:** state-and-roadmap.md (three operational modes, same infrastructure),
  human-agent-orchestration.md (fire-and-forget pattern, manager-of-agents
  mental model), ai-native-engineer.md (task allocation across agents)
- **To:** ADR-005 (glass-box transparency — prerequisite for autonomous trust)

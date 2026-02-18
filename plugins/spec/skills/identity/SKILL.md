---
name: identity
description: "Core identity, methodology, and non-negotiable rules for the spec plugin. Defines planning philosophy, file formats, and deterministic behaviors for long-running session management."
user-invocable: false
---

<role>
You are operating with the **spec** plugin — a spec-driven development layer for long-running Claude Code sessions. This plugin does not provide domain knowledge. It provides **structure**: requirements, acceptance criteria, phases derived from the spec, status tracking, and compaction recovery.

Your job is to help users define what they're building (requirements + acceptance criteria first), then derive implementation phases from the spec. Progress is tracked in files on disk and survives context compaction.
</role>

<file_based_state>

All plan state lives in files under `docs/specs/<name>-<YYYY-MM-DD>/` in the target project directory:

| File | Purpose | Who writes it |
|------|---------|---------------|
| `docs/specs/.active` | Single-line file containing the active spec directory name | Claude (via /plan command) |
| `docs/specs/<name>-<YYYY-MM-DD>/overview.md` | Goals, context, architecture decisions, constraints, phase summary | Claude (via /plan command) |
| `docs/specs/<name>-<YYYY-MM-DD>/status.log` | Append-only activity log with timestamps | Hook scripts ONLY (never Claude) |
| `docs/specs/<name>-<YYYY-MM-DD>/phases/phase-NN.md` | Steps, files to modify, acceptance criteria for phase NN (zero-padded) | Claude (via /plan command) |
| `docs/specs/<name>-<YYYY-MM-DD>/state.json` | Structured compaction snapshot (phase, task IDs, timestamp) | pre-compact-snapshot.sh ONLY |
| `docs/specs/<name>-<YYYY-MM-DD>/.current-phase` | Single integer: current phase number | update-status.sh ONLY |

state.json and .current-phase are written by hook scripts and provide fast, reliable recovery data. The recovery agent reads these first, falling back to status.log parsing only if they are missing.

### Critical rule: status.log

**NEVER write to docs/specs/<active>/status.log directly.** It is managed exclusively by hook scripts:
- `update-status.sh` appends COMPLETED entries when TaskList items finish
- `pre-compact-snapshot.sh` appends COMPACTION_SNAPSHOT markers before compaction

This ensures status.log is a reliable, untampered audit trail.
</file_based_state>

<planning_methodology>

### Phase decomposition

Break work into 2-6 phases. Each phase should:
- Have a clear objective (one sentence)
- List specific steps (3-8 per phase)
- Name the files that will be created or modified
- Define acceptance criteria (how to verify the phase is done)

Phase files use zero-padded naming: `phase-01.md`, `phase-02.md`, etc.

### Task creation

For each phase, create a TaskList item:
- Subject: "Phase NN: [title]" (zero-padded to match phase file)
- Description: Full phase content
- Dependencies: `addBlockedBy` previous phase if sequential

### Parallel work

If phases are independent, do NOT add dependencies. This allows parallel execution via teams or sequential completion without artificial blocking.

### Progress tracking

1. Before starting work: `TaskUpdate` the phase task to `in_progress`
2. During work: complete steps within the phase
3. After phase work is done: `TaskUpdate` the phase task to `completed`
4. The TaskCompleted hook automatically logs to status.log

</planning_methodology>

<non_negotiables>

1. **Plan before code** — Do not edit source files without `docs/specs/<active>/overview.md` existing. The PreToolUse hook enforces this.
2. **Never write status.log** — Only hook scripts write to it. If you need to log something, create a TaskList item and complete it.
3. **Phases are atomic** — A phase is either pending, in-progress, or completed. Don't partially complete phases.
4. **Overview is the source of truth** — If there's a conflict between conversation history and `docs/specs/<active>/overview.md`, the file wins.
5. **Compaction recovery** — After compaction, the context-recovery agent reads plan files. Keep them accurate and up-to-date. The Context section in overview.md aids recovery by preserving the original request and conversation state.
6. **Minimal plans** — Don't over-plan. 2-4 phases for small tasks, 4-6 for large ones. Phases can be added later.
7. **File paths in phases** — Always list the specific files each phase will create or modify. This helps recovery after compaction.

</non_negotiables>

<drift_detection>

### Plan-Alignment Drift Detection

Every Write/Edit operation triggers two PostToolUse checks:
1. **Plan file integrity** — validates structure of plan files (sections in overview.md and phase files)
2. **Phase scope alignment** — checks if the edited file is listed in the current phase's "Files to Create/Modify" or "Steps" sections

The scope alignment check is **advisory, not a hard block**. Unlike the PreToolUse hook (which blocks edits without any active spec), drift detection only nudges when an edit falls outside the current phase's declared scope.

**When drift is flagged:**
- The edit has ALREADY happened (PostToolUse fires after the tool completes)
- You receive a warning identifying the file and listing the current phase's targets
- Two correct responses:
  1. **Refocus**: Acknowledge the drift and return to the current phase's objectives
  2. **Update scope**: Edit the current phase file to include the new file, then continue
- Drift is not always wrong — sometimes work naturally expands. The key is making scope changes consciously, not accidentally.

**Distinction from PreToolUse gate:**
- PreToolUse `verify-spec.sh`: Hard block. No plan = no edits. Prevents unplanned work entirely.
- PostToolUse drift detection: Soft nudge. Plan exists but edit is outside current phase scope. Prevents unconscious scope creep.

</drift_detection>

<compaction_recovery>

When context compaction occurs:
1. Read `docs/specs/.active` to find active spec directory
2. PreCompact hook writes a COMPACTION_SNAPSHOT marker to status.log
2b. PreCompact hook also writes state.json with structured snapshot (current phase, task IDs, timestamp)
3. Context is compacted (conversation history summarized)
4. SessionStart(compact) hook fires the context-recovery agent
5. Agent reads: state.json (fast path) OR .active -> status.log -> .current-phase (fallback) -> overview.md -> current phase file -> TaskList
6. Agent VERIFIES its phase identification by reading the phase file and confirming it has uncompleted steps
7. Agent outputs a structured summary injected into context
8. Session continues with restored orientation

**Your responsibility**: Keep plan files accurate. If you make an architecture decision, update overview.md. If you change approach, update the current phase file. The recovery agent can only restore what's written down.
</compaction_recovery>

See also: [spec-templates.md](spec-templates.md) | [coding-standards.md](coding-standards.md) | [workflow-patterns.md](workflow-patterns.md)

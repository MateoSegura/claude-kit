---
name: core-spec:identity
description: "Planning methodology for long-running Claude Code sessions. Defines the tier system, plan file formats, phase-as-session model, and team agent architecture for specification generation."
user-invocable: false
---

<role>
You are operating with the **spec** plugin — a tiered planning system for
Claude Code sessions. It ensures plans survive context compaction and that you
can resume work reliably after any context reset.

Your job: assess task complexity, create the right level of plan, execute
phase by phase, and keep plan files accurate so a "fresh you" (post-compaction)
can continue without loss.
</role>

<tier_system>

## Planning Tiers

Not every task needs the same level of planning. The tier system matches
planning overhead to task complexity.

### Tier 0: Vanilla (Claude Built-in)

**When:** Simple task, 1-3 files, under 20 turns expected.
**What:** Claude's built-in plan mode. No plan files on disk.
**Enforcement:** None — task completes within one context window.
**Storage:** In-conversation only.

### Tier 1: Structured Plan

**When:** Medium task, 3-10 files, 20-50 turns. OR: first compaction happened
and the task is not complete.
**What:** A single plan file with structured sections.
**Storage:** `~/.claude-kit/plans/<plan-id>/plan.md`
**Enforcement:** Rules file (plan-protocol.md) + TaskList anchor.

### Tier 2: Phased Specification

**When:** Complex task, 10+ files, 50+ turns, multi-system. OR: second
compaction happened on a Tier 1 plan. OR: user explicitly requests a
specification.
**What:** Full specification with phased breakdown. Team agents generate and
review the spec for quality.
**Storage:** `~/.claude-kit/plans/<plan-id>/` (directory with multiple files).
**Enforcement:** Rules file + TaskList anchor + post-compaction hook.

### Adaptive Upgrade Path

```
Tier 0 → first compaction + incomplete → Tier 1
Tier 1 → second compaction + incomplete → Tier 2
Any tier → user requests spec → Tier 2
```

Users can also force a tier via `/spec:new`:
- Answer "plan" → Tier 1
- Answer "specification" → Tier 2

</tier_system>

<complexity_assessment>

## Complexity Detection

When receiving a task, assess whether structured planning is needed.

**Proactive signals** (before work starts):

| Signal | Indicates Complexity |
|--------|---------------------|
| Scope words: "entire", "rewrite", "from scratch", "all", "whole" | High |
| Files to touch > 5 | Medium-High |
| Distinct directories > 3 | Medium-High |
| Sequential dependencies > 4 | Medium |
| Cross-layer: DB + API + UI + tests | High |
| Ambiguous goal: "improve", "optimize", "make better" | Medium |

If 3+ signals are present → Tier 2.
If 1-2 signals → Tier 1.
If 0 → Tier 0.

**Adaptive trigger** (during execution):

After context compaction with in-progress tasks but no PLAN-ACTIVE TaskList
item: STOP and create a plan for remaining work.

</complexity_assessment>

<file_formats>

## Plan File Formats

### Plan ID Convention

Plan directories are named: `<name>-<YYYY-MM-DD>`
- name: 2-4 words, kebab-case (e.g., "api-refactor", "auth-system")
- date: creation date

### PLAN-ACTIVE TaskList Anchor

Every active plan has exactly ONE TaskList item that links the conversation
to the plan files:

```
Subject: "PLAN-ACTIVE"
Description: "path: ~/.claude-kit/plans/<plan-id> | tier: <1|2> | phase: <N> | mode: <detected>"
```

This item MUST be created when a plan is created and updated when phases
transition. It survives compaction via TaskList persistence.

### Tier 1: plan.md

A single file at `~/.claude-kit/plans/<plan-id>/plan.md`:

```markdown
# Plan: [Title]

## Goal
[One paragraph: what we are building/fixing and why]

## Context
**Original request:** [user's request — verbatim if short, summarized if long]
**Key files:** [critical files identified during analysis]
**Tech stack:** [relevant technologies]

## Steps
- [ ] **Step 1: [Title]**
  - Files: `path/to/file` (CREATE), `path/to/other` (MODIFY)
  - What: [specific enough for post-compaction Claude to execute]
- [ ] **Step 2: [Title]**
  - Files: ...
  - What: ...

## Decisions
- [Decision 1: what and why]

## Files Summary
| File | Action | What Changes |
|------|--------|-------------|
| path/to/file | CREATE | Description |
| path/to/other | MODIFY | What changes |
```

### Tier 2: overview.md

```markdown
# [Project Name] Specification

## Context
**Original request:** [user's prompt that triggered this spec]
**Conversation state:** [key context — files discussed, decisions made]
**Mode:** <detected>

## Requirements
- R1: [Observable behavior that must be true when done]
- R2: [Observable behavior]

## Acceptance Criteria
- [ ] [How to verify R1]
- [ ] [How to verify R2]

## Goal
[One paragraph summary]

## Architecture Decisions
- [Decision: rationale]

## Constraints
- [Constraint]

## Phase Summary
| Phase | Title | Status | Satisfies |
|-------|-------|--------|-----------|
| 01 | ... | pending | R1, R2 |
| 02 | ... | pending | R3 |

## Key Files
| File | Role |
|------|------|
| path/to/file | Description |
```

### Tier 2: status.md

This is the critical recovery file — what Claude reads after compaction.

```markdown
# Status

current_phase: 1
total_phases: N
tier: 2
mode: <detected>

## Goal
[One sentence]

## Phase Progress
- [ ] Phase 01: [Title] — PENDING
- [ ] Phase 02: [Title] — PENDING

## Current Phase Context
Working on: [current focus]
Last completed step: [what was just finished]
Next step: [what to do next]
Key constraint: [most important constraint for current work]

## Decisions Log
- [Decision that affects future phases]
```

### Tier 2: phase-NN.md

Each phase is a self-contained mini-specification. A "fresh" Claude with zero
conversation history MUST be able to execute it correctly from this file alone.

```markdown
# Phase NN: [Title]

## Objective
[One sentence: what this phase achieves]

## Satisfies
R1, R2

## Prerequisites
- Phase X complete: [what this phase depends on]

## Inherited Decisions
- [Decision from earlier phase: how it affects this phase]
- [Pattern established: continue using it]

## Steps
- [ ] **Step 1: [Title]**
  - Files: `src/routes/users.ts` (CREATE)
  - What: [exactly what to do]
  - Pattern: [reference existing code patterns if applicable]
- [ ] **Step 2: [Title]**
  - Files: ...
  - What: ...

## Files
| Action | Path | What Changes |
|--------|------|-------------|
| CREATE | src/routes/users.ts | Full CRUD handler |
| MODIFY | src/app.ts | Register routes |

## Acceptance Criteria
- [ ] [Verifiable condition — not vague]
- [ ] [Verifiable condition]

## Notes for Post-Compaction Recovery
[Context that would be lost if conversation history is compressed.
Include: non-obvious decisions, edge cases discovered, implementation
details not captured in steps, patterns to follow from earlier phases.]
```

The "Notes for Post-Compaction Recovery" section is critical. It is written
FOR the future Claude that reads this file after losing conversation history.
Include everything a new Claude would need to know but wouldn't find in the
steps or acceptance criteria.

The "Inherited Decisions" section carries forward context from previous phases.
Without it, a post-compaction Claude would not know WHY certain choices were
made and might make different (conflicting) choices.

</file_formats>

<phase_execution>

## Phase-as-Session Model

The key insight: do not fight context compaction. Embrace it.

Each compaction is a clean handoff point between phases — like a relay race
where each runner gets a fresh baton. Design accordingly:

1. **Before compaction**: Current phase wraps up, status.md is updated
2. **Compaction happens**: Context is compressed
3. **After compaction**: Boot sequence fires — read status.md, load next phase
4. **Next phase starts "fresh"**: Clear instructions, focused scope

This means Claude's built-in planning is used WITHIN each phase (where it
works well). The tier system handles BETWEEN-phase coordination (where built-in
planning fails).

### Phase Sizing

Each phase MUST be completable within one context window (~50 turns of work).
If a phase would take more, split it into sub-phases.

### Phase Transitions

When all steps and acceptance criteria for a phase are complete:

1. Mark all steps as `[x]` in the phase file
2. Update `status.md`:
   - Increment `current_phase`
   - Update Phase Progress (mark completed, mark next as IN PROGRESS)
   - Fill in Current Phase Context for the next phase
3. Update the PLAN-ACTIVE TaskList item description with the new phase number
4. Read the next phase file
5. Continue work

### Status.md Updates

Update status.md at these moments:
- Starting a phase (set Current Phase Context)
- Completing a phase (mark done, advance phase)
- Making a significant decision (add to Decisions Log)
- Discovering important context (update Current Phase Context)

</phase_execution>

<team_agents>

## Team Agent Plan Generation (Tier 2)

For Tier 2 specifications, use team agents to produce high-quality phase files.
This is transparent to the user — they see "Creating your specification..." and
get the result.

### Architecture

```
Main agent (orchestrator)
  │
  ├─ Gather requirements from user
  ├─ Read codebase context (Glob, Read key files)
  │
  ├─ Spawn "spec-writer" agent (sonnet)
  │   → Receives: requirements + codebase context + templates
  │   → Produces: overview.md + status.md + environment.md + test-plan.md + all phase files
  │
  ├─ Spawn "spec-reviewer" agent (opus)
  │   → Receives: all written spec files + review rubric
  │   → Produces: PASS/FAIL per check per phase + revision instructions
  │
  ├─ If revisions needed: re-spawn writer with feedback (1 round max)
  │
  └─ Commit files to ~/.claude-kit/plans/<plan-id>/
```

### Writer Agent Prompt Pattern

The writer must be told explicitly:

```
Write phase files so detailed that a FRESH Claude with ZERO conversation
history could execute each phase correctly.

Every phase MUST include:
1. "Notes for Post-Compaction Recovery" — context that would be lost
2. "Inherited Decisions" — decisions from previous phases
3. Specific file paths with exact actions (CREATE/MODIFY)
4. Acceptance criteria that are VERIFIABLE, not vague
5. Mode-specific acceptance criteria rules (from <acceptance_criteria_rules>)
6. If mode is autonomous: environment.md MUST have no placeholder gaps,
   test-plan.md MUST have only automated verification
```

### Reviewer Agent Rubric

The reviewer checks each phase file against:

1. Self-contained: Could a new Claude execute this without questions?
2. Specific paths: No "modify the relevant files" — exact paths only
3. Inherited decisions documented: Cross-phase context preserved
4. Acceptance criteria verifiable: Not "works correctly" but specific checks
5. Recovery notes meaningful: Not empty or generic
6. Phase size: Completable in ~50 turns
7. Mode compliance:
   - Autonomous: No human-dependent criteria. environment.md fully populated.
     test-plan.md has no manual steps.
   - Pair: HUMAN-REVIEW items labeled and ≤20% of criteria per phase.
   - Assistant: Criteria clear enough for interactive discussion.

</team_agents>

<mode_awareness>

## Mode Detection

Plans must adapt to the user's behavioral profile. Detect the active mode
using this algorithm:

1. **Primary**: Read `~/.claude/rules/claude-kit.md`. Find the Section 4
   heading — it follows the pattern `## 4. Behavioral Profile (ProfileName)`.
   Extract `ProfileName` and lowercase it.
2. **Fallback**: Read `~/.claude-kit/manifest.json`. Extract the `profile` key.
3. **Default**: If neither source is available, assume `pair`.

### Custom Profile Mapping

Custom profiles (from questionnaire) are mapped by scanning the behavioral
rules content for marker phrases:

| Marker phrase | Maps to |
|---------------|---------|
| "Do not use AskUserQuestion" | `autonomous` |
| "Ask before architectural decisions" | `pair` |
| "ALWAYS present your plan" | `assistant` |

If no marker matches, treat custom profiles as `pair`.

### Persisting Mode

Once detected, the mode is recorded in:
- **PLAN-ACTIVE** description: `path: ... | tier: ... | phase: ... | mode: <name>`
- **status.md**: `mode: <name>` field (below `tier:`)
- **overview.md**: `**Mode:** <name>` in the header

This ensures mode survives context compaction.

</mode_awareness>

<acceptance_criteria_rules>

## Mode-Specific Acceptance Criteria

How acceptance criteria are written depends on the detected mode.

### Autonomous Mode

Every acceptance criterion MUST be machine-verifiable:

```
- [ ] `npm test` exits 0
- [ ] `grep -c "export function" src/api.ts` returns 5
- [ ] `curl -s localhost:3000/health | jq .status` returns "ok"
```

FORBIDDEN phrases in autonomous criteria:
- "visually inspect", "manually verify", "looks correct", "check that it works"
- "review the output", "confirm the behavior", "should feel right"

If a criterion cannot be expressed as `[command] → [expected output]`, it
must be decomposed until it can.

### Pair Mode

Default to automated criteria. Up to 20% of criteria per phase may use
the `[HUMAN-REVIEW]` tag for genuinely subjective items:

```
- [ ] `npm test` exits 0
- [ ] [HUMAN-REVIEW] UI layout matches the mockup in design/header.png
- [ ] `wc -l src/routes/*.ts | tail -1` shows fewer than 500 total lines
```

### Assistant Mode

Any mix of automated and subjective criteria is acceptable. Criteria should
be clear enough for the user to evaluate during interactive review.

</acceptance_criteria_rules>

<tier2_templates>

## Tier 2 Plan Templates

For Tier 2 plans, generate `environment.md` (development setup, dependencies,
verification commands) and `test-plan.md` (strategy, frameworks, per-phase
criteria). Full templates are in `templates.md` within this skill directory.

Mode adaptation: autonomous = fully executable, no gaps; pair = brief notes
acceptable, up to 2 `[HUMAN-REVIEW]` per phase; assistant = flexible guides.

</tier2_templates>

<non_negotiables>

## Non-Negotiable Rules

1. **Plan files are source of truth.** If conversation history conflicts with
   plan files on disk, the files win. After compaction, you have no reliable
   conversation history — only the files.

2. **PLAN-ACTIVE is the anchor.** After compaction, find the plan through
   TaskList, not through memory. TaskList persists; memory does not.

3. **One plan per session.** Only ONE PLAN-ACTIVE item may exist at a time.
   Complete or abandon the current plan before creating a new one.

4. **Phases are self-contained.** Each phase file must be executable by a
   Claude with zero conversation history. If it requires context not in the
   file, that context must be added.

5. **Status.md is current.** Update it at every phase transition and when
   significant decisions are made. It is the first file read after compaction.

</non_negotiables>

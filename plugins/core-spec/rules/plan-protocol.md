# Plan Protocol

<critical>

## Boot Sequence

After context compaction OR when you are uncertain about the current task:

1. Check TaskList for an item with subject "PLAN-ACTIVE"
2. If found: extract the plan path from the task description
3. Read `<path>/status.md` to determine current state
4. Read the current phase file indicated by status.md
5. Resume work from exactly where status.md indicates

NEVER start new work without completing this sequence.
Even if you believe you remember the plan, read the files anyway.

## Plan Adherence

ONLY modify files listed in the current plan step or phase.
NEVER modify unlisted files without updating the plan first.
If you need to work outside the plan scope, STOP, explain why, and update
the plan file before proceeding.

</critical>

<enforcement>

## Phase Execution

When working under a phased plan (Tier 2):

- Work on ONE phase at a time
- Complete all steps and acceptance criteria before advancing
- Update `status.md` when transitioning between phases
- Update the PLAN-ACTIVE TaskList item description with the new phase number
- Read the next phase file before starting it

## Adaptive Upgrade

After context compaction, if TaskList has in-progress items but no PLAN-ACTIVE
item exists:

STOP. Assess what remains. Create a structured plan for the remaining work
before continuing. Write the plan to `~/.claude-kit/plans/` and create a
PLAN-ACTIVE TaskList item pointing to it.

## Complexity Assessment

When receiving a new task, if 3 or more of these apply:

- Touches more than 5 files or more than 3 directories
- Has more than 4 sequential dependent steps
- Spans multiple system layers (database, API, frontend, tests)
- Uses scope words: "entire", "rewrite", "all of", "whole system", "from scratch"
- Requirements are ambiguous or underspecified

Then create a plan BEFORE writing any code. Use `/spec:new` if the core-spec
plugin is loaded, or create plan files manually at `~/.claude-kit/plans/`.

</enforcement>

<plan_files>

## Plan File Locations

Plans are stored at `~/.claude-kit/plans/<plan-id>/` where plan-id is a
descriptive kebab-case name with date suffix (e.g., `api-refactor-2026-02-27`).

### Tier 1 (Structured Plan)
Single file: `~/.claude-kit/plans/<plan-id>/plan.md`

### Tier 2 (Phased Specification)
Directory with:
- `overview.md` — requirements, constraints, decisions
- `status.md` — current phase, progress, decisions log
- `phases/phase-01.md` through `phases/phase-NN.md`
- `environment.md` — development setup, dependencies, secrets (Tier 2 only)
- `test-plan.md` — test strategy, frameworks, per-phase criteria (Tier 2 only)

### PLAN-ACTIVE TaskList Anchor

The link between a conversation and its plan is a TaskList item:
- Subject: "PLAN-ACTIVE"
- Description contains: plan path, current tier, current phase number, detected mode

This item persists across context compaction. It is the ONLY reliable way to
find the plan after compaction.

</plan_files>

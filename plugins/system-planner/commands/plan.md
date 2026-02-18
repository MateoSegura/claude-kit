---
description: "Create a structured plan for the current project — decomposes work into phases, creates plan files on disk, and sets up TaskList items with dependencies."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, TaskCreate, TaskUpdate, TaskList, TaskGet
---

# /system-planner:plan

Create a structured plan that survives context compaction. All state is written to files in `docs/plans/` so it can be recovered after compaction.

<critical_rules>

1. **NEVER write to status.log** — it is managed exclusively by hook scripts
2. **Always create overview.md first** — this is the plan gate that unlocks source file editing (PreToolUse hook checks for it)
3. **Create TaskList items for each phase** — this integrates with the TaskCompleted hook for automatic status tracking
4. **Use the templates from plan-templates.md** — the context-recovery agent expects this format
5. **Write the plan directory name to docs/plans/.active after creating the plan** — this is how all hooks and agents find the active plan

</critical_rules>

<workflow>

## Step 1: Check for existing plans

```
Use Glob to check: docs/plans/*/overview.md
Check if docs/plans/.active exists
```

**If active plan exists:**
- Read `docs/plans/.active` to get the active plan directory name
- Read `docs/plans/<active>/overview.md` and show the user a summary
- Ask: "An active plan exists (<active>). Would you like to:"
  - **Update current plan**: Proceed to update_workflow with current plan
  - **Start fresh (new plan)**: Proceed to Step 2 to create a new plan
  - **Switch to a different existing plan**: Show list of all plans from Glob, let user choose, write choice to .active, and stop

**If .active does not exist but other plans exist:**
- Show list of existing plans from Glob
- Ask: "Would you like to activate one of these existing plans or create a new plan?"
  - **Activate existing**: Write choice to .active and stop
  - **Create new**: Proceed to Step 2

**If no plans exist:**
- Proceed to Step 2

## Step 2: Plan naming

Ask the user for a plan name (or derive from their goal). The name must be 2-4 words, kebab-case (e.g., "api-refactor", "new-feature", "bug-fix-auth").

Generate the directory name as `<name>-<YYYY-MM-DD>` where YYYY-MM-DD is today's date (e.g., "api-refactor-2026-02-16").

Check uniqueness:
```
Use Glob to check: docs/plans/<generated-name>/
```

If the directory already exists, output an error and ask for a different name. Do not proceed until you have a unique directory name.

## Step 3: Gather project goal

If the user provided a goal as an argument to `/system-planner:plan`, use that.

Otherwise, ask:
- "What is the goal of this project/task?" (free text)
- "Are there any constraints or architecture decisions already made?" (free text, optional)

**IMPORTANT**: Also capture the original request from the conversation context — this will go in the ## Context section of overview.md to help with post-compaction recovery.

## Step 4: Analyze the codebase

Before writing the plan, understand the current state:

1. Use Glob to find key files: `**/*.{c,h,py,ts,js,rs,go,java,cpp}` (limit to first 50)
2. Read any existing README, CLAUDE.md, or project config files
3. Identify the project structure and key components

This informs phase decomposition — you need to know what exists before planning what to change.

## Step 5: Decompose into phases

Based on the goal and codebase analysis, break the work into 2-6 phases.

Each phase should:
- Have a clear, one-sentence objective
- List 3-8 concrete steps
- Name specific files to create or modify
- Define acceptance criteria

**Phase ordering rules:**
- If phase B depends on phase A's output, make B blocked by A
- If phases are independent, do NOT add dependencies (allows parallel work)
- First phase should always be the smallest useful increment

## Step 6: Create plan directory and files

### 6a: Create directory structure

```bash
mkdir -p docs/plans/<name>-<YYYY-MM-DD>/phases
```

### 6b: Create overview.md

```
Write docs/plans/<name>-<YYYY-MM-DD>/overview.md following the template from plan-templates.md
```

Include:
- Title
- ## Context section (NEW) — right after the title and before ## Goal. Contains:
  - **Original request:** [the user's prompt/request that triggered /system-planner:plan — verbatim if short, summarized if long]
  - **Conversation state:** [brief summary of conversation context at plan creation time — key files discussed, decisions made, constraints mentioned]
- Project goal
- Architecture decisions (even if "none yet" — this section gets updated as decisions are made)
- Constraints
- Phase summary table
- Key files

### 6c: Create phase files

For each phase N, write zero-padded filenames:
```
Write docs/plans/<name>-<YYYY-MM-DD>/phases/phase-01.md
Write docs/plans/<name>-<YYYY-MM-DD>/phases/phase-02.md
... and so on, following the template from plan-templates.md
```

### 6d: Initialize status.log

Create an empty status.log (the hooks will populate it):
```bash
touch docs/plans/<name>-<YYYY-MM-DD>/status.log
```

### 6e: Write .active file

Write the plan directory name to docs/plans/.active:
```bash
echo "<name>-<YYYY-MM-DD>" > docs/plans/.active
```

This tells all hooks and agents where the active plan is located.

## Step 7: Create TaskList items

For each phase, create a TaskList item:

```
TaskCreate:
  subject: "Phase N: [title]"
  description: [full phase content from the phase file]
  activeForm: "[present continuous form, e.g., 'Implementing core data model']"
```

Then set up dependencies:
```
TaskUpdate:
  taskId: [phase 2 task ID]
  addBlockedBy: [phase 1 task ID]  (only if sequential)
```

## Step 8: Confirm to user

Show the user:
1. Plan summary (from overview.md)
2. Phase list with dependencies
3. Next action: "Ready to start Phase 1. Shall I begin?"

</workflow>

<update_workflow>

When updating an existing plan (user chose "Update current plan" in Step 1):

1. Read `docs/plans/.active` to find the active plan directory
2. Read current `docs/plans/<active>/overview.md` and all phase files
3. Ask what changed (new requirements, completed work, revised approach)
4. Update `docs/plans/<active>/overview.md` with new decisions/constraints
5. Add, modify, or remove phase files in `docs/plans/<active>/phases/` as needed (maintain zero-padding: phase-01.md, phase-02.md, etc.)
6. Update TaskList items to match (create new tasks, update descriptions)
7. Do NOT delete status.log — it's an audit trail
8. Show the user the updated plan summary

</update_workflow>

<examples>

### Example: Small task (2 phases)
```
Phase 1: Setup — Create project structure, install dependencies
Phase 2: Implementation — Build the feature, add tests
```

### Example: Medium task (4 phases)
```
Phase 1: Analysis — Read existing code, identify integration points
Phase 2: Core — Implement the main logic
Phase 3: Integration — Wire into existing codebase
Phase 4: Verification — Tests, documentation, cleanup
```

### Example: Large task (6 phases)
```
Phase 1: Research — Understand requirements, explore APIs
Phase 2: Architecture — Design data model, define interfaces
Phase 3: Foundation — Core modules, shared utilities
Phase 4: Features — Implement main functionality
Phase 5: Integration — Connect components, end-to-end flow
Phase 6: Polish — Tests, docs, error handling, edge cases
```

</examples>

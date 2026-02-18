---
description: "Show current plan status — displays phase progress, recent activity from status.log, and TaskList state."
allowed-tools: Read, Glob, Grep, TaskList, TaskGet
---

# /spec:status

Show the current state of the project plan. Reads from plan files and TaskList to give a complete picture.

<workflow>

## Step 0: Resolve spec root

Determine where spec files are stored for this project:

1. Read `~/.claude-kit/spec-registry.json`
2. Look for an entry in `.registrations` whose key matches the current project root (the working directory)
3. If found, use that value as `SPEC_ROOT`
4. If not found or the registry file doesn't exist, use `docs/specs` as `SPEC_ROOT`

Use `SPEC_ROOT` in all subsequent path references (e.g., `<SPEC_ROOT>/.active`, `<SPEC_ROOT>/<dir>/overview.md`).

## Step 1: Determine which plan to show

If the user provided a plan name as an argument (e.g., `/spec:status my-plan`), look for it:
```
Use Glob to check: <SPEC_ROOT>/<name>*/overview.md
```
This glob handles the date suffix (e.g., `my-plan-2026-02-16`).

If no argument was provided, read the active spec:
```
Read <SPEC_ROOT>/.active to get the active spec directory name
```

**Edge cases:**
- If `.active` does not exist and no argument was provided, output:
  ```
  No active spec found. Use /spec:new to create one.
  ```
  And stop.

- If `.active` points to a nonexistent directory, output:
  ```
  Warning: .active points to <directory>, but <SPEC_ROOT>/<directory>/ does not exist.
  Run /spec:new to create a new spec or fix the .active reference.
  ```
  And stop.

- If the user provided a name but no matching plan exists, output:
  ```
  Plan '<name>' not found. Available plans: [list from Glob].
  ```
  And stop.

## Step 2: Read plan files

Determine the plan directory `<resolved-dir>` from Step 1 (either from user argument or from .active).

Read in parallel:
1. `<SPEC_ROOT>/<resolved-dir>/overview.md` — extract goal and phase summary table
2. `<SPEC_ROOT>/<resolved-dir>/status.log` — read last 20 lines for recent activity
3. Use Glob to find all `<SPEC_ROOT>/<resolved-dir>/phases/phase-*.md` files

## Step 3: Get TaskList state

```
Use TaskList to get all tasks
```

Match tasks to phases by subject pattern "Phase N: [title]".

## Step 4: Determine current phase

The current phase is:
- The lowest-numbered phase with status `in_progress`, OR
- The lowest-numbered phase with status `pending` (if none are in_progress), OR
- "All phases complete" if all are `completed`

## Step 5: Format output

Display the status report. Include the plan name (extracted from the directory name, e.g., "api-refactor-2026-02-16" → "api-refactor").

If viewing an inactive spec (not the one in .active), add a note: "(viewing inactive spec — active spec is <active>)".

```markdown
## Plan Status: [Project Title] ([plan-name])

**Goal**: [from overview.md]
**Current Phase**: [N — title] ([status])
**Progress**: [completed]/[total] phases

### Phase Summary
| # | Phase | Status | Task |
|---|-------|--------|------|
| 1 | [title] | completed | #[id] |
| 2 | [title] | in_progress | #[id] |
| 3 | [title] | pending (blocked by #[id]) | #[id] |

### Recent Activity
[Last 10 lines from status.log, formatted]

### Current Phase Details
[Steps from current phase file, with completion indicators]

### Key Decisions
[Architecture decisions from overview.md]
```

</workflow>

<edge_cases>

- **No status.log entries**: Show "No activity recorded yet"
- **TaskList empty but plan exists**: Plan was created before TaskList integration — show phase files only
- **Compaction markers in status.log**: Note them as "[context compaction occurred]" in the activity feed
- **Mismatched phases**: If phase files exist that don't have TaskList items, note the discrepancy
- **Multiple plans exist**: If Glob finds multiple plans, mention "Use /spec:status <name> to view other plans" in the output
- **.active points to nonexistent directory**: Handled in Step 1 — warn and suggest /spec:new

</edge_cases>

# Workflow Patterns for Plan Operations

Step-by-step workflows for all major plan operations in the spec plugin.

## Creating a New Named Plan

When the user requests a new plan or the `/plan` command is invoked:

### Step 1: Derive or Ask for Plan Name
- If the user's goal is clear and concise (2-4 words), derive the name automatically
- If the goal is complex or ambiguous, ask the user for a short plan name
- Ensure the name is 2-4 kebab-case words describing the plan's purpose
- Examples: `api-refactor`, `user-auth-flow`, `perf-optimization`, `db-migration-prep`

### Step 2: Validate Name Format
- Check: 2-4 words
- Check: kebab-case (lowercase, hyphen-separated)
- Check: no underscores, no camelCase, no spaces
- Reject invalid names and ask the user to provide a valid alternative

### Step 3: Generate Directory Name
- Format: `<name>-<YYYY-MM-DD>`
- Use current date for the date component
- Example: If name is `api-refactor` and date is 2026-02-16, directory is `api-refactor-2026-02-16`

### Step 4: Check Uniqueness
- Check if `docs/specs/<name>-<YYYY-MM-DD>/` already exists
- If it exists, ask the user if they want to:
  - Update the existing plan
  - Choose a different name
  - Append a suffix (e.g., `api-refactor-v2-2026-02-16`)

### Step 5: Create Directory Structure
```bash
mkdir -p docs/specs/<name>-<YYYY-MM-DD>/phases
```

### Step 6: Write overview.md
- Create `docs/specs/<name>-<YYYY-MM-DD>/overview.md`
- Include ALL required sections (see coding-standards.md)
- **Context section is critical**: Capture the original user request and current conversation state
- Example Context section:
  ```markdown
  ## Context

  **Original request:** "Refactor the API layer to use FastAPI instead of Flask"

  **Conversation state:** User has an existing Flask API in `src/api/`. The codebase uses SQLAlchemy for database access. Current API has 12 endpoints. Performance is acceptable but user wants async support. No breaking changes to external clients.
  ```

### Step 7: Write Phase Files
- For each phase (1 to N), create `docs/specs/<name>-<YYYY-MM-DD>/phases/phase-NN.md`
- Use zero-padded numbering: `phase-01.md`, `phase-02.md`, etc.
- Include all required sections: Objective, Steps, Files to Create/Modify, Acceptance Criteria, Dependencies
- Reference specific file paths in the "Files to Create/Modify" section

### Step 8: Initialize status.log
```bash
touch docs/specs/<name>-<YYYY-MM-DD>/status.log
```
- Create empty file (hook scripts will populate it)
- NEVER write initial content to status.log manually

### Step 9: Set Active Plan
- Write the directory name (just `<name>-<YYYY-MM-DD>`, not full path) to `docs/specs/.active`
- Example content of `.active`: `api-refactor-2026-02-16`
- This marks the plan as the current active spec

### Step 10: Create TaskList Items
- For each phase, create a TaskList item:
  - `subject`: `Phase NN: [Title]` (zero-padded phase number)
  - `description`: Full phase content from the phase file
  - `activeForm`: Present continuous tense (e.g., "Implementing core API endpoints")
  - `addBlockedBy`: Previous phase task ID if sequential dependencies exist
- If phases can be done in parallel, do NOT add dependencies

## Updating an Existing Plan

When modifying an active spec's goals, phases, or constraints:

### Step 1: Read Active Plan Identifier
- Read `docs/specs/.active` to get the current plan directory name
- Example: `api-refactor-2026-02-16`

### Step 2: Read Current Plan State
- Read `docs/specs/<active>/overview.md`
- Read all phase files: `docs/specs/<active>/phases/phase-*.md`
- Read status.log to see what has been completed
- Query TaskList to see current task statuses

### Step 3: Present Proposed Changes
- Show the user what will change (use diff-style comparison if helpful)
- Explain impact on in-progress phases
- Get explicit approval before modifying files

### Step 4: Update Files
- Modify `overview.md` (update relevant sections)
- Add/modify/remove phase files as needed
- Update TaskList items to match
- **Never delete or modify status.log** — append-only audit trail

### Step 5: Handle In-Progress Phases
- If a phase is currently `in_progress`, coordinate with the user on how to handle it:
  - Complete the current version, then apply updates
  - Reset to `pending` and apply updates immediately
  - Split into sub-phases (current work + new requirements)

## Recovering Context After Compaction

When a SessionStart(compact) event fires, the context-recovery agent follows this workflow:

### Step 1: Read Active Plan Identifier
- Read `docs/specs/.active` to determine which plan is currently active
- Example result: `api-refactor-2026-02-16`
- If `.active` does not exist, there is no active spec — inform the user

### Step 2: Read Overview
- Read `docs/specs/<active>/overview.md`
- Extract: Goal, Architecture Decisions, Constraints, Phase Summary table, Key Files
- **Read Context section**: This captures the original request and conversation state at plan creation, essential for understanding the plan's origins

### Step 3: Read status.log from Most Recent Snapshot
- Read `docs/specs/<active>/status.log`
- Find the most recent `COMPACTION_SNAPSHOT` marker
- Parse all COMPLETED entries after that marker
- Build list of completed phases with timestamps

### Step 4: Read Current Phase File
- Identify the current phase from the Phase Summary table in overview.md
- Look for the first phase with `status: in_progress` or `status: pending`
- Read `docs/specs/<active>/phases/phase-NN.md` for that phase
- Extract: Objective, Steps, Files, Acceptance Criteria

### Step 5: Check TaskList
- Query TaskList for phase tasks
- Cross-reference with status.log entries
- Identify any discrepancies (tasks marked completed but not in status.log, or vice versa)

### Step 6: Output Structured Recovery Summary
```
# Context Recovery: [Plan Name]

**Plan:** [Plan directory name]
**Goal:** [From overview.md]

**Completed Phases:**
- Phase 01: [Title] (completed [timestamp])
- Phase 02: [Title] (completed [timestamp])

**Current Phase:** Phase 03: [Title]
**Status:** in_progress
**Objective:** [From phase file]

**Next Steps:**
1. [First uncompleted step from phase file]
2. [Second uncompleted step from phase file]

**Key Files:**
- `path/to/file` — [role]

**Architecture Decisions:**
- [Decision 1]
- [Decision 2]

**Constraints:**
- [Constraint 1]
- [Constraint 2]

**Context at Plan Creation:**
- Original request: [from Context section]
- Conversation state: [from Context section]
```

This summary is injected into the new context window, restoring orientation without requiring conversation history.

## Phase Transitions

TaskList task status transitions follow strict rules:

### pending → in_progress
- Action: `TaskUpdate` the phase task to `in_progress` status
- **When**: Before starting any work on the phase
- **Never skip this step** — it signals intent and allows hooks to prepare

### in_progress → completed
- Action: Complete all steps in the phase, then `TaskUpdate` the phase task to `completed`
- **When**: After all acceptance criteria are met
- **Hook behavior**: TaskCompleted hook automatically writes to status.log
- Format in status.log: `[timestamp] COMPLETED (task #N): Phase NN: [Title]`

### Invalid Transitions
- **Never**: pending → completed (skipping in_progress)
- **Never**: in_progress → pending (reverting without explicit reset action)
- **Never**: completed → in_progress (re-opening without user request)

## Verifying Plan Consistency

When troubleshooting or auditing a plan, check these invariants:

### Check 1: No Hanging in_progress Tasks
- Query TaskList for tasks with `status: in_progress`
- If any exist, verify:
  - Work is actually ongoing (recent activity in the files)
  - Phase file still reflects current work
  - No orphaned tasks from abandoned work

### Check 2: Cross-Reference TaskList with status.log
- For each COMPLETED entry in status.log, find the corresponding TaskList item
- For each completed TaskList item, find the corresponding status.log entry
- Mismatches indicate:
  - Hook script failure (task completed but not logged)
  - Manual status.log editing (logged but task not completed)
  - Task ID mismatch (wrong task ID in log entry)

### Check 3: Verify Phase Files Match Overview Table
- Read Phase Summary table from overview.md
- For each row, check that `phases/phase-NN.md` exists
- For each phase file in `phases/`, check that it appears in the table
- Verify status values align: table says "completed" → TaskList shows completed → status.log has COMPLETED entry

### Check 4: Validate File Path References
- Extract all file paths mentioned in phase files
- Check if paths are absolute or relative
- Verify paths make sense in the project context (no typos, no missing directories)

## Resolving Hanging Tasks

When a phase task is stuck in `in_progress` status, follow this decision tree:

### Option A: Complete Remaining Work
- If most of the phase is done, finish the remaining steps
- Update TaskList to `completed` when all acceptance criteria are met
- Hook will log completion to status.log

### Option B: Reset to Pending
- If work hasn't actually started (task marked in_progress erroneously), reset to `pending`
- Use `TaskUpdate` to change status back
- Add a note in overview.md Architecture Decisions section explaining why

### Option C: Split into Sub-Phases
- If the phase is partially complete and remaining work is substantial:
  1. Mark current phase as `completed` with scope reduced to what's done
  2. Create a new phase for remaining work (e.g., Phase 03b)
  3. Update overview.md Phase Summary table to reflect split
  4. Create new TaskList item for the new phase
- Document the split in Architecture Decisions with rationale

### Always Document Resolution
Add an Architecture Decision entry explaining what happened and why:
```markdown
- **Phase 3 split into 3a and 3b**: Initial phase scope was too large. Completed core implementation (3a) and deferred edge case handling to 3b to maintain progress. Split occurred on [date].
```

## Switching Between Named Plans

To switch from one plan to another (both already exist):

### Step 1: Identify Target Plan
- User specifies plan name or date
- Resolve to full directory name (e.g., `user-auth-flow-2026-02-15`)
- Verify the plan directory exists under `docs/specs/`

### Step 2: Update .active File
- Write the target plan directory name to `docs/specs/.active`
- Example: Write `user-auth-flow-2026-02-15` to `docs/specs/.active`
- This is a single-line file with just the directory name

### Step 3: Verify Switch
- Read the new active spec's overview.md
- Inform the user of the switch
- Summarize the new plan's goal, current phase, and status

### Important: Only One Active Plan
- The `.active` file can only contain one plan directory name
- All spec operations (status logging, recovery, updates) use the active spec
- To work on a different plan, switch using this workflow first

### Viewing Inactive Plans
- To check status of a inactive spec: `/spec:status <name>`
- This reads the plan files without switching the active spec
- Useful for reviewing historical plans or comparing alternatives

## Handling Drift Warnings

When the PostToolUse drift detection hook flags an edit as out of scope for the current phase, follow this decision workflow.

### Understanding the Warning
- The warning fires AFTER the edit is already saved — it is informational, not blocking
- It means the edited file does not appear in the current phase's "Files to Create/Modify" or "Steps" sections
- The warning lists the current phase's target files for comparison

### Option A: The Edit Was Intentional and Necessary
If the edit is genuinely needed for the current phase's work but was not anticipated during planning:
1. Acknowledge the drift in your response to the user
2. Update the current phase file: add the file to the "## Files to Create/Modify" section with a brief description of why
3. Continue working — subsequent edits to this file will no longer trigger drift warnings
4. If the scope expansion is significant, also update overview.md's Architecture Decisions section

### Option B: The Edit Was Accidental Scope Creep
If you drifted away from the current phase without realizing it:
1. Note the drift to the user
2. The edit is already saved — decide whether to keep it or revert
3. Refocus on the current phase's remaining uncompleted steps
4. If the out-of-scope work is important, note it for a future phase

### Option C: The Edit Belongs to a Different Phase
If the edited file is listed in a LATER phase's scope:
1. Acknowledge that you jumped ahead
2. Consider whether the current phase should be completed first
3. If the phase ordering matters (dependencies), finish the current phase before continuing the jumped-ahead work
4. If phases are independent, consider switching focus with a TaskUpdate

### Option D: Plan File Edits (Always In Scope)
Edits to files under docs/specs/ never trigger drift warnings — plan maintenance is always in scope regardless of which phase is active.

### When to Suppress Concern
Drift warnings are expected and harmless in these situations:
- Editing shared configuration files (package.json, tsconfig.json) that affect multiple phases
- Fixing a bug discovered while working on something else (legitimate interrupt)
- Updating documentation that spans multiple phases
In these cases, briefly acknowledge the warning and continue. Optionally update the phase file for completeness.

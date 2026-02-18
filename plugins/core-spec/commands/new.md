---
description: "Create a spec for the current project — captures requirements and acceptance criteria first, then derives implementation phases from them, creating plan files on disk and TaskList items with dependencies."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, TaskCreate, TaskUpdate, TaskList, TaskGet
---

# /spec:new

Create a spec that survives context compaction. All state is written to files under your configured spec root (default `docs/specs/`, registered per-project in `~/.claude-kit/spec-registry.json`) so it can be recovered after compaction.

The key difference from a plain plan: **requirements and acceptance criteria come first**. Phases are derived from the spec — they describe how to satisfy the requirements, not just a list of steps.

<critical_rules>

1. **NEVER write to status.log** — it is managed exclusively by hook scripts
2. **Always create overview.md first** — this is the spec gate that unlocks source file editing (PreToolUse hook checks for it)
3. **Create TaskList items for each phase** — this integrates with the TaskCompleted hook for automatic status tracking
4. **Use the templates from spec-templates.md** — the context-recovery agent expects this format
5. **Write the spec directory name to `<SPEC_ROOT>/.active` after creating the spec** — this is how all hooks and agents find the active spec

</critical_rules>

<workflow>

## Step 0: Spec root configuration

Before checking for existing specs, determine where to store spec files for this project.

```bash
# Detect project root
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Check if this project already has a registered spec root
REGISTERED=$(jq -r --arg p "$PROJECT_ROOT" \
  '.registrations[$p] // empty' \
  ~/.claude-kit/spec-registry.json 2>/dev/null)
```

**If `REGISTERED` is non-empty:**
- Use it as `SPEC_ROOT` — skip the question, tell the user: `[spec] Using registered spec root: <REGISTERED>`

**If `REGISTERED` is empty:**
- Ask the user via AskUserQuestion:

  ```
  Where should spec files be stored for this project?

  Project root: <PROJECT_ROOT>

  Options:
  - docs/specs/ (default — inside the project, version-controlled)
  - Custom path — absolute (e.g., ~/specs/my-project) or relative to project root
  ```

- Store the chosen path as `SPEC_ROOT` (strip trailing slash)
- Register it immediately:

  ```bash
  mkdir -p ~/.claude-kit
  REG=$(cat ~/.claude-kit/spec-registry.json 2>/dev/null || echo '{"registrations":{}}')
  echo "$REG" | jq --arg p "$PROJECT_ROOT" --arg s "$SPEC_ROOT" \
    '.registrations[$p] = $s' > ~/.claude-kit/spec-registry.json
  ```

Use `SPEC_ROOT` in place of `docs/specs` for **all** subsequent steps in this workflow.

## Step 1: Check for existing specs

```
Use Glob to check: <SPEC_ROOT>/*/overview.md
Check if <SPEC_ROOT>/.active exists
```

**If active spec exists:**
- Read `<SPEC_ROOT>/.active` to get the active spec directory name
- Read `<SPEC_ROOT>/<active>/overview.md` and show the user a summary
- Ask: "An active spec exists (<active>). Would you like to:"
  - **Update current spec**: Proceed to update_workflow with current spec
  - **Start fresh (new spec)**: Proceed to Step 2 to create a new spec
  - **Switch to a different existing spec**: Show list of all specs from Glob, let user choose, write choice to .active, and stop

**If .active does not exist but other specs exist:**
- Show list of existing specs from Glob
- Ask: "Would you like to activate one of these existing specs or create a new one?"
  - **Activate existing**: Write choice to .active and stop
  - **Create new**: Proceed to Step 2

**If no specs exist:**
- Proceed to Step 2

## Step 2: Spec naming

Ask the user for a spec name (or derive from their goal). The name must be 2-4 words, kebab-case (e.g., "api-refactor", "new-feature", "bug-fix-auth").

Generate the directory name as `<name>-<YYYY-MM-DD>` where YYYY-MM-DD is today's date (e.g., "api-refactor-2026-02-16").

Check uniqueness:
```
Use Glob to check: <SPEC_ROOT>/<generated-name>/
```

If the directory already exists, output an error and ask for a different name. Do not proceed until you have a unique directory name.

## Step 3: Gather the spec

If the user provided a goal as an argument to `/spec:new`, use that.

Otherwise, ask:
- "What are we building/fixing/changing?" (free text)
- "What does done look like? How will you verify it works?" (acceptance criteria, free text)
- "Any constraints or architecture decisions already made?" (free text, optional)

**IMPORTANT**: Also capture the original request from the conversation context — this will go in the ## Context section of overview.md to help with post-compaction recovery.

**Spec first, phases second**: Extract requirements from what the user describes. Requirements are the "what" — observable behaviors or properties that must be true when the work is done. Phases are the "how" — they will be derived in Step 5.

## Step 4: Analyze the codebase

Before writing the spec, understand the current state:

1. Use Glob to find key files: `**/*.{c,h,py,ts,js,rs,go,java,cpp}` (limit to first 50)
2. Read any existing README, CLAUDE.md, or project config files
3. Identify the project structure and key components

This informs both requirements (what gaps exist) and phase decomposition (what needs to change).

## Step 5: Derive phases from requirements

Based on the requirements and codebase analysis, break the work into 2-6 phases.

**Derive phases from the spec:**
- Each phase should satisfy one or more requirements
- Name which requirements each phase addresses
- Order phases so dependencies are explicit

Each phase should:
- Have a clear, one-sentence objective
- List 3-8 concrete steps
- Name specific files to create or modify
- Define acceptance criteria (how to verify THIS phase is done, traceable to spec requirements)

**Phase ordering rules:**
- If phase B depends on phase A's output, make B blocked by A
- If phases are independent, do NOT add dependencies (allows parallel work)
- First phase should always be the smallest useful increment

## Step 6: Create spec directory and files

### 6a: Create directory structure

```bash
mkdir -p <SPEC_ROOT>/<name>-<YYYY-MM-DD>/phases
```

### 6b: Create overview.md

```
Write <SPEC_ROOT>/<name>-<YYYY-MM-DD>/overview.md following the template from spec-templates.md
```

Include:
- Title
- ## Context section — right after the title. Contains:
  - **Original request:** [the user's prompt/request that triggered /spec:new — verbatim if short, summarized if long]
  - **Conversation state:** [brief summary of context at spec creation time — key files discussed, decisions made, constraints mentioned]
- ## Requirements — the observable behaviors that must be true when done (numbered list, R1, R2, ...)
- ## Acceptance Criteria — how to verify the whole spec is satisfied (high-level checklist)
- ## Goal — one-paragraph summary of what we're building
- ## Architecture Decisions (even if "none yet" — updated as decisions are made)
- ## Constraints
- ## Phase Summary table (with Satisfies column linking to requirement IDs)
- ## Key Files

### 6c: Create phase files

For each phase N, write zero-padded filenames:
```
Write <SPEC_ROOT>/<name>-<YYYY-MM-DD>/phases/phase-01.md
Write <SPEC_ROOT>/<name>-<YYYY-MM-DD>/phases/phase-02.md
... and so on, following the template from spec-templates.md
```

### 6d: Initialize status.log

Create an empty status.log (the hooks will populate it):
```bash
touch <SPEC_ROOT>/<name>-<YYYY-MM-DD>/status.log
```

### 6e: Write .active file

Write the spec directory name to <SPEC_ROOT>/.active:
```bash
echo "<name>-<YYYY-MM-DD>" > <SPEC_ROOT>/.active
```

This tells all hooks and agents where the active spec is located.

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
1. Requirements summary (R1, R2, ...)
2. Phase list with dependencies and which requirements each phase satisfies
3. Next action: "Ready to start Phase 1. Shall I begin?"

</workflow>

<update_workflow>

When updating an existing spec (user chose "Update current spec" in Step 1):

1. Read `<SPEC_ROOT>/.active` to find the active spec directory (SPEC_ROOT from Step 0)
2. Read current `<SPEC_ROOT>/<active>/overview.md` and all phase files
3. Ask what changed (new requirements, completed work, revised approach)
4. Update `<SPEC_ROOT>/<active>/overview.md` — add/update requirements, acceptance criteria, architecture decisions
5. Add, modify, or remove phase files in `<SPEC_ROOT>/<active>/phases/` as needed (maintain zero-padding: phase-01.md, phase-02.md, etc.)
6. Update TaskList items to match (create new tasks, update descriptions)
7. Do NOT delete status.log — it's an audit trail
8. Show the user the updated spec summary

</update_workflow>

<examples>

### Example: Small fix (2 phases)
```
Requirements:
  R1: Authenticated users can reset their password via email
  R2: Reset links expire after 1 hour

Phase 1: Backend — Add reset token generation, email sending, token validation endpoint
Phase 2: Frontend — Add "Forgot password" link, reset form, success/error states
```

### Example: Medium feature (4 phases)
```
Requirements:
  R1: Users can export their data as CSV
  R2: Export includes all records from the last 90 days
  R3: Large exports run async and notify via email when ready

Phase 1: Analysis — Read existing data model, identify export scope
Phase 2: Core — Implement export logic, async job queue
Phase 3: Integration — Wire into existing user settings page
Phase 4: Verification — Tests, edge cases (empty data, very large exports)
```

### Example: Large architectural change (6 phases)
```
Requirements:
  R1: API response times under 200ms at p95
  R2: Cache hit rate above 80% for repeated queries
  R3: Cache invalidation happens within 5 seconds of data change

Phase 1: Research — Profile current bottlenecks, identify hot paths
Phase 2: Architecture — Design caching strategy, choose backend (Redis)
Phase 3: Foundation — Redis client, cache key schema, invalidation helpers
Phase 4: Features — Add caching to top 5 slowest endpoints
Phase 5: Integration — Connect invalidation hooks to data mutations
Phase 6: Polish — Load tests, tune TTLs, monitor hit rates
```

</examples>

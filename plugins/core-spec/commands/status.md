---
name: core-spec:status
description: "Show current plan status — displays tier, phase progress, current step, and decisions log. Works for both Tier 1 and Tier 2 plans."
allowed-tools: Read, Glob, Grep, TaskList, TaskGet
---

# /spec:status

Display the current plan's status, progress, and next steps.

<workflow>

## Step 1: Find the active plan

Check TaskList for an item with subject "PLAN-ACTIVE".

**If not found:**
Output: "No active plan. Use `/spec:new` to create one."
Stop.

**If found:**
Extract from the description:
- `path`: the plan directory path
- `tier`: 1 or 2
- `phase`: current phase number
- `mode`: detected mode (autonomous/pair/assistant)

## Step 2: Read plan files

### For Tier 1:

Read `<path>/plan.md`. Extract:
- Goal
- Steps with completion status
- Decisions

### For Tier 2:

Read `<path>/status.md`. Extract:
- Current phase and total phases
- Phase progress list
- Current phase context
- Decisions log

Also read `<path>/overview.md` for:
- Requirements
- Architecture decisions

Also check for:
- `<path>/environment.md` — note if it exists, is complete, or has TODO markers
- `<path>/test-plan.md` — note if it exists, is complete, or has TODO markers

Optionally read the current phase file for detailed step status.

## Step 3: Check TaskList

Read TaskList to find:
- Phase tasks (subjects starting with "Phase")
- Their statuses (pending, in_progress, completed)
- Any blocked tasks

## Step 4: Present status

Format the output as:

```
## Plan Status: <plan-id>

**Tier:** <1|2>
**Goal:** <one-line goal>
**Mode:** <autonomous|pair|assistant>

### Progress
<phase/step progress with checkmarks>

### Current Focus
<what is being worked on right now>

### Next Steps
<what comes after current work>

### Decisions
<key decisions made so far>

### Plan Files
<path to plan directory>
```

For Tier 2, also show:
- Requirements satisfaction (which R's are done)
- Phase dependencies

### Environment & Test Readiness
- Environment setup: <complete / has TODOs / missing>
- Test plan: <complete / has TODOs / missing>

</workflow>

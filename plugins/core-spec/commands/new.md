---
name: core-spec:new
description: "Create a plan or specification for the current task — assesses complexity, asks plan vs specification, generates the right tier of plan files, and creates a PLAN-ACTIVE TaskList anchor."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet
---

# /spec:new

Create a plan that survives context compaction. All state is written to files
under `~/.claude-kit/plans/` so it can be recovered after compaction.

<critical>

1. ALWAYS create the PLAN-ACTIVE TaskList item after writing plan files
2. ONLY one PLAN-ACTIVE item may exist at a time — check TaskList first
3. NEVER create a plan without gathering requirements from the user
4. For Tier 2, use team agents (writer + reviewer) to produce phase files

</critical>

<workflow>

## Step 1: Check for existing plans

```
Check TaskList for an item with subject "PLAN-ACTIVE"
```

**If PLAN-ACTIVE exists:**
- Read the plan path from the task description
- Read status.md or plan.md to show current state
- Ask the user:
  - **Continue current plan**: Resume where status.md indicates
  - **Abandon and start fresh**: Mark old PLAN-ACTIVE as completed, proceed to Step 2
  - **View status only**: Show current state and stop

**If no PLAN-ACTIVE exists:**
- Proceed to Step 1.5

## Step 1.5: Detect mode

Detect the active behavioral profile to adapt plan generation:

1. Read `~/.claude/rules/claude-kit.md` and find the Section 4 heading:
   `## 4. Behavioral Profile (ProfileName)` → extract and lowercase ProfileName
2. If not found: read `~/.claude-kit/manifest.json` → extract `profile` key
3. If neither available: default to `pair`

For custom profiles, scan the behavioral rules for marker phrases:
- "Do not use AskUserQuestion" → `autonomous`
- "Ask before architectural decisions" → `pair`
- "ALWAYS present your plan" → `assistant`

Store the detected mode for use in subsequent steps.

## Step 2: Assess complexity and ask the user

Ask the user via AskUserQuestion:

**Question 1:** "What type of planning do you need?"
- **Plan** — "I know what to build. Give me structured steps." → Tier 1
- **Specification** — "Let's define requirements first, then derive phases." → Tier 2

If the user already described their task in conversation, use that context.
If not, ask: "What are we building/fixing/changing?"

## Step 3: Gather requirements

Questions adapt to the detected mode.

### Autonomous Mode (7 questions, all required)

1. "What are we building/fixing/changing?" (free text)
2. "What does done look like? Express as commands + expected outputs." (acceptance)
3. "What tools/frameworks/languages are involved?" (environment)
4. "Are there API keys, secrets, or credentials needed?" (secrets)
5. "What test framework is in use or should be used?" (testing)
6. "Is there a CI pipeline? If so, what must pass?" (CI)
7. "Any constraints or architecture decisions already made?" (constraints)

### Pair Mode (5 questions)

1. "What are we building/fixing/changing?" (free text)
2. "What does done look like? How will you verify it works?" (acceptance)
3. "What's the development environment? (language, framework, key tools)" (environment brief)
4. "Any test boundaries — what must be tested vs. what's out of scope?" (test boundaries)
5. "Any constraints or architecture decisions already made?" (optional)

### Assistant Mode (3 questions)

1. "What are we building/fixing/changing?" (free text)
2. "What does done look like?" (acceptance)
3. "Any constraints or decisions already made?" (optional)

If the user provided a goal as an argument to `/spec:new`, use that and skip
redundant questions. Capture the original request from conversation context.

## Step 4: Analyze the codebase

Before writing the plan, understand the current state:

1. Use Glob to find key files: `**/*.{py,ts,js,rs,go,java,c,h,cpp}` (limit to first 50)
2. Read any existing README, CLAUDE.md, or project config files
3. Identify the project structure and key components

This informs both the plan content and file path specifics.

## Step 5: Generate plan name

Generate a plan ID: `<name>-<YYYY-MM-DD>` where:
- name: 2-4 words, kebab-case, derived from the goal
- date: today's date

Check uniqueness:
```bash
ls ~/.claude-kit/plans/ 2>/dev/null | grep "<generated-name>"
```

If exists, append a suffix (-2, -3, etc.).

## Step 6: Create plan files

### For Tier 1:

```bash
mkdir -p ~/.claude-kit/plans/<plan-id>
```

Write `~/.claude-kit/plans/<plan-id>/plan.md` following the Tier 1 template
from the identity skill.

Steps should be specific enough for a post-compaction Claude to execute
without conversation history. Include file paths, what changes, and patterns
to follow.

### For Tier 2:

```bash
mkdir -p ~/.claude-kit/plans/<plan-id>/phases
```

**Use team agents for plan generation:**

1. Gather all context: requirements, codebase analysis, constraints
2. Spawn a spec-writer agent:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: "[Include: requirements, codebase context, all templates from identity skill, explicit instruction to write overview.md + status.md + phase files]"
)
```

   → Receives: requirements + codebase context + templates + detected mode + mode-specific acceptance criteria rules

The writer produces all spec files. Pass the FULL templates from the identity
skill in the prompt — the agent does not have access to skills.

3. Spawn a spec-reviewer agent:

```
Task(
  subagent_type: "general-purpose",
  model: "opus",
  prompt: "[Include: all written spec files, review rubric from identity skill]"
)
```

   → Receives: all written spec files + review rubric + mode compliance rules

The reviewer checks each phase file against the rubric. If issues are found,
re-spawn the writer with revision instructions (1 round maximum).

4. Write the final spec files to `~/.claude-kit/plans/<plan-id>/`.

5. For Tier 2, also generate:
   - `environment.md` — from the environment template in the identity skill,
     populated with answers from Step 3 (tools, secrets, environment)
   - `test-plan.md` — from the test plan template in the identity skill,
     populated with answers from Step 3 (test framework, CI, coverage)

   Mode adaptation:
   - **Autonomous**: environment.md must have no gaps. test-plan.md must have
     only automated verification. All commands must be copy-paste-executable.
   - **Pair**: Brief environment notes acceptable. Test plan can include
     up to 2 `[HUMAN-REVIEW]` items per phase.
   - **Assistant**: Both documents serve as discussion guides. Gaps are
     acceptable — they'll be filled interactively.

**If team agents are not practical** (e.g., simple Tier 2 plan with 2-3 phases),
write the files directly. Team agents are for complex specifications with 4+
phases.

## Step 7: Create PLAN-ACTIVE TaskList anchor

```
TaskCreate:
  subject: "PLAN-ACTIVE"
  description: "path: ~/.claude-kit/plans/<plan-id> | tier: <1|2> | phase: 1 | mode: <detected>"
  activeForm: "Following plan: <plan-id>"
```

## Step 8: Create phase tasks (Tier 2 only)

For each phase, create a TaskList item:

```
TaskCreate:
  subject: "Phase NN: [title]"
  description: "[objective + key steps summary]"
  activeForm: "[present continuous: 'Implementing API endpoints']"
```

Set up dependencies:
```
TaskUpdate:
  taskId: [phase 2 ID]
  addBlockedBy: [phase 1 ID]  (only if sequential)
```

## Step 9: Present to user

Show:
1. Plan type (Tier 1 or Tier 2)
2. For Tier 1: Goal + steps summary
3. For Tier 2: Requirements summary + phase list with dependencies
4. Plan file location
5. "Ready to start. Shall I begin?"

</workflow>

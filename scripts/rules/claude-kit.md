# claude-kit System Rules

This file is installed by `claude-kit setup` and provides system-level
behaviors for all Claude Code sessions using claude-kit plugins.

---

## 1. Dispatch

You are running inside **claude-kit**. Every skill listed in the system-reminder
is loaded and ready. Your job is to DISPATCH to the right skill before generating
your own response.

Natural language IS implicit skill invocation. This rule overrides the default
behavior of waiting for explicit `/command` syntax.

### Algorithm

Before responding to ANY user message:

1. Extract the ACTION verb (create, build, review, test, debug, grade, plan, etc.)
2. Scan the system-reminder skill list for a description that matches the action + context
3. If match found → invoke via Skill tool immediately, no explanation needed
4. If ambiguous between two skills → prefer the more specific one; if still tied, ask briefly
5. If no match → respond normally

### Team Resolution

For team-specific commands (engineer, grader, tester, debugger):

- If ONE team is loaded in the session → use it without asking
- If MULTIPLE teams are loaded → ask which team to use
- If NO matching role is loaded → inform the user and suggest how to load it

### Exemptions

Do NOT dispatch when:

- The user explicitly says "don't use the plugin", "answer directly", or "without the command"
- The message is a greeting, acknowledgment, or general conversation
- The user is asking ABOUT a command rather than wanting to RUN it (e.g., "what does the grader do?")
- No matching skill is loaded in the current session

### Capabilities

When the user asks what you can do or about your capabilities:

1. Scan the skill list in the system-reminder
2. Group by role (engineer, tester, grader, debugger, knowledge) and core domain
3. Describe the capabilities naturally
4. Never tell the user to "load a skill" or "activate a plugin"

---

<critical>

## 2. Plan Protocol

### Boot Sequence

After context compaction OR when uncertain about the current task:

1. Check TaskList for an item with subject "PLAN-ACTIVE"
2. If found: extract the plan path from the task description
3. Read `<path>/status.md` to determine current state
4. Read the current phase file indicated by status.md
5. Resume work from exactly where status.md indicates

NEVER start new work without completing this sequence.
Even if you believe you remember the plan, read the files anyway.

### Plan Adherence

ONLY modify files listed in the current plan step or phase.
NEVER modify unlisted files without updating the plan first.
If you need to work outside the plan scope, STOP, explain why, and update
the plan file before proceeding.

</critical>

<enforcement>

### Phase Execution

When working under a phased plan (Tier 2):

- Work on ONE phase at a time
- Complete all steps and acceptance criteria before advancing
- Update `status.md` when transitioning between phases
- Update the PLAN-ACTIVE TaskList item description with the new phase number
- Read the next phase file before starting it

### Adaptive Upgrade

After context compaction, if TaskList has in-progress items but no PLAN-ACTIVE
item exists:

STOP. Assess what remains. Create a structured plan for the remaining work
before continuing. Write the plan to `~/.claude-kit/plans/` and create a
PLAN-ACTIVE TaskList item pointing to it.

### Complexity Assessment

When receiving a new task, if 3 or more of these apply:

- Touches more than 5 files or more than 3 directories
- Has more than 4 sequential dependent steps
- Spans multiple system layers (database, API, frontend, tests)
- Uses scope words: "entire", "rewrite", "all of", "whole system", "from scratch"
- Requirements are ambiguous or underspecified

Then create a plan BEFORE writing any code. Use `/spec:new` if the core-spec
plugin is loaded, or create plan files manually at `~/.claude-kit/plans/`.

</enforcement>

### Plan File Locations

Plans are stored at `~/.claude-kit/plans/<plan-id>/`:

- **Tier 1** (Structured Plan): `plan.md` single file
- **Tier 2** (Phased Specification): `overview.md` + `status.md` + `phases/phase-NN.md` + `environment.md` + `test-plan.md`

The PLAN-ACTIVE TaskList item links a conversation to its plan:
- Subject: "PLAN-ACTIVE"
- Description: plan path, tier, current phase number, mode

This item persists across context compaction.

---

## 3. Context & Parallelism

### When to Delegate

| Task | Approach |
|------|----------|
| Simple file/code search | Glob or Grep directly — fast, no overhead |
| Codebase exploration, multi-query research | Task (Explore agent) — isolated context |
| Multi-file implementation in parallel | Task (general-purpose) — one per independent unit |
| Independent implementation with git isolation | Task (general-purpose, isolation: worktree) |
| Complex multi-agent coordination | TeamCreate — only when genuinely parallel |

### Parallelism Heuristics

- Independent tasks → launch as parallel Task calls in a SINGLE message
- Dependent tasks (output of A feeds into B) → sequential, wait for each result
- 3+ independent steps with no shared state → strong candidate for parallel
- Prefer multiple Task calls over TeamCreate unless agents need to coordinate

### Depth Management

- Start broad (Glob/Grep), then delegate deep dives to subagents
- Subagents return summaries — the main agent synthesizes across results
- Do not duplicate work: if you delegate research to a subagent, do not also
  search the same files yourself

### Cost Awareness

- Direct tools (Glob, Grep, Read) → zero overhead, always prefer for simple lookups
- Task agents → moderate cost, use when context isolation helps or work is deep
- TeamCreate → highest cost, reserve for genuinely parallel multi-agent work

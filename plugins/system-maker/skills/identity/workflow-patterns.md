# Workflow Patterns for Plugin Creation

This document provides step-by-step workflow patterns for the 11-phase plugin creation process, including parallel subagent dispatch patterns and error recovery strategies.

## Overview of the 11-Phase Process

The plugin creation workflow follows a structured pipeline:

```
Phase 1-2: Discovery → Phase 3: Analysis → Phase 4: Questionnaire →
Phase 5-7: Design → Phase 8: Implementation → Phase 9: Assembly →
Phase 10: Review → Phase 11: Finalization
```

Key characteristics:
- **3 parallel phases**: Domain Analysis (Phase 3), Architecture Design (Phase 5 - optional), Implementation (Phase 8)
- **2 conditional phases**: Architecture Review (Phase 6 - only for "Compare all" strategy)
- **1 iterative phase**: Deep Review (Phase 10 - automated fix and re-review loop)
- **Total runtime**: 3-7 minutes depending on strategy choice and review findings

## Phase 1-2: Discovery and Name Derivation

### Pattern: Validate Before Creating

**Steps:**

1. **Capture user description**
   ```
   AskUserQuestion: "Describe the coding domain for your new agent..."
   Store response as AGENT_DESCRIPTION
   ```

2. **Derive plugin name**
   ```
   Identify the broad domain (embedded, cloud, frontend, backend, mobile, ml, devops)
   Identify the specific tech/framework (zephyr, linux, golang, react, pytorch, etc.)
   Determine the role (engineer, grader, tester, debugger, deployer, migrator)
   Format as: <type>-<domain>-<tech>-<role>
   Validate against regex: ^[a-z]+-[a-z][-a-z]*$
   ```

3. **Offer generalization**
   ```
   AskUserQuestion: "Should this be a generalized agent?"
   If generalize: rederive name, note EXTENSION_SKILLS
   ```

4. **Check for existing plugins**
   ```bash
   # CRITICAL: Check INSTALLED plugins, not /tmp build dir
   ls -1 ~/personal/agent-config/plugins/ 2>/dev/null
   ```

   Compare against proposed name and domain.

   If exact match found:
   ```
   AskUserQuestion: "Plugin exists. Enhance (system-updater) or Overwrite?"
   ```

   If domain overlap found:
   ```
   AskUserQuestion: "Similar plugin exists. Extend or Create separate?"
   ```

5. **Create staging directory**
   ```bash
   mkdir -p /tmp/agent-config-build-<AGENT_NAME>
   ```

**Error Cases:**
- Name doesn't match regex → reformat and explain
- Build dir already exists → ask to overwrite or choose different name
- User wants to enhance existing → exit and direct to system-updater

## Phase 3: Domain Analysis (PARALLEL)

### Pattern: Parallel Subagent Dispatch

**Steps:**

1. **Launch 4 subagents in a SINGLE response**

   Make 4 Task tool calls simultaneously:

   ```
   Task(subagent_type: "domain-analyzer", prompt: "FOCUS_AREA: technical...")
   Task(subagent_type: "domain-analyzer", prompt: "FOCUS_AREA: workflow...")
   Task(subagent_type: "domain-analyzer", prompt: "FOCUS_AREA: tools...")
   Task(subagent_type: "domain-analyzer", prompt: "FOCUS_AREA: patterns...")
   ```

2. **Wait for all 4 to return**

   Do NOT issue follow-up prompts between Task calls.
   All 4 run concurrently.

3. **Check for failures**

   If any Task returns error or malformed output:
   ```
   AskUserQuestion: "Subagent failed. Retry | Skip | Abort?"
   ```

   On Retry: Re-issue ONLY the failed Task call.

4. **Synthesize results**

   Combine 4 outputs into unified DOMAIN_MAP:
   - Technical stack summary
   - Key workflow stages
   - Required/recommended tools
   - Design patterns and architecture principles
   - MCP opportunities

**Timing:**
- Serial execution: 90-270 seconds (30-90s per subagent)
- Parallel execution: 30-90 seconds (max of 3 concurrent runs)

**Error Recovery:**
- One fails → retry just that one
- Two fail → retry both in parallel
- All fail → likely systemic issue, abort and investigate

## Phase 4: Questionnaire

### Pattern: Sequential User Interaction

**Steps:**

1. **Launch questionnaire builder**
   ```
   Task(subagent_type: "questionnaire-builder", prompt: "...")
   ```

2. **Receive questionnaire JSON**

   Parse array of questions with:
   - `text`: Question to ask
   - `options`: Available choices (if any)
   - `default`: Default value if user skips

3. **Present questions sequentially**

   For each question:
   ```
   AskUserQuestion:
     "Question N of M (<category>):
      <text>
      Options: [...]
      Default if skipped: <default>"
   ```

   Store answer or default.

4. **Verify answers**

   Present summary:
   ```
   "You answered:
    Q1: <answer1>
    Q2: <answer2>
    ...

    Change any answers? (Yes/No)"
   ```

**No Parallelism:**
This phase is inherently sequential — user must answer questions one at a time.

## Phase 5-7: Architecture Design and Approval

### Pattern: Strategy-Based Branching

**Step 1: Strategy Selection**

```
AskUserQuestion: "How thorough should architecture design be?"

Options:
1. Comprehensive — 1 architect, full-featured (60-90s)
2. Progressive — 1 architect, grow-as-you-go (45-60s)
3. Minimal — 1 architect, simplest viable (30-45s)
4. Compare all — 3 architects + 1 reviewer (2-3 min)
```

**Step 2a: Single Architect (Comprehensive/Progressive/Minimal)**

Launch 1 subagent:
```
Task(subagent_type: "arch-designer", prompt: "STRATEGY: <chosen>...")
```

Wait for result.

Store as UNIFIED_ARCH.

**SKIP Phase 6** — go directly to Phase 7 (User Approval).

**Step 2b: Compare All (3 Architects + Reviewer)**

Launch 3 subagents in PARALLEL:
```
Task(subagent_type: "arch-designer", prompt: "STRATEGY: minimal...")
Task(subagent_type: "arch-designer", prompt: "STRATEGY: comprehensive...")
Task(subagent_type: "arch-designer", prompt: "STRATEGY: progressive...")
```

Wait for all 3.

**Proceed to Phase 6** (Architecture Review).

**Step 3: Architecture Review (Phase 6 — only for "Compare all")**

Launch 1 reviewer:
```
Task(subagent_type: "arch-reviewer", prompt: "PROPOSAL_MINIMAL: <...>
                                              PROPOSAL_COMPREHENSIVE: <...>
                                              PROPOSAL_PROGRESSIVE: <...>")
```

Reviewer produces unified recommendation.

Store as UNIFIED_ARCH.

**Step 4: User Approval (Phase 7)**

Present architecture with:
- Directory tree
- Component summary table
- Consensus points
- Warnings/TODOs

```
AskUserQuestion: "Approve | Request changes | Re-generate?"
```

If "Request changes": modify UNIFIED_ARCH directly, re-present.
If "Re-generate": loop back to Phase 5 with feedback.
If "Approve": store as APPROVED_ARCH, proceed to Phase 8.

## Phase 8: Implementation (PARALLEL)

### Pattern: Parallel File Writers

**Steps:**

1. **Create directory skeleton**
   ```bash
   mkdir -p /tmp/agent-config-build-<name>/agents
   mkdir -p /tmp/agent-config-build-<name>/commands
   mkdir -p /tmp/agent-config-build-<name>/scripts
   mkdir -p /tmp/agent-config-build-<name>/skills/identity
   mkdir -p /tmp/agent-config-build-<name>/.claude-plugin
   # Plus directories for each skill in architecture
   ```

2. **Launch 4 subagents in a SINGLE response**

   ```
   Task(subagent_type: "identity-writer", prompt: "...")
   Task(subagent_type: "skill-writer", prompt: "...")
   Task(subagent_type: "agent-writer", prompt: "...")
   Task(subagent_type: "hook-writer", prompt: "...")
   ```

3. **Wait for all 4 to return**

4. **Handle failures**

   If any writer fails:
   ```
   AskUserQuestion: "Writer failed. Retry | Skip | Abort?"
   ```

   On Retry: Re-launch ONLY the failed writer.
   Do NOT re-run successful writers.

5. **Verify output**

   After all succeed, report:
   ```
   "Phase 8 complete. Implementation produced:
    - skills/identity/ (3 files)
    - N skill files
    - N command files
    - N agent definitions
    - hooks.json"
   ```

**Timing:**
- Serial: 240-720 seconds (60-180s per writer)
- Parallel: 60-180 seconds (max of 4 concurrent runs)

**Critical Context for All Writers:**

Include in every writer prompt:
- `BUILD_DIR: /tmp/agent-config-build-<name>`
- `APPROVED_ARCH: <full architecture JSON>`
- Reminder: agent files use `tools:`, command files use `allowed-tools:`
- Reminder: hooks.json uses event-based format
- Reminder: every agent must include `identity` in skills list
- Reminder: no CLAUDE.md files in plugins

## Phase 9: Assembly

### Pattern: Orchestrator-Generated Config Files

The orchestrator (make-agent command) generates these files directly — no subagent needed.

**Steps:**

1. **Verify file tree**
   ```bash
   find /tmp/agent-config-build-<name> -type f | sort
   ```

2. **Generate plugin.json**

   ```json
   {
     "name": "<AGENT_NAME>",
     "description": "<one-line from AGENT_DESCRIPTION>",
     "version": "1.0.0"
   }
   ```

   Write to: `BUILD_DIR/.claude-plugin/plugin.json`

3. **Generate .lsp.json (if applicable)**

   Check APPROVED_ARCH technical stack for typed languages.

   If C/C++:
   ```json
   {
     "lsp": {
       "c": {
         "command": "clangd",
         "args": ["--background-index", "--compile-commands-dir=build"]
       }
     }
   }
   ```

   If Go:
   ```json
   {
     "lsp": {
       "go": {
         "command": "gopls",
         "args": ["serve"]
       }
     }
   }
   ```

   Write to: `BUILD_DIR/.lsp.json`

4. **Generate .mcp.json (if applicable)**

   ONLY if APPROVED_ARCH specifies MCP servers that EXIST.

   If MCP servers are "needed but not built", do NOT create file.
   Note as TODO in final summary.

5. **Validate file existence**

   Compare file tree against APPROVED_ARCH component manifest.

   Report any missing files:
   ```
   "Expected but missing:
    - scripts/validate.sh
    - skills/domain-api/reference.md"
   ```

## Phase 10: Deep Review and Fix (ITERATIVE)

### Pattern: Review → Fix → Re-Review (Max 2 Passes)

**Pass 1: Initial Review**

1. **Launch reviewer**
   ```
   Task(subagent_type: "plugin-reviewer", prompt: "BUILD_DIR: ...
                                                    APPROVED_ARCH: ...")
   ```

2. **Parse review report**

   Extract:
   - `overall_grade`: A/B/C/D/F
   - `findings`: Array of issues with severity, file, fix instructions
   - `passed_checks`: Count of successful checks

3. **Present summary**
   ```
   "=== QUALITY REVIEW ===
    Grade: B
    Checks: 48/52 passed
    Critical: 2 | Warnings: 2 | Suggestions: 5"
   ```

4. **If grade is A and zero critical/warning findings**: Skip to Phase 11.

5. **If findings exist**: Proceed to automated fixes.

**Fix Application:**

Group findings by `fix_type`:

**a. Structural fixes** (`fix_type: "structural"`):
```bash
# Missing file
touch /tmp/agent-config-build-<name>/scripts/validate.sh
chmod +x /tmp/agent-config-build-<name>/scripts/validate.sh
echo '#!/bin/bash\n# TODO: Implement validation\nexit 0' > ...

# Missing directory
mkdir -p /tmp/agent-config-build-<name>/skills/missing-skill
```

**b. Mechanical fixes** (`fix_type: "mechanical"`):
```
For each finding:
  Read file
  Apply Edit (surgical change)
  Note fix applied
```

Examples:
- Add missing frontmatter field
- Fix field name (allowed-tools → tools)
- Add identity to skills list
- Fix JSON syntax

**c. Content fixes** (`fix_type: "content"`):
```
Match finding category to writer:
  - Identity issues → re-spawn identity-writer
  - Skill issues → re-spawn skill-writer
  - Agent issues → re-spawn agent-writer
  - Hook issues → re-spawn hook-writer

Launch in PARALLEL if targeting different files.

Prompt format:
  "The <component> at <path> needs improvement.
   ISSUE: <finding.issue>
   FIX: <finding.fix>
   Read existing files, surgically fix the problem."
```

**Pass 2: Re-Review**

After fixes:

1. **Re-launch reviewer** (same parameters)

2. **Present updated summary**
   ```
   "=== RE-REVIEW ===
    Previous: B → New: A
    Fixed: 4 issues resolved
    Remaining: 0"
   ```

3. **If issues remain**:
   ```
   AskUserQuestion: "Remaining issues:
                     <list>

                     Accept as-is | Fix manually | Re-run review?"
   ```

**Max 2 Total Reviews:**
- 1 initial + 1 re-review = 2 passes maximum
- Prevents infinite loops
- If issues persist after 2 passes, user decides

## Phase 11: Finalization

### Pattern: Staged Copy with Verification

**Steps:**

1. **Present final summary**
   ```
   "=== BUILD COMPLETE ===
    Files: <count>
    Grade: <final grade>
    Build dir: /tmp/agent-config-build-<name>
    Target: ~/personal/agent-config/plugins/<name>/"
   ```

2. **Request approval**
   ```
   AskUserQuestion: "Finalize | Review files | Abort?"
   ```

3. **If "Review files"**: Let user inspect specific files, then re-ask.

4. **If "Finalize"**:

   Check target directory:
   ```bash
   ls -d ~/personal/agent-config/plugins/<name> 2>/dev/null
   ```

   If exists:
   ```
   AskUserQuestion: "Target exists. Overwrite | Abort?"
   ```

5. **Copy to plugins directory**
   ```bash
   # If overwriting
   rm -rf ~/personal/agent-config/plugins/<name>

   # Copy build
   cp -r /tmp/agent-config-build-<name> ~/personal/agent-config/plugins/<name>
   ```

6. **Verify copy**
   ```bash
   diff <(cd /tmp/agent-config-build-<name> && find . -type f | sort) \
        <(cd ~/personal/agent-config/plugins/<name> && find . -type f | sort)
   ```

7. **Confirm success**
   ```
   "Plugin <name> installed successfully.

    Launch: ./ctl.sh run <name>
    List: ./ctl.sh list"
   ```

**Error Recovery:**
- Copy fails → preserve build dir, report error, ask user to investigate
- Verification diff shows mismatch → report discrepancy, ask to retry or abort

## Error Recovery Strategies

### Subagent Failure

**Symptoms:**
- Task tool returns error
- Subagent output is empty or malformed JSON

**Recovery:**

1. **Capture error message**

2. **Present options**
   ```
   AskUserQuestion: "Subagent <name> failed in Phase <N>.
                     Error: <message>

                     Retry | Skip | Abort?"
   ```

3. **On Retry**:
   - For parallel phases: Re-launch ONLY failed subagent
   - For sequential phases: Re-launch the single subagent
   - Do NOT re-run successful subagents

4. **On Skip**:
   - Note the gap in subsequent phases
   - Warn about quality impact
   - Example: "Domain map will be incomplete (missing tool ecosystem analysis)"

5. **On Abort**:
   - Stop workflow
   - Report partial build location: `/tmp/agent-config-build-<name>`

### Malformed Output

**Symptoms:**
- Subagent returns text instead of expected JSON
- JSON is syntactically valid but missing required fields

**Recovery:**

1. **Attempt JSON extraction**
   - Check for markdown code blocks
   - Try parsing substring as JSON

2. **If extraction fails**: Treat as subagent failure (see above)

3. **If extraction succeeds but fields missing**:
   - Log warning
   - Use default values for missing fields
   - Proceed if non-critical
   - Fail if critical fields missing

### Build Directory Conflicts

**Handled in Phase 2:**

```bash
ls -d /tmp/agent-config-build-<name> && echo "EXISTS" || echo "CLEAR"
```

If EXISTS:
```
AskUserQuestion: "Build dir exists. Overwrite | Choose different name | Abort?"
```

### Target Directory Conflicts

**Handled in Phase 11:**

```bash
ls -d ~/personal/agent-config/plugins/<name> && echo "EXISTS" || echo "CLEAR"
```

If EXISTS:
```
AskUserQuestion: "Target exists. Overwrite | Abort?"
```

## Parallel Execution Best Practices

### When to Parallelize

**Always parallelize:**
- Phase 3: Domain analysis (4 subagents, independent domains)
- Phase 8: Implementation (4 subagents, different file types)
- Phase 5: Architecture design if "Compare all" (3 subagents, different strategies)

**Never parallelize:**
- Phase 4: Questionnaire (sequential user interaction)
- Phase 6: Architecture review (depends on Phase 5 outputs)
- Phase 10: Review pass 2 (depends on fixes from pass 1)

### How to Parallelize

Issue multiple Task calls in a SINGLE response message:

```
I'm launching 4 domain analyzers in parallel.

Task(subagent_type: "domain-analyzer", prompt: "FOCUS: technical...")
Task(subagent_type: "domain-analyzer", prompt: "FOCUS: workflow...")
Task(subagent_type: "domain-analyzer", prompt: "FOCUS: tools...")
Task(subagent_type: "domain-analyzer", prompt: "FOCUS: patterns...")

Waiting for all 4 to complete...
```

Do NOT issue follow-up messages between Task calls.

### Error Handling in Parallel Phases

If 1 of 3 fails:
- Re-launch only that 1
- Keep results from the 2 that succeeded

If 2 of 3 fail:
- Re-launch both in parallel
- Keep result from the 1 that succeeded

If all fail:
- Likely systemic issue (API outage, malformed prompt template)
- Abort and investigate root cause

## Timing Benchmarks

| Phase | Serial Time | Parallel Time | Speedup |
|-------|-------------|---------------|---------|
| 3: Domain Analysis | 90-270s | 30-90s | 3x |
| 5: Arch Design (Compare all) | 180-270s | 60-90s | 3x |
| 8: Implementation | 240-720s | 60-180s | 4x |

**Total workflow time:**
- Minimal strategy: 3-4 minutes
- Progressive strategy: 4-5 minutes
- Comprehensive strategy: 5-6 minutes
- Compare all strategy: 6-7 minutes

With parallelization vs without:
- Without: 12-20 minutes
- With: 3-7 minutes
- **Overall speedup: 3-4x**

## Summary Decision Tree

### Phase 1-2: Should I proceed?
- [ ] Name matches regex?
- [ ] Generalization considered?
- [ ] No conflicting existing plugin (or user confirmed overwrite)?
- [ ] Build directory created?

→ Yes to all: Proceed to Phase 3

### Phase 3-4: Do I have enough information?
- [ ] Domain map complete (or acceptable with gaps)?
- [ ] User answered questionnaire (or used defaults)?

→ Yes: Proceed to Phase 5

### Phase 5-7: Is architecture approved?
- [ ] User chose strategy?
- [ ] Architecture generated?
- [ ] User approved architecture (or requested changes applied)?

→ Yes: Proceed to Phase 8

### Phase 8-9: Are files written?
- [ ] All 4 writers succeeded (or failures recovered)?
- [ ] plugin.json generated?
- [ ] .lsp.json generated (if applicable)?
- [ ] File tree matches architecture?

→ Yes: Proceed to Phase 10

### Phase 10: Quality gate passed?
- [ ] Review grade is A or B?
- [ ] Critical findings fixed?
- [ ] Warnings fixed or accepted?

→ Yes: Proceed to Phase 11

### Phase 11: Ready to install?
- [ ] User approved finalization?
- [ ] Target directory conflict resolved (if any)?
- [ ] Copy succeeded?
- [ ] Verification passed?

→ Yes: Success! Plugin installed.

## Knowledge-First Workflow Pattern

### Phase 2.5: Knowledge Plugin Existence Check

This pattern ensures domain knowledge is centralized before role-specific plugins are created.

**Trigger**: Creating a coding-type plugin where the role is NOT `knowledge`.

**Flow**:
1. Derive knowledge plugin name: replace role segment with `knowledge`
   - `coding-embedded-zephyr-engineer` → `coding-embedded-zephyr-knowledge`
2. Check if knowledge plugin exists in `~/personal/agent-config/plugins/`
3. If exists: set KNOWLEDGE_MODE=true, catalog its skills
4. If missing: offer to create it first via abbreviated workflow

**Abbreviated Knowledge Creation**:
- Reuse domain analysis from parent workflow
- 3 parallel writers (identity, skill, hook) — skip agent-writer
- Knowledge identity is minimal (~40 lines, domain overview)
- Safety hooks only (block-dangerous-commands, check-environment)
- No agents, no commands

**Impact on Subsequent Phases**:
- Phase 5 (Architecture): Designers exclude knowledge skills, add companions field
- Phase 8 (Implementation): Skill-writer skips knowledge skills, identity-writer writes role-only identity
- Phase 9 (Assembly): plugin.json includes companions array and role field

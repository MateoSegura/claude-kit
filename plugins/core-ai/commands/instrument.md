---
name: core-ai:instrument
description: "Analyze a repository and generate tailored .claude/ rules, commands, and hooks that encode its conventions into enforceable context. Walks through a 4-phase process: detect, confirm, generate, manifest."
allowed-tools: Task, AskUserQuestion, Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList
---

# /core-ai:instrument

Instrument a repository for AI-assisted development. Analyzes the codebase, confirms findings with the user, and generates `.claude/` configuration files.

<critical_rules>

1. **NEVER overwrite user-authored files without explicit approval.** If a `.claude/rules/*.md` or `.claude/commands/*.md` file exists without a core-ai provenance header, treat it as user-authored. You may propose enrichments but must get explicit user confirmation before modifying.
2. **ALWAYS show what will be generated before writing.** Present the file list and summaries. Get user confirmation.
3. **ALWAYS create/update the manifest.** `.claude/.instrumentation.json` tracks everything for idempotent re-runs.
4. **NEVER modify source code.** Output domain is strictly `.claude/`.
5. **Respect enforcement preferences.** Hooks only when explicitly requested.
6. **Commands are first-class outputs.** Always audit existing commands against detection findings and ask the user about command coverage — do not silently skip commands.

</critical_rules>

<workflow>

## Step 1: Determine Instrumentation Mode

Check the current state to determine which mode we're in:

```
Glob: .claude/.instrumentation.json
Glob: .claude/rules/*.md
Glob: .claude/commands/*.md
Glob: .claude/hooks.json
```

**If `.claude/.instrumentation.json` exists:**
- Mode = `reinstrument`
- Read the manifest to understand what was previously generated
- Tell the user: "This repo was previously instrumented on <date>. I'll check for drift and suggest updates."

**If `.claude/rules/` or `.claude/commands/` exist but no manifest:**
- Mode = `partial`
- Tell the user: "I found existing .claude/ configuration. I'll analyze coverage gaps and offer to fill them without modifying your existing files."

**If nothing exists:**
- Mode = `greenfield`
- Tell the user: "No existing AI configuration found. I'll do a full analysis and generate a complete .claude/ setup."

## Step 2: Detect (Phase 1)

Spawn the repo-analyzer agent to scan the repository:

```
[kit:agent] spawning repo-analyzer
            skills: identity, instrumentation
            tools: Read, Glob, Grep, Bash
            mode: plan
```

```
Task(
  subagent_type: "general-purpose",
  name: "repo-analyzer",
  prompt: "You are the repo-analyzer agent for core-ai instrumentation.

PROJECT_ROOT: <project root path>
MODE: <greenfield|partial|reinstrument>
EXISTING_MANIFEST: <manifest contents if reinstrument, otherwise 'none'>

<paste full repo-analyzer agent instructions>

Scan this repository and return the detection model JSON."
)
```

Parse the returned JSON detection model.

## Step 3: Confirm (Phase 2)

Present the detection findings to the user in a clear summary:

```
Here's what I found:

  Stack:
    Language:     <primary_language> (<framework if any>)
    Package mgr:  <package_manager>
    Tests:        <test_framework>, <test_placement>
    Linting:      <linter> + <formatter>
    CI:           <ci_system>
    Git:          <commit_format>, <merge_strategy>
    Structure:    <layout>
    <other notable findings>

  Existing .claude/ inventory:
    Memory:     <which CLAUDE.md locations exist, any @imports>
    Settings:   <settings.json present? permissions, sandbox, model, etc.>
    Rules:      <N files — list by topic, note path-scoped rules>
    Commands:   <N files — list names, note audit status>
    Agents:     <N files — list names and purposes>
    Skills:     <N files — list names>
    Hooks:      <source(s), N events covered, enforcement style>
    MCP:        <configured? which servers?>

  Coverage gaps:
    <for each coverage_map category that is partial or missing, explain what's
     detected but not encoded in .claude/ config>
```

Then ask clarifying questions using AskUserQuestion. Ask 3-5 questions total, adapting to what was detected:

**Question 1 — Verify detection:**
"Does this look accurate? Anything to correct?"

**Question 2 — Workflows:**
Always ask about workflows, even if some were detected. The goal is to understand
what the user wants automated via commands, not just what exists.

"What workflows would you like AI agents to be able to run via commands? I detected
the following — select the ones you want covered, and add any I missed."

Options (adapt to detection — show detected workflows pre-checked, offer undetected
ones as suggestions):
- Release process (detected: describe what was found / not detected: ask how releases work)
- Code review / pre-commit checks
- Running tests
- Dev environment setup
- Deploy / publish
- Other (let user describe)

If existing commands cover some of these workflows, note it:
"I found existing commands: release.md, validate-all.md. I'll audit them against
what I detected and propose enrichments if anything is missing."

**Question 3 — Boundaries:**
"Are there things an AI agent should never do in this repo?"

Options:
- Standard safety (don't touch .env, don't force-push main)
- Custom boundaries (let user describe)
- No special restrictions

**Question 4 — Enforcement level:**
"How strict should convention enforcement be?"

Options:
- Strict — block violations before they happen (hooks)
- Moderate — warn but allow (recommended)
- Relaxed — document conventions in rules only, no hooks

**Question 5 — Scope (if mode is partial):**
"What would you like me to generate?"

Options based on coverage gaps from the detection model.

## Step 4: Plan Generation

Based on detection + user answers, build the generation plan. Commands are a
first-class output alongside rules and hooks — never skip the command audit.

### 4a. Rules

One rule per uncovered category:
- Git conventions (if `coverage_map.git` is `missing` or `partial`)
- Testing standards (if test framework detected and `coverage_map.testing` is `missing`)
- Code style (if linter detected and `coverage_map.code_style` is `missing`)
- Release workflow (if user described a release process)
- Project structure (if `coverage_map.project_structure` is `missing`)
- Architecture (if user provided architecture decisions)
- Security (if user provided security policies)
- Dependencies (if `coverage_map.dependencies` is `missing`)

### 4b. Commands — Audit + Generate

This is a two-part process: audit existing commands, then plan new ones.

**Part 1 — Audit existing commands:**

For every `.claude/commands/*.md` that already exists:

1. Read the file contents
2. Compare against the detection model: does the command reference the correct
   build commands, test layers, CI workflows, branch conventions, and tooling
   that were detected?
3. Classify each command:
   - **Complete** — the command already reflects detected conventions accurately
   - **Stale/incomplete** — the command exists but is missing detected context
     (e.g., release command doesn't reference the 3-layer test suite, or uses
     a generic flow that doesn't match the detected CI/release workflow)

For stale/incomplete commands, prepare a specific enrichment proposal:
```
  Enrich: .claude/commands/release.md (user-authored)
    Currently missing:
    - No reference to the 3-layer test validation before release
    - Doesn't mention the CHANGELOG version-entry consistency check
    Proposed additions: <brief summary of what would be added>
```

**User-authored commands (no provenance header) require explicit user approval
before modification.** Present the enrichment proposal clearly and ask.

Commands with a core-ai provenance header can be updated automatically.

**Part 2 — Generate new commands:**

For each workflow the user selected in Question 2 that has NO existing command:
- release.md (if user selected release process)
- review.md (if user selected code review / pre-commit checks)
- test.md (if user selected running tests)
- setup.md (if user selected dev environment setup)
- deploy.md (if user selected deploy/publish)
- Custom commands from user's "Other" descriptions

New commands use the actual detected build/test/lint commands — not generic
placeholders.

### 4c. Hooks

Only if enforcement level is `strict` or `moderate`:
- Commit format (if Conventional Commits detected)
- Sensitive file guard (always, if any enforcement)
- Test presence warning (if test framework detected)

### 4d. Present the plan

Present the full plan to the user with all three categories:

```
Based on your answers, here's what I'll generate:

  Rules:
    .claude/rules/git-conventions.md      ← from: git history, your input
    .claude/rules/testing-standards.md    ← from: vitest config, CI workflow
    ...

  Commands — New:
    .claude/commands/test.md              ← from: detected test layers
    ...

  Commands — Enrich (requires your approval):
    .claude/commands/release.md           ← add: 3-layer validation, CHANGELOG checks
    ...

  Commands — Already complete:
    .claude/commands/validate-all.md      ← matches detection, no changes needed
    ...

  Hooks:
    .claude/hooks.json                    ← commit format enforcement (moderate)
    ...

  Skipping (already covered):
    Git workflow — .claude/rules/git-workflow.md exists (user-authored)
    ...

Want me to proceed? You can also add/remove items.
```

Wait for user confirmation before generating. If the user declines enrichment
of specific commands, respect that and only generate what was approved.

## Step 5: Generate (Phase 3)

Spawn generator agents for each output type needed. Run them in parallel when possible:

### If rules are needed:
Spawn the rule-generator agent with the detection model, user answers, and list of rules to generate.

### If commands are needed (new or enrichment):
Spawn the command-generator agent with:
- The detection model
- User answers (including workflow descriptions from Question 2)
- List of **new** commands to generate
- List of **existing commands to enrich** with their current contents and the
  specific enrichment proposals from Step 4b
- Clear instruction on which commands are user-authored (enrich with care) vs
  core-ai-generated (can update freely)

The command-generator must:
- For new commands: generate from scratch using detected conventions
- For enrichments: read the existing command, preserve its structure and voice,
  and surgically add the missing context identified in the audit
- For user-authored enrichments: add a comment noting what was added:
  `<!-- Enriched by core-ai:instrument on YYYY-MM-DD — added: <summary> -->`

### If hooks are needed (enforcement level is not relaxed):
Spawn the hook-generator agent with the detection model, user answers, enforcement level, and list of hooks to generate.

As each agent completes, report what was generated:

```
Generated: .claude/rules/testing-standards.md
  ← detected: Vitest, co-located test files
  ← user confirmed: 80% coverage target

Generated: .claude/commands/test.md (new)
  ← detected: 3-layer test suite (py_compile, smoke tests, plugin validation)

Enriched: .claude/commands/release.md (user-authored, approved)
  ← added: 3-layer pre-release validation reference
  ← added: CHANGELOG version-entry consistency check
```

## Step 6: Create Manifest (Phase 4)

After all generators complete, create or update `.claude/.instrumentation.json`:

1. Compute SHA-256 hash of each generated file:
   ```bash
   sha256sum .claude/rules/<file>.md | cut -d' ' -f1
   ```

2. Build the manifest JSON:
   ```json
   {
     "version": "1",
     "created": "<today or original date if re-instrumenting>",
     "updated": "<today>",
     "generator": "core-ai:instrument",
     "detection": {
       <summary from detection model>
     },
     "files": {
       "<path>": {
         "generated": "<today>",
         "action": "<created|enriched>",
         "sources": ["<source1>", "<source2>"],
         "hash": "<sha256>"
       }
     },
     "user_answers": {
       <preserved user responses for re-instrumentation>
     }
   }
   ```
   Use `"action": "created"` for new files and `"action": "enriched"` for
   user-authored files that were modified with approval. Enriched files are
   tracked so re-instrumentation knows what was added vs what was original.

3. Write to `.claude/.instrumentation.json`

## Step 7: Summary

Present the final summary to the user:

```
Instrumentation complete.

  Created:  <N> rule files, <N> new commands, <N> hooks
  Enriched: <N> existing commands
  Manifest: .claude/.instrumentation.json

  These rules will be active in every Claude Code session in this project.
  Enriched commands now reflect detected conventions from your codebase.

  To update later:
  - Say "update instrumentation" or run /core-ai:instrument again
  - Manual edits to generated files are safe — re-instrumentation
    detects and preserves them
  - Enriched commands retain a comment marking what was added
```

</workflow>

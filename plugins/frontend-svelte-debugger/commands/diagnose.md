---
name: frontend-svelte-debugger:diagnose
description: "Triage and diagnose failures in Svelte 5 / SvelteKit applications. Classifies symptoms into failure domains, routes to specialist agents, and delivers structured diagnostic reports. Read-only — never writes or modifies code."
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
---

# Diagnose

Entry point for all Svelte 5 / SvelteKit failure diagnosis. Accepts error messages, stack traces, symptom descriptions, test output, or log file paths. Delivers a structured diagnostic report using the hybrid TL;DR + markdown format.

This command is strictly read-only. It never writes, edits, or modifies any file.

## Workflow

### Step 1: Intake

Accept input in any of these forms:
- Paste of a browser console error or stack trace
- Output from `npx svelte-check`, `vitest`, or `playwright`
- A symptom description in plain English
- A file path to a log file (use Read to load it)
- A combination of the above

If input is a file path, read the file before proceeding.

### Step 2: Clarification Round (one round only, if needed)

If ANY of the following critical context is missing, ask one targeted question using AskUserQuestion before dispatching triage. Do not ask multiple questions — identify the single most important missing piece:

- **No error text at all** — ask for the exact error message or console output
- **Symptom mentions "doesn't work" with no specifics** — ask what was expected vs what happened
- **File paths are referenced but not shared** — ask if the user can share the relevant file

Skip this step if sufficient evidence exists to classify the failure domain. One clarification round maximum — proceed to triage with whatever is available after the first response.

### Step 3: Triage

Spawn the triage agent using Task:

```
subagent_type: triage
prompt: |
  Classify the following failure into one or more diagnostic domains using
  the decision tree in diagnostic-heuristics.

  Input:
  <paste full user-provided input here>

  Domains to classify into:
  - COMPILER: svelte-check errors, TypeScript errors, rune compilation errors
  - REACTIVITY: stale UI, missed updates, $effect loops, context failures
  - SSR: hydration_mismatch, load function errors, prerender failures
  - STYLING: CSS/Tailwind failures, scoped style leakage, layout issues
  - ACCESSIBILITY: WCAG violations, ARIA issues, keyboard navigation failures
  - HARDWARE: Tauri IPC errors, USB/BLE/LAN/Audio device failures, Rust panic traces
  - BUILD: Vite plugin errors, adapter config, dependency resolution, circular imports
  - TEST: Vitest/Playwright failures, assertion mismatches
  - CROSS-DOMAIN: spans two or more domains

  Output a JSON object with:
  {
    "domains": ["DOMAIN1", ...],       // all applicable domains
    "confidence": "HIGH|MEDIUM|LOW",   // based on evidence quality
    "key_evidence": ["...", "..."],    // 2-4 most diagnostic pieces of evidence
    "needs_files": ["path/to/check"]  // files to read for deeper diagnosis, if any
  }
```

### Step 4: File Collection (if triage identifies files to read)

If the triage output includes `needs_files`, use Glob and Grep to locate and Read those files. Prioritize:
1. The file named in the stack trace (most specific)
2. The route file (`+page.svelte`, `+page.server.ts`) for the failing route
3. `svelte.config.js` and `vite.config.ts` for build/adapter issues
4. `src/app.d.ts` for TypeScript ambient type issues

Use Grep to search for the exact error pattern if a file path is not known:
```bash
grep -r "pattern-from-error" src/ --include="*.svelte" --include="*.ts" -l
```

### Step 5: Specialist Diagnosis

Dispatch one specialist agent per identified domain. If multiple domains are identified, dispatch all in parallel (multiple Task calls in a single response):

**COMPILER specialist**:
```
subagent_type: compiler-ts-analyst
prompt: |
  Diagnose this compiler/TypeScript failure.
  Evidence: <triage key_evidence + file contents if collected>
```

**REACTIVITY specialist**:
```
subagent_type: reactivity-analyst
prompt: |
  Diagnose this reactivity failure ($state, $derived, $effect, context).
  Evidence: <triage key_evidence + file contents if collected>
```

**SSR specialist**:
```
subagent_type: routing-ssr-analyst
prompt: |
  Diagnose this SSR/routing/hydration failure.
  Evidence: <triage key_evidence + file contents if collected>
```

**STYLING specialist**:
```
subagent_type: styling-layout-analyst
prompt: |
  Diagnose this CSS/Tailwind/layout failure.
  Evidence: <triage key_evidence + file contents if collected>
```

**ACCESSIBILITY specialist**:
```
subagent_type: accessibility-analyst
prompt: |
  Diagnose this accessibility/WCAG violation.
  Evidence: <triage key_evidence + file contents if collected>
```

**HARDWARE specialist**:
```
subagent_type: hardware-ipc-analyst
prompt: |
  Diagnose this Tauri IPC/hardware integration failure.
  Evidence: <triage key_evidence + file contents if collected>
```

**BUILD specialist**:
```
subagent_type: build-bundle-analyst
prompt: |
  Diagnose this Vite/SvelteKit build failure.
  Evidence: <triage key_evidence + file contents if collected>
```

**TEST specialist**:
```
subagent_type: test-failure-analyst
prompt: |
  Diagnose this test failure. Classify as test bug vs app bug.
  Evidence: <triage key_evidence + file contents if collected>
```

### Step 6: Synthesize and Report

Collect all specialist findings. Present the unified diagnostic report in the hybrid format:

1. **TL;DR line**: `[DOMAIN] [CONFIDENCE] — one-sentence root cause`
2. **Root Cause section**: 2-4 sentence explanation
3. **Evidence section**: cited file:line references
4. **Fix section**: numbered steps
5. **Verification section**: how to confirm the fix worked

For CROSS-DOMAIN findings, use the multi-cause template from output-format.

For LOW confidence findings, use the low-confidence template and include recommended diagnostic steps.

For INSUFFICIENT-EVIDENCE cases, use the escalation template with specific collection instructions.

## Hard Constraints

- Never suggest writing, editing, or creating any file
- Never run commands that modify files (`npm install`, `git`, write operations)
- Bash is permitted only for read operations: `grep`, `cat`, `ls`, `find`, `npx svelte-check`, `npx tsc --noEmit`
- If the user asks for a code fix, explain that this command diagnoses only — direct them to share the diagnosis with their engineer agent
- Maximum one clarification round before proceeding to triage with available evidence

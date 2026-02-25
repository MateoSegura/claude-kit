---
name: coding-frontend-svelte-tester:test
allowed-tools: Task, Read, Glob, Grep, Bash, AskFollowupQuestion
description: Write tests for a target file or component, then run them. Auto-detects the appropriate test type from the target. Spawns the correct test-writer agent followed by the test-runner agent.
---

# Test Command

Write tests for a target, then run them. Accepts a target (file path, component, or route) and an optional test type. Auto-detects the test type from the target if not specified.

## Step 1: Understand the Request

Parse the user's input to determine:
- **Target**: The file, component, or directory to test (required)
- **Test type**: `unit`, `component`, `e2e`, `a11y`, or `auto` (default: `auto`)
- **Scope**: Single file, multiple files, or "all" for the whole project

If the target is ambiguous, ask: what file or component should I write tests for?

## Step 2: Detect Test Type (if auto)

Read the target file to determine which test type to write:

| File Pattern | Test Type | Writer Agent |
|---|---|---|
| `*.svelte` | component | component-test-writer |
| `*.svelte.ts` (rune store) | unit | unit-test-writer |
| `+page.svelte`, `+layout.svelte` | e2e | e2e-test-writer |
| `+page.server.ts`, `+page.ts` | unit | unit-test-writer |
| `+server.ts` (API route) | unit | unit-test-writer |
| `*.ts` utility/lib | unit | unit-test-writer |
| Interactive `*.svelte` with ARIA roles | a11y + component | a11y-test-writer + component-test-writer |

Rules:
- A `.svelte` file containing form inputs, dialogs, menus, or interactive widgets → also write a11y tests
- A route file (`+page.svelte`) that represents a multi-step user flow → prefer e2e over component
- If the user explicitly says "a11y" or "accessibility", spawn a11y-test-writer regardless of file type

## Step 3: Check for Existing Tests

Before writing, check if a test file already exists:

```
<target>.test.ts
<target>.svelte.test.ts
<target>.browser.test.ts
```

If a test file exists:
- Read it to understand what is already covered
- Instruct the writer agent to ADD missing tests, not overwrite existing ones

## Step 4: Spawn Test Writer Agent(s)

Spawn the appropriate writer agent using Task. Pass:
- The target file path (absolute)
- The content of the target file (read it first)
- Any existing test file content (if found)
- The test type to write
- Instruction to follow behavior-first testing, strict TypeScript, Svelte 5 runes only

**Single test type:**
```
Spawn: <unit-test-writer | component-test-writer | e2e-test-writer | a11y-test-writer>
Input: "Write [unit|component|e2e|a11y] tests for [target].
Target file content: [content].
Existing tests: [existing content or 'none'].
Focus on behavior-first testing. Use Svelte 5 runes only. TypeScript strict mode."
```

**Component with a11y (parallel writers):**
Spawn component-test-writer AND a11y-test-writer simultaneously in the same Task call response. They write to separate files:
- `Component.svelte.test.ts` (component tests)
- `Component.a11y.test.ts` (accessibility tests)

## Step 5: Spawn Test Runner

After all writer agents complete (wait for their output), spawn the test-runner agent:

```
Spawn: test-runner
Input: "Run the tests that were just written.
Test file(s): [list of files written].
Test type: [unit|component|e2e|a11y].
Report all failures with the failing assertion and line number."
```

## Step 6: Handle Results

**If all tests pass:**
Report success with:
- Number of tests written
- Number of tests passing
- Coverage change (if available)

**If tests fail:**
1. Read the failure output from test-runner
2. Determine if the failure is:
   - **Test bug**: The test is incorrect → spawn the appropriate writer agent to fix it
   - **Implementation bug**: The source code has a bug → report it to the user, do NOT fix production code
   - **Environment issue**: Missing dependency, wrong config → report setup steps to the user

**If test-runner finds a production bug:**
Report clearly: "The test revealed a bug in [file]: [description]. The test correctly catches this. Fix the production code to make the tests pass."

## Step 7: Spawn Test Reviewer (Optional)

If the user asks for a review, or if more than 10 tests were written, spawn the test-reviewer agent:

```
Spawn: test-reviewer
Input: "Review the following test file(s) for quality.
Check for: behavior-first style, proper isolation, meaningful assertions,
correct Svelte 5 runes usage, no implementation-detail testing.
Files: [list test file paths]"
```

## Error Handling

- **Target file not found**: Ask the user to verify the path
- **Writer agent fails**: Retry once. If it fails again, report the error and ask the user whether to skip or abort
- **Test runner times out**: Report timeout and show the command the user can run manually
- **Missing test dependency** (vitest-browser-svelte, playwright): Show the install command and stop

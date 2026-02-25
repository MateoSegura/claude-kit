---
name: frontend-svelte-tester:scaffold-tests
allowed-tools: Task, Read, Glob, Grep, Bash, AskFollowupQuestion
description: Generate test file stubs for a directory or module. Creates .test.ts skeleton files with describe blocks and test names derived from exports and components — without writing assertions. Used for rapid test scaffolding before implementing tests incrementally.
---

# Scaffold Tests Command

Generate test skeleton files for an entire directory or module. Creates the test file structure (describe blocks, test names, TODOs) without writing assertions. Used as the first step when adding tests to an untested codebase.

## What Scaffolding Produces

Each scaffolded test file contains:
- Correct file extension (`.test.ts`, `.svelte.test.ts`, `.browser.test.ts`)
- Import statements for the subject under test
- One `describe` block per exported function/component
- `it('TODO: [behavior description]')` stubs derived from function/prop names
- `// TODO: Write assertions` markers
- Proper TypeScript setup (no assertions, no `any` types)

What it does NOT include:
- Actual assertions (those come from the `test` command)
- Implementation details
- Mocks (stubs only where obviously needed for imports)

## Step 1: Identify Target Scope

Parse the user's input:
- **Directory**: scaffold all source files in the directory (`src/lib/utils/`, `src/lib/components/`)
- **Single file**: scaffold one test file for one source file
- **Module**: scaffold all files in `src/lib/<module-name>/`

If no target is given, ask: "Which directory or file should I scaffold tests for?"

## Step 2: Discover Source Files

Use Glob to find source files in the target:

```
For components: src/**/*.svelte (excluding +page.svelte, +layout.svelte — those go to E2E)
For utilities:  src/**/*.ts (excluding *.test.ts, *.d.ts, index.ts barrel files)
For stores:     src/**/*.svelte.ts
```

Filter out files that already have test files:
- `Foo.svelte` → check for `Foo.svelte.test.ts`, `Foo.browser.test.ts`
- `utils.ts` → check for `utils.test.ts`

Report to the user: "Found [N] files that need test scaffolding. Skipping [M] files that already have tests."

If more than 20 files are found, ask the user to confirm before proceeding.

## Step 3: Read and Analyze Each Source File

For each file to scaffold, read the source and extract:

**For `.ts` utility files:**
- All `export function` declarations → one describe block + test stubs per function
- All `export const` (factory functions, class instances) → test stubs
- All exported types/interfaces → note for type-safe test setup (no test needed)

**For `.svelte` component files:**
- `$props()` destructuring → identify all props for test stubs
- `onclick`, `onchange`, and other callback props → stub for interaction tests
- Conditional rendering (`{#if}`) → stub for each visible state
- `{#each}` blocks → stub for list rendering and empty state
- Async blocks (`{#await}`) → stub for loading/success/error states

**For `.svelte.ts` store files:**
- All exported `$state`, factory functions → stub reactive tests

## Step 4: Spawn Writer Agents in Parallel

Determine which writer to use per file type:

| File Type | Writer Agent |
|---|---|
| `.svelte` component | component-test-writer |
| `.svelte` with interactive elements | a11y-test-writer |
| `.ts` utility/lib | unit-test-writer |
| `.svelte.ts` store | unit-test-writer |

Spawn writers in parallel batches of up to 4 simultaneous agents. Each agent receives:

```
Spawn: <writer-agent>
Input: "Generate a SCAFFOLD-ONLY test file for [source file path].

Source file content:
[content of source file]

Rules for scaffolding:
1. Create the file at: [test file path]
2. Write ONLY describe blocks and it() stubs — NO assertions
3. it() names should describe user-visible behavior (not implementation)
4. Add '// TODO: Add assertions' inside each it() body
5. Add a stub import for the component/module under test
6. For components: add one describe block per prop set / user interaction type
7. For utilities: add one describe block per exported function
8. TypeScript strict mode — no 'any' types
9. Use Svelte 5 import patterns (no Svelte 4 APIs)
10. DO NOT call render(), DO NOT add vi.mock(), DO NOT add expect() calls"
```

## Step 5: Report Scaffolded Files

After all writers complete, report:

```
Scaffolded [N] test files:

Unit tests:
  src/lib/utils/format.test.ts          (6 test stubs)
  src/lib/utils/validate.test.ts        (8 test stubs)
  src/lib/stores/cart.svelte.test.ts    (5 test stubs)

Component tests:
  src/lib/components/Button.svelte.test.ts    (4 test stubs)
  src/lib/components/Modal.svelte.test.ts     (7 test stubs)

A11y tests:
  src/lib/components/Form.a11y.test.ts        (3 test stubs)

Next steps:
  1. Run /test <file> to fill in assertions for a specific test file
  2. Run /coverage to see which files most need testing
  3. Or fill in the TODO stubs manually
```

## Step 6: Verify Files Were Created

Run a quick check to ensure all expected test files exist:

```bash
# For each scaffolded file, verify it exists
ls -la <test file paths>
```

If any file is missing (writer agent failed silently), report it clearly and offer to retry.

## Error Handling

- **No source files found in target**: Tell the user which glob patterns were searched and suggest broadening the target path
- **All files already have tests**: Report that no scaffolding is needed; offer to use `/coverage` to find gaps in existing tests instead
- **Writer agent fails for specific file**: Skip that file, continue with the rest, report the failure at the end
- **Target directory does not exist**: Ask for the correct path — list `src/lib/` contents to help the user

---
allowed-tools: Task, Read, Glob, Grep, Bash, AskFollowupQuestion
description: Run test coverage analysis, identify files below the 80% threshold, and optionally generate tests to fill the gaps. Spawns coverage-analyzer for analysis, then optionally spawns test-writer agents for gap-filling.
---

# Coverage Command

Analyze test coverage and optionally fill gaps. The workflow has two phases: analysis (always runs) and gap-filling (optional, user-approved).

## Step 1: Check Prerequisites

Before running coverage, verify the project is set up:

1. Check `vitest.config.ts` exists and has `coverage` configuration
2. Check `package.json` for `@vitest/coverage-v8` or `@vitest/coverage-istanbul`
3. If either is missing, provide setup instructions and stop

```bash
# Check for coverage provider
grep -r "coverage" vitest.config.ts
cat package.json | grep -E "coverage-v8|coverage-istanbul"
```

If coverage is not configured, show the user the configuration to add to `vitest.config.ts` and stop. Do not run coverage on an unconfigured project.

## Step 2: Run Coverage

Run the full test suite with coverage instrumentation:

```bash
npx vitest run --coverage --reporter=verbose
```

Wait for completion. Capture:
- Exit code (0 = thresholds met, 1 = thresholds missed)
- Terminal output (text reporter)
- Path to `coverage/coverage-summary.json`

If coverage run fails with a non-threshold error (e.g., test failures), report the failures and ask the user whether to continue with partial coverage data or fix the failures first.

## Step 3: Spawn Coverage Analyzer

Spawn the coverage-analyzer agent with the coverage data:

```
Spawn: coverage-analyzer
Input: "Analyze the test coverage for this Svelte 5 / SvelteKit project.
Coverage summary JSON: [path to coverage/coverage-summary.json].
Project threshold: 80% (statements, branches, functions, lines).
Coverage terminal output: [paste terminal summary].

Tasks:
1. List all files below the 80% threshold, sorted by branch coverage ascending.
2. For each file below threshold, identify the specific uncovered code paths
   (read the source file and correlate with uncovered line numbers).
3. Categorize each gap: critical path / error handling / edge case / type guard.
4. Prioritize which gaps to fill first based on risk to users.
5. Produce a coverage improvement plan: which tests to add, which test type
   (unit/component/e2e/a11y), and estimated coverage gain per test file."
```

Present the coverage-analyzer's findings to the user.

## Step 4: Ask About Gap-Filling

After presenting the analysis, ask:

"I found [N] files below 80% coverage. The highest-priority gaps are:
[list top 3-5 from coverage-analyzer output]

Options:
1. Fill all gaps — write tests for every file below threshold (~[N] test files)
2. Fill priority gaps — write tests for critical paths only (~[M] test files)
3. Fill one file — specify which file
4. Analysis only — done, I'll write tests manually

Which would you like?"

## Step 5: Spawn Gap-Filling Writers (if requested)

Based on the user's choice, spawn the appropriate test-writer agents.

**Determine writer type per file:**
- `.svelte` files → component-test-writer (and a11y-test-writer if has interactive elements)
- `.ts` utilities, stores, load functions → unit-test-writer
- `+page.server.ts` → unit-test-writer
- Route-level flows → e2e-test-writer (handle separately, mention to user)

**Spawn writers in parallel** when filling multiple files at once (up to 3 simultaneous):
```
Spawn simultaneously:
- unit-test-writer for src/lib/utils/validate.ts (covering error branches lines 28-35)
- component-test-writer for src/lib/components/Alert.svelte (covering dismissible prop)
- unit-test-writer for src/lib/stores/cart.svelte.ts (covering remove with coupon)
```

For each writer, pass:
- The source file content (read it first)
- The specific uncovered lines from coverage-analyzer's output
- Instruction to focus only on the uncovered paths (not re-test existing coverage)
- The current test file content (if one exists — read it first to avoid duplication)

## Step 6: Re-Run Coverage After Gap-Filling

After all gap-filling writers complete, re-run coverage to verify improvement:

```bash
npx vitest run --coverage --reporter=verbose
```

Compare the new coverage numbers to the baseline from Step 2.

Report:
- Files that crossed the 80% threshold (success)
- Files still below threshold (and why — if complex, recommend manual review)
- Overall coverage change: `Was X%, now Y%`

## Step 7: Summary Report

Provide a final summary:

```
Coverage Analysis Summary
========================
Before: XX.X% statements | XX.X% branches | XX.X% functions | XX.X% lines
After:  XX.X% statements | XX.X% branches | XX.X% functions | XX.X% lines

Files improved: N
Files still below threshold: M (listed below)
New test files written: N

Files below threshold (if any):
- src/lib/complex-module.ts — 68% branches
  Remaining gaps require integration tests or manual testing
  (complex async flows not suited for unit tests)
```

## Error Handling

- **No tests exist yet**: Run coverage anyway to see baseline (will be ~0%), then offer scaffolding instead of gap-filling
- **Coverage provider not installed**: Show `pnpm add -D @vitest/coverage-v8` and stop
- **JSON summary not found**: Check if `coverage/` directory exists; if not, coverage likely failed — show error output
- **Writer agent produces duplicate tests**: The coverage-analyzer should identify specific lines to target; pass those line numbers explicitly to avoid duplication

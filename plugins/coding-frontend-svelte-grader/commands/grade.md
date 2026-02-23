---
allowed-tools: Task, Read, Glob, Grep, Bash, AskUserQuestion
description: Grade a single Svelte/SvelteKit codebase across all 8 dimensions. Spawns 8 dimension reviewers in parallel, then aggregates scores, then generates a report.
---

# Grade — Single Codebase Evaluation

You orchestrate a complete Svelte/SvelteKit grading run for a single codebase. The pipeline has three sequential phases:

1. **Phase 1 (Parallel):** Launch all 8 dimension reviewers simultaneously
2. **Phase 2 (Sequential):** Run score-aggregator on the 8 dimension payloads
3. **Phase 3 (Sequential):** Run report-generator on the scorecard

You never grade code yourself. You coordinate subagents and synthesize their outputs.

---

## Step 0: Gather Input

If the user has not provided a codebase path or description, ask:

```
AskUserQuestion: "What should I grade? Please provide:
1. The path to the codebase root directory (e.g., /home/user/my-svelte-app)
2. Optional: a project name for the report (defaults to directory name)
3. Optional: any specific dimensions to focus on or exclude"
```

Validate the path exists and contains Svelte/SvelteKit files before proceeding. Check for:
- `svelte.config.js` or `svelte.config.ts` — confirms SvelteKit project
- At least one `.svelte` file — confirms Svelte components exist

If neither is found, report to the user and stop.

---

## Step 1: Scan Project Structure

Before launching reviewers, run a quick structural scan to give each reviewer accurate starting context:

```bash
# Run these to understand the project layout
find {project_root} -name "*.svelte" | head -50
find {project_root} -name "tsconfig.json" | head -5
find {project_root} -name "vitest.config*" | head -5
find {project_root} -name "tailwind.config*" | head -5
find {project_root} -name "*.test.*" -o -name "*.spec.*" | head -20
cat {project_root}/package.json
```

Collect:
- `has_typescript`: boolean (tsconfig.json present)
- `has_tailwind`: boolean (tailwind.config present)
- `has_tests`: boolean (test files found)
- `component_count`: number of .svelte files
- `project_name`: directory name or user-provided name

---

## Step 2: Launch 8 Dimension Reviewers in Parallel

Launch ALL 8 agents in a single response. Do not wait between them.

Pass each reviewer:
- The absolute path to the project root
- The structural scan summary from Step 1
- Instruction to output a JSON payload conforming to the dimension reviewer schema (see scoring-engine skill)
- Instruction to be BLIND: evaluate the code objectively with no knowledge of the author

### Agent 1: component-reviewer
```
subagent_type: component-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}
  Component count: {component_count}
  Has TypeScript: {has_typescript}
  Has Tailwind: {has_tailwind}

  Evaluate Dimension 1: Component Quality (weight: 15%).

  Your task:
  1. Find and read Svelte component files (focus on src/lib/components/ and src/routes/)
  2. Evaluate: $props() usage, component size, single responsibility, snippet usage, Svelte 5 API compliance
  3. Check for Svelte 4 anti-patterns: `export let`, `on:event` syntax, `<slot>`
  4. Output a JSON payload with dimension="component-quality", score (0-100), findings array, confidence

  Read dimension-rubrics.md from the grading-rubrics skill for exact scoring criteria.
  Output ONLY the JSON payload. No prose.
```

### Agent 2: state-reviewer
```
subagent_type: state-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}
  Component count: {component_count}

  Evaluate Dimension 2: State Management (weight: 15%).

  Your task:
  1. Grep for $state, $derived, $effect usage patterns
  2. Grep for Svelte 4 patterns: `$:`, `export let`, writable/readable stores
  3. Check for prop drilling (same prop in 3+ component chain)
  4. Check for $effect used to set derived state
  5. Check for .svelte.ts files vs .ts for global state
  6. Output a JSON payload with dimension="state-management", score (0-100), findings array, confidence

  Read dimension-rubrics.md for exact criteria. A single `$:` reactive declaration = Critical finding.
  Output ONLY the JSON payload. No prose.
```

### Agent 3: styling-reviewer
```
subagent_type: styling-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}
  Has Tailwind: {has_tailwind}

  Evaluate Dimension 3: Styling/CSS (weight: 10%).

  Your task:
  1. Check Tailwind utility usage vs custom CSS for standard layout patterns
  2. Check for inline style attributes on non-dynamic elements
  3. Check responsive breakpoint coverage (sm:, md:, lg:)
  4. Check for custom property (CSS variable) usage for design tokens
  5. Check for !important abuse, deep selector nesting
  6. Output a JSON payload with dimension="styling-css", score (0-100), findings array, confidence

  If project has no Tailwind AND no CSS, mark dimension as N/A with na_reason.
  Read dimension-rubrics.md for exact criteria.
  Output ONLY the JSON payload. No prose.
```

### Agent 4: a11y-reviewer
```
subagent_type: a11y-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}

  Evaluate Dimension 4: Accessibility (weight: 15%).

  Your task:
  1. Check for div/span used as interactive elements (div onclick, div role=button)
  2. Check keyboard accessibility: all interactive elements must be keyboard-reachable
  3. Check for missing ARIA labels on icon-only buttons
  4. Check for focus management in modals/dialogs
  5. Check semantic HTML: nav, main, button, a, h1-h6 used appropriately
  6. Check form inputs have associated labels (not just placeholder)
  7. Check for WCAG 2.2 focus-visible styles
  8. Output a JSON payload with dimension="accessibility", score (0-100), findings array, confidence

  WCAG 2.1.1 (keyboard) and WCAG 2.1.2 (no keyboard trap) failures = Critical.
  Read dimension-rubrics.md for exact WCAG success criterion breakdowns.
  Output ONLY the JSON payload. No prose.
```

### Agent 5: performance-reviewer
```
subagent_type: performance-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}

  Evaluate Dimension 5: Performance (weight: 15%).

  Your task:
  1. Check +page.server.ts vs +page.ts usage — private data must be in .server.ts
  2. Check for $effect chains that should be $derived
  3. Check for missing image dimensions (causes layout shift)
  4. Check for unnecessary eager imports of large components
  5. Check for streaming patterns for slow data loads
  6. Check for data-sveltekit-preload-data on navigation links
  7. Output a JSON payload with dimension="performance", score (0-100), findings array, confidence

  Read dimension-rubrics.md for exact criteria.
  Output ONLY the JSON payload. No prose.
```

### Agent 6: typescript-reviewer
```
subagent_type: typescript-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}
  Has TypeScript: {has_typescript}

  Evaluate Dimension 6: TypeScript Usage (weight: 10%).

  Your task:
  1. Read tsconfig.json — check for "strict": true (Critical if false or missing)
  2. Grep for `as any` casts — Major per instance
  3. Check $props() declarations have explicit interface Props
  4. Check load functions use types from ./$types
  5. Check for @ts-ignore suppressions — Major per instance
  6. Output a JSON payload with dimension="typescript-usage", score (0-100), findings array, confidence

  If project has no TypeScript at all, mark dimension as N/A with na_reason.
  strict: false = Critical finding that forces overall FAIL.
  Read dimension-rubrics.md for exact criteria.
  Output ONLY the JSON payload. No prose.
```

### Agent 7: testing-reviewer
```
subagent_type: testing-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}
  Has Tests: {has_tests}

  Evaluate Dimension 7: Testing Quality (weight: 10%).

  Your task:
  1. Find all test files (*.test.ts, *.spec.ts)
  2. If zero test files: Critical finding, mark testing-quality as failed
  3. Check for getByRole vs getByTestId usage
  4. Check for snapshot tests (toMatchSnapshot)
  5. Check for implementation testing vs behavior testing
  6. Check test description quality (descriptive vs "test 1")
  7. Check for cleanup and test isolation
  8. Output a JSON payload with dimension="testing-quality", score (0-100), findings array, confidence

  If no vitest.config.ts AND project appears to be a prototype, you may mark N/A.
  Zero tests in a non-prototype = Critical failure.
  Read dimension-rubrics.md for exact criteria.
  Output ONLY the JSON payload. No prose.
```

### Agent 8: ux-reviewer
```
subagent_type: ux-reviewer
input: |
  Project root: {project_root}
  Project name: {project_name}

  Evaluate Dimension 8: UX Patterns (weight: 10%).

  Your task:
  1. Check forms use use:enhance from $app/forms
  2. Check for loading state indicators on async operations
  3. Check for +error.svelte error boundaries at route level
  4. Check for empty state designs on lists/grids
  5. Check for actionable error messages (not generic "An error occurred")
  6. Check for optimistic update patterns where appropriate
  7. Output a JSON payload with dimension="ux-patterns", score (0-100), findings array, confidence

  Missing use:enhance = Major finding.
  Missing +error.svelte at top-level = Major finding.
  Read dimension-rubrics.md for exact criteria.
  Output ONLY the JSON payload. No prose.
```

---

## Step 3: Collect Reviewer Outputs

Wait for all 8 agents to complete. Collect their JSON payloads.

If any reviewer fails (error or no output):
- Log which dimension failed
- Set that dimension's payload to: `{ "dimension": "{dim}", "score": null, "pass": false, "critical_failure": false, "na": false, "na_reason": null, "findings": [], "positive_notes": [], "confidence": "low", "incomplete_review": true }`
- Continue to aggregation — do not stop the pipeline

---

## Step 4: Run score-aggregator

Pass all 8 dimension payloads to the score-aggregator agent:

```
subagent_type: score-aggregator
input: |
  Project: {project_name}
  Graded at: {timestamp}

  Dimension payloads (JSON array):
  {paste all 8 JSON payloads}

  Apply the full aggregation algorithm from aggregation-rules.md:
  1. Check for critical_failure overrides
  2. Separate N/A dimensions
  3. Redistribute N/A weights
  4. Compute weighted composite
  5. Determine per-dimension and overall pass/fail
  6. Assign letter grade
  7. Compute confidence score

  Output the complete scorecard JSON conforming to the aggregator output schema.
  Output ONLY the JSON scorecard. No prose.
```

---

## Step 5: Run report-generator

Pass the scorecard to the report-generator agent:

```
subagent_type: report-generator
input: |
  Project: {project_name}
  Project root: {project_root}
  Report output directory: {project_root}/grade-reports/

  Scorecard JSON:
  {paste aggregator JSON output}

  Generate:
  1. Markdown grade report: {project_root}/grade-reports/{project_name}-grade-report.md
  2. JSON scorecard: {project_root}/grade-reports/{project_name}-scorecard.json

  Follow the templates in report-formats.md exactly.
  Write both files. Confirm file paths after writing.
```

---

## Step 6: Present Summary to User

After the report-generator completes, present a brief summary:

```
Grading complete for {project_name}

Score: {composite_score}/100 — {letter_grade} — {PASS|FAIL}

Dimension Scorecard:
  Component Quality:  {score}/100
  State Management:   {score}/100
  Styling/CSS:        {score}/100
  Accessibility:      {score}/100
  Performance:        {score}/100
  TypeScript Usage:   {score}/100
  Testing Quality:    {score}/100
  UX Patterns:        {score}/100

{If critical failures: "CRITICAL FAILURES: {list}"}

Top 3 Issues to Fix:
1. [{severity}] {title} ({dimension})
2. [{severity}] {title} ({dimension})
3. [{severity}] {title} ({dimension})

Reports written to:
  {project_root}/grade-reports/{project_name}-grade-report.md
  {project_root}/grade-reports/{project_name}-scorecard.json
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Path does not exist | Report error, stop |
| No .svelte files found | Report error, stop — not a Svelte project |
| Reviewer returns invalid JSON | Log warning, use fallback payload, continue |
| Aggregator fails | Report error, show raw dimension scores, stop before report generation |
| Report generator fails | Report error, show scorecard JSON in terminal |
| User cancels mid-run | Save any completed dimension payloads to `{project_root}/grade-reports/.partial-grade.json` |

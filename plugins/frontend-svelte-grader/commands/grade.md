---
name: frontend-svelte-grader:grade
allowed-tools: Task, Read, Glob, Grep, Bash, AskUserQuestion, TeamCreate, TeamDelete, SendMessage
description: Grade a single Svelte/SvelteKit codebase across all 8 dimensions. Spawns 8 dimension reviewers in parallel, then aggregates scores, then generates a report.
---

# Grade — Single Codebase Evaluation

You orchestrate a complete Svelte/SvelteKit grading run for a single codebase. The pipeline has three sequential phases:

1. **Phase 1 (Team):** Create a grading team — the team-lead spawns 8 reviewers in parallel, collects results, runs aggregation, and returns a single scorecard
2. **Phase 2 (Sequential):** Run report-generator on the scorecard
3. **Phase 3 (Sequential):** Present summary to user

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

## Step 2: Grade via Reviewer Team

Create a team to coordinate parallel review and aggregation. This keeps all 8 reviewer outputs contained — the orchestrator receives a single scorecard instead of 8 raw payloads.

### 2a. Create the team and launch team-lead

```
TeamCreate("grading")
```

Spawn a team-lead agent:

```
subagent_type: general-purpose
team_name: grading
name: team-lead
input: |
  You are the grading team-lead for "{project_name}".

  Project root: {project_root}
  Structural scan: {paste structural scan summary from Step 1}

  Your job:
  1. Spawn all 8 dimension reviewers in parallel (one Task call with 8 agents)
  2. Collect all 8 JSON payloads
  3. Handle failures: if any reviewer fails, use this fallback payload:
     { "dimension": "{dim}", "score": null, "pass": false, "critical_failure": false, "na": false, "na_reason": null, "findings": [], "positive_notes": [], "confidence": "low", "incomplete_review": true }
  4. Spawn the score-aggregator agent with all 8 payloads
  5. Send the final scorecard back via SendMessage to the orchestrator

  Dimension reviewers to spawn (pass each the project root, structural scan, and instruction to output ONLY JSON):

  - component-reviewer: Dimension 1 — Component Quality (weight: 15%)
    Evaluate $props() usage, component size, single responsibility, snippet usage, Svelte 5 API compliance.
    Check for Svelte 4 anti-patterns: `export let`, `on:event`, `<slot>`.
    Read dimension-rubrics.md from grading-rubrics skill.

  - state-reviewer: Dimension 2 — State Management (weight: 15%)
    Grep for $state, $derived, $effect. Check for Svelte 4 patterns ($:, writable/readable stores).
    Check prop drilling and $effect misuse. Read dimension-rubrics.md.

  - styling-reviewer: Dimension 3 — Styling/CSS (weight: 10%)
    Check Tailwind utility usage, inline styles, responsive breakpoints, CSS variables, !important abuse.
    Has Tailwind: {has_tailwind}. Read dimension-rubrics.md.

  - a11y-reviewer: Dimension 4 — Accessibility (weight: 15%)
    Check div/span as interactive elements, keyboard accessibility, ARIA labels, focus management,
    semantic HTML, form labels, WCAG 2.2 focus-visible. Read dimension-rubrics.md.

  - performance-reviewer: Dimension 5 — Performance (weight: 15%)
    Check +page.server.ts usage, $effect chains, image dimensions, eager imports,
    streaming patterns, preload-data. Read dimension-rubrics.md.

  - typescript-reviewer: Dimension 6 — TypeScript Usage (weight: 10%)
    Check tsconfig strict mode, `as any` casts, $props() interfaces, $types imports.
    Has TypeScript: {has_typescript}. Read dimension-rubrics.md.

  - testing-reviewer: Dimension 7 — Testing Quality (weight: 10%)
    Find test files, check getByRole vs getByTestId, snapshot tests, behavior testing.
    Has Tests: {has_tests}. Read dimension-rubrics.md.

  - ux-reviewer: Dimension 8 — UX Patterns (weight: 10%)
    Check use:enhance, loading states, +error.svelte, empty states, error messages.
    Read dimension-rubrics.md.

  After collecting all 8 payloads, spawn score-aggregator with:
    Project: {project_name}
    Graded at: {timestamp}
    All 8 dimension payloads as JSON array
    Instruction to apply aggregation-rules.md algorithm

  When you have the scorecard, send it back:
    SendMessage(type="message", recipient="orchestrator", content=<scorecard JSON>)
```

### 2b. Receive scorecard and clean up

Wait for the team-lead's message containing the aggregated scorecard JSON.

```
TeamDelete("grading")
```

Proceed to Step 3 (report generation) with the scorecard.

---

## Step 3: Run report-generator

Compute a timestamped output directory:
```
output_dir = {project_root}/reports/<YYYY-MM-DD_HH-MM-SS>/
```
Create the directory before spawning the report generator.

Pass the scorecard to the report-generator agent:

```
subagent_type: report-generator
input: |
  Project: {project_name}
  Project root: {project_root}
  Report output directory: {project_root}/reports/<YYYY-MM-DD_HH-MM-SS>/

  Scorecard JSON:
  {paste aggregator JSON output}

  Generate:
  1. Markdown grade report: {output_dir}/{project_name}-grade-report.md
  2. JSON scorecard: {output_dir}/{project_name}-scorecard.json
  3. Zip archive: {output_dir}/contents.zip (containing all report files)

  Follow the templates in report-formats.md exactly.
  Write both files, then zip them. Confirm file paths after writing.
```

---

## Step 4: Present Summary to User

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

Reports: {project_root}/reports/<YYYY-MM-DD_HH-MM-SS>/contents.zip
  Contains: {project_name}-grade-report.md, {project_name}-scorecard.json
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Path does not exist | Report error, stop |
| No .svelte files found | Report error, stop — not a Svelte project |
| Team-lead fails | Report error, show any partial data available, stop |
| Team-lead sends incomplete scorecard | Log warning, proceed to report generation with available data |
| Report generator fails | Report error, show scorecard JSON in terminal |
| User cancels mid-run | Save any completed dimension payloads to `{project_root}/reports/.partial-grade.json` |

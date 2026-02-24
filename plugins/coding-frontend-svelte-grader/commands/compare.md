---
allowed-tools: Task, Read, Glob, Grep, Bash, AskUserQuestion
description: Compare two Svelte/SvelteKit codebases (or two branches/commits of the same project) side-by-side. Runs the full 8-dimension grading pipeline on both, then generates a comparative scorecard showing dimension-by-dimension deltas, regressions, and improvements.
---

# Compare — A/B Codebase Comparison

You orchestrate a side-by-side comparison of two Svelte/SvelteKit codebases. Run the full grading pipeline on each, then produce a comparative report showing which performs better across all 8 dimensions.

Common use cases:
- PR review: compare feature branch vs main
- Refactoring assessment: before vs after
- Candidate evaluation: submission A vs submission B
- Framework migration: Svelte 4 version vs Svelte 5 version

---

## Step 0: Gather Input

If the user has not provided both codebase paths, ask:

```
AskUserQuestion: "Please provide the two codebases to compare:

Option A — Two separate directories:
  Path A: /path/to/codebase-a
  Path B: /path/to/codebase-b

Option B — Two git branches/commits in the same repo:
  Repo path: /path/to/repo
  Branch/commit A: main (or a commit SHA)
  Branch/commit B: feature/my-changes

Option C — Two commits in the current repo:
  Branch/commit A: (e.g., HEAD~1 or a SHA)
  Branch/commit B: (e.g., HEAD or a SHA)

Also provide (optional):
  - Label for A (e.g., 'Before Refactor', 'main', 'Submission A')
  - Label for B (e.g., 'After Refactor', 'PR #42', 'Submission B')"
```

Set defaults: Label A = "Project A", Label B = "Project B".

---

## Step 1: Prepare Both Codebases

### For two separate directories:
Validate both paths exist and contain Svelte files. Run the structural scan for each:

```bash
# For each project root (A and B):
find {root} -name "*.svelte" | wc -l
find {root} -name "tsconfig.json" | head -3
find {root} -name "vitest.config*" | head -3
find {root} -name "tailwind.config*" | head -3
find {root} -name "*.test.*" -o -name "*.spec.*" | wc -l
cat {root}/package.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name','unknown'))"
```

### For git branches in the same repo:
Check out each branch into a temporary directory:

```bash
# Create temp directories for each version
TEMP_A=$(mktemp -d)
TEMP_B=$(mktemp -d)

# Shallow checkout of each branch/commit into temp dirs
git -C {repo_path} worktree add --detach $TEMP_A {branch_or_commit_a}
git -C {repo_path} worktree add --detach $TEMP_B {branch_or_commit_b}

# Set project roots
PROJECT_ROOT_A=$TEMP_A
PROJECT_ROOT_B=$TEMP_B
```

Note: Clean up worktrees at the end with `git worktree remove`.

---

## Step 2: Run Full Grading Pipeline on BOTH Codebases in Parallel

Launch ALL 16 dimension reviewer agents simultaneously (8 for A, 8 for B). This is the most important optimization — do not run them sequentially.

Name convention: prefix agent inputs with `[A]` or `[B]` to distinguish outputs.

### Launch 8 reviewers for Project A (all in parallel with Project B reviewers):

For each of the 8 dimensions, spawn the dimension reviewer with project root set to `{project_root_a}` and a label note `"[Grading: {label_a}]"` at the start of the input.

Use the exact same reviewer inputs as documented in `grade.md`, with `{project_root}` replaced by `{project_root_a}`.

Reviewers to spawn for Project A:
- `component-reviewer` with Project A root
- `state-reviewer` with Project A root
- `styling-reviewer` with Project A root
- `a11y-reviewer` with Project A root
- `performance-reviewer` with Project A root
- `typescript-reviewer` with Project A root
- `testing-reviewer` with Project A root
- `ux-reviewer` with Project A root

### Launch 8 reviewers for Project B (simultaneously with Project A reviewers):

Reviewers to spawn for Project B:
- `component-reviewer` with Project B root
- `state-reviewer` with Project B root
- `styling-reviewer` with Project B root
- `a11y-reviewer` with Project B root
- `performance-reviewer` with Project B root
- `typescript-reviewer` with Project B root
- `testing-reviewer` with Project B root
- `ux-reviewer` with Project B root

**Total: 16 agents launched in one parallel batch.**

---

## Step 3: Aggregate Scores for Each Project Separately

After all 16 reviewers complete, run two score-aggregator agents in parallel (one per project):

### Aggregator for Project A:
```
subagent_type: score-aggregator
input: |
  Project: {label_a}
  Graded at: {timestamp}

  Dimension payloads for {label_a} (JSON array):
  {paste all 8 Project A dimension payloads}

  Apply full aggregation algorithm from aggregation-rules.md.
  Output the complete scorecard JSON. Label all fields with project="{label_a}".
  Output ONLY the JSON scorecard. No prose.
```

### Aggregator for Project B:
```
subagent_type: score-aggregator
input: |
  Project: {label_b}
  Graded at: {timestamp}

  Dimension payloads for {label_b} (JSON array):
  {paste all 8 Project B dimension payloads}

  Apply full aggregation algorithm from aggregation-rules.md.
  Output the complete scorecard JSON. Label all fields with project="{label_b}".
  Output ONLY the JSON scorecard. No prose.
```

---

## Step 4: Compute Delta Analysis

Before calling the report-generator, compute the deltas yourself so the report-generator has them ready:

For each dimension:
```
delta[dimension] = scorecard_b.dimensions[dimension].score - scorecard_a.dimensions[dimension].score
```

Classify each dimension:
- `delta > 5`: Improvement (B is meaningfully better)
- `delta < -5`: Regression (A is meaningfully better, B regressed)
- `-5 ≤ delta ≤ 5`: No significant change

Compute overall delta:
```
overall_delta = scorecard_b.result.composite_score - scorecard_a.result.composite_score
```

Identify:
- `strongest_improvement`: dimension with highest positive delta
- `worst_regression`: dimension with most negative delta
- `shared_findings`: findings with the same title present in both scorecards

---

## Step 5: Run report-generator for Comparative Report

Compute a timestamped output directory:
```
output_dir = <parent_directory>/reports/<YYYY-MM-DD_HH-MM-SS>/
```
- If comparing two separate directories: parent = parent directory of Project A
- If comparing git branches: parent = {repo_path}

Create the directory before spawning the report generator.

```
subagent_type: report-generator
input: |
  Mode: comparative
  Label A: {label_a}
  Label B: {label_b}

  Scorecard A:
  {paste scorecard A JSON}

  Scorecard B:
  {paste scorecard B JSON}

  Pre-computed deltas:
  {paste delta analysis}

  Output directory: {output_dir}

  Generate these files:
  1. {output_dir}/comparison-{label_a_slug}-vs-{label_b_slug}-report.md
     Use the comparative report template from report-formats.md
  2. {output_dir}/{label_a_slug}-scorecard.json (Project A scorecard)
  3. {output_dir}/{label_b_slug}-scorecard.json (Project B scorecard)
  4. {output_dir}/comparison-{label_a_slug}-vs-{label_b_slug}-scorecard.json (combined)
  5. {output_dir}/contents.zip (archive of all report files)

  In the comparative report:
  - Highlight regressions in {label_b} vs {label_a} explicitly
  - Highlight improvements in {label_b} vs {label_a} explicitly
  - List findings present in BOTH projects (shared technical debt)
  - List findings unique to each project

  After writing all files, zip them into contents.zip.
  Output ONLY file write confirmations. No prose.
```

---

## Step 6: Present Comparison Summary to User

```
Comparison complete: {label_a} vs {label_b}

                        {label_a}    {label_b}    Delta
  Composite Score:      {score_a}    {score_b}    {delta:+.1f}
  Overall Result:       {PASS|FAIL}  {PASS|FAIL}  —

  Dimension Comparison:
  Component Quality:    {score_a}    {score_b}    {delta:+d}  [{better}]
  State Management:     {score_a}    {score_b}    {delta:+d}  [{better}]
  Styling/CSS:          {score_a}    {score_b}    {delta:+d}  [{better}]
  Accessibility:        {score_a}    {score_b}    {delta:+d}  [{better}]
  Performance:          {score_a}    {score_b}    {delta:+d}  [{better}]
  TypeScript Usage:     {score_a}    {score_b}    {delta:+d}  [{better}]
  Testing Quality:      {score_a}    {score_b}    {delta:+d}  [{better}]
  UX Patterns:          {score_a}    {score_b}    {delta:+d}  [{better}]

  {If regressions exist:}
  REGRESSIONS in {label_b}:
    - {dimension}: {score_a} → {score_b} (−{abs_delta} pts)

  {If improvements exist:}
  IMPROVEMENTS in {label_b}:
    + {dimension}: {score_a} → {score_b} (+{delta} pts)

  Reports: {output_dir}/contents.zip
    Contains: comparison report, individual scorecards
```

---

## Step 7: Git Worktree Cleanup (branch comparison only)

If git worktrees were created in Step 1, clean them up:

```bash
git -C {repo_path} worktree remove {TEMP_A} --force
git -C {repo_path} worktree remove {TEMP_B} --force
rm -rf $TEMP_A $TEMP_B
```

---

## Pipeline Summary

```
Input: Project A path + Project B path
         │
         ▼
Structural scan (both projects)
         │
         ▼
┌────────────────────────────────────────────────────────────────────┐
│  16 PARALLEL REVIEWERS (8 per project)                             │
│  comp-A  state-A  css-A  a11y-A  perf-A  ts-A  test-A  ux-A      │
│  comp-B  state-B  css-B  a11y-B  perf-B  ts-B  test-B  ux-B      │
└────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  2 PARALLEL AGGREGATORS                  │
│  score-aggregator-A   score-aggregator-B │
└──────────────────────────────────────────┘
         │
         ▼
Delta computation (inline, no subagent needed)
         │
         ▼
report-generator (comparative mode)
         │
         ▼
Output: comparison-report.md + 3 scorecard JSON files
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| One project path does not exist | Report error with which path failed, stop |
| Git branch does not exist | Report error, list available branches, stop |
| Reviewer fails for one project | Use fallback payload, note incomplete in report |
| Both reviewers fail for same dimension | Flag dimension as "inconclusive" in comparative report |
| Aggregator fails for one project | Show raw dimension scores in terminal, stop before report generation |
| Git worktree creation fails | Try `git stash && git checkout {branch}` alternative approach, warn user |

---

## Cost Note

This command runs 16 dimension reviewers (vs 8 for a single grade). Budget approximately 2x the API cost of the `grade` command. For cost-conscious usage, consider running `grade` on each project separately and manually comparing the resulting scorecards.

---
name: frontend-svelte-grader:compare
allowed-tools: Task, Read, Glob, Grep, Bash, AskUserQuestion, TeamCreate, TeamDelete, SendMessage
description: Compare two Svelte/SvelteKit codebases (or two branches/commits of the same project) side-by-side. Runs the full 8-dimension grading pipeline on both, then generates a comparative scorecard showing dimension-by-dimension deltas, regressions, and improvements.
---

# Compare — A/B Codebase Comparison

You orchestrate a side-by-side comparison of two Svelte/SvelteKit codebases. Create parallel grading teams (one per project) to independently run the full 8-dimension pipeline, then produce a comparative report showing which performs better across all dimensions.

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

## Step 2: Grade Both Codebases via Parallel Teams

Create two teams (one per project) to contain the reviewer sprawl. Each team-lead manages 8 reviewers + aggregation, sending back a single scorecard.

### 2a. Create both teams in parallel

```
TeamCreate("grading-a")
TeamCreate("grading-b")
```

### 2b. Launch team-leads for both projects simultaneously

Spawn both team-leads in a single response:

**Team-lead A:**
```
subagent_type: general-purpose
team_name: grading-a
name: team-lead
input: |
  You are the grading team-lead for "{label_a}".

  Project root: {project_root_a}
  Structural scan: {paste structural scan for Project A}

  Your job:
  1. Spawn all 8 dimension reviewers in parallel (component-reviewer, state-reviewer,
     styling-reviewer, a11y-reviewer, performance-reviewer, typescript-reviewer,
     testing-reviewer, ux-reviewer)
  2. Pass each reviewer the project root, structural scan, and instruction to output ONLY JSON
  3. Collect all 8 JSON payloads (use fallback payload for any failures)
  4. Spawn score-aggregator with all 8 payloads
  5. Send the final scorecard back via SendMessage to the orchestrator

  Use the exact same reviewer inputs as documented in grade.md, with project root = {project_root_a}.
  Label all output with project="{label_a}".
```

**Team-lead B:**
```
subagent_type: general-purpose
team_name: grading-b
name: team-lead
input: |
  You are the grading team-lead for "{label_b}".

  Project root: {project_root_b}
  Structural scan: {paste structural scan for Project B}

  [Same instructions as Team-lead A, but for Project B with project root = {project_root_b}]
  Label all output with project="{label_b}".
```

### 2c. Receive scorecards and clean up

Wait for both team-leads' messages containing their aggregated scorecard JSONs.

```
TeamDelete("grading-a")
TeamDelete("grading-b")
```

Proceed to Step 3 (delta analysis) with both scorecards.

---

## Step 3: Compute Delta Analysis

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

## Step 4: Run report-generator for Comparative Report

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

## Step 5: Present Comparison Summary to User

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

## Step 6: Git Worktree Cleanup (branch comparison only)

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
┌──────────────────────────────────────────────────────────────┐
│  2 PARALLEL GRADING TEAMS                                    │
│                                                              │
│  Team A (team-lead-a):              Team B (team-lead-b):    │
│    8 reviewers → aggregator           8 reviewers → aggregator│
│    → scorecard A                      → scorecard B          │
└──────────────────────────────────────────────────────────────┘
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
| Team-lead fails for one project | Use fallback payload, note incomplete in report |
| Both team-leads fail for same dimension | Flag dimension as "inconclusive" in comparative report |
| Git worktree creation fails | Try `git stash && git checkout {branch}` alternative approach, warn user |

---

## Cost Note

This command creates 2 parallel grading teams, each running 8 dimension reviewers internally. Budget approximately 2x the API cost of the `grade` command. For cost-conscious usage, consider running `grade` on each project separately and manually comparing the resulting scorecards.

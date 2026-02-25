---
name: cloud-python-grader:grade-diff
allowed-tools: Read, Glob, Grep, Bash, Task
description: Fast diff-scoped pre-commit review. Accepts a git diff range (default: staged changes), scopes grading to changed files and their direct dependents, and produces a focused report suitable for pre-commit or PR review gates.
---

# grade-diff — Diff-Scoped Pre-Commit Review

Run a focused 8-dimension review scoped to changed files only. Designed for pre-commit hooks, CI gates, and PR review workflows where only the diff needs grading. Faster than `/grade` because it reviews only changed code — not the full service.

**Never write or edit any source files.** This command is read-only. All output is the grading report.

## Usage

```
/cloud-python-grader:grade-diff [diff-range]
```

- `diff-range` — Any valid git diff specification. Defaults to `--staged` (staged changes for commit).

Examples:
- `/grade-diff` — Review staged changes (pre-commit)
- `/grade-diff HEAD~1..HEAD` — Review last commit
- `/grade-diff main..feature/payments` — Review a feature branch vs main
- `/grade-diff HEAD~3..HEAD` — Review last 3 commits

---

## Workflow

### Step 1: Resolve Diff Range

1. If no argument provided, use `--staged` as the diff range.
2. Run: `git diff <diff-range> --name-only` to get the list of changed files.
3. Filter to Python files (`*.py`) and YAML manifest files (`*.yaml`, `*.yml` under `k8s/` or `deploy/`).
4. If the changed file list is empty: report "No Python or manifest files in diff range `<range>`. Nothing to review." and stop.
5. Get the full diff content: `git diff <diff-range> -- <filtered files>`.
6. Report to the user: "Reviewing N changed file(s): <list of files>"

### Step 2: Expand to Direct Dependents

For each changed Python file, find direct importers within the same service:

```bash
# For each changed file module (e.g., app/services/payment.py → app.services.payment)
grep -r "from app.services.payment import\|import app.services.payment" --include="*.py" -l
```

Include dependents in the review scope — they may be broken by interface changes in the diff — but clearly label them as "dependency context" files (not changed files) in the report.

Limit dependent expansion: include at most 10 additional files. If more than 10 dependents exist, note "N additional dependent files not expanded — consider running `/grade` for full analysis."

### Step 3: Collect Diff Context

Before spawning review subagents:

1. Read `pyproject.toml` or `setup.cfg` for framework and dependency context.
2. Read the full diff output (from Step 1) — this is the primary review material.
3. Read the full content of each changed file (not just the diff lines) — subagents need full context to assess correctness.
4. Note which lines were added (`+`) vs removed (`-`) in the diff — findings on removed lines are informational only, not blocking.

### Step 4: Run Dimension Reviews

Spawn dimension review subagents in parallel. Because this is a diff review, subagents should:

- Focus findings on **added or modified lines** (lines prefixed with `+` in the diff)
- Flag findings on removed lines only if the removal itself introduces a risk (e.g., removing a security check)
- Use the full file content for context but scope the score to changed code quality

Pass each subagent:
- The diff content (added/removed lines)
- The full content of changed files
- The list of dependent context files (for interface change detection)
- Its dimension name, rubric, and the instruction to focus on changed code

Subagent assignments — run all in parallel:

| Subagent | Dimension | Diff focus |
|----------|-----------|------------|
| reviewer-async | async-correctness | New async functions, added await patterns |
| reviewer-types | type-safety | New/modified function signatures, Pydantic model changes |
| reviewer-security | security | New string assignments, new HTTP calls, new DB queries |
| reviewer-observability | observability | New log calls, new exception handlers |
| reviewer-contracts | api-contracts | New or modified route decorators, response model changes |
| reviewer-performance | performance-risk | New queries, new loops, new endpoint handlers |
| reviewer-tests | test-coverage | New test files or test functions; coverage of changed code |
| reviewer-k8s | k8s-hygiene | Changed YAML manifests only |

If no YAML files changed: skip reviewer-k8s and mark k8s-hygiene as "Not in diff scope."
If no test files changed: run reviewer-tests against existing test files to check if the changed production code has corresponding tests.

### Step 5: Compute Focused Score

Apply the same weights as `/grade`:

```
async-correctness:  score * 0.20
type-safety:        score * 0.15
security:           score * 0.20
observability:      score * 0.10
api-contracts:      score * 0.15
performance-risk:   score * 0.10
test-coverage:      score * 0.05
k8s-hygiene:        score * 0.05
```

For dimensions with no changed code in scope (e.g., no YAML changed), exclude from weighted calculation and note "N/A — not in diff."

Assign grade letter using same thresholds as `/grade`.

### Step 6: Produce Focused Report

Output the report in this structure:

---

```
# Diff Review Report — <diff-range>
Reviewed: <timestamp>
Changed files: <N> | Dependency context files: <M>
Diff size: +<added> / -<removed> lines

## Final Score: <score>/100 — Grade <letter>
(Scoped to diff — run /grade for full-service analysis)

### Dimension Breakdown

| Dimension          | Score | In Diff? | Contribution |
|--------------------|-------|----------|--------------|
| async-correctness  | XX    | yes      | XX.X         |
| type-safety        | XX    | yes      | XX.X         |
| security           | XX    | yes      | XX.X         |
| observability      | XX    | yes      | XX.X         |
| api-contracts      | XX    | yes      | XX.X         |
| performance-risk   | XX    | yes      | XX.X         |
| test-coverage      | XX    | yes      | XX.X         |
| k8s-hygiene        | N/A   | no       | —            |
| **TOTAL**          |       |          | **XX.X**     |

## Blocking Findings (Critical + High — must fix before commit/merge)

[List all CRITICAL and HIGH findings, sorted by severity then dimension]
[For each finding: location, impact, recommendation]

## Non-Blocking Findings (Medium + Low)

[List all MEDIUM and LOW findings]

## Changed Files Reviewed

[List each changed file with its dimension findings count]

## Dependency Impact

[List any breaking interface changes detected in changed files that affect dependent files]
[e.g., "PaymentService.charge() return type changed from PaymentResult to dict — 3 callers affected"]

## Merge Recommendation

[One of:]
- APPROVE — No Critical or High findings in changed code. Ready to merge.
- APPROVE WITH CONDITIONS — No Critical findings. High findings tracked.
- REQUEST CHANGES — X Critical/High finding(s) in changed code. Fix before merge.
```

---

## Diff-Specific Rules

### Findings on Removed Code
- Do NOT report findings for code that was removed in the diff.
- Exception: if a removal introduces new risk (e.g., a security check was removed), report as a finding on the removal itself with a clear label: "[REMOVED]".

### Test Coverage for Changed Code
If production code was changed but no corresponding test change is present in the diff:
- Check whether existing tests cover the changed code paths.
- If no test covers the changed path: report as [HIGH] test-coverage — "No test coverage for changed code in `<file>:<function>`."

### API Contract Change Detection
When a Pydantic response model or route signature is changed:
- Compare old version (`-` lines) with new version (`+` lines).
- Flag removed fields, type changes, or renamed endpoints as potential breaking changes.
- If the change appears backwards-compatible (added optional field), report as [LOW].
- If the change removes a field or changes a type, report as [CRITICAL] api-contracts.

### Performance Scope
Focus performance-risk on:
- New endpoints added (do they have pagination?)
- New database queries added (are they bounded?)
- New loops added (N+1 risk?)
Do NOT penalize existing performance issues not touched by the diff — those are covered by `/grade`.

## Error Handling

- **Not a git repository**: Report "This command requires a git repository. Ensure you are in the correct directory." and stop.
- **Invalid diff range**: Report the git error message and suggest valid formats.
- **Staged area empty (with `--staged`)**: Report "No staged changes found. Stage files with `git add` first, or provide a diff range."
- **Binary files in diff**: Skip binary files silently; note them in the report as "Binary files excluded."
- **Subagent failure**: Same escalation rules as `/grade` — mark dimension N/A, note failure, compute partial score.

---
name: cloud-python-grader:grade
allowed-tools: Read, Glob, Grep, Bash, Task, TeamCreate, TeamDelete, SendMessage
description: Full-service on-demand code review. Accepts a service path or file glob, grades all 8 dimensions via parallel subagents, and produces a unified report with weighted final score, per-dimension scores, findings list, and inline annotations.
---

# grade — Full Code Review

Run a comprehensive 8-dimension review of a Python cloud microservice. Produces a unified grading report with a weighted final score, per-dimension breakdown, severity-annotated findings, and actionable recommendations.

**Never write or edit any source files.** This command is read-only. All output is the grading report.

## Usage

```
/cloud-python-grader:grade [path]
```

- `path` — service directory (e.g. `services/payments`) or file glob (e.g. `src/**/*.py`). Defaults to current working directory.

---

## Workflow

### Step 1: Resolve Scope

1. If the user provided a path argument, use it directly.
2. If no argument provided, ask the user: "What service or files should I review? (Provide a directory path or glob pattern.)"
3. Expand the scope:
   - If a directory: glob `**/*.py` and `**/k8s/**/*.yaml` + `**/deploy/**/*.yaml` within it.
   - If a glob: use as-is.
4. Verify at least one Python file exists in scope. If not, report: "No Python files found at `<path>`. Please check the path and try again."
5. Report scope to the user: "Reviewing N Python files and M manifest files in `<path>`."

### Step 2: Collect Context

Read the following files before spawning review subagents, to pass as shared context:

1. `pyproject.toml` or `setup.cfg` — dependencies, mypy config, pytest config.
2. `Dockerfile` (if present) — base image, user, entrypoint.
3. Entry point file (`main.py`, `app.py`, `app/main.py`) — framework detection (FastAPI, aiohttp, gRPC).
4. One representative route/handler file to orient the subagents.

Summarize detected context:
- Framework: FastAPI / aiohttp / gRPC / other
- Python version: from pyproject.toml or Dockerfile
- Key dependencies: pydantic, sqlalchemy, asyncpg, opentelemetry, etc.

### Step 3: Grade via Reviewer Team

Create a team to coordinate all 8 dimension reviewers and score computation. The team-lead spawns reviewers in parallel, collects results, computes the weighted final score, and sends back a synthesized scorecard.

**Create team:**
```
TeamCreate("grading")
```

**Spawn team-lead:**
```
subagent_type: general-purpose
team_name: grading
name: team-lead
input: |
  You are the grading team-lead for this Python cloud service review.

  Service path: {service_path}
  File list: {resolved file list}
  Context summary: {framework, Python version, key deps}

  Your job:
  1. Spawn all 8 dimension reviewers in parallel (one Task call with 8 agents):

     | Subagent | Dimension | Focus files |
     |----------|-----------|-------------|
     | reviewer-async | async-correctness | All *.py files |
     | reviewer-types | type-safety | All *.py files, mypy config |
     | reviewer-security | security | All *.py files, .env.*, config files |
     | reviewer-observability | observability | All *.py files, logging config |
     | reviewer-contracts | api-contracts | Route/endpoint files, Pydantic models |
     | reviewer-performance | performance-risk | All *.py files, ORM models |
     | reviewer-tests | test-coverage | tests/, test_*.py, *_test.py |
     | reviewer-k8s | k8s-hygiene | **/k8s/**/*.yaml, **/deploy/**/*.yaml, Dockerfile, app entry point |

  2. Pass each reviewer: the file list, context summary, its dimension name,
     and instruction to output structured findings in this format:
     ```
     DIMENSION: <name>
     SCORE: <0-100>
     FINDINGS:
     - [SEVERITY] Short title | file:line | Impact sentence | Recommendation sentence
     ...
     SUMMARY: One-sentence dimension summary.
     ```

  3. Collect all 8 results. If a subagent failed or returned malformed output:
     assign that dimension score = N/A and note the failure.

  4. Compute the weighted final score:
     async-correctness:  score * 0.20
     type-safety:        score * 0.15
     security:           score * 0.20
     observability:      score * 0.10
     api-contracts:      score * 0.15
     performance-risk:   score * 0.10
     test-coverage:      score * 0.05
     k8s-hygiene:        score * 0.05
     final_score = sum of weighted dimension scores
     If any dimension is N/A, exclude its weight from the denominator.

  5. Assign grade letter: 90-100=A, 80-89=B, 70-79=C, 60-69=D, <60=F

  6. Send back ALL results via SendMessage to the orchestrator:
     - All 8 dimension results (scores, findings, summaries)
     - The computed final_score and grade letter
     - List of any N/A dimensions and why
```

**Receive results and clean up:**

Wait for the team-lead's message containing the synthesized review results.

```
TeamDelete("grading")
```

Proceed to Step 4 (gather git context) with the received results.

### Step 4: Gather Git Context

Collect git metadata from the service directory:
```bash
cd <service_path> && \
  echo "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')" && \
  echo "commit=$(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')" && \
  echo "dirty=$(git diff --quiet 2>/dev/null && echo 'clean' || echo 'dirty')" && \
  echo "remote=$(git remote get-url origin 2>/dev/null || echo 'N/A')"
```

### Step 7: Write Report Files

Compute a timestamped output directory:
```
output_dir = <service_path>/reports/<YYYY-MM-DD_HH-MM-SS>/
```
Create the directory before writing.

Write three files to the output directory:

1. **`{output_dir}/report.md`** — Full markdown report with the structure below
2. **`{output_dir}/scorecard.json`** — Machine-readable JSON from the score-synthesizer output (include a `git` object with branch, commit, dirty, remote fields)
3. **`{output_dir}/contents.zip`** — Archive containing both files above

Create the zip:
```bash
cd <output_dir> && zip contents.zip report.md scorecard.json 2>/dev/null
```

#### Markdown report structure:

```
# Python Cloud Service — Code Quality Report

| | |
|---|---|
| **Service** | <service name or path> |
| **Date** | <timestamp> |
| **Scope** | <N files> |
| **Branch** | `<git_branch>` |
| **Commit** | `<git_commit_short>` |
| **Working Tree** | <git_clean_or_dirty> |

## Final Score: <score>/100 — Grade <letter>

### Dimension Breakdown

| Dimension          | Score | Weight | Contribution |
|--------------------|-------|--------|--------------|
| async-correctness  | XX    | 20%    | XX.X         |
| type-safety        | XX    | 15%    | XX.X         |
| security           | XX    | 20%    | XX.X         |
| observability      | XX    | 10%    | XX.X         |
| api-contracts      | XX    | 15%    | XX.X         |
| performance-risk   | XX    | 10%    | XX.X         |
| test-coverage      | XX    | 5%     | XX.X         |
| k8s-hygiene        | XX    | 5%     | XX.X         |
| **TOTAL**          |       |        | **XX.X**     |

## Critical Findings (must fix before merge)

[List all CRITICAL severity findings across all dimensions, sorted by dimension]

## High Findings (fix before release)

[List all HIGH severity findings across all dimensions]

## Medium Findings (fix within 1–2 sprints)

[List all MEDIUM severity findings]

## Low Findings (informational)

[List all LOW severity findings]

## Dimension Summaries

### async-correctness — XX/100
<one-sentence summary from subagent>

### type-safety — XX/100
<one-sentence summary from subagent>

[... repeat for each dimension ...]

## Merge Recommendation

[One of:]
- APPROVE — No Critical or High findings. Ready to merge.
- APPROVE WITH CONDITIONS — No Critical findings. High findings tracked in issues.
- REQUEST CHANGES — X Critical finding(s) must be resolved before merge.
- REJECT — Score below 60. Significant rework required.
```

### Step 7: Present Summary to User

Display a brief terminal summary:

```
=== Code Review Complete ===

Service: <service name or path>
Score: <score>/100 — Grade <letter>
Merge: <APPROVE|APPROVE WITH CONDITIONS|REQUEST CHANGES|REJECT>

Top 3 Issues:
1. [SEVERITY] title (dimension)
2. [SEVERITY] title (dimension)
3. [SEVERITY] title (dimension)

Reports: <service_path>/reports/<YYYY-MM-DD_HH-MM-SS>/contents.zip
  Contains: report.md, scorecard.json
```

---

## Error Handling

- **No files found**: Report scope error and stop. Do not produce a partial report.
- **Subagent failure (1–2 dimensions)**: Report as N/A, note the failure, compute partial weighted score, flag in report header.
- **Subagent failure (3+ dimensions)**: Report all failures, suggest the user retry individual dimensions with `/grade-diff` scoped to specific files.
- **No YAML manifests found**: Mark k8s-hygiene as "Not applicable — no Kubernetes manifests found in scope" and exclude from weighted score.
- **No test files found**: Mark test-coverage with score of 40 and finding: "[HIGH] test-coverage — No test files found in scope."

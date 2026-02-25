---
name: embedded-zephyr-grader:grade
allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Write, Bash, TeamCreate, TeamDelete, SendMessage
description: Grade a single Zephyr RTOS submission using automated tools and LLM review to generate a comprehensive scorecard
---

# Grade Zephyr Submission

You orchestrate the grading of a single Zephyr RTOS submission by spawning specialized subagents and aggregating their results into a comprehensive report.

## Input Parameters

Accept these parameters from the user (ask if not provided):

1. **submission_path** (required): Path to the submission directory
2. **boards** (optional): Target board name(s), comma-separated for multi-board (e.g., `nrf52840dk_nrf52840` or `nrf52840dk_nrf52840,nucleo_f401re`)
   - If not provided, auto-detect from project files (CMakeLists.txt, prj.conf, boards/ overlays, west.yml)
   - If detection fails, grading cannot proceed — report an error to the user and stop
3. **weight_overrides** (optional): Custom dimension weights as JSON
   - Example: `{"compilability": 0.25, "static_analysis": 0.20}`
4. **llm_passes** (optional): Number of LLM review passes for consistency (default: 1)
5. **output_formats** (optional): List of output formats (default: `["markdown", "json"]`)
   - Options: `markdown`, `json`, `html`

## Workflow

### Phase 1: Intake and Validation

**Spawn:** `submission-intake` agent

**Input:**
```json
{
  "submission_path": "<path>",
  "boards": ["<board>", "<board2>"]
}
```

Pass `boards` as an array. If the user provided a comma-separated string, split it into an array before passing. If the user did not specify boards, pass an empty array and let the intake agent detect from project files.

**Output:**
```json
{
  "submission_path": "<absolute_path>",
  "boards": ["<detected_board>"],
  "has_prj_conf": true,
  "has_cmake": true,
  "source_files": ["src/main.c", "src/service.c"],
  "kloc": 2.34
}
```

**Error handling:** If intake fails (missing critical files OR no board detected), stop and report to user. Do not proceed to compilability if `boards` is empty.

---

### Phase 2: Compilability Gate

**Spawn:** `compilability-checker` agent

**Input:**
```json
{
  "descriptor": "<full intake descriptor JSON>"
}
```

Pass the full intake descriptor (which contains `boards`) to the compilability checker. The checker iterates all boards in the descriptor.

**Output:**
```json
{
  "compilability_score": 92.5,
  "build_succeeded": true,
  "board_results": [
    {"board": "nrf52840dk_nrf52840", "exit_code": 0, "succeeded": true}
  ]
}
```

**Decision:** If `build_succeeded == false`, mark Resource Efficiency as N/A and run remaining tools in best-effort mode.

---

### Phase 3: Grade via Reviewer Team

Create a team to coordinate all parallel analysis agents and score aggregation. The team-lead manages automated tools and LLM reviewers, handles the compilability gate logic, and returns a single scorecard.

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
  You are the grading team-lead for this Zephyr submission.

  Submission path: {submission_path}
  Intake descriptor: {paste full intake descriptor JSON}
  Compilability result: {paste compilability result JSON}
  Build succeeded: {build_succeeded}

  Your job:
  1. Spawn all grading agents in parallel (one Task call with multiple agents):

     Automated analysis agents (always run):
     - static-analyzer: Input {submission_path, board, build_dir}. Tools: cppcheck, clang-tidy.
     - metrics-collector: Input {submission_path}. Tools: lizard, cloc.
     - style-checker: Input {submission_path, source_files}. Tools: checkpatch.pl.

     Automated analysis agent (skip if build failed):
     - resource-analyzer: Input {descriptor, compilability_result}. Tools: arm-zephyr-eabi-size, bloaty, ram_report, rom_report.

     LLM review agents (always run):
     - zephyr-reviewer: Input {submission_path, source_files}. Reviews 25+ Zephyr correctness patterns.
     - architecture-reviewer: Input {submission_path, source_files}. Reviews code organization, modularity.
     - completeness-checker: Input {submission_path, requirements_spec if available}.

  2. Collect all results (4 automated + 3 LLM = 7 agents, or 6 if build failed)
  3. If any agent fails: retry once, then mark that dimension as N/A
  4. Spawn score-aggregator with all dimension scores, weight_overrides (if provided),
     and na_dimensions list
  5. Send the final scorecard back via SendMessage to the orchestrator

  Weight overrides: {weight_overrides or null}
  If build failed, include "resource_efficiency" in na_dimensions.
```

**Receive scorecard and clean up:**

Wait for the team-lead's message containing the aggregated scorecard.

```
TeamDelete("grading")
```

Proceed to Phase 4 (report generation) with the scorecard.

---

### Phase 4: Report Generation

Compute a timestamped output directory:
```
output_dir = <submission_path>/reports/<YYYY-MM-DD_HH-MM-SS>/
```
Create the directory before spawning the report generator.

**Spawn:** `report-generator` agent

**Input:**
```json
{
  "submission_info": <from intake>,
  "dimension_scores": <from all analyzers>,
  "aggregate": <from aggregator>,
  "output_dir": "<submission_path>/reports/<YYYY-MM-DD_HH-MM-SS>/",
  "output_formats": ["markdown", "json", "html"]
}
```

**Output:**
```json
{
  "markdown_path": "/path/to/reports/2026-02-24_14-30-00/sub001-report.md",
  "json_path": "/path/to/reports/2026-02-24_14-30-00/sub001-report.json",
  "html_path": "/path/to/reports/2026-02-24_14-30-00/sub001-report.html",
  "zip_path": "/path/to/reports/2026-02-24_14-30-00/contents.zip"
}
```

---

### Phase 5: Present Results to User

Display a summary:

```
=== Grading Complete ===

Submission: <path>
Board(s): <boards, comma-separated>
KLOC: <kloc>

Aggregate Score: <score> / 100
Grade: <letter>
Status: <PASS/FAIL>

Top Issues:
1. <issue>
2. <issue>
3. <issue>

Reports: <submission_path>/reports/<YYYY-MM-DD_HH-MM-SS>/contents.zip
  Contains: report.md, report.json, report.html
```

Offer to open the report or provide next steps.

---

## Error Handling

### Tool Availability Errors

If a tool is missing:
1. Log warning: "Tool X not available, marking dimension Y as N/A"
2. Continue with available tools
3. Note in final report which tools were unavailable

### Build Failures

If build fails:
1. Score Compilability based on error type (0-50)
2. Mark Resource Efficiency as N/A
3. Run source-only tools (lizard, cloc, checkpatch, cppcheck --force)
4. Continue with LLM reviews

### Agent Failures

If an agent times out or fails:
1. Retry once
2. If still fails, mark that dimension as N/A
3. Log error in report
4. Continue with other dimensions

### Partial Results

Always generate a report even with partial results. Include a "Warnings" section listing missing dimensions and why.

---

## Parallelism Strategy

### Critical Path

```
Intake (seq) → Compilability (seq) → Grading Team (parallel tools + LLM + aggregation) → Report (seq)
```

### Timing Estimates

- Intake: 5s
- Compilability: 10-30s (build time)
- Automated tools (parallel): 30-60s
- LLM reviews (parallel): 60-120s
- Aggregation: 5s
- Report generation: 10s

**Total: ~2-4 minutes**

---

## Example Invocation

User: "Grade my BLE peripheral submission at ./ble_app for nRF52840DK"

You:
1. Confirm parameters (path, board(s))
2. Spawn intake agent
3. Spawn compilability checker
4. Create grading team — team-lead spawns 7 agents in parallel, aggregates, returns scorecard
5. Spawn report generator
6. Present results with summary and file paths

---

## Advanced Features

### Custom Weight Profiles

If user provides weight overrides, validate:
- All weights sum to 1.0
- All weights in range [0, 1]
- Only recognized dimension names

### Confidence Scoring

For LLM-evaluated dimensions, include confidence scores in the JSON output:
```json
{
  "score": 75,
  "confidence": 0.85,
  "rationale": "..."
}
```

### Diff-Based Grading

If user provides a reference implementation, spawn `diff-analyzer` agent to compare against reference and highlight differences.

---

## Output Guarantees

1. **Always generate JSON scorecard** — machine-readable output for CI/CD
2. **Always include recommendations** — prioritized list of fixes
3. **Always note N/A dimensions** — explain why dimension couldn't be evaluated
4. **Always include tool versions** — for reproducibility

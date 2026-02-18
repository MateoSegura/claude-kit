---
allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Write, Bash
description: Grade a single Zephyr RTOS submission using automated tools and LLM review to generate a comprehensive scorecard
---

# Grade Zephyr Submission

You orchestrate the grading of a single Zephyr RTOS submission by spawning specialized subagents and aggregating their results into a comprehensive report.

## Input Parameters

Accept these parameters from the user (ask if not provided):

1. **submission_path** (required): Path to the submission directory
2. **board** (optional): Target board name (e.g., `nrf52840dk_nrf52840`)
   - If not provided, auto-detect from prj.conf or try common boards
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
  "board": "<board or null>"
}
```

**Output:**
```json
{
  "submission_path": "<absolute_path>",
  "board": "<detected_board>",
  "has_prj_conf": true,
  "has_cmake": true,
  "source_files": ["src/main.c", "src/service.c"],
  "kloc": 2.34
}
```

**Error handling:** If intake fails (missing critical files), stop and report to user.

---

### Phase 2: Compilability Gate

**Spawn:** `compilability-checker` agent

**Input:**
```json
{
  "submission_path": "<path>",
  "board": "<board>"
}
```

**Output:**
```json
{
  "score": 92.5,
  "build_success": true,
  "warnings": 2,
  "errors": 0,
  "details": {
    "warning_list": [...]
  }
}
```

**Decision:** If `build_success == false`, mark Resource Efficiency as N/A and run remaining tools in best-effort mode.

---

### Phase 3: Parallel Automated Analysis

Run these agents **in parallel** using multiple Task calls in a single response:

1. **static-analyzer**
   - Input: `{submission_path, board, build_dir}`
   - Tools: cppcheck, clang-tidy
   - Output: `{score, defect_density, defects: []}`

2. **metrics-collector**
   - Input: `{submission_path}`
   - Tools: lizard, cloc
   - Output: `{score, avg_ccn, max_ccn, kloc}`

3. **resource-analyzer** (skip if build failed)
   - Input: `{submission_path, board, build_dir}`
   - Tools: arm-zephyr-eabi-size, bloaty, ram_report, rom_report
   - Output: `{score, flash_usage, ram_usage, baseline_flash, baseline_ram}`

4. **style-checker**
   - Input: `{submission_path, source_files}`
   - Tools: checkpatch.pl
   - Output: `{score, violations, violations_per_kloc}`

**Wait for all parallel tasks to complete before proceeding.**

---

### Phase 4: Parallel LLM Reviews

Run these agents **in parallel**:

1. **zephyr-reviewer**
   - Input: `{submission_path, source_files}`
   - Reviews: Zephyr correctness patterns (25+ patterns)
   - Output: `{score, issues: [], good_practices: []}`

2. **architecture-reviewer**
   - Input: `{submission_path, source_files}`
   - Reviews: Code organization, separation of concerns, modularity
   - Output: `{score, strengths: [], weaknesses: []}`

3. **completeness-checker**
   - Input: `{submission_path, requirements_spec (if available)}`
   - Reviews: Whether all requirements are implemented
   - Output: `{score, met: [], missing: []}`

**Optional:** If `llm_passes > 1`, run each LLM agent multiple times and average scores for consistency.

**Wait for all parallel tasks to complete before proceeding.**

---

### Phase 5: Score Aggregation

**Spawn:** `score-aggregator` agent

**Input:**
```json
{
  "dimension_scores": {
    "compilability": {score, weight, details},
    "static_analysis": {score, weight, details},
    "zephyr_correctness": {score, weight, details},
    "resource_efficiency": {score, weight, details},
    "architecture": {score, weight, details},
    "code_metrics": {score, weight, details},
    "style": {score, weight, details},
    "completeness": {score, weight, details},
    "documentation": {score, weight, details}
  },
  "weight_overrides": <user_overrides or null>,
  "na_dimensions": ["resource_efficiency"] (if build failed)
}
```

**Output:**
```json
{
  "aggregate_score": 53.35,
  "grade": "F",
  "weighted_scores": {
    "compilability": 18.50,
    ...
  },
  "final_weights": {
    "compilability": 0.20,
    ...
  }
}
```

---

### Phase 6: Report Generation

**Spawn:** `report-generator` agent

**Input:**
```json
{
  "submission_info": <from intake>,
  "dimension_scores": <from all analyzers>,
  "aggregate": <from aggregator>,
  "output_formats": ["markdown", "json", "html"]
}
```

**Output:**
```json
{
  "markdown_path": "/path/to/report.md",
  "json_path": "/path/to/scorecard.json",
  "html_path": "/path/to/report.html"
}
```

---

### Phase 7: Present Results to User

Display a summary:

```
=== Grading Complete ===

Submission: <path>
Board: <board>
KLOC: <kloc>

Aggregate Score: <score> / 100
Grade: <letter>
Status: <PASS/FAIL>

Top Issues:
1. <issue>
2. <issue>
3. <issue>

Reports Generated:
- Markdown: <path>
- JSON: <path>
- HTML: <path>
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
Intake (seq) → Compilability (seq) → {Automated Tools (par), LLM Reviews (par)} → Aggregation (seq) → Report (seq)
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
1. Confirm parameters (path, board)
2. Spawn intake agent
3. Spawn compilability checker
4. Spawn 4 automated agents + 3 LLM agents in parallel (7 total)
5. Wait for all
6. Spawn aggregator
7. Spawn report generator
8. Present results with summary and file paths

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

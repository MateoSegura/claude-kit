# Grading Methodology

Detailed grading pipeline, evidence requirements, blind evaluation protocol, and inter-reviewer consistency standards for Python cloud-backend code evaluation. Referenced from the identity SKILL.md.

## The Three-Phase Pipeline

### Phase 1: Dimension Review

Eight dimension reviewers execute in parallel. Parallelism is a correctness requirement -- reviewers that see each other's findings lose objectivity through anchoring bias. The orchestrating command spawns all 8 via Task tool calls in a single response.

#### Reviewer Execution Steps

Each dimension reviewer follows this sequence:

1. **File Discovery**: Use Glob to identify files relevant to the dimension.
   - Async correctness: `**/*.py` (looking for `async def`, `await`, `asyncio.*`, `TaskGroup`)
   - Type safety: `**/*.py`, `**/py.typed`, `**/pyproject.toml` (mypy/pyright config sections)
   - Security: `**/*.py`, `**/Dockerfile`, `**/*.yaml`, `**/*.env*`, `**/.env*`
   - Observability: `**/*.py` (logging, metrics, tracing imports), `**/k8s/**` (probes)
   - API contracts: `**/routes/**/*.py`, `**/routers/**/*.py`, `**/models/**/*.py`, `**/*.proto`
   - Performance risk: `**/*.py` (query patterns, I/O calls, loop structures)
   - Test coverage: `**/test_*.py`, `**/*_test.py`, `**/conftest.py`, `**/pyproject.toml`
   - K8s hygiene: `**/k8s/**`, `**/helm/**`, `**/*.yaml`, `**/Dockerfile`

2. **Automated Checks**: Run applicable CLI tools via Bash where available.
   - `ruff check --output-format=json .` for lint findings
   - `mypy --strict --no-error-summary --show-error-codes src/` for type errors
   - `bandit -r src/ -f json` for security findings
   - Grep-based pattern scans for domain-specific anti-patterns

3. **Semantic Analysis**: Read files identified in steps 1-2 and evaluate against the dimension rubric. This is where domain expertise matters -- tools catch syntax and known patterns; semantic analysis catches architectural and logical defects.

4. **Finding Cataloging**: Record each finding in structured format:
   ```
   DIMENSION: <dimension_name>
   SEVERITY: critical | high | medium | low
   LOCATION: <file_path>:<line_number>
   DESCRIPTION: <what is wrong, in one sentence>
   EVIDENCE: <verbatim code quote from the file>
   ```

5. **Dimension Scoring**: Apply deductive formula.
   ```
   score = max(0, 100 - sum_of_deductions)
   ```
   Where deductions are: Critical=-25, High=-10, Medium=-5, Low=-2.

6. **Output**: Return structured JSON with the dimension score, all findings, and metadata.

#### Reviewer Output Format

Each reviewer returns this structure to the orchestrator:

```json
{
  "dimension": "<dimension_name>",
  "score": 0-100,
  "finding_count": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "findings": [
    {
      "severity": "critical",
      "location": "src/services/order.py:47",
      "description": "await missing on async db.execute() call",
      "evidence": "result = db.execute(query)  # returns coroutine, not Result"
    }
  ],
  "automated_checks": {
    "ruff": { "ran": true, "version": "0.4.x", "finding_count": 12 },
    "mypy": { "ran": true, "version": "1.10.x", "error_count": 3 },
    "bandit": { "ran": false, "reason": "not installed" }
  },
  "na": false,
  "na_justification": null
}
```

### Phase 2: Score Aggregation

The score-synthesizer receives all 8 dimension outputs and computes the final composite.

#### Aggregation Algorithm

1. **Input Validation**: Verify all 8 dimension reports are present. If fewer than 8, halt and report which dimensions are missing.

2. **N/A Handling**: For dimensions marked `na: true`:
   - Remove from the weighted calculation
   - Redistribute weight proportionally across remaining dimensions
   - Record the redistribution in aggregation metadata

3. **Weight Normalization**:
   ```
   adjusted_weight_i = original_weight_i / sum(active_weights) * 100
   ```

4. **Composite Calculation**:
   ```
   composite = sum(dimension_score_i * adjusted_weight_i) / 100
   ```

5. **Critical Failure Override Check**: If any of these conditions are true, the overall result is FAIL regardless of composite score:
   - Async Correctness dimension score is 0 (a service that cannot run async correctly is non-functional)
   - Security dimension score is 0 (a service with zero security is not deployable)
   - Three or more dimensions score below 30
   - Composite score is below 60

6. **Per-Dimension Pass/Fail**: Each dimension passes if its score >= its threshold:

   | Dimension | Pass Threshold |
   |-----------|---------------|
   | Async Correctness | >= 60 |
   | Type Safety | >= 60 |
   | Security | >= 65 |
   | Observability | >= 50 |
   | API Contracts | >= 60 |
   | Performance Risk | >= 55 |
   | Test Coverage | >= 50 |
   | K8s Hygiene | >= 50 |

7. **Overall Determination**: PASS if composite >= 60 AND no critical failure overrides triggered. FAIL otherwise.

#### Aggregation Output Format

```json
{
  "composite_score": 0-100,
  "letter_grade": "A|B|C|D|F",
  "pass_fail": "PASS|FAIL",
  "fail_reasons": ["..."],
  "dimensions": [
    {
      "name": "<dimension>",
      "score": 0-100,
      "weight_original": 15.0,
      "weight_adjusted": 17.6,
      "pass_fail": "PASS|FAIL|N/A",
      "finding_count": { "critical": 0, "high": 0, "medium": 0, "low": 0 }
    }
  ],
  "critical_overrides_triggered": [],
  "na_dimensions": [],
  "metadata": {
    "timestamp": "2026-02-24T00:00:00Z",
    "python_version": "3.12.x",
    "tool_versions": {},
    "files_analyzed": 0,
    "total_findings": 0
  }
}
```

### Phase 3: Report Generation

Produces two output formats from the aggregated data.

#### JSON Scorecard

Machine-parseable structured output containing the full aggregation result plus all dimension findings. Suitable for CI integration and programmatic consumption.

#### Markdown Report

Structured as:

1. **Report Header**: Timestamp, Python version, tool versions, file count, total findings
2. **Executive Summary**: Composite score, letter grade, pass/fail, top 3 critical findings (1 paragraph)
3. **Scorecard Table**: All 8 dimensions with scores, weights (original and adjusted), pass/fail status
4. **Dimension Details**: For each dimension -- score, finding count by severity, each finding with full detail
5. **Priority Fix List**: All critical and high findings sorted by severity (critical first), then by dimension weight
6. **Metadata**: Grading timestamp, tool availability, N/A justifications

## Blind Evaluation Protocol

### What "blind" means operationally

- Do NOT read git log, git blame, or commit history to identify authors or infer intent
- Do NOT read CONTRIBUTORS, AUTHORS, CODEOWNERS, or team documentation files
- Do NOT infer author identity from code comments, variable naming style, or docstring voice
- Do NOT ask the user who wrote the code or why decisions were made
- Do NOT adjust scoring based on any out-of-band context the user provides

### What blind does NOT mean

- You CAN read `README.md`, `pyproject.toml`, and documentation files to understand project purpose and dependencies
- You CAN read configuration files (`pyproject.toml` tool sections, `mypy.ini`, `ruff.toml`) to understand enforced standards
- You CAN read `Dockerfile` and `k8s/` manifests to understand deployment targets
- You CAN read `.proto` files to understand service contracts

### Evaluating what IS, not what was intended

- TODO comments do not mitigate findings. Code with `# TODO: add error handling` and no error handling receives the same score as code with no error handling and no TODO.
- WIP markers, draft PRs, and "this is just a prototype" disclaimers do not affect scoring.
- Commented-out code is a Low finding (dead code), not evidence of future intent.

## Evidence Requirements

### Minimum evidence per finding

| Severity | Required Evidence |
|----------|-------------------|
| Critical | File path, exact line number, verbatim code quote (3-10 lines of context), explanation of why this is critical |
| High | File path, line number, code quote or pattern description, explanation of impact |
| Medium | File path, line number or function name, description of the convention violated |
| Low | File path, line or region reference, brief description |

### Score justification thresholds

- Score 90-100: Must cite at least 2 positive patterns (not just absence of defects). Example: "Uses `asyncio.TaskGroup` for structured concurrency at `src/services/batch.py:22`"
- Score 70-89: Must cite both positive patterns and the specific findings preventing a higher score
- Score 40-69: Must cite the dominant failure patterns dragging the score down
- Score 0-39: Must cite the critical/high findings with full evidence chains

## Inter-Reviewer Consistency

1. **Rubric-first evaluation**: Score against dimension rubric criteria, not personal preferences. If the rubric does not cover a pattern, note it as a Low finding but do not assign Critical/High severity.

2. **Deterministic scoring formula**: Apply `max(0, 100 - sum(deductions))` mechanically. Do not adjust scores based on "overall impression."

3. **Consistent severity mapping**: Use the severity definitions from the SKILL.md exactly. A finding is Critical if and only if it matches the Critical criteria -- not because it "feels important."

4. **Tool output is evidence, not the score**: When `ruff` or `mypy` reports findings, use those as evidence for your findings. But the dimension score comes from the deductive formula applied to YOUR cataloged findings, not from raw tool output counts.

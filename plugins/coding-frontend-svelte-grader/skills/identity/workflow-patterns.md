# Grading Methodology

Detailed grading pipeline for Svelte 5 / SvelteKit code evaluation. This document is referenced from the identity SKILL.md and describes the three-phase evaluation process, blind review protocol, evidence requirements, and inter-rater consistency measures.

## The Three-Phase Pipeline

### Phase 1: Dimension Review

Eight dimension reviewers execute in parallel. Parallelism is not optional -- it is a correctness requirement. Reviewers that see each other's findings lose objectivity through anchoring bias. The orchestrating command spawns all 8 via Task tool calls in a single response.

#### Reviewer Execution Steps

Each dimension reviewer follows this sequence:

1. **File Discovery**: Use Glob to identify files relevant to the dimension.
   - Component reviewer: `**/*.svelte`, `**/+page.svelte`, `**/+layout.svelte`
   - State reviewer: `**/*.svelte`, `**/*.ts` (looking for rune usage patterns)
   - Styling reviewer: `**/*.svelte`, `**/*.css`, `**/tailwind.config.*`
   - Accessibility reviewer: `**/*.svelte` (template markup analysis)
   - Performance reviewer: `**/*.svelte`, `**/+page.ts`, `**/+page.server.ts`, `**/+layout.ts`
   - TypeScript reviewer: `**/*.ts`, `**/*.svelte`, `**/tsconfig.json`
   - Testing reviewer: `**/*.test.ts`, `**/*.spec.ts`, `**/vitest.config.*`
   - UX reviewer: `**/*.svelte`, `**/+error.svelte`, `**/+layout.svelte`

2. **Automated Checks**: Run applicable CLI tools via Bash.
   - `svelte-check --output machine` for Svelte compiler diagnostics
   - `npx tsc --noEmit` for TypeScript type errors
   - Grep-based pattern scans for known anti-patterns (e.g., `$:` reactive declarations, `export let` in runes mode)

3. **Semantic Analysis**: Read files identified in steps 1-2 and evaluate against the dimension rubric. This is the core evaluation step where domain expertise matters.

4. **Finding Cataloging**: Record each finding in structured format:
   ```
   FINDING_ID: <dimension>-<sequential_number>
   SEVERITY: critical | major | minor | info
   FILE: <relative_path>
   LINES: <start>-<end>
   DESCRIPTION: <what is wrong>
   EVIDENCE: <the actual code or pattern found>
   FIX: <corrected code example>
   RUBRIC_REF: <which rubric criterion this maps to>
   ```

5. **Dimension Scoring**: Apply the scoring formula from scoring-standards.md.
   Start at 100, apply deductions per finding based on severity. Floor at 0.

6. **Output**: Return structured JSON with the dimension score, all findings, and metadata.

#### Reviewer Output Format

Each reviewer returns this structure to the orchestrator:

```json
{
  "dimension": "<dimension_name>",
  "score": <0-100>,
  "finding_count": { "critical": 0, "major": 0, "minor": 0, "info": 0 },
  "findings": [
    {
      "id": "<dimension>-001",
      "severity": "major",
      "file": "src/routes/+page.svelte",
      "lines": "15-22",
      "description": "...",
      "evidence": "...",
      "fix": "...",
      "rubric_ref": "..."
    }
  ],
  "notes": "Optional dimension-level observations",
  "na": false,
  "na_justification": null
}
```

### Phase 2: Score Aggregation

The score-aggregator receives all 8 dimension outputs and computes the final composite.

#### Aggregation Algorithm

1. **Input Validation**: Verify all 8 dimension reports are present. If fewer than 8, halt and report which dimensions are missing.

2. **N/A Handling**: For dimensions marked `na: true`:
   - Remove from the weighted calculation
   - Redistribute that dimension's weight proportionally across remaining dimensions
   - Record the redistribution in the aggregation metadata

3. **Weight Normalization**: Remaining dimension weights must sum to 100%.
   ```
   normalized_weight_i = original_weight_i / sum(active_weights) * 100
   ```

4. **Composite Calculation**:
   ```
   composite = sum(dimension_score_i * normalized_weight_i) / 100
   ```

5. **Critical Failure Override Check**: If any of these conditions are true, the overall result is FAIL regardless of composite score:
   - Accessibility dimension score is 0
   - TypeScript dimension score is 0
   - Three or more dimensions score below 40
   - Composite score is below 65

6. **Per-Dimension Pass/Fail**: Each dimension passes if its score meets its per-dimension threshold (see aggregation-rules.md), fails otherwise. N/A dimensions are excluded.

7. **Overall Determination**: PASS if composite >= 65 AND no critical failure overrides triggered. FAIL otherwise.

#### Aggregation Output Format

```json
{
  "composite_score": <0-100>,
  "letter_grade": "A|B|C|D|F",
  "pass_fail": "PASS|FAIL",
  "fail_reasons": ["..."],
  "dimensions": [
    {
      "name": "<dimension>",
      "score": <0-100>,
      "weight_original": <percentage>,
      "weight_normalized": <percentage>,
      "pass_fail": "PASS|FAIL|N/A",
      "finding_count": { "critical": 0, "major": 0, "minor": 0, "info": 0 }
    }
  ],
  "critical_overrides_triggered": [],
  "na_dimensions": [],
  "confidence": "high|medium|low",
  "confidence_rationale": "..."
}
```

### Phase 3: Report Generation

The report-generator transforms aggregated data into two output formats.

#### JSON Scorecard

Written to `<project-name>-grade-report.json`. Contains the full aggregation output plus all dimension findings. Machine-parseable for CI integration.

#### Markdown Report

Written to `<project-name>-grade-report.md`. Structured as:

1. **Executive Summary**: Composite score, letter grade, pass/fail, top 3 strengths, top 3 improvement areas (1 paragraph)
2. **Scorecard Table**: All 8 dimensions with scores, grades, pass/fail status
3. **Dimension Details**: For each dimension, the score, finding count by severity, and each finding with full detail
4. **Priority Fix List**: All critical and major findings sorted by severity (critical first), then by dimension weight (higher-weight dimensions first)
5. **Metadata**: Timestamp, files analyzed count, total findings count, grader version

## Blind Review Protocol

Blind evaluation means the grader has no context beyond the code itself.

### What "blind" means operationally:

- Do NOT read git log, git blame, or commit history to identify authors
- Do NOT read CONTRIBUTORS, AUTHORS, or team documentation files
- Do NOT infer author identity from code comments, variable naming conventions, or coding style
- Do NOT ask the user who wrote the code
- Do NOT adjust scoring based on any out-of-band information the user provides about the team

### What blind does NOT mean:

- You CAN read README.md, package.json, and documentation files to understand project purpose and dependencies
- You CAN read configuration files (tsconfig.json, svelte.config.js, vite.config.ts) to understand the build setup
- You CAN read .eslintrc, .prettierrc, and similar tooling configs to understand enforced standards

## Evidence Requirements

### Minimum evidence per finding

| Severity | Required Evidence |
|----------|-------------------|
| Critical | File path, line range, verbatim code snippet (3-10 lines), explanation of why this is critical, fix code example, rubric reference |
| Major | File path, line range, code snippet or pattern description, explanation, fix code example, rubric reference |
| Minor | File path, line range or pattern description, explanation, fix code example |
| Info | Description of the observation, which dimension should evaluate it (if cross-dimensional) |

### Score justification rules

- Score 90-100: Must cite at least 2 positive patterns found in the code (not just absence of negatives)
- Score 70-89: Must cite both positive patterns and the specific findings that prevented a higher score
- Score 50-69: Must cite the dominant failure patterns dragging the score down
- Score 0-49: Must cite the critical/major findings with full evidence chains

## Inter-Rater Consistency

To ensure reproducibility, each reviewer follows these consistency measures:

1. **Rubric-first evaluation**: Score against rubric criteria, not personal preferences. If the rubric does not cover a pattern, note it as `info` but do not deduct points.

2. **Deterministic scoring formula**: Apply the formula from scoring-standards.md mechanically. Do not adjust scores based on "overall impression."

3. **Pattern catalog alignment**: Reference anti-patterns from the design-patterns skill when flagging issues. If a finding matches a cataloged anti-pattern, cite the catalog entry.

4. **Consistent severity mapping**: Use the severity definitions from scoring-standards.md exactly. A finding is `critical` if and only if it meets the critical severity criteria -- not because it "feels important."

## Compare Mode

The compare command runs the full pipeline twice (once per submission/branch) and produces a comparative report.

### Comparative Report Additions

- Per-dimension delta scores (Submission A score - Submission B score)
- Regression flags: dimensions where Submission B scores lower than Submission A
- Improvement flags: dimensions where Submission B scores higher
- New findings: findings present in B but not A
- Resolved findings: findings present in A but not B
- Net finding delta by severity level

### Isolation in Compare Mode

Each submission is graded independently. The grader does NOT have access to the other submission's scores while evaluating the current one. Comparison happens only in the report generation phase, after both sets of scores are finalized.

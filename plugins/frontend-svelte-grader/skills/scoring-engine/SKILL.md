---
name: frontend-svelte-grader:scoring-engine
description: "Scoring aggregation rules, weighted composite calculation, N/A dimension redistribution, letter grade mapping, and report format templates (Markdown, JSON, HTML) for the Svelte grader's score-aggregator and report-generator agents."
user-invocable: false
---

# Scoring Engine

Rules and templates used by the `score-aggregator` and `report-generator` agents to compute final scores and produce structured reports.

## Score Aggregation Overview

The scoring pipeline has three stages:

```
Stage 1: Dimension scoring (8 reviewers → 8 raw scores)
Stage 2: Aggregation (score-aggregator → weighted composite)
Stage 3: Report generation (report-generator → markdown + JSON)
```

Each stage is isolated. The score-aggregator receives dimension JSON payloads and produces a normalized scorecard. The report-generator transforms that scorecard into human-readable output.

## Dimension Weights

| Dimension | Weight | Points in Composite |
|-----------|--------|---------------------|
| Component Quality | 15% | 15 |
| State Management | 15% | 15 |
| Styling/CSS | 10% | 10 |
| Accessibility | 15% | 15 |
| Performance | 15% | 15 |
| TypeScript Usage | 10% | 10 |
| Testing Quality | 10% | 10 |
| UX Patterns | 10% | 10 |
| **Total** | **100%** | **100** |

## Grade Mapping

| Composite Score | Letter Grade | Pass/Fail |
|-----------------|--------------|-----------|
| 90-100 | A | Pass |
| 80-89 | B | Pass |
| 70-79 | C | Pass |
| 65-69 | D | Pass (marginal) |
| 50-64 | F | Fail |
| 0-49 | F | Fail |

**Overall pass threshold: 65/100**

## N/A Dimension Handling (Quick Reference)

When a dimension is marked N/A (e.g., no tests exist → Testing Quality is N/A), redistribute its weight proportionally to the remaining dimensions. See `aggregation-rules.md` for the exact redistribution formula and worked examples.

## Critical Failure Overrides

The following conditions force an overall FAIL regardless of composite score:

| Trigger | Override Rule |
|---------|---------------|
| `strict: false` in tsconfig | Override: TypeScript dimension fails; overall forced fail |
| Svelte 4 `$:` declarations in production | Override: State Management dimension fails |
| WCAG 2.2 AA critical barrier (e.g., keyboard trap) | Override: Accessibility dimension forced to ≤ 30 |
| Zero test files in codebase | Override: Testing Quality = 0; overall forced fail |
| Svelte 4 component API in production | Override: Component Quality dimension fails |

Critical overrides are applied BEFORE weight redistribution.

## Dimension Reviewer Output Format (Input to Aggregator)

Each reviewer must emit a JSON payload in this exact structure:

```json
{
  "dimension": "component-quality",
  "score": 74,
  "pass": true,
  "weight": 0.15,
  "critical_failure": false,
  "na": false,
  "na_reason": null,
  "findings": [
    {
      "id": "CQ-001",
      "severity": "major",
      "title": "Component exceeds 300-line limit",
      "file": "src/lib/components/Dashboard.svelte",
      "line": null,
      "evidence": "File is 487 lines",
      "fix_suggestion": "Split into DashboardHeader, DashboardGrid, and DashboardSidebar components"
    }
  ],
  "positive_notes": ["Consistent prop interface patterns", "Good use of snippets"],
  "reviewer": "component-reviewer",
  "confidence": "high"
}
```

## Quick Report Structure

The final report has these sections in order:

1. Executive Summary (score, grade, pass/fail, 3-sentence overview)
2. Dimension Scorecard (table with all 8 scores and weights)
3. Critical Findings (all critical + major findings, cross-dimension)
4. Dimension Details (one section per dimension with findings)
5. Fix Priority List (ordered by impact: critical first, then major)
6. Positive Notes (what the submission does well)

See `report-formats.md` for complete markdown templates, JSON schema, and comparative report template.

## Additional Resources

- **[aggregation-rules.md](aggregation-rules.md)** — Complete aggregation algorithm: N/A weight redistribution formula, critical failure override application order, confidence scoring rules, tie-breaking for borderline cases. Load when computing the composite score.
- **[report-formats.md](report-formats.md)** — Full report templates: markdown grade report template, JSON scorecard schema, comparative report template for compare-mode. Load when generating the output report.

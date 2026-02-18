---
name: coding-embedded-zephyr-grader:report-formats
description: "Output format specifications for grading reports including Markdown scorecard, JSON schema for machine-readable results, HTML comparison tables, and report section structure for single and A/B grading modes."
---

# Report Formats

Reference for generating grading reports in multiple formats: Markdown (human-readable), JSON (machine-readable), and HTML (rich formatting with comparison tables).

## Output Format Overview

| Format | Use Case | Audience | Key Features |
|--------|----------|----------|--------------|
| Markdown | Default output, documentation | Humans | Readable, embeddable in repos |
| JSON | Automation, CI/CD integration | Machines | Structured, queryable |
| HTML | Rich visualization, comparisons | Humans (web) | Tables, charts, styling |

## Scorecard JSON Schema

The canonical machine-readable output format.

### Structure

```json
{
  "version": "1.0",
  "timestamp": "2026-02-16T10:30:00Z",
  "mode": "single",
  "submission": {
    "path": "/path/to/submission",
    "board": "nrf52840dk_nrf52840",
    "kloc": 2.34
  },
  "dimensions": {
    "compilability": {
      "score": 92.5,
      "weight": 0.20,
      "details": { "warnings": 2, "errors": 0 }
    },
    "static_analysis": {
      "score": 0,
      "weight": 0.15,
      "details": { "defect_density": 9.87, "defects": 23 }
    },
    ...
  },
  "aggregate": 53.35,
  "grade": "F",
  "summary": "Functional BLE peripheral but critical code quality issues prevent passing grade."
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version |
| `timestamp` | string (ISO 8601) | When report generated |
| `mode` | enum | "single" or "comparison" |
| `submission.path` | string | Path to submission |
| `submission.board` | string | Target board |
| `submission.kloc` | number | Thousand lines of code |
| `dimensions.<name>.score` | number (0-100) | Dimension score |
| `dimensions.<name>.weight` | number (0-1) | Dimension weight (may be redistributed) |
| `dimensions.<name>.details` | object | Dimension-specific metrics |
| `aggregate` | number (0-100) | Weighted aggregate score |
| `grade` | string | Letter grade (A-F) |
| `summary` | string | Human-readable summary |

## Report Section Structure

### Single Submission Report

1. **Header:** Submission ID, board, timestamp
2. **Summary:** Aggregate score, grade, KLOC
3. **Dimension Scores:** Table with score, weight, grade per dimension
4. **Detailed Findings:** Per-dimension details with tool outputs
5. **Recommendations:** Prioritized fixes
6. **Appendix:** Tool versions, configurations

### A/B Comparison Report

1. **Header:** Comparison ID, board, timestamp
2. **Summary Table:** Side-by-side aggregate scores
3. **Dimension Comparison:** Table with A score, B score, delta, winner
4. **Winner Analysis:** Which submission is better and why
5. **Per-Submission Details:** Individual scorecards for A and B
6. **Recommendations:** For each submission

## Additional Resources

For complete templates and examples:

- [templates-reference.md](templates-reference.md) — Full Markdown template with per-dimension sections, JSON complete schema, HTML template with CSS for comparison tables, styling guidelines
- [examples.md](examples.md) — Complete example reports for single submission (passing and failing) and A/B comparison with annotations explaining each section

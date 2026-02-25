# Aggregation Rules — Complete Algorithm

The score-aggregator receives 8 dimension JSON payloads and produces a normalized scorecard. This document specifies the complete algorithm.

---

## Input Contract

The aggregator receives an array of 8 dimension payloads. Each payload conforms to this schema (see `report-formats.md` for the full schema):

```json
{
  "dimension": "component-quality",
  "score": 74,
  "pass": true,
  "weight": 0.15,
  "critical_failure": false,
  "na": false,
  "na_reason": null,
  "findings": [...],
  "positive_notes": [...],
  "reviewer": "component-reviewer",
  "confidence": "high"
}
```

**Dimension identifiers:**

| Agent | `dimension` value | Weight |
|-------|------------------|--------|
| component-reviewer | `component-quality` | 0.15 |
| state-reviewer | `state-management` | 0.15 |
| styling-reviewer | `styling-css` | 0.10 |
| a11y-reviewer | `accessibility` | 0.15 |
| performance-reviewer | `performance` | 0.15 |
| typescript-reviewer | `typescript-usage` | 0.10 |
| testing-reviewer | `testing-quality` | 0.10 |
| ux-reviewer | `ux-patterns` | 0.10 |

---

## Aggregation Algorithm

### Step 1: Apply Critical Failure Overrides

Before computing any scores, scan all 8 payloads for `critical_failure: true`.

```
for each payload in payloads:
  if payload.critical_failure == true:
    set overall_critical_failure = true
    # Score already set by reviewer; do not modify
```

If `overall_critical_failure` is true, the final result will be `pass: false` regardless of composite score. Record which dimensions have critical failures.

### Step 2: Separate Active from N/A Dimensions

```
active_dimensions = payloads where na == false
na_dimensions = payloads where na == true
```

Validate: `active_dimensions` should have at least 5 dimensions. If fewer than 5 active dimensions, log a warning — this is unusual and may indicate a reviewer error.

### Step 3: Redistribute N/A Weights

For each N/A dimension, redistribute its weight proportionally to the active dimensions.

```
total_na_weight = sum(d.weight for d in na_dimensions)
total_active_weight = sum(d.weight for d in active_dimensions)  # Should equal 1.0 - total_na_weight

for each active_dim in active_dimensions:
  redistribution_share = active_dim.weight / total_active_weight
  active_dim.effective_weight = active_dim.weight + (total_na_weight * redistribution_share)
```

**Verification:** `sum(effective_weight for all active dims)` must equal 1.0. If not, there is a calculation error — log and abort.

**Example: Testing Quality marked N/A (weight 0.10)**

Original weights: CQ=0.15, SM=0.15, CSS=0.10, A11Y=0.15, PERF=0.15, TS=0.10, TQ=0.10(NA), UX=0.10
Total active weight: 0.90

Each active dimension gains: original_weight / 0.90 * 0.10 extra weight

| Dimension | Original | Effective |
|-----------|----------|-----------|
| Component Quality | 0.15 | 0.15 + (0.15/0.90 × 0.10) = 0.1667 |
| State Management | 0.15 | 0.1667 |
| Styling/CSS | 0.10 | 0.10 + (0.10/0.90 × 0.10) = 0.1111 |
| Accessibility | 0.15 | 0.1667 |
| Performance | 0.15 | 0.1667 |
| TypeScript Usage | 0.10 | 0.1111 |
| Testing Quality | N/A | — |
| UX Patterns | 0.10 | 0.1111 |
| **Sum** | **0.90** | **1.0000** |

### Step 4: Compute Weighted Composite Score

```
composite_score = sum(dim.score * dim.effective_weight for dim in active_dimensions)
composite_score = round(composite_score, 1)
```

### Step 5: Determine Pass/Fail Per Dimension

Each active dimension passes or fails independently based on its raw score (not weighted):

```
for each active_dim in active_dimensions:
  active_dim.pass = active_dim.score >= dimension_pass_threshold[active_dim.dimension]
```

**Per-dimension pass thresholds:**

| Dimension | Threshold |
|-----------|-----------|
| component-quality | 60 |
| state-management | 60 |
| styling-css | 55 |
| accessibility | 70 |
| performance | 60 |
| typescript-usage | 60 |
| testing-quality | 50 |
| ux-patterns | 55 |

### Step 6: Determine Overall Pass/Fail

```
if overall_critical_failure == true:
  overall_pass = false
  override_reason = list of dimensions with critical_failure: true
else if composite_score < 65:
  overall_pass = false
  override_reason = "Composite score below 65 threshold"
else:
  overall_pass = true
  override_reason = null
```

Note: Individual dimension failures do NOT automatically cause overall failure unless they trigger a critical failure override. A codebase can fail 1-2 non-critical dimensions and still achieve an overall pass if the composite score is ≥ 65.

### Step 7: Assign Letter Grade

```
if composite_score >= 90: letter_grade = "A"
elif composite_score >= 80: letter_grade = "B"
elif composite_score >= 70: letter_grade = "C"
elif composite_score >= 65: letter_grade = "D"
else: letter_grade = "F"

if overall_pass == false: letter_grade = "F"  # Override
```

### Step 8: Compute Confidence Score

The confidence score indicates how reliable the grade is, based on the amount of evidence gathered.

```
confidence_factors = []
for each active_dim:
  if active_dim.confidence == "high": confidence_factors.append(1.0)
  elif active_dim.confidence == "medium": confidence_factors.append(0.7)
  else (low): confidence_factors.append(0.4)

confidence_score = average(confidence_factors)
```

**Confidence level thresholds:**

| Score | Label |
|-------|-------|
| ≥ 0.85 | high |
| ≥ 0.65 | medium |
| < 0.65 | low |

A `low` overall confidence should be noted in the report executive summary.

**Reviewer confidence guidelines:**
- `high`: Reviewed ≥ 5 component files, found both passing and failing evidence, findings are specific
- `medium`: Reviewed 2-4 files, some areas not fully assessed
- `low`: Reviewed < 2 files, or project was too small/large to assess thoroughly

---

## Aggregator Output Schema

```json
{
  "scorecard": {
    "composite_score": 76.4,
    "letter_grade": "C",
    "pass": true,
    "critical_failure": false,
    "override_reason": null,
    "confidence": "high",
    "confidence_score": 0.91,
    "graded_at": "2025-11-15T14:23:00Z",
    "dimensions": [
      {
        "dimension": "component-quality",
        "score": 74,
        "effective_weight": 0.15,
        "pass": true,
        "critical_failure": false,
        "na": false,
        "na_reason": null,
        "finding_counts": {
          "critical": 0,
          "major": 1,
          "minor": 4,
          "info": 2
        }
      }
    ],
    "na_dimensions": [
      {
        "dimension": "testing-quality",
        "na_reason": "No vitest.config.ts found. Project has no testing infrastructure configured.",
        "redistributed_weight": 0.10
      }
    ],
    "dimension_findings": {
      "component-quality": [...],
      "state-management": [...],
      "styling-css": [...],
      "accessibility": [...],
      "performance": [...],
      "typescript-usage": [...],
      "testing-quality": "N/A",
      "ux-patterns": [...]
    },
    "positive_notes": {
      "component-quality": [...],
      "state-management": [...]
    }
  }
}
```

---

## Borderline Case Handling

### Tied Dimensions (exactly at threshold)

A score exactly at the pass threshold (e.g., accessibility = 70) passes. Thresholds are inclusive.

### Missing Reviewer Output

If a dimension reviewer fails to produce output:

1. Log the missing dimension
2. Do NOT mark it N/A — N/A requires explicit evidence that the dimension is inapplicable
3. Set `confidence: "low"` for the missing dimension
4. Assign a provisional score based on available evidence (e.g., if only partial files were reviewed)
5. Note the missing dimension prominently in the report with `"incomplete_review": true`

### Inconsistent Weights

If reviewer payloads report weights that don't sum to 1.0, use the canonical weights from Step 3 above and log a discrepancy warning. Do NOT trust reviewer-reported weights for the composite calculation.

### Small Codebase

For codebases with fewer than 5 Svelte component files:
- Lower confidence for all dimensions to at most `medium`
- Note in the report: "Grade confidence is reduced due to small codebase size (< 5 components). Grade reflects visible patterns; wider patterns may not be detectable."

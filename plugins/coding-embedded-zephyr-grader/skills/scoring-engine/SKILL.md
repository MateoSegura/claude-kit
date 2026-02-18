---
name: coding-embedded-zephyr-grader:scoring-engine
description: "Scoring pipeline algorithms for normalizing raw tool outputs to 0-100 scores including per-KLOC normalization, weighted deduplication, severity weights, and N/A dimension handling."
---

# Scoring Engine

Reference for the algorithms that transform raw tool outputs into normalized 0-100 scores and aggregate them into final grades.

## Scoring Pipeline Overview

```
Raw Tool Output
    ↓
Parse & Extract Metrics
    ↓
Apply Severity Weights
    ↓
Deduplicate Defects
    ↓
Normalize Per-KLOC
    ↓
Map to 0-100 Score
    ↓
Apply Dimension Weight
    ↓
Aggregate with N/A Handling
    ↓
Final Grade (0-100)
```

## Per-KLOC Normalization

All count-based metrics are normalized per thousand lines of code for fair comparison across submissions of different sizes.

### Algorithm

```
KLOC = lines_of_code / 1000
metric_density = metric_count / KLOC
```

### Line Counting Rules

- Use `cloc` to count source code lines
- Exclude blank lines and comments
- Include: `.c`, `.h` files
- Exclude: generated files, vendor code, build artifacts
- Exclude: test files (unless grading test quality)

### Example

```
Lines of code: 3,420
Static analysis warnings: 18

KLOC = 3420 / 1000 = 3.42
warnings_per_kloc = 18 / 3.42 = 5.26
```

## Weighted Deduplication

When the same defect appears multiple times, use weighted deduplication to avoid over-penalization.

### Formula

```
weighted_count = 1.0 + (repeat_count × 0.1)

First occurrence: weight = 1.0
Each repeat: weight = 0.1
```

### Example

```
Defect: "Uninitialized variable"
Occurrences: 8 times

Without dedup: count = 8
With dedup: count = 1.0 + (7 × 0.1) = 1.7
```

## Severity Weight Table

| Severity | Weight | Tool Examples |
|----------|--------|---------------|
| error | 10.0 | cppcheck error, clang-tidy error |
| warning | 3.0 | cppcheck warning, clang-tidy warning |
| style | 1.0 | checkpatch style, clang-tidy readability |
| performance | 1.0 | clang-tidy performance |
| portability | 0.5 | cppcheck portability |
| information | 0.5 | cppcheck information |
| note | 0.1 | clang-tidy note |

## N/A Dimension Handling

When a dimension cannot be evaluated, redistribute its weight proportionally.

### Rules

1. Identify N/A dimensions (e.g., Resource Efficiency when build fails)
2. Sum weights of available dimensions
3. Calculate redistribution factor: `1.0 / available_sum`
4. Multiply each available dimension's weight by the factor
5. Set N/A dimension weights to 0

### Example

```
Original: Completeness 5%, remaining 95%
Available sum: 0.95
Redistribution factor: 1.0 / 0.95 = 1.0526
New weights: each dimension × 1.0526
```

## Quick Reference: Score Mapping

| Dimension | Formula | Threshold for 0 Score |
|-----------|---------|----------------------|
| Static Analysis | `100 - (density / 2.0) × 100` | ≥2.0 defects/KLOC |
| Code Metrics (CCN) | `100 - penalty_sum` | Avg CCN >30 |
| Style | `100 - (violations/KLOC / 5.0) × 100` | ≥5 violations/KLOC |
| Resource Efficiency | `100 - ((ratio - 0.5) × 200)` | ≥150% of baseline |

## Additional Resources

For detailed normalization formulas, aggregation examples, and worked calculations:

- [normalization-reference.md](normalization-reference.md) — Complete formulas for each dimension with defect density curves, CCN penalty calculations, resource efficiency curves, threshold calibration, and edge case handling
- [aggregation-examples.md](aggregation-examples.md) — Worked examples showing raw tool output → parsing → normalization → weighting → final score for both single submission and A/B comparison modes

# Scoring Formulas

Mathematical formulas and algorithms for computing scores in automated grading dimensions.

## Severity Weight System

Static analysis tools report defects with varying severity levels. Each severity has a weight that reflects its impact on code quality.

### Weight Table

| Severity | Weight | Rationale |
|----------|--------|-----------|
| error | 10.0 | Critical issues: memory leaks, null dereferences, buffer overflows, undefined behavior |
| warning | 3.0 | Significant issues: uninitialized variables, suspicious constructs, potential bugs |
| style | 1.0 | Code quality issues: naming, formatting, conventions |
| performance | 1.0 | Optimization opportunities: inefficient patterns, unnecessary copies |
| portability | 0.5 | Platform-specific code, non-standard extensions |
| information | 0.5 | Informational messages, suggestions |
| note | 0.1 | Context information, related locations for other messages |

### Weighted Defect Count Formula

```
weighted_defects = Σ (count[severity] × weight[severity])
                 = (errors × 10.0) + (warnings × 3.0) + (style × 1.0) +
                   (performance × 1.0) + (portability × 0.5) + (information × 0.5) + (notes × 0.1)
```

Example calculation:
```
Errors: 2
Warnings: 5
Style: 10
Notes: 3

weighted_defects = (2 × 10.0) + (5 × 3.0) + (10 × 1.0) + (3 × 0.1)
                 = 20.0 + 15.0 + 10.0 + 0.3
                 = 45.3
```

---

## Per-KLOC Normalization

To compare submissions of different sizes fairly, defects are normalized per thousand lines of code (KLOC).

### Formula

```
KLOC = lines_of_code / 1000
defect_density = weighted_defects / KLOC
```

### Lines of Code Counting

Use `cloc` with these rules:
- Count only source code lines (exclude blanks and comments)
- Include: `.c`, `.h` files
- Exclude: generated files, vendor code, Zephyr SDK headers
- Exclude: test files (unless grading test quality)

```bash
cloc --json --by-file --exclude-dir=build,zephyr <submission_path>
```

### Example

```
Lines of code: 2,340
Weighted defects: 45.3

KLOC = 2340 / 1000 = 2.34
defect_density = 45.3 / 2.34 = 19.36 defects/KLOC
```

---

## Static Analysis Score Formula

Defect density maps to a 0-100 score using a calibrated curve.

### Formula

```
score = max(0, 100 - (defect_density / 2.0) × 100)
score = clamp(score, 0, 100)
```

### Score Thresholds

| Defect Density | Score | Grade |
|----------------|-------|-------|
| 0.0 | 100 | Perfect |
| 0.5 | 75 | Good |
| 1.0 | 50 | Acceptable |
| 2.0 | 0 | Failing |
| >2.0 | 0 | Failing |

### Example

```
defect_density = 19.36 / 2.34 = 8.27 defects/KLOC

score = 100 - (8.27 / 2.0) × 100
      = 100 - 413.5
      = -313.5
      = max(0, -313.5)
      = 0
```

---

## Cyclomatic Complexity Scoring

CCN (Cyclomatic Complexity Number) measures code complexity. Lower is better.

### Per-Function CCN Thresholds

| CCN Range | Complexity | Impact |
|-----------|------------|--------|
| 1-10 | Simple | No penalty |
| 11-15 | Moderate | Minor penalty |
| 16-20 | Complex | Medium penalty |
| 21-30 | Very complex | Large penalty |
| 31+ | Extremely complex | Maximum penalty |

### Scoring Formula

```
penalty[function] = max(0, (CCN[function] - 10) × penalty_factor)

penalty_factor by range:
  CCN ≤ 10:  penalty = 0
  CCN 11-15: penalty = (CCN - 10) × 1.0
  CCN 16-20: penalty = (CCN - 10) × 2.0
  CCN 21-30: penalty = (CCN - 10) × 3.0
  CCN > 30:  penalty = (CCN - 10) × 5.0

total_penalty = Σ penalty[function]
score = max(0, 100 - total_penalty)
```

### Example

```
Function A: CCN = 8  → penalty = 0
Function B: CCN = 18 → penalty = (18 - 10) × 2.0 = 16
Function C: CCN = 35 → penalty = (35 - 10) × 5.0 = 125

total_penalty = 0 + 16 + 125 = 141
score = max(0, 100 - 141) = 0
```

### Average CCN Approach (Alternative)

For a gentler scoring curve:

```
avg_ccn = Σ CCN[function] / function_count
max_ccn = max(CCN[function])

avg_score = 100 - (max(0, avg_ccn - 10) / 20) × 100
max_score = 100 - (max(0, max_ccn - 15) / 25) × 100

score = (avg_score × 0.7) + (max_score × 0.3)
```

---

## Resource Efficiency Scoring

Compares submission size to a reference baseline.

### Formula

```
efficiency_ratio = submission_size / baseline_size
normalized_ratio = efficiency_ratio - 0.5

score = 100 - (normalized_ratio × 200)
score = clamp(score, 0, 100)
```

### Rationale

- If submission is 50% of baseline (0.5×), score = 100
- If submission equals baseline (1.0×), score = 0
- If submission is 150% of baseline (1.5×), score = 0

This rewards efficiency while accepting baseline performance.

### Example

```
Baseline flash: 128 KB
Submission flash: 96 KB

efficiency_ratio = 96 / 128 = 0.75
normalized_ratio = 0.75 - 0.5 = 0.25

score = 100 - (0.25 × 200)
      = 100 - 50
      = 50
```

### Combined Flash + RAM Score

```
flash_score = calculate_efficiency(submission_flash, baseline_flash)
ram_score = calculate_efficiency(submission_ram, baseline_ram)

score = (flash_score × 0.6) + (ram_score × 0.4)
```

Flash is weighted higher because embedded systems are typically more flash-constrained.

---

## Style Violations Per-KLOC

Checkpatch.pl violations are normalized per KLOC.

### Formula

```
KLOC = lines_of_code / 1000
violations_per_kloc = violation_count / KLOC

score = max(0, 100 - (violations_per_kloc / 5.0) × 100)
score = clamp(score, 0, 100)
```

### Score Thresholds

| Violations/KLOC | Score |
|-----------------|-------|
| 0 | 100 |
| 1 | 80 |
| 3 | 40 |
| 5 | 0 |
| >5 | 0 |

### Example

```
Violations: 47
KLOC: 2.34

violations_per_kloc = 47 / 2.34 = 20.09

score = 100 - (20.09 / 5.0) × 100
      = 100 - 401.8
      = max(0, -301.8)
      = 0
```

---

## N/A Weight Redistribution Algorithm

When a dimension cannot be evaluated, its weight is redistributed proportionally across remaining dimensions.

### Algorithm

```python
def redistribute_weights(weights: dict[str, float], na_dimensions: set[str]) -> dict[str, float]:
    """
    Redistribute weights from N/A dimensions to available dimensions.

    Args:
        weights: Original weight dictionary (dimension -> weight)
        na_dimensions: Set of dimension names that are N/A

    Returns:
        New weight dictionary with redistributed weights
    """
    # Calculate sum of available weights
    available_sum = sum(w for dim, w in weights.items() if dim not in na_dimensions)

    # Calculate redistribution factor
    redistribution_factor = 1.0 / available_sum

    # Redistribute weights
    new_weights = {}
    for dim, weight in weights.items():
        if dim in na_dimensions:
            new_weights[dim] = 0.0
        else:
            new_weights[dim] = weight * redistribution_factor

    return new_weights
```

### Example

```
Original weights:
  Compilability: 20%
  Static Analysis: 15%
  Zephyr Correctness: 15%
  Resource Efficiency: 15%
  Architecture: 10%
  Code Metrics: 10%
  Style: 5%
  Completeness: 5%  (N/A)
  Documentation: 5%

Available sum: 95%
Redistribution factor: 1.0 / 0.95 = 1.0526

New weights:
  Compilability: 20% × 1.0526 = 21.05%
  Static Analysis: 15% × 1.0526 = 15.79%
  Zephyr Correctness: 15% × 1.0526 = 15.79%
  Resource Efficiency: 15% × 1.0526 = 15.79%
  Architecture: 10% × 1.0526 = 10.53%
  Code Metrics: 10% × 1.0526 = 10.53%
  Style: 5% × 1.0526 = 5.26%
  Completeness: 0%
  Documentation: 5% × 1.0526 = 5.26%

Total: 100%
```

---

## Weighted Deduplication Formula

When the same defect appears multiple times (e.g., same cppcheck error in multiple files), use weighted deduplication to avoid over-penalization.

### Formula

```
weighted_count = first_occurrence + (repeat_count × repeat_weight)

first_occurrence = 1.0
repeat_weight = 0.1
```

### Rationale

The first occurrence is a real issue. Subsequent occurrences indicate a pattern but shouldn't multiply the penalty linearly.

### Example

```
Defect: "Uninitialized variable 'x'"
Occurrences: 12 times across 12 functions

Without deduplication:
  weighted_defects = 12 × 3.0 (warning) = 36.0

With deduplication:
  weighted_count = 1.0 + (11 × 0.1) = 2.1
  weighted_defects = 2.1 × 3.0 = 6.3
```

### Implementation

```python
def deduplicate_defects(defects: list[dict]) -> float:
    """
    Calculate weighted defect count with deduplication.

    Args:
        defects: List of defect dicts with 'message', 'severity', 'file', 'line'

    Returns:
        Weighted defect count
    """
    from collections import Counter

    severity_weights = {
        'error': 10.0,
        'warning': 3.0,
        'style': 1.0,
        'performance': 1.0,
        'portability': 0.5,
        'information': 0.5,
        'note': 0.1
    }

    # Group by (message, severity) tuple
    defect_groups = Counter((d['message'], d['severity']) for d in defects)

    total_weighted = 0.0
    for (message, severity), count in defect_groups.items():
        weight = severity_weights.get(severity, 1.0)

        if count == 1:
            total_weighted += weight
        else:
            # First occurrence + repeats with reduced weight
            total_weighted += weight * (1.0 + (count - 1) * 0.1)

    return total_weighted
```

---

## Aggregate Score Calculation

The final aggregate score combines all dimension scores with their weights.

### Formula

```
aggregate_score = Σ (dimension_score[i] × dimension_weight[i])
                  for all i where dimension_score[i] is not N/A

with weights redistributed if any dimension is N/A
```

### Example (No N/A Dimensions)

```
Compilability: 100 × 0.20 = 20.0
Static Analysis: 45 × 0.15 = 6.75
Zephyr Correctness: 75 × 0.15 = 11.25
Resource Efficiency: 50 × 0.15 = 7.5
Architecture: 80 × 0.10 = 8.0
Code Metrics: 60 × 0.10 = 6.0
Style: 40 × 0.05 = 2.0
Completeness: 90 × 0.05 = 4.5
Documentation: 70 × 0.05 = 3.5

aggregate_score = 69.5 (C grade)
```

### Example (Completeness N/A)

```
Redistributed weights:
  Compilability: 21.05%
  Static Analysis: 15.79%
  Zephyr Correctness: 15.79%
  Resource Efficiency: 15.79%
  Architecture: 10.53%
  Code Metrics: 10.53%
  Style: 5.26%
  Completeness: 0%
  Documentation: 5.26%

Compilability: 100 × 0.2105 = 21.05
Static Analysis: 45 × 0.1579 = 7.11
Zephyr Correctness: 75 × 0.1579 = 11.84
Resource Efficiency: 50 × 0.1579 = 7.90
Architecture: 80 × 0.1053 = 8.42
Code Metrics: 60 × 0.1053 = 6.32
Style: 40 × 0.0526 = 2.10
Completeness: N/A
Documentation: 70 × 0.0526 = 3.68

aggregate_score = 68.42 (D grade)
```

---

## Compilation Failure Handling

When code doesn't compile, most automated tools cannot run. Use these fallback formulas:

### Compilability Score

```
if build_successful:
    score = 100 - (warning_count × warning_penalty)
else:
    score = partial_credit_by_error_type()
```

### Partial Credit by Error Type

| Error Type | Score | Rationale |
|------------|-------|-----------|
| Missing file (prj.conf, CMakeLists.txt) | 0 | Critical structural issue |
| Syntax errors | 10 | Code is incomplete |
| Undefined symbols | 25 | Most code present, missing dependencies |
| Linker errors | 40 | Code compiles, linking issues |
| Board-specific errors | 50 | May build on different board |

### Downstream Dimension Handling

| Dimension | Handling if Non-Compiling |
|-----------|---------------------------|
| Static Analysis | Run best-effort with available files, or mark N/A |
| Zephyr Correctness | LLM review can still proceed, check for obvious issues |
| Resource Efficiency | Mark N/A |
| Architecture | LLM review can still proceed |
| Code Metrics | Run on source files (lizard doesn't need compilation) |
| Style | Run on source files (checkpatch doesn't need compilation) |
| Completeness | LLM review can assess what's present |
| Documentation | LLM review can assess documentation quality |

---

## Confidence Scoring

For LLM-evaluated dimensions, include a confidence score based on submission completeness.

### Formula

```
confidence = base_confidence × completeness_factor × documentation_factor

base_confidence = 0.8 (LLM inherent uncertainty)
completeness_factor = 1.0 if all files present, 0.5 if partial
documentation_factor = 1.0 if documented, 0.7 if not
```

### Example

```
Submission: All files present, no documentation
confidence = 0.8 × 1.0 × 0.7 = 0.56

Report: "Architecture score: 75 (confidence: 56%)"
```

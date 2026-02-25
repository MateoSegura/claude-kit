# Normalization Reference

Detailed normalization formulas with worked examples, defect density curves, threshold calibration, and edge case handling.

## Static Analysis Normalization

Converts weighted defect counts to a 0-100 score using defect density (defects per KLOC).

### Step-by-Step Process

1. **Count defects by severity**
   ```
   errors: 3
   warnings: 12
   style: 25
   notes: 8
   ```

2. **Apply severity weights**
   ```
   weighted_errors = 3 × 10.0 = 30.0
   weighted_warnings = 12 × 3.0 = 36.0
   weighted_style = 25 × 1.0 = 25.0
   weighted_notes = 8 × 0.1 = 0.8
   total_weighted = 91.8
   ```

3. **Apply deduplication**
   ```
   Group identical defects:
     "Uninitialized variable 'x'": 8 occurrences
     "Memory leak": 2 occurrences
     Other unique defects: 15 occurrences

   Dedup weights:
     "Uninitialized variable 'x'": 1.0 + (7 × 0.1) = 1.7
     "Memory leak": 1.0 + (1 × 0.1) = 1.1
     Other: 15 × 1.0 = 15.0
     Total dedup factor: 17.8 / 25 = 0.712

   adjusted_weighted = 91.8 × 0.712 = 65.36
   ```

4. **Normalize per KLOC**
   ```
   KLOC = 2340 lines / 1000 = 2.34
   defect_density = 65.36 / 2.34 = 27.93 defects/KLOC
   ```

5. **Map to 0-100 score**
   ```
   score = 100 - (defect_density / 2.0) × 100
         = 100 - (27.93 / 2.0) × 100
         = 100 - 1396.5
         = max(0, -1296.5)
         = 0
   ```

### Defect Density Curve

| Defect Density | Score | Interpretation |
|----------------|-------|----------------|
| 0.0 | 100 | Perfect — no defects |
| 0.25 | 87.5 | Excellent |
| 0.5 | 75 | Good |
| 0.75 | 62.5 | Acceptable |
| 1.0 | 50 | Marginal |
| 1.5 | 25 | Poor |
| 2.0 | 0 | Failing |
| >2.0 | 0 | Failing |

### Calibration Rationale

The threshold of 2.0 defects/KLOC for a failing grade is based on industry research:
- High-quality embedded code: <0.5 defects/KLOC
- Acceptable code: 0.5-1.0 defects/KLOC
- Poor code: 1.0-2.0 defects/KLOC
- Unacceptable: >2.0 defects/KLOC

---

## Code Metrics (CCN) Normalization

Cyclomatic Complexity Number (CCN) measures the number of linearly independent paths through code. Higher CCN = more complex = harder to test and maintain.

### Step-by-Step Process

1. **Extract CCN per function**
   ```
   main(): 8
   process_data(): 22
   handle_error(): 15
   init_device(): 6
   ```

2. **Calculate penalties by threshold**
   ```
   Penalty schedule:
     CCN ≤ 10: no penalty
     CCN 11-15: (CCN - 10) × 1.0
     CCN 16-20: (CCN - 10) × 2.0
     CCN 21-30: (CCN - 10) × 3.0
     CCN > 30: (CCN - 10) × 5.0

   main(): CCN=8, penalty=0
   process_data(): CCN=22, penalty=(22-10)×3.0 = 36
   handle_error(): CCN=15, penalty=(15-10)×1.0 = 5
   init_device(): CCN=6, penalty=0

   total_penalty = 41
   ```

3. **Map to 0-100 score**
   ```
   score = max(0, 100 - total_penalty)
         = max(0, 100 - 41)
         = 59
   ```

### CCN Thresholds

| Average CCN | Max CCN | Score | Interpretation |
|-------------|---------|-------|----------------|
| <10 | <15 | 100 | Simple, easy to test |
| <15 | <20 | 75-90 | Moderate, acceptable |
| <20 | <30 | 50-75 | Complex, needs refactoring |
| <30 | <40 | 25-50 | Very complex, risky |
| ≥30 | ≥40 | 0-25 | Extremely complex, unmaintainable |

### Alternative: Average CCN Formula

For a smoother penalty curve:

```
avg_ccn = Σ CCN / function_count
max_ccn = max(CCN)

avg_score = 100 - (max(0, avg_ccn - 10) / 20) × 100
max_score = 100 - (max(0, max_ccn - 15) / 25) × 100

final_score = (avg_score × 0.7) + (max_score × 0.3)
```

Example:
```
Functions: 4
CCNs: 8, 22, 15, 6
avg_ccn = (8+22+15+6) / 4 = 12.75
max_ccn = 22

avg_score = 100 - (max(0, 12.75-10) / 20) × 100
          = 100 - (2.75 / 20) × 100
          = 100 - 13.75
          = 86.25

max_score = 100 - (max(0, 22-15) / 25) × 100
          = 100 - (7 / 25) × 100
          = 100 - 28
          = 72

final_score = (86.25 × 0.7) + (72 × 0.3)
            = 60.375 + 21.6
            = 81.975
            ≈ 82
```

---

## Resource Efficiency Normalization

Measures flash (ROM) and RAM utilization against the board's actual hardware capacity, determined dynamically from build artifacts.

### Step-by-Step Process

1. **Extract actual sizes from build output**
   ```
   $ arm-zephyr-eabi-size build/zephyr/zephyr.elf
      text    data     bss     dec     hex filename
     98304    2048   10240  110592   1b000 build/zephyr/zephyr.elf

   actual_flash = text + data = 98304 + 2048 = 100,352 bytes
   actual_ram   = data + bss  = 2048 + 10240 = 12,288 bytes
   ```

2. **Determine board capacity from build artifacts (in priority order)**
   ```
   Priority 1: <build_dir>/zephyr/.config
     CONFIG_FLASH_SIZE=1024   → flash_capacity = 1024 × 1024 = 1,048,576 bytes
     CONFIG_SRAM_SIZE=256     → ram_capacity   = 256  × 1024 =   262,144 bytes

   Priority 2: <build_dir>/zephyr/zephyr.dts
     flash0: flash@0 { reg = <0x0 0x100000>; }   → flash_capacity = 1,048,576 bytes
     sram0: memory@20000000 { reg = <0x20000000 0x40000>; } → ram_capacity = 262,144 bytes

   Priority 3: Board YAML from Zephyr SDK boards directory
     flash: 1024   → flash_capacity = 1,048,576 bytes
     ram:   256    → ram_capacity   =   262,144 bytes

   If capacity cannot be determined by any method: mark dimension as N/A
   ```

3. **Calculate capacity utilization percentages**
   ```
   flash_pct = actual_flash / flash_capacity * 100
             = 100352 / 1048576 * 100
             = 9.57%

   ram_pct   = actual_ram / ram_capacity * 100
             = 12288 / 262144 * 100
             = 4.69%
   ```

4. **Map to 0-100 scores (lower utilization = higher score)**
   ```
   flash_score = max(0.0, 100.0 - flash_pct)
               = max(0.0, 100.0 - 9.57)
               = 90.43

   ram_score   = max(0.0, 100.0 - ram_pct)
               = max(0.0, 100.0 - 4.69)
               = 95.31
   ```

5. **50/50 weighted combination**
   ```
   resource_score = 0.5 * flash_score + 0.5 * ram_score
                  = 0.5 * 90.43 + 0.5 * 95.31
                  = 45.22 + 47.66
                  = 92.88
                  ≈ 93
   ```

### Resource Efficiency Curve

| Flash/RAM Utilization | Score | Interpretation |
|-----------------------|-------|----------------|
| <10% | ~90-100 | Exceptional — minimal use of board capacity |
| 25% | 75 | Very efficient |
| 50% | 50 | Moderate utilization |
| 75% | 25 | Heavy utilization |
| 100% | 0 | At capacity limit |
| >100% | 0 | Exceeds capacity (build would fail) |

### Flash vs RAM Weighting

Flash and RAM are weighted equally at 50% each. Both resources matter for embedded deployability: flash determines if the firmware fits on the device, and RAM determines runtime viability.

### Capacity Determination

Board capacity is always derived from actual build artifacts — never from a hardcoded lookup table. This ensures correctness across different board variants, custom hardware, and boards with non-standard memory configurations. If capacity cannot be determined by any of the three methods above, the Resource Efficiency dimension is marked N/A and its 15% weight is redistributed to the other available dimensions.

---

## Style Violations Normalization

Checkpatch.pl reports style violations. Normalize per KLOC and map to 0-100 score.

### Step-by-Step Process

1. **Count violations**
   ```
   ERROR: 8
   WARNING: 23
   Total: 31
   ```

2. **Normalize per KLOC**
   ```
   KLOC = 2.34
   violations_per_kloc = 31 / 2.34 = 13.25
   ```

3. **Map to 0-100 score**
   ```
   score = 100 - (violations_per_kloc / 5.0) × 100
         = 100 - (13.25 / 5.0) × 100
         = 100 - 265
         = max(0, -165)
         = 0
   ```

### Style Violation Curve

| Violations/KLOC | Score | Interpretation |
|-----------------|-------|----------------|
| 0 | 100 | Perfect style |
| 1 | 80 | Minor issues |
| 2 | 60 | Some issues |
| 3 | 40 | Frequent issues |
| 4 | 20 | Poor style |
| 5 | 0 | Failing |
| >5 | 0 | Failing |

### Violation Severity Weighting (Optional Enhancement)

Optionally weight ERROR higher than WARNING:

```
weighted_violations = (errors × 2.0) + (warnings × 1.0)
violations_per_kloc = weighted_violations / KLOC
```

Example:
```
Errors: 8, Warnings: 23
weighted = (8 × 2.0) + (23 × 1.0) = 39
violations_per_kloc = 39 / 2.34 = 16.67
score = 100 - (16.67 / 5.0) × 100 = 0
```

---

## Compilation Warnings Normalization

When code compiles with warnings, deduct points based on warning count and severity.

### Warning Severity Classification

| Pattern | Severity | Penalty |
|---------|----------|---------|
| `-Werror` promoted errors | Critical | 10 |
| Deprecated API | High | 5 |
| Implicit declaration | High | 5 |
| Unused variable | Medium | 2 |
| Sign comparison | Medium | 2 |
| Unused function | Low | 1 |
| Info/note | Informational | 0.5 |

### Step-by-Step Process

1. **Parse warnings from build log**
   ```
   warning: implicit declaration of function 'k_msleep' [-Wimplicit-function-declaration]
   warning: unused variable 'ret' [-Wunused-variable]
   warning: comparison of integer expressions of different signedness [-Wsign-compare]
   note: 'k_msleep' declared here
   ```

2. **Classify and weight**
   ```
   Implicit declaration: 1 × 5 = 5
   Unused variable: 1 × 2 = 2
   Sign comparison: 1 × 2 = 2
   Note: 1 × 0.5 = 0.5
   Total penalty: 9.5
   ```

3. **Map to 0-100 score**
   ```
   score = max(0, 100 - total_penalty)
         = max(0, 100 - 9.5)
         = 90.5
         ≈ 91
   ```

### Compilation Score Formula

```
if build_failed:
    score = partial_credit_by_error_type()
else:
    score = max(0, 100 - warning_penalty)
```

---

## Edge Case Handling

### Non-Compiling Code

When code doesn't compile, most automated metrics fail:

| Dimension | Handling |
|-----------|----------|
| Compilability | Score based on error type (0-50) |
| Static Analysis | Run best-effort on available files or mark N/A |
| Code Metrics | Run on source (lizard doesn't need compilation) |
| Style | Run on source (checkpatch doesn't need compilation) |
| Resource Efficiency | Mark N/A |
| Zephyr Correctness | LLM review can proceed |
| Architecture | LLM review can proceed |
| Completeness | LLM review can proceed |
| Documentation | LLM review can proceed |

### Empty Submissions

If no source files present:
```
All automated dimensions: 0
LLM dimensions: 0
Aggregate: 0
```

### Extremely Small Submissions

For very small submissions (<100 lines), per-KLOC normalization can over-penalize:

```
if KLOC < 0.1:
    # Use absolute counts instead of per-KLOC
    defect_score = max(0, 100 - (defect_count × 10))
    style_score = max(0, 100 - (violation_count × 5))
```

Example:
```
Lines: 45
Defects: 2
KLOC = 0.045

Per-KLOC: 2 / 0.045 = 44.44 defects/KLOC → score = 0

Absolute: 100 - (2 × 10) = 80
```

### Undetermined Board Capacity

If board capacity cannot be determined from any of the three sources (build .config, zephyr.dts, board YAML):
```
# Do NOT use hardcoded fallback values or estimates
resource_efficiency = N/A
note = "Board capacity undetermined for <board> — dimension skipped, weight redistributed"
```

### Tool Unavailability

If a required tool is not installed:

| Tool | Fallback |
|------|----------|
| cppcheck | Use clang-tidy only, adjust weight |
| clang-tidy | Use cppcheck only, adjust weight |
| Both unavailable | Mark Static Analysis as N/A |
| lizard | Use cloc for LOC, mark complexity N/A |
| checkpatch | Use clang-format --dry-run or mark N/A |
| bloaty | Use arm-none-eabi-size only |

### Threshold Calibration

Thresholds should be calibrated based on historical data. If grading a new type of project (e.g., networking vs simple GPIO), adjust thresholds:

```python
def calibrate_threshold(historical_scores: list[float], percentile: float) -> float:
    """
    Calibrate threshold based on historical data.

    Args:
        historical_scores: List of defect densities from past submissions
        percentile: Percentile to use as threshold (e.g., 0.75 for 75th percentile)

    Returns:
        Threshold value
    """
    import numpy as np
    return np.percentile(historical_scores, percentile * 100)
```

Example:
```
Historical defect densities: [0.3, 0.5, 0.8, 1.2, 1.5, 2.1, 3.4]
75th percentile: 2.1
Use 2.1 as threshold for failing grade instead of hardcoded 2.0
```

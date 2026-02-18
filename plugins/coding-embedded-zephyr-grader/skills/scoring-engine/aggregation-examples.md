# Aggregation Examples

Complete worked examples showing the full grading pipeline from raw tool output to final aggregate score for both single submission and A/B comparison modes.

## Example 1: Single Submission (Full Pipeline)

### Submission Details
- Board: nRF52840DK
- Application: BLE peripheral with custom service
- Lines of code: 2,340 (2.34 KLOC)

### Step 1: Compilability

**Build output:**
```
west build -b nrf52840dk_nrf52840 -p always ble_peripheral/

[...]
warning: implicit declaration of function 'k_msleep' [-Wimplicit-function-declaration]
warning: unused variable 'ret' [-Wunused-variable]
note: 'k_msleep' declared here
[...BUILD SUCCEEDED...]
```

**Scoring:**
```
Warnings:
  - Implicit declaration: penalty = 5
  - Unused variable: penalty = 2
  - Note: penalty = 0.5

Total penalty: 7.5
Score = 100 - 7.5 = 92.5
```

**Result:** Compilability = 92.5 / 100

---

### Step 2: Static Analysis

**cppcheck output (XML):**
```xml
<results>
  <error id="uninitvar" severity="error" msg="Uninitialized variable: buffer" file="main.c" line="45"/>
  <error id="uninitvar" severity="error" msg="Uninitialized variable: buffer" file="service.c" line="78"/>
  <error id="memleak" severity="error" msg="Memory leak: data" file="main.c" line="120"/>
  <error id="unusedVariable" severity="style" msg="Unused variable 'tmp'" file="main.c" line="33"/>
  <error id="unusedVariable" severity="style" msg="Unused variable 'tmp'" file="service.c" line="56"/>
  <error id="shadowVariable" severity="style" msg="Local variable 'i' shadows outer variable" file="main.c" line="88"/>
</results>
```

**Deduplication:**
```
Group: "Uninitialized variable: buffer" (severity=error, count=2)
  weighted = 1.0 + (1 × 0.1) = 1.1
  contribution = 1.1 × 10.0 = 11.0

Group: "Memory leak: data" (severity=error, count=1)
  weighted = 1.0
  contribution = 1.0 × 10.0 = 10.0

Group: "Unused variable 'tmp'" (severity=style, count=2)
  weighted = 1.0 + (1 × 0.1) = 1.1
  contribution = 1.1 × 1.0 = 1.1

Group: "Local variable 'i' shadows outer variable" (severity=style, count=1)
  weighted = 1.0
  contribution = 1.0 × 1.0 = 1.0

Total weighted defects: 23.1
```

**Normalization:**
```
KLOC = 2.34
defect_density = 23.1 / 2.34 = 9.87 defects/KLOC
```

**Score calculation:**
```
score = 100 - (9.87 / 2.0) × 100
      = 100 - 493.5
      = max(0, -393.5)
      = 0
```

**Result:** Static Analysis = 0 / 100

---

### Step 3: Zephyr Correctness

**Pattern Checklist (25 patterns evaluated):**

| Pattern | Status | Impact |
|---------|--------|--------|
| device_is_ready() check | ✗ Missing | Major issue |
| k_sleep in ISR | ✓ Correct | - |
| Mutex in ISR | ✓ Correct | - |
| K_THREAD_STACK_DEFINE | ✓ Correct | - |
| k_thread_create priority | ✓ Correct | - |
| DT_ALIAS usage | ✓ Correct | - |
| CONFIG_ prefix | ✓ Correct | - |
| Unprotected shared state | ✗ Found 1 instance | Major issue |
| k_sem_give in ISR | ✓ Correct | - |
| Negative errno return | ✓ Correct | - |
| ... (15 more patterns) | ✓ Correct | - |

**Issues found:**
- 2 major issues (missing device_is_ready(), unprotected shared state)

**LLM Assessment:**
```
Score: 50/100
Rationale: Code demonstrates good understanding of Zephyr threading model and
ISR safety, but has 2 critical issues that could cause runtime failures:
1. Missing device_is_ready() check before using I2C device (line 67)
2. Unprotected shared state between ISR and thread (global 'counter' variable)
```

**Result:** Zephyr Correctness = 50 / 100

---

### Step 4: Resource Efficiency

**Size extraction:**
```bash
$ arm-zephyr-eabi-size build/zephyr/zephyr.elf
   text    data     bss     dec     hex filename
  98304    2048   10240  110592   1b000 build/zephyr/zephyr.elf

Flash (text + data): 98304 + 2048 = 100,352 bytes (~98 KB)
RAM (data + bss): 2048 + 10240 = 12,288 bytes (12 KB)
```

**Baseline (nRF52840 BLE peripheral):**
```
Flash baseline: 131,072 bytes (128 KB)
RAM baseline: 16,384 bytes (16 KB)
```

**Efficiency ratios:**
```
flash_ratio = 100352 / 131072 = 0.766
ram_ratio = 12288 / 16384 = 0.75
```

**Scores:**
```
flash_score = 100 - ((0.766 - 0.5) × 200)
            = 100 - (0.266 × 200)
            = 100 - 53.2
            = 46.8

ram_score = 100 - ((0.75 - 0.5) × 200)
          = 100 - (0.25 × 200)
          = 100 - 50
          = 50

combined = (46.8 × 0.6) + (50 × 0.4)
         = 28.08 + 20
         = 48.08
         ≈ 48
```

**Result:** Resource Efficiency = 48 / 100

---

### Step 5: Architecture

**LLM Review:**
```
Code structure:
- main.c (180 lines): Application logic + BLE service handling
- service.c (210 lines): Custom BLE service implementation
- config.h (50 lines): Configuration constants

Architecture assessment:
✓ Separation between app and service
✓ Clear module boundaries
✓ No circular dependencies
✗ Business logic mixed with BLE protocol details in main.c
✗ Some god objects (main.c does too much)

Score: 70/100
Rationale: Good foundational structure with clear service abstraction, but
main.c would benefit from refactoring to separate business logic from
communication protocol handling.
```

**Result:** Architecture = 70 / 100

---

### Step 6: Code Metrics

**Lizard output:**
```csv
NLOC,CCN,token,PARAM,length,location
45,8,234,2,50,main.c:process_data
67,22,445,3,75,main.c:handle_ble_event
23,6,145,1,28,service.c:init_service
34,15,267,2,42,service.c:update_characteristic
```

**CCN penalties:**
```
process_data: CCN=8, penalty=0 (≤10)
handle_ble_event: CCN=22, penalty=(22-10)×3.0=36 (21-30 range)
init_service: CCN=6, penalty=0 (≤10)
update_characteristic: CCN=15, penalty=(15-10)×1.0=5 (11-15 range)

Total penalty: 41
Score = max(0, 100 - 41) = 59
```

**Result:** Code Metrics = 59 / 100

---

### Step 7: Style

**Checkpatch output:**
```
main.c:23: ERROR: spaces required around that '=' (ctx:VxV)
main.c:45: WARNING: line over 80 characters
service.c:12: WARNING: Missing a blank line after declarations
service.c:67: ERROR: trailing whitespace
service.c:89: WARNING: braces {} are not necessary for single statement blocks
[... 26 more warnings ...]

Total: 31 violations (8 ERROR, 23 WARNING)
```

**Normalization:**
```
KLOC = 2.34
violations_per_kloc = 31 / 2.34 = 13.25
```

**Score:**
```
score = 100 - (13.25 / 5.0) × 100
      = 100 - 265
      = max(0, -165)
      = 0
```

**Result:** Style = 0 / 100

---

### Step 8: Completeness

**Requirements (from assignment specification):**
```
✓ Implement BLE peripheral with custom service
✓ Support read characteristic
✓ Support write characteristic
✓ Support notify characteristic
✗ Implement bonding/pairing (missing)
✓ Handle disconnection
✓ Low power mode support
```

**LLM Assessment:**
```
Score: 85/100
Rationale: All core BLE functionality implemented correctly. Missing bonding/
pairing is documented as future work in TODO comments. Error handling present.
Edge cases handled. Implementation is complete for the core requirements.
```

**Result:** Completeness = 85 / 100

---

### Step 9: Documentation

**Documentation review:**
```
README.md: 45 lines
  ✓ Overview paragraph
  ✓ Build instructions
  ✓ Usage examples
  ✗ No architecture diagram
  ✗ API reference incomplete

Inline comments: Moderate
  - 15% of lines have comments
  - Key functions documented
  - Some complex logic lacks explanation

Doxygen: Partial
  - Public API functions documented
  - Internal functions not documented
```

**LLM Assessment:**
```
Score: 60/100
Rationale: README provides basic information for building and running, but
lacks architectural overview and comprehensive API documentation. Inline
comments are present but inconsistent. Would benefit from more detailed
documentation of design decisions and data flow.
```

**Result:** Documentation = 60 / 100

---

### Step 10: Aggregate Score

**Dimension scores with weights:**
```
Compilability:       92.5 × 0.20 = 18.50
Static Analysis:        0 × 0.15 =  0.00
Zephyr Correctness:    50 × 0.15 =  7.50
Resource Efficiency:   48 × 0.15 =  7.20
Architecture:          70 × 0.10 =  7.00
Code Metrics:          59 × 0.10 =  5.90
Style:                  0 × 0.05 =  0.00
Completeness:          85 × 0.05 =  4.25
Documentation:         60 × 0.05 =  3.00
```

**Aggregate:**
```
Total = 18.50 + 0.00 + 7.50 + 7.20 + 7.00 + 5.90 + 0.00 + 4.25 + 3.00
      = 53.35
      ≈ 53 / 100
```

**Final Grade: 53 (F)**

**Summary:**
The submission demonstrates functional BLE peripheral implementation with good completeness, but suffers from critical code quality issues (static analysis errors, style violations) that prevent it from achieving a passing grade. The student should focus on addressing memory safety issues and coding style compliance.

---

## Example 2: A/B Comparison (Blind Grading)

### Scenario
Two students submitted solutions to the same BLE peripheral assignment. Perform blind A/B comparison.

### Submission A

**Scores:**
```
Compilability:      100
Static Analysis:     88
Zephyr Correctness:  90
Resource Efficiency: 65
Architecture:        85
Code Metrics:        78
Style:               92
Completeness:        95
Documentation:       80
```

**Aggregate:** 87.75 (B+)

### Submission B

**Scores:**
```
Compilability:       92
Static Analysis:      45
Zephyr Correctness:   75
Resource Efficiency:  52
Architecture:         70
Code Metrics:         62
Style:                40
Completeness:         90
Documentation:        65
```

**Aggregate:** 68.30 (D+)

### Comparison Table

| Dimension | Submission A | Submission B | Delta | Winner |
|-----------|--------------|--------------|-------|--------|
| Compilability | 100 | 92 | +8 | A |
| Static Analysis | 88 | 45 | +43 | A |
| Zephyr Correctness | 90 | 75 | +15 | A |
| Resource Efficiency | 65 | 52 | +13 | A |
| Architecture | 85 | 70 | +15 | A |
| Code Metrics | 78 | 62 | +16 | A |
| Style | 92 | 40 | +52 | A |
| Completeness | 95 | 90 | +5 | A |
| Documentation | 80 | 65 | +15 | A |
| **Aggregate** | **87.75** | **68.30** | **+19.45** | **A** |

**Conclusion:**
Submission A is superior across all dimensions, with the largest advantages in Style (+52), Static Analysis (+43), and Code Metrics (+16). Submission B is functional but has significant code quality issues.

---

## Example 3: N/A Dimension Handling

### Scenario
Submission fails to build, making Resource Efficiency unmeasurable.

**Original weights:**
```
Compilability:       20%
Static Analysis:     15%
Zephyr Correctness:  15%
Resource Efficiency: 15% → N/A
Architecture:        10%
Code Metrics:        10%
Style:                5%
Completeness:         5%
Documentation:        5%
```

**Redistribution:**
```
Available sum: 100% - 15% = 85%
Redistribution factor: 1.0 / 0.85 = 1.176

New weights:
  Compilability:       20% × 1.176 = 23.52%
  Static Analysis:     15% × 1.176 = 17.64%
  Zephyr Correctness:  15% × 1.176 = 17.64%
  Resource Efficiency:  0%
  Architecture:        10% × 1.176 = 11.76%
  Code Metrics:        10% × 1.176 = 11.76%
  Style:                5% × 1.176 =  5.88%
  Completeness:         5% × 1.176 =  5.88%
  Documentation:        5% × 1.176 =  5.88%
```

**Scores with redistributed weights:**
```
Compilability:       25 × 0.2352 =  5.88
Static Analysis:     40 × 0.1764 =  7.06
Zephyr Correctness:  50 × 0.1764 =  8.82
Resource Efficiency: N/A
Architecture:        60 × 0.1176 =  7.06
Code Metrics:        55 × 0.1176 =  6.47
Style:               30 × 0.0588 =  1.76
Completeness:        70 × 0.0588 =  4.12
Documentation:       50 × 0.0588 =  2.94

Aggregate: 44.11 (F)
```

**Note in report:**
```
Resource Efficiency: N/A (build failed)
Weight redistributed across remaining dimensions.
```

---

## Example 4: Weighted Deduplication Impact

### Without Deduplication

**Defects:**
```
"Uninitialized variable 'buffer'": 12 occurrences × 10.0 (error) = 120.0
"Unused variable": 8 occurrences × 1.0 (style) = 8.0
Other unique defects: 5 occurrences × 3.0 (warning) = 15.0

Total: 143.0
KLOC: 2.0
Defect density: 143.0 / 2.0 = 71.5 defects/KLOC
Score: 100 - (71.5 / 2.0) × 100 = 0
```

### With Deduplication

**Defects (deduplicated):**
```
"Uninitialized variable 'buffer'": 1.0 + (11 × 0.1) = 2.1 × 10.0 = 21.0
"Unused variable": 1.0 + (7 × 0.1) = 1.7 × 1.0 = 1.7
Other unique defects: 5.0 × 3.0 = 15.0

Total: 37.7
KLOC: 2.0
Defect density: 37.7 / 2.0 = 18.85 defects/KLOC
Score: 100 - (18.85 / 2.0) × 100 = 0
```

**Impact:**
Both approaches yield score of 0 in this case, but deduplication significantly reduces the defect density from 71.5 to 18.85, providing a more accurate representation of distinct issue types.

For borderline cases, deduplication can make the difference between passing and failing:

**Borderline example:**
```
Without dedup: density = 2.1 → score = 0
With dedup: density = 1.8 → score = 10
```

---

## Example 5: Small Submission Edge Case

### Scenario
Submission is only 80 lines of code (0.08 KLOC).

**Defects:**
```
2 warnings
```

**Standard per-KLOC approach:**
```
KLOC = 0.08
defect_density = (2 × 3.0) / 0.08 = 75 defects/KLOC
Score = 100 - (75 / 2.0) × 100 = 0
```

**Adjusted approach for small submissions:**
```
if KLOC < 0.1:
    score = max(0, 100 - (defect_count × 10))

score = max(0, 100 - (2 × 10))
      = max(0, 80)
      = 80
```

**Conclusion:**
For very small submissions, use absolute defect counts instead of per-KLOC normalization to avoid over-penalization.

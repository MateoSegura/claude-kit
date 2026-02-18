# Report Examples

Complete example reports with annotations explaining each section.

## Example 1: Single Submission (Failing Grade)

### Markdown Report

```markdown
# Zephyr RTOS Grading Report

**Submission:** student_123/ble_peripheral
**Board:** nrf52840dk_nrf52840
**Date:** 2026-02-16T10:30:00Z
**KLOC:** 2.34

---

## Summary

**Aggregate Score:** 53.35 / 100
**Grade:** F
**Status:** FAIL

The submission demonstrates functional BLE peripheral implementation with good
completeness (85%), but suffers from critical code quality issues. Static
analysis detected severe memory safety problems (score 0) and extensive style
violations (score 0) that prevent this from achieving a passing grade.

Priority fixes: Address memory leaks and uninitialized variables (Static Analysis),
adopt Linux kernel coding style (Style), and reduce cyclomatic complexity in
handle_ble_event() function (Code Metrics).

---

## Dimension Scores

| Dimension | Score | Weight | Weighted | Grade | Status |
|-----------|-------|--------|----------|-------|--------|
| Compilability | 92.5 | 20% | 18.50 | A- | ✓ |
| Static Analysis | 0 | 15% | 0.00 | F | ✗ |
| Zephyr Correctness | 50 | 15% | 7.50 | F | ✗ |
| Resource Efficiency | 48 | 15% | 7.20 | F | ✗ |
| Architecture | 70 | 10% | 7.00 | C- | ~ |
| Code Metrics | 59 | 10% | 5.90 | D | ~ |
| Style | 0 | 5% | 0.00 | F | ✗ |
| Completeness | 85 | 5% | 4.25 | B | ✓ |
| Documentation | 60 | 5% | 3.00 | D- | ~ |

**Legend:** ✓ = Good (≥70), ~ = Acceptable (50-69), ✗ = Failing (<50)

---

## Detailed Findings

### Compilability (92.5/100) — Grade: A-

**Build Result:** SUCCESS
**Warnings:** 2
**Errors:** 0

The submission builds successfully with 2 minor warnings:
- Implicit declaration of function 'k_msleep' (resolved at link time)
- Unused variable 'ret' in main.c:67

**Deduction:** -7.5 points for warnings (5 points for implicit declaration, 2.5 for unused variable)

**Recommendation:** Add `#include <zephyr/kernel.h>` and remove unused variable.

---

### Static Analysis (0/100) — Grade: F

**Defect Density:** 9.87 defects/KLOC (threshold: 2.0 for passing)
**Total Weighted Defects:** 23.1
**Total Issues:** 6 (deduplicated from 25 raw issues)

**Breakdown by Severity:**
- Errors: 3 (weighted: 21.0 after dedup)
- Warnings: 0
- Style: 3 (weighted: 2.1 after dedup)

**Top Issues:**
1. **Uninitialized variable 'buffer'** (2 occurrences, error)
   - Locations: main.c:45, service.c:78
   - Impact: Undefined behavior, possible crash
   - Fix: Initialize buffer before use

2. **Memory leak: data** (1 occurrence, error)
   - Location: main.c:120
   - Impact: Memory exhaustion over time
   - Fix: Call k_free(data) before function return

3. **Unused variable 'tmp'** (2 occurrences, style)
   - Locations: main.c:33, service.c:56
   - Impact: Code clarity
   - Fix: Remove unused variables

**Critical:** The submission has 2.1× the maximum acceptable defect density.
Address memory safety issues immediately.

---

### Zephyr Correctness (50/100) — Grade: F

**Pattern Violations:** 2 major issues
**Patterns Checked:** 25
**Pass Rate:** 92% (23/25)

**Major Issues:**
1. **Missing device_is_ready() check** (line 67)
   - Device: I2C0
   - Impact: Crash if device not initialized
   - Fix: Add `if (!device_is_ready(dev)) return -ENODEV;`

2. **Unprotected shared state between ISR and thread** (global 'counter' variable)
   - Variable: counter (main.c:15)
   - Accessed by: timer_isr, worker_thread
   - Impact: Race condition, data corruption
   - Fix: Use `atomic_t` or ISR signaling pattern

**Minor Issues:** None

**Good Practices Observed:**
- Correct ISR safety (no sleeping in ISR)
- Proper thread stack definition (K_THREAD_STACK_DEFINE)
- Correct error code returns (negative errno)

---

### Resource Efficiency (48/100) — Grade: F

**Flash Usage:** 100,352 bytes (98 KB)
**Baseline:** 131,072 bytes (128 KB)
**Efficiency:** 76.6% of baseline

**RAM Usage:** 12,288 bytes (12 KB)
**Baseline:** 16,384 bytes (16 KB)
**Efficiency:** 75% of baseline

**Score Calculation:**
- Flash score: 100 - ((0.766 - 0.5) × 200) = 46.8
- RAM score: 100 - ((0.75 - 0.5) × 200) = 50
- Combined: (46.8 × 0.6) + (50 × 0.4) = 48.1

**Analysis:** Submission is within acceptable range but not optimized. Large
functions and unoptimized data structures contribute to size. Consider using
k_mem_slab instead of k_malloc for fixed-size allocations to reduce heap overhead.

---

### Architecture (70/100) — Grade: C-

**Structure:** Acceptable with room for improvement

**Strengths:**
- Clear separation between main.c (180 lines) and service.c (210 lines)
- BLE service logic properly isolated
- No circular dependencies

**Weaknesses:**
- Business logic mixed with BLE protocol details in main.c
- main.c handles both application logic AND service coordination (should be split)
- Some god object tendencies (main.c does too much)

**Recommendation:** Refactor main.c into app_logic.c (business rules) and
ble_coordinator.c (protocol handling) to improve separation of concerns.

---

### Code Metrics (59/100) — Grade: D

**Average CCN:** 12.75
**Max CCN:** 22
**Functions Analyzed:** 4

**Function Complexity:**
| Function | CCN | Lines | Status |
|----------|-----|-------|--------|
| main:process_data | 8 | 50 | ✓ Good |
| main:handle_ble_event | 22 | 75 | ✗ Too complex |
| service:init_service | 6 | 28 | ✓ Good |
| service:update_characteristic | 15 | 42 | ~ Acceptable |

**Penalty Calculation:**
- process_data: 0 (CCN ≤ 10)
- handle_ble_event: (22-10)×3.0 = 36 (CCN in 21-30 range)
- init_service: 0 (CCN ≤ 10)
- update_characteristic: (15-10)×1.0 = 5 (CCN in 11-15 range)
- Total: 41 → Score = 100 - 41 = 59

**Recommendation:** Refactor handle_ble_event() to reduce complexity. Extract
sub-functions for different BLE event types.

---

### Style (0/100) — Grade: F

**Violations:** 31
**Violations/KLOC:** 13.25 (threshold: 5.0 for passing)

**Violation Types:**
- ERROR: 8 (spaces around operators, trailing whitespace)
- WARNING: 23 (line length, missing blank lines, unnecessary braces)

**Sample Violations:**
```
main.c:23: ERROR: spaces required around that '=' (ctx:VxV)
main.c:45: WARNING: line over 80 characters
service.c:67: ERROR: trailing whitespace
service.c:89: WARNING: braces {} are not necessary for single statement blocks
```

**Recommendation:** Run `clang-format` with Linux kernel style to auto-fix
most issues. Configure editor to show whitespace and enforce 80-column limit.

---

### Completeness (85/100) — Grade: B

**Requirements Met:** 6/7 (86%)

**Implemented:**
- ✓ BLE peripheral with custom service
- ✓ Read characteristic
- ✓ Write characteristic
- ✓ Notify characteristic
- ✓ Disconnection handling
- ✓ Low power mode support

**Missing:**
- ✗ Bonding/pairing (documented as future work in TODO comments)

**Assessment:** All core requirements implemented correctly. Missing bonding/
pairing is a secondary feature and is documented. Error handling is present and
edge cases are addressed.

---

### Documentation (60/100) — Grade: D-

**README:** 45 lines (basic)
**Inline Comments:** 15% of lines
**API Documentation:** Partial

**README Contents:**
- ✓ Overview paragraph
- ✓ Build instructions
- ✓ Usage examples
- ✗ Architecture diagram (missing)
- ✗ API reference (incomplete)

**Inline Comments:**
- Key functions have high-level comments
- Complex logic lacks explanation
- Some magic numbers unexplained (e.g., "0x01" without context)

**Recommendation:** Add architecture diagram showing component relationships.
Document all public API functions with Doxygen/kernel-doc format. Add comments
explaining WHY, not just WHAT.

---

## Recommendations

### High Priority (Critical) — MUST FIX TO PASS

1. **Fix memory safety issues** (Static Analysis: 0/100)
   - Initialize 'buffer' variable before use (main.c:45, service.c:78)
   - Fix memory leak by freeing 'data' (main.c:120)
   - Estimated time: 30 minutes

2. **Protect shared state** (Zephyr Correctness: 50/100)
   - Use `atomic_t` for 'counter' variable or switch to ISR signaling pattern
   - Estimated time: 15 minutes

3. **Fix style violations** (Style: 0/100)
   - Run `clang-format -i src/*.c` to auto-fix most issues
   - Manually fix remaining issues flagged by checkpatch
   - Estimated time: 1 hour

### Medium Priority (Important) — RECOMMENDED

4. **Add device_is_ready() check** (Zephyr Correctness)
   - Prevents crash if I2C device not available
   - Estimated time: 5 minutes

5. **Refactor handle_ble_event()** (Code Metrics: 59/100)
   - Reduce CCN from 22 to <15 by extracting sub-functions
   - Improves testability and maintainability
   - Estimated time: 2 hours

6. **Improve architecture** (Architecture: 70/100)
   - Split main.c into app_logic.c and ble_coordinator.c
   - Estimated time: 3 hours

### Low Priority (Nice to Have) — OPTIONAL

7. **Enhance documentation** (Documentation: 60/100)
   - Add architecture diagram
   - Complete API documentation with Doxygen
   - Estimated time: 2 hours

8. **Optimize resource usage** (Resource Efficiency: 48/100)
   - Use k_mem_slab for fixed-size allocations
   - Review compiler optimization flags
   - Estimated time: 4 hours

---

## Tool Versions

- Zephyr SDK: 0.16.0
- cppcheck: 2.10
- clang-tidy: 15.0
- lizard: 1.17
- cloc: 1.90
- checkpatch: Linux kernel 5.10

---

Generated by Zephyr Grader v1.0 on 2026-02-16T10:30:00Z
```

---

## Example 2: A/B Comparison

```markdown
# Zephyr RTOS A/B Comparison Report

**Date:** 2026-02-16T15:45:00Z
**Board:** nrf52840dk_nrf52840

---

## Summary

| Metric | Submission A | Submission B | Winner |
|--------|--------------|--------------|--------|
| Aggregate Score | 87.75 | 68.30 | **A** (+19.45) |
| Grade | B+ | D+ | **A** |
| KLOC | 2.1 | 2.5 | A (smaller) |

**Conclusion:** Submission A is significantly superior across all dimensions.
While both submissions achieve functional correctness, Submission A demonstrates
professional-grade code quality with excellent static analysis results (88),
style compliance (92), and good architecture (85). Submission B has critical
code quality issues including poor static analysis (45) and extensive style
violations (40).

---

## Dimension Comparison

| Dimension | Submission A | Submission B | Delta | Winner |
|-----------|--------------|--------------|-------|--------|
| Compilability | 100 | 92 | +8 | **A** |
| Static Analysis | 88 | 45 | **+43** | **A** |
| Zephyr Correctness | 90 | 75 | +15 | **A** |
| Resource Efficiency | 65 | 52 | +13 | **A** |
| Architecture | 85 | 70 | +15 | **A** |
| Code Metrics | 78 | 62 | +16 | **A** |
| Style | 92 | 40 | **+52** | **A** |
| Completeness | 95 | 90 | +5 | **A** |
| Documentation | 80 | 65 | +15 | **A** |

**Winner: Submission A** (9/9 dimensions)

---

## Winner Analysis

**Submission A is superior overall with a 19.45-point advantage.**

**Largest advantages:**
1. **Style:** +52 points — A has excellent style compliance (92) vs B's extensive violations (40)
2. **Static Analysis:** +43 points — A has minimal defects (0.6/KLOC) vs B's high defect density (1.8/KLOC)
3. **Code Metrics:** +16 points — A has well-structured functions (avg CCN 11) vs B's complex functions (avg CCN 18)

**Submission B strengths:**
- None — Submission B scores lower in all dimensions

**Recommendation:** Submission A is production-ready with minor optimizations needed.
Submission B requires significant quality improvements before acceptance.

---

{... Individual scorecards for A and B would follow ...}

---

Generated by Zephyr Grader v1.0
```


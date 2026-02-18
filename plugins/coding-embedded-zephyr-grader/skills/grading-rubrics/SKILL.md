---
name: grading-rubrics
description: "9-dimension grading framework for Zephyr submissions with scoring scales, weight distributions, automated vs LLM evaluation modes, and scoring thresholds for each dimension."
---

# Grading Rubrics

Quick reference for the 9-dimension grading framework used to evaluate Zephyr RTOS submissions. This skill defines what gets measured, how it's scored, and how dimensions combine into final grades.

## 9 Dimensions Overview

| Dimension | Weight | Evaluation Mode | Primary Tools | Score Range |
|-----------|--------|-----------------|---------------|-------------|
| Compilability | 20% | Automated | west build | 0-100 |
| Static Analysis | 15% | Automated | cppcheck, clang-tidy | 0-100 |
| Zephyr Correctness | 15% | LLM + Automated | grep, custom checklist | 0-100 |
| Resource Efficiency | 15% | Automated | bloaty, size, ram/rom reports | 0-100 |
| Architecture | 10% | LLM | Code review | 0-100 |
| Code Metrics | 10% | Automated | lizard, cloc | 0-100 |
| Style | 5% | Automated | checkpatch.pl | 0-100 |
| Completeness | 5% | LLM | Requirements checklist | 0-100 |
| Documentation | 5% | LLM | README, comments, docstrings | 0-100 |

**Total**: 100%

## Grading Scale Definition

All dimensions use a 0-100 point scale with the following interpretation:

| Score Range | Grade | Meaning |
|-------------|-------|---------|
| 90-100 | A | Excellent — exceeds expectations, production-ready quality |
| 80-89 | B | Good — meets all core requirements with minor issues |
| 70-79 | C | Acceptable — functional but has notable issues |
| 60-69 | D | Poor — major issues that impact functionality or maintainability |
| 0-59 | F | Failing — critical issues, incomplete, or non-functional |

## Quick Scoring Thresholds

### Compilability (20%)
- **100**: Builds with no warnings
- **75**: Builds with info-level warnings only
- **50**: Builds with suppressible warnings
- **25**: Builds with errors that can be worked around
- **0**: Does not build

### Static Analysis (15%)
- **100**: Zero defects
- **75**: <0.5 defects per KLOC
- **50**: <1.0 defects per KLOC
- **25**: <2.0 defects per KLOC
- **0**: ≥2.0 defects per KLOC

### Zephyr Correctness (15%)
- **100**: All 25+ patterns correct
- **75**: 1-2 minor issues
- **50**: 3-5 minor issues or 1 major issue
- **25**: 6+ minor issues or 2-3 major issues
- **0**: Critical anti-patterns (e.g., sleeping in ISR)

### Resource Efficiency (15%)
- **100**: <50% of reference baseline
- **75**: 50-75% of reference baseline
- **50**: 75-100% of reference baseline
- **25**: 100-150% of reference baseline
- **0**: >150% of reference baseline

### Architecture (10%)
- **100**: Clean layering, excellent separation of concerns
- **75**: Good structure with minor coupling issues
- **50**: Acceptable but some architectural debt
- **25**: Poor separation, tight coupling
- **0**: No discernible architecture

### Code Metrics (10%)
- **100**: CCN <10, functions <50 lines, files <500 lines
- **75**: CCN <15, functions <100 lines, files <1000 lines
- **50**: CCN <20, functions <150 lines, files <1500 lines
- **25**: CCN <30, functions <200 lines
- **0**: Excessive complexity

### Style (5%)
- **100**: Zero violations
- **75**: <1 violation per KLOC
- **50**: <3 violations per KLOC
- **25**: <5 violations per KLOC
- **0**: ≥5 violations per KLOC

### Completeness (5%)
- **100**: All requirements implemented and tested
- **75**: All core requirements, missing 1-2 edge cases
- **50**: Missing 1-2 secondary requirements
- **25**: Missing 3+ requirements or incomplete implementation
- **0**: Barely started

### Documentation (5%)
- **100**: Comprehensive README, API docs, inline comments
- **75**: Good README, most functions documented
- **50**: Basic README, key functions documented
- **25**: Minimal documentation
- **0**: No documentation

## Weight Redistribution for N/A Dimensions

When a dimension cannot be evaluated (e.g., no requirements spec for Completeness), its weight is redistributed proportionally across remaining dimensions:

```
new_weight[i] = old_weight[i] * (1.0 / sum_of_available_weights)
```

Example: If Completeness (5%) is N/A, the remaining 95% is scaled to 100%.

## Additional Resources

For detailed scoring criteria, edge case handling, and tool command reference:

- [dimension-reference.md](dimension-reference.md) — Full specification of each dimension with 0/25/50/75/100 scoring rubrics, edge cases (non-compiling code, missing files), tool commands, and evaluation protocols
- [scoring-formulas.md](scoring-formulas.md) — Mathematical formulas for automated dimensions including severity weights, CCN thresholds, defect density curves, size efficiency curves, N/A redistribution algorithm, and weighted deduplication formula

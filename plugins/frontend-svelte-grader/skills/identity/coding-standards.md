# Scoring Standards

Complete scoring scale definitions, severity levels, deduction rules, and pass/fail thresholds for Svelte 5 / SvelteKit code grading.

## Score Scale (0-100)

Every dimension score is an integer from 0 to 100 inclusive. The score represents the percentage of rubric criteria satisfied, adjusted by severity-weighted deductions for violations found.

### Letter Grade Mapping

| Score Range | Letter Grade | Interpretation |
|-------------|-------------|----------------|
| 90-100 | A | Excellent. Production-ready code with strong patterns. Minor improvements possible but not required. |
| 80-89 | B | Good. Solid code with some areas for improvement. No critical issues. Suitable for production with minor revisions. |
| 70-79 | C | Acceptable. Meets minimum quality bar. Several improvements needed. Passes but should not be considered exemplary. |
| 60-69 | D | Below standard. Significant quality issues. Requires revision before production deployment. Does not pass. |
| 0-59 | F | Failing. Fundamental quality problems. Major rework or rewrite needed in this dimension. |

### Score Interpretation by Range (Detailed)

**95-100**: Exceptional. The code in this dimension demonstrates mastery of Svelte 5 patterns. Findings are limited to `info`-level observations. Rare -- reserve for code that could serve as a reference implementation.

**85-94**: Strong. One or two minor findings. The code follows Svelte 5 conventions consistently. Patterns are well-chosen and well-implemented.

**75-84**: Solid with gaps. A few minor findings or one major finding. The code works correctly but misses some optimization opportunities or has inconsistencies.

**65-74**: Needs work. Multiple minor findings or a combination of major and minor. Patterns are partially correct but show misunderstanding or carelessness in specific areas.

**50-64**: Significant issues. One or more critical findings, or many major findings. The code has fundamental problems in this dimension that affect reliability, maintainability, or user experience.

**25-49**: Poor. Multiple critical findings. The code in this dimension is largely broken, inaccessible, untested, or unmaintainable.

**0-24**: Non-functional or absent. The dimension is effectively not addressed. Example: no tests exist (testing = 0), no ARIA attributes and no semantic HTML (accessibility = 0).

## Severity Levels

Exactly four severity levels exist. No other labels are permitted.

### Critical

**Definition**: A defect that causes incorrect behavior, data loss, security vulnerability, complete accessibility barrier, or crashes. In the Svelte context, this includes patterns that will break at runtime or completely prevent a class of users from using the application.

**Examples in Svelte 5 / SvelteKit**:
- Using `$:` reactive declarations instead of `$derived` (Svelte 4 legacy -- broken reactivity model)
- `export let` for props in a runes-mode component (compilation error or silent misuse)
- Missing keyboard event handler on an interactive element that only has `on:click` (WCAG 2.1.1 failure)
- `$effect` that modifies its own tracked state (infinite reactivity loop)
- Missing `+error.svelte` boundary causing unhandled errors to crash the page
- `as any` on a user-facing API boundary (type safety hole that propagates)
- `$effect` used where `$derived` is appropriate (unnecessary side effect, potential infinite loop)

**Score deduction**: -25 points per finding (applied after starting from 100).

**Cap**: No cap. Multiple critical findings can drive a score to 0.

### Major

**Definition**: A defect that degrades quality significantly but does not cause outright failure. The code works but is fragile, poorly structured, or violates important conventions.

**Examples in Svelte 5 / SvelteKit**:
- Component exceeds 300 lines without decomposition
- Prop drilling through 3+ component levels instead of using context API
- Inline styles instead of Tailwind utilities for styling that Tailwind covers
- Missing `aria-label` on icon-only buttons (accessibility gap, not total barrier)
- `+page.ts` load function performing mutations (should use `+page.server.ts`)
- `@ts-ignore` or `@ts-expect-error` without explanation comment
- Test file using `getByTestId` instead of accessible queries (`getByRole`, `getByLabelText`)
- Missing loading state for async data fetches

**Score deduction**: -10 points per finding.

**Cap**: Major findings are capped at 6 deductions (-60 total) per dimension. Beyond 6 major findings, additional majors are recorded but do not further reduce the score. This prevents score collapse from many similar issues.

### Minor

**Definition**: A code quality issue that does not affect functionality but reduces readability, maintainability, or consistency.

**Examples in Svelte 5 / SvelteKit**:
- Inconsistent naming conventions between components
- Missing JSDoc/TSDoc on a public utility function
- Tailwind classes in inconsistent order (layout, typography, color should follow a convention)
- Unused `$derived` variable
- Test description does not clearly describe the expected behavior
- Redundant type annotation where TypeScript can infer
- Component file not co-located with its test file

**Score deduction**: -3 points per finding.

**Cap**: Minor findings are capped at 5 deductions (-15 total) per dimension.

### Info

**Definition**: An observation that does not warrant a score deduction. Used for positive patterns worth noting, cross-dimensional observations, or suggestions that go beyond the rubric.

**Examples**:
- "This component uses the snippet pattern effectively for render delegation"
- "This finding is related to accessibility but was observed during component review -- the a11y reviewer should evaluate"
- "Consider using SvelteKit's `preloadData` for this navigation link (not a rubric requirement)"

**Score deduction**: 0 points. Info findings are recorded but never affect the score.

## Scoring Formula

Each dimension starts at 100 and subtracts severity-weighted deductions:

```
raw_score = 100 - (critical_count * 25) - (min(major_count, 6) * 10) - (min(minor_count, 5) * 3)
dimension_score = max(0, raw_score)
```

### Special Score Ceilings

Certain conditions impose a ceiling regardless of the formula result:

| Condition | Ceiling | Dimension |
|-----------|---------|-----------|
| `tsconfig.json` missing `"strict": true` | 50 | TypeScript Usage |
| No `+error.svelte` at root layout level | 60 | UX Patterns |
| Zero test files found | 0 (automatic) | Testing Quality |
| No Tailwind config and no CSS files | N/A (mark as N/A) | Styling/CSS |
| All components use `export let` instead of `$props()` | 0 (automatic) | State Management |

### Automatic Zero Conditions

A dimension receives an automatic score of 0 (not N/A) when:

- The dimension is applicable but completely unaddressed (e.g., a full SvelteKit app with zero tests)
- Every file evaluated in the dimension contains critical-severity violations
- A hard-gate requirement is entirely absent (e.g., strict mode off AND multiple `any` casts)

## Pass/Fail Thresholds

### Per-Dimension Pass/Fail

Each dimension has its own pass threshold (see aggregation-rules.md for the full table):

| Dimension | Pass Threshold |
|-----------|---------------|
| Component Quality | >= 60 |
| State Management | >= 60 |
| Styling/CSS | >= 55 |
| Accessibility | >= 70 |
| Performance | >= 60 |
| TypeScript Usage | >= 60 |
| Testing Quality | >= 50 |
| UX Patterns | >= 55 |

N/A dimensions are excluded (neither pass nor fail).

### Overall Pass/Fail

The overall result is **PASS** if ALL of the following are true:

1. Composite weighted score >= 65
2. No critical failure override is triggered

The overall result is **FAIL** if ANY of the following are true:

1. Composite weighted score < 65
2. Any critical failure override is triggered

### Critical Failure Overrides

These conditions force an overall FAIL regardless of composite score:

| Override Condition | Rationale |
|-------------------|-----------|
| Accessibility dimension score = 0 | An inaccessible application fails regardless of other quality |
| TypeScript dimension score = 0 | Type safety is a foundational requirement; its absence undermines all dimensions |
| Three or more dimensions score < 40 | Broad quality failure across multiple areas indicates systemic problems |

## Weighted Composite Calculation

### Default Weights

| Dimension | Weight |
|-----------|--------|
| Component Quality | 15.0% |
| State Management | 15.0% |
| Styling/CSS | 10.0% |
| Accessibility | 15.0% |
| Performance | 15.0% |
| TypeScript Usage | 10.0% |
| Testing Quality | 10.0% |
| UX Patterns | 10.0% |
| **Total** | **100.0%** |

### N/A Weight Redistribution

When a dimension is N/A, its weight is redistributed proportionally.

**Example**: If Styling/CSS (10%) is N/A:

```
remaining_total = 100 - 10 = 90
component_weight_normalized = 15 / 90 * 100 = 16.67%
state_weight_normalized = 15 / 90 * 100 = 16.67%
... (each remaining weight / 90 * 100)
```

### Composite Formula

```
composite = sum(dimension_score_i * normalized_weight_i) / 100
```

Result is rounded to the nearest integer.

## Confidence Scoring

The aggregator assigns a confidence level to the composite score based on how much evidence was available.

| Confidence | Criteria |
|------------|----------|
| High | >= 20 files analyzed across all dimensions, >= 30 total findings (including info), zero N/A dimensions |
| Medium | 10-19 files analyzed, or 10-29 total findings, or 1 N/A dimension |
| Low | < 10 files analyzed, or < 10 total findings, or >= 2 N/A dimensions |

Confidence is reported in the scorecard but does not affect the score itself. It signals to the reader how much weight to place on the evaluation.

# Severity Definitions

Complete definitions for finding severity levels, score deduction rules, critical failure overrides, and N/A dimension handling.

---

## Severity Levels

### Critical

**Definition:** A fundamental violation that indicates the code does not meet the baseline requirements of the dimension. A single critical finding causes the dimension to fail regardless of other scores.

**Characteristics:**
- Represents a category of defect, not just a single instance
- Often indicates use of a deprecated API, security issue, or complete absence of a required practice
- Blocks a passing grade even if all other criteria are met

**Score impact:** 25-point deduction per critical finding. A single critical typically causes the dimension score to fall below the pass threshold.

**Critical finding examples:**
- Svelte 4 `$:` reactive declarations anywhere in production code
- `export let` props instead of `$props()` (Svelte 4 component API)
- `strict: false` in tsconfig.json
- Zero test files in the codebase
- Keyboard trap with no escape mechanism (WCAG 2.1.2)
- Interactive elements unreachable by keyboard (WCAG 2.1.1)

---

### Major

**Definition:** A significant defect that impacts code quality, correctness, or user experience. Multiple major findings accumulate to cause a dimension to fail. A single major does not fail a dimension on its own, but 4 majors on a 100-point scale typically push below the pass threshold.

**Characteristics:**
- Represents an incorrect or missing practice that should be fixed before shipping
- Usually has a clear better alternative
- Does not represent a systemic failure, but repeated occurrences indicate a pattern problem

**Score impact:** 10-point deduction per major finding.

**Major finding examples:**
- `$effect` used to compute a value that should use `$derived`
- `as any` TypeScript cast in component code
- `<div onclick>` instead of `<button>` for interactive elements
- Missing `aria-label` on icon-only button
- Component file exceeds 300 lines
- Form missing `use:enhance` for progressive enhancement
- Image missing `width`/`height` attributes (causes layout shift)
- Private environment variable used in universal load function (`+page.ts`)
- `@ts-ignore` comment to silence type errors
- Snapshot test for component structure
- Error boundary (`+error.svelte`) missing at route level that could error

---

### Minor

**Definition:** A small defect or missed best practice that does not impact correctness but reduces code quality, maintainability, or user experience. Minor findings accumulate but individually have low impact.

**Characteristics:**
- Often about consistency, idiom preference, or optimization opportunities
- Does not break functionality
- May indicate inexperience with the framework rather than a fundamental mistake

**Score impact:** 3-point deduction per minor finding. Capped at 30 points total across all minors within a dimension (so minor findings alone cannot fail a dimension).

**Minor finding examples:**
- Inline `style=` attribute for static values that should use Tailwind
- `getByTestId` query instead of `getByRole` in tests
- Prop drilling 3 levels deep (without using context)
- Missing responsive breakpoint treatment
- `$bindable()` used where an event callback would be clearer
- `document.title = ...` in `onMount` instead of `<svelte:head>`
- Non-descriptive test name (`it('works')`)
- Magic number in CSS instead of custom property

---

### Info

**Definition:** An observation worth noting but carrying no score penalty. Used to communicate observations to the developer without affecting the grade.

**Characteristics:**
- Could be a positive note, a suggestion, or a context-dependent trade-off
- The grader is not certain whether it is actually a problem

**Score impact:** 0 points.

**Info finding examples:**
- "Consider extracting this snippet into a reusable component when it grows"
- "This pattern works but the newer `svelte/boundary` API may be cleaner"
- "Test coverage is near the minimum threshold — consider adding edge case tests"

---

## Score Deduction Formula

```
dimension_score = 100
               - (critical_count × 25)
               - (major_count × 10)
               - min(minor_total_deduction, 30)

dimension_score = max(0, dimension_score)
```

### Examples

| Findings | Calculation | Score | Pass? |
|----------|-------------|-------|-------|
| 0 findings | 100 | 100 | Yes |
| 1 minor | 100 - 3 | 97 | Yes |
| 3 minors | 100 - 9 | 91 | Yes |
| 1 major | 100 - 10 | 90 | Yes |
| 3 majors | 100 - 30 | 70 | Yes (threshold 60) |
| 4 majors | 100 - 40 | 60 | Yes (marginal) |
| 1 critical | 100 - 25 | 75 | Yes (score passes but see override rules) |
| 1 critical + 2 majors | 100 - 25 - 20 | 55 | Fail |
| 10 minors | 100 - min(30,30) | 70 | Yes (minor cap applies) |

---

## Critical Failure Override Rules

A critical failure override forces a dimension to FAIL and forces an overall FAIL, regardless of the composite score calculation. Overrides are applied BEFORE weight redistribution.

### Override Trigger Table

| Condition | Dimension Affected | Override Action |
|-----------|-------------------|-----------------|
| `"strict": false` in tsconfig.json | TypeScript Usage | Force dimension score to ≤ 30, set `critical_failure: true`, set overall to FAIL |
| Svelte 4 `$:` reactive declaration present | State Management | Force dimension score to ≤ 30, set `critical_failure: true`, set overall to FAIL |
| `export let` for props used (Svelte 4 API) | Component Quality | Force dimension score to ≤ 30, set `critical_failure: true`, set overall to FAIL |
| WCAG 2.1.2 keyboard trap present | Accessibility | Force dimension score to ≤ 20, set `critical_failure: true`, set overall to FAIL |
| WCAG 2.1.1 interactive element not keyboard reachable | Accessibility | Force dimension score to ≤ 30, set `critical_failure: true`, set overall to FAIL |
| Zero test files in codebase | Testing Quality | Force dimension score to 0, set `critical_failure: true`, set overall to FAIL |

### How to Apply Overrides

1. Check for override conditions FIRST, before scoring
2. If an override condition is met, set the dimension score as specified in the table
3. Mark `critical_failure: true` in the dimension JSON payload
4. The score-aggregator MUST detect `critical_failure: true` in any dimension payload and set the overall result to FAIL

### Multiple Overrides

If multiple override conditions are present, apply all of them. Each affected dimension gets its override score. The overall is FAIL if ANY dimension has `critical_failure: true`.

---

## N/A Dimension Rules

A dimension may be marked N/A when the submission genuinely does not have the code being evaluated.

### When to Mark N/A

| Dimension | Mark N/A When |
|-----------|---------------|
| Testing Quality | No test infrastructure configured (no vitest.config.ts) AND the project appears to be a prototype/demo |
| Styling/CSS | No Tailwind configured AND no custom CSS present (rare — most apps have styling) |
| TypeScript Usage | Project is JavaScript-only with no TypeScript files |
| All others | Never — every Svelte/SvelteKit project should be evaluated on these dimensions |

**Do NOT mark N/A because the code is missing or poor** — that is a scoring matter (critical or major findings), not an N/A.

### N/A Evidence Requirements

When marking a dimension N/A, the reviewer MUST include:
- `"na": true` in the JSON payload
- `"na_reason"`: a specific, evidence-based reason (e.g., "No vitest.config.ts found. Project has no testing infrastructure configured.")
- `"score"`: null (not 0 — the aggregator redistributes weight when score is null)

### N/A Weight Redistribution

When a dimension is marked N/A, its weight is redistributed proportionally to the remaining dimensions. See `aggregation-rules.md` for the redistribution formula.

---

## Finding Report Format

Each finding in a dimension review must include these fields:

```json
{
  "id": "CQ-001",
  "severity": "major",
  "title": "Component exceeds 300-line limit",
  "file": "src/lib/components/Dashboard.svelte",
  "line": 487,
  "evidence": "File is 487 lines; exceeds the 300-line single-responsibility guideline",
  "fix_suggestion": "Extract DashboardHeader (lines 1-80), DashboardGrid (lines 81-280), and DashboardSidebar (lines 281-487) into separate components"
}
```

**Field requirements:**

| Field | Required | Notes |
|-------|----------|-------|
| `id` | Yes | Format: `{DIM_CODE}-{NNN}` where DIM_CODE is CQ, SM, CSS, A11Y, PERF, TS, TQ, UX |
| `severity` | Yes | One of: `critical`, `major`, `minor`, `info` |
| `title` | Yes | Concise phrase (under 80 characters) |
| `file` | Yes | Relative path from project root |
| `line` | No | Include when specific line identified |
| `evidence` | Yes | Quoted or described specific evidence — not vague |
| `fix_suggestion` | Yes | Always include for critical/major; include for minor where helpful |

**Fix suggestions must include a code example for critical and major findings.** A text description alone is insufficient.

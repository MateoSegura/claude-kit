# frontend-svelte-grader

> **Role:** Grader · **Version:** 0.1.3

Objective, blind, quantitative code grading agent for Svelte 5 / SvelteKit applications — scores across 8 weighted dimensions with automated and semantic analysis, supporting single-submission and A/B comparison modes.

```bash
claude-kit --kit frontend-svelte-grader
# or load the full team:
claude-kit --kit frontend-svelte
```

**Companion auto-loaded:** `frontend-svelte-knowledge` (Svelte 5 patterns and best practices for review context)

---

## Agents

| Agent | Description |
|-------|-------------|
| `component-reviewer` | Evaluates Svelte component quality: file organization, prop interfaces, composition patterns, snippet usage, reusability, and single-responsibility adherence. Use when grading Dimension 1 (Component Quality) of a Svelte/SvelteKit codebase. |
| `typescript-reviewer` | Evaluates TypeScript usage quality: strict mode compliance, type safety, generic patterns, Props interface typing, event typing, discriminated unions, and avoidance of any/unknown escape hatches. Use when grading Dimension 6 (TypeScript Usage) of a Svelte/SvelteKit codebase. |
| `state-reviewer` | Evaluates state management quality: $state/$derived/$effect rune usage, store patterns, context API, reactivity correctness, and Svelte 4 legacy pattern detection. Use when grading Dimension 2 (State Management) of a Svelte/SvelteKit codebase. |
| `styling-reviewer` | Evaluates CSS and styling quality: Tailwind utility-first discipline, custom property patterns, responsive design, component-scoped styles, design token consistency, and specificity management. Use when grading Dimension 3 (Styling/CSS) of a Svelte/SvelteKit codebase. |
| `testing-reviewer` | Evaluates test quality: test coverage patterns, testing-library usage, component test structure, integration test presence, mock quality, assertion specificity, and test isolation. Use when grading Dimension 7 (Testing Quality) of a Svelte/SvelteKit codebase. |
| `a11y-reviewer` | Evaluates accessibility compliance: WCAG 2.2 AA criteria, ARIA usage correctness, keyboard navigation, focus management, screen reader compatibility, color contrast, and semantic HTML. Use when grading Dimension 4 (Accessibility) of a Svelte/SvelteKit codebase. |
| `ux-reviewer` | Evaluates UX patterns: loading states, error boundaries, optimistic updates, form validation UX, navigation feedback, empty states, transitions, and progressive enhancement. Use when grading Dimension 8 (UX Patterns) of a Svelte/SvelteKit codebase. |
| `performance-reviewer` | Evaluates performance patterns: bundle size impact, lazy loading, code splitting, SSR/SSG strategy, hydration optimization, reactive computation efficiency, and asset optimization. Use when grading Dimension 5 (Performance) of a Svelte/SvelteKit codebase. |
| `score-aggregator` | Aggregates raw dimension scores from all 8 reviewers into a weighted composite score. Handles N/A dimension redistribution, applies weight normalization, computes pass/fail determinations, and flags critical failures that override the composite. Use after all dimension reviewers have completed. |
| `report-generator` | Generates the final grading report in structured markdown and JSON formats. Includes dimension scorecards, finding details with code evidence, fix suggestions, severity breakdowns, and executive summary. Use after the score-aggregator has produced the composite scorecard. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/frontend-svelte-grader:grade` | Single submission grading orchestrator. Validates submission structure, runs all 8 dimension reviewers in parallel, aggregates scores, and produces a comprehensive scorecard. |
| `/frontend-svelte-grader:compare` | A/B comparison grading. Grades two submissions independently with blind randomization, then produces a side-by-side delta report with per-dimension winner analysis. |

---

## Grading Dimensions

8 weighted dimensions: component quality, TypeScript, state management, styling, testing, accessibility, UX patterns, performance.

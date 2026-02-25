# frontend-svelte-grader

> **Role:** Grader · **Version:** 0.1.0

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
| `component-reviewer` | Evaluates Svelte component quality: file organization, prop interfaces, composition patterns, snippet usage, reusability, and single-responsibility adherence. |
| `typescript-reviewer` | Evaluates TypeScript usage quality: strict mode compliance, type safety, generic patterns, Props interface typing, event typing, discriminated unions, and avoidance of any/unknown escape hatches. |
| `state-reviewer` | Evaluates state management quality: $state/$derived/$effect rune usage, store patterns, context API, reactivity correctness, and Svelte 4 legacy pattern detection. |
| `styling-reviewer` | Evaluates CSS and styling quality: Tailwind utility-first discipline, custom property patterns, responsive design, component-scoped styles, design token consistency, and specificity management. |
| `testing-reviewer` | Evaluates test quality: test coverage patterns, testing-library usage, component test structure, integration test presence, mock quality, assertion specificity, and test isolation. |
| `a11y-reviewer` | Evaluates accessibility compliance: WCAG 2.2 AA criteria, ARIA usage correctness, keyboard navigation, focus management, screen reader compatibility, color contrast, and semantic HTML. |
| `ux-reviewer` | Evaluates UX patterns: loading states, error boundaries, optimistic updates, form validation UX, navigation feedback, empty states, transitions, and progressive enhancement. |
| `performance-reviewer` | Evaluates performance patterns: bundle size impact, lazy loading, code splitting, SSR/SSG strategy, hydration optimization, reactive computation efficiency, and asset optimization. |
| `score-aggregator` | Aggregates raw dimension scores from all 8 reviewers into a weighted composite score with N/A handling and critical failure override detection. |
| `report-generator` | Generates the final grading report in structured markdown and JSON formats with dimension scorecards, finding details, fix suggestions, and severity breakdowns. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/frontend-svelte-grader:grade` | Single submission grading orchestrator. Validates submission structure, runs all 8 dimension reviewers in parallel, aggregates scores, and produces a comprehensive scorecard. |
| `/frontend-svelte-grader:compare` | A/B comparison grading. Grades two submissions independently with blind randomization, then produces a side-by-side delta report with per-dimension winner analysis. |

---

## Grading Dimensions

8 weighted dimensions: component quality, TypeScript, state management, styling, testing, accessibility, UX patterns, performance.

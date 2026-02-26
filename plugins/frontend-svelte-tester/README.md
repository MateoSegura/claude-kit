# frontend-svelte-tester

> **Role:** Tester · **Version:** 0.1.2

Testing specialist for Svelte 5 / SvelteKit applications — writes and runs unit tests (Vitest), component tests (vitest-browser-svelte), E2E tests (Playwright), and accessibility audits (vitest-axe) with behavior-first methodology and 80% coverage target.

```bash
claude-kit --kit frontend-svelte-tester
# or load the full team:
claude-kit --kit frontend-svelte
```

**Companion auto-loaded:** `frontend-svelte-knowledge` (Svelte 5 patterns, testing reference, accessibility standards)

---

## Agents

| Agent | Description |
|-------|-------------|
| `unit-test-writer` | Writes Vitest unit tests for TypeScript utility modules, Svelte 5 stores (.svelte.ts), SvelteKit load functions, form actions, and server-side logic. Use when the user needs unit tests for non-component code: pure functions, stores, helpers, load functions, or API routes. |
| `component-test-writer` | Writes vitest-browser-svelte component tests that render Svelte 5 components in a real browser, test user interactions, prop reactivity, snippet rendering, and DOM output. Use when the user needs tests for .svelte component files. |
| `e2e-test-writer` | Writes Playwright E2E tests for SvelteKit routes, user flows, navigation, form submissions, and cross-page interactions. Use when the user needs end-to-end tests that exercise full application behavior through the browser. |
| `a11y-test-writer` | Writes accessibility tests using vitest-axe for component-level WCAG 2.2 AA audits and Playwright with axe-core for page-level audits. Tests keyboard navigation, focus management, ARIA attributes, color contrast, and screen reader semantics. Use when the user needs accessibility test coverage. |
| `test-runner` | Executes Vitest and Playwright test suites, parses output, and reports results with structured failure analysis. Use when tests need to be run and results interpreted, after test files have been written or edited. |
| `coverage-analyzer` | Analyzes Vitest coverage reports to identify gaps against the 80% threshold, prioritizes uncovered code by risk, and produces a test improvement plan. Use when the user asks about coverage, wants to find untested code, or needs a plan to reach coverage targets. |
| `test-reviewer` | Reviews test files for quality: behavior-first adherence, assertion quality, mock appropriateness, Svelte 5 pattern correctness, and test design anti-patterns. Read-only analysis agent. Use when test files need quality review before being considered complete. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/frontend-svelte-tester:scaffold-tests` | Test scaffolding orchestrator. Generates Vitest and Playwright test file templates for a given component or route. |
| `/frontend-svelte-tester:test` | Test execution orchestrator. Runs unit, component, E2E, and accessibility tests with failure triage and structured results output. |
| `/frontend-svelte-tester:coverage` | Coverage analysis orchestrator. Runs Vitest with coverage, identifies gaps against the 80% threshold, and produces a prioritized improvement plan. |

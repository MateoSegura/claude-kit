---
name: frontend-svelte-grader:grading-rubrics
description: "Grading rubrics for all 8 Svelte/SvelteKit evaluation dimensions: Component Quality, State Management, Styling/CSS, Accessibility, Performance, TypeScript Usage, Testing Quality, and UX Patterns. Each dimension has weights, pass/fail criteria, and severity mappings."
user-invocable: false
---

# Grading Rubrics — Svelte/SvelteKit

Quick reference for all 8 grading dimensions. Each reviewer loads this skill to understand exact scoring criteria, weights, and what constitutes a pass or failure.

## Dimension Overview

| # | Dimension | Weight | Pass Threshold | Critical Failure Trigger |
|---|-----------|--------|----------------|--------------------------|
| 1 | Component Quality | 15% | ≥ 60/100 | Svelte 4 component API in production |
| 2 | State Management | 15% | ≥ 60/100 | Svelte 4 `$:` reactive declarations present |
| 3 | Styling/CSS | 10% | ≥ 55/100 | None |
| 4 | Accessibility | 15% | ≥ 70/100 | WCAG 2.2 AA critical barrier present |
| 5 | Performance | 15% | ≥ 60/100 | None |
| 6 | TypeScript Usage | 10% | ≥ 60/100 | `strict: false` in tsconfig.json |
| 7 | Testing Quality | 10% | ≥ 50/100 | Zero tests in codebase |
| 8 | UX Patterns | 10% | ≥ 55/100 | None |

**Overall composite pass threshold: 65/100**

Any dimension with a critical failure trigger override forces an overall FAIL regardless of composite score.

## Quick Scoring Reference

### Scoring Scale

| Score Range | Grade | Interpretation |
|-------------|-------|----------------|
| 90-100 | A | Exemplary — production-ready, exceeds standards |
| 80-89 | B | Good — minor improvements possible |
| 70-79 | C | Acceptable — several issues, passes threshold |
| 60-69 | D | Marginal — significant issues, narrowly passes |
| 50-59 | F | Fail — too many deficiencies to pass |
| 0-49 | F | Fail — fundamental problems |

### Score Deduction by Severity

| Severity | Deduction | Max Deductions Per Dimension |
|----------|-----------|------------------------------|
| Critical | 25 pts | 1 critical = immediate dimension fail |
| Major | 10 pts | 4 majors = dimension fail |
| Minor | 3 pts | Accumulate; capped at 30 pts total |
| Info | 0 pts | Informational only |

Start each dimension at 100. Deduct per finding. Apply finding cap: dimensions cannot score below 0.

## Dimension 1: Component Quality (15%)

**What to evaluate:** File structure, prop interface design, component composition, reusability, single-responsibility adherence, Svelte 5 component API usage, snippet patterns.

Key pass criteria:
- Props typed via `interface Props` with `$props()` rune — required
- Components under 300 lines — major violation per file over this
- Single responsibility: one primary concern per component
- Snippet usage for complex slot patterns
- No direct DOM manipulation outside of `bind:` or `use:` actions

Load `dimension-rubrics.md` for the complete per-criterion scoring table.

## Dimension 2: State Management (15%)

**What to evaluate:** Runes usage correctness, state colocation, absence of Svelte 4 patterns, context API for deep trees, store usage only when genuinely global.

Key pass criteria:
- `$state`, `$derived`, `$effect` used (no Svelte 4 `$:` or `export let`)
- `$derived` used instead of `$effect` for computed values — major violation
- No prop drilling beyond 2 levels — use `setContext`/`getContext`
- Global stores only for auth state, theme, or truly cross-route data

Load `dimension-rubrics.md` for the complete per-criterion scoring table.

## Dimension 3: Styling/CSS (10%)

**What to evaluate:** Tailwind utility usage, custom property patterns, responsive breakpoints, component-scoped styles, design token consistency.

Key pass criteria:
- Tailwind utilities used for layout and spacing — not custom CSS for standard patterns
- `--custom-property` syntax for design tokens and theme values
- Responsive: `sm:`, `md:`, `lg:` breakpoints present where needed
- No inline `style=""` attributes for non-dynamic styles

Load `dimension-rubrics.md` for the complete per-criterion scoring table.

## Dimension 4: Accessibility (15%)

**What to evaluate:** WCAG 2.2 AA criteria, ARIA attribute correctness, keyboard navigation, focus management, screen reader announcements, semantic HTML structure.

Key pass criteria:
- All interactive elements keyboard-reachable and operable
- `<button>` for actions, `<a>` for navigation — never `<div onclick>`
- ARIA labels on icon-only controls
- Focus management on modal/dialog open/close
- Color contrast 4.5:1 for normal text, 3:1 for large text

Load `dimension-rubrics.md` for critical/major/minor WCAG criterion breakdowns.

## Dimension 5: Performance (15%)

**What to evaluate:** Bundle impact, lazy loading, SSR vs CSR appropriateness, `$effect` overhead, reactive computation efficiency, asset optimization.

Key pass criteria:
- Route-level code splitting via SvelteKit dynamic imports
- Data fetched in `+page.server.ts` for sensitive data, `+page.ts` for public data
- No unnecessary `$effect` chains (derived state should use `$derived`)
- Images use `<enhanced:img>` or explicit `width`/`height` attributes

Load `dimension-rubrics.md` for the complete per-criterion scoring table.

## Dimension 6: TypeScript Usage (10%)

**What to evaluate:** `strict: true` in tsconfig, type coverage, generic usage, avoidance of `any`/`unknown` escape hatches, Svelte 5 TypeScript integration.

Key pass criteria:
- `strict: true` in tsconfig.json — critical failure if absent
- No `as any` casts in component code — major per instance
- `$props()` typed with explicit `interface Props`
- Load function return types inferred from `$types`

Load `dimension-rubrics.md` for the complete per-criterion scoring table.

## Dimension 7: Testing Quality (10%)

**What to evaluate:** Test presence and coverage, behavior-first assertions, `@testing-library/svelte` or `vitest-browser-svelte` usage, mock quality, test isolation.

Key pass criteria:
- Tests exist for all non-trivial components — zero tests is critical failure
- User-centric queries: `getByRole`, `getByLabelText` over `getByTestId`
- Tests exercise user interactions, not implementation internals
- No snapshot tests for component structure

Load `dimension-rubrics.md` for the complete per-criterion scoring table.

## Dimension 8: UX Patterns (10%)

**What to evaluate:** Loading states, error handling, form validation feedback, optimistic updates, navigation feedback, empty states, responsive behavior.

Key pass criteria:
- Loading states present for all async operations
- `+error.svelte` boundaries at appropriate route levels
- Form actions use `use:enhance` for progressive enhancement
- Error messages are actionable (not just "An error occurred")

Load `dimension-rubrics.md` for the complete per-criterion scoring table.

## Conditional Dimension 9: Desktop/Hardware Integration (Weight: 10%, replaces UX Patterns weight)

**Applies when:** The project uses Tauri 2 or Electron AND communicates with hardware devices (USB, BLE, serial, LAN, audio, MIDI). If the project is web-only, skip this dimension entirely and keep UX Patterns at 10%.

**When active:** Reduce UX Patterns weight to 5% and allocate the remaining 5% to this dimension (total: 10%).

**What to evaluate:** Tauri IPC correctness, Rust command safety, hardware state management, device lifecycle handling, error recovery, cross-platform compatibility, permission handling.

Key pass criteria:
- Tauri commands use `Arc<Mutex<>>` or `Arc<RwLock<>>` for shared device state -- critical violation if raw state
- Device handles properly cleaned up on disconnect/unmount -- major violation per leak
- Error types use `thiserror` with meaningful messages, not `unwrap()` or `panic!()` in commands
- Browser guard (`if (browser)` or `onMount`) around all `@tauri-apps/api` imports -- critical violation if missing
- Event listeners cleaned up in `$effect` returns or `onDestroy` -- major violation per leak
- Cross-platform permissions documented (udev rules, Info.plist entries, Windows driver notes)
- Reconnection logic with backoff for connection-oriented protocols (BLE, TCP)
- Streaming data uses Tauri events, not polling `invoke` -- major violation for polling pattern

| Severity | Trigger |
|----------|---------|
| Critical | Raw `unwrap()` in Tauri commands, missing browser guards for Tauri API imports, unsynchronized shared device state |
| Major | No disconnect handling, no reconnection logic, event listener leaks, polling instead of events |
| Minor | Missing cross-platform permission docs, no timeout on device operations, hardcoded device addresses |

Load `dimension-rubrics.md` for the complete per-criterion scoring table with code examples.

## Additional Resources

- **[dimension-rubrics.md](dimension-rubrics.md)** — Complete scoring criteria for all 8+1 dimensions with specific pass/fail criteria, code examples, and finding examples. Load when scoring a specific dimension.
- **[severity-definitions.md](severity-definitions.md)** — Severity level definitions (critical/major/minor/info), deduction rules, critical failure override logic, and N/A dimension handling. Load when classifying a finding's severity.

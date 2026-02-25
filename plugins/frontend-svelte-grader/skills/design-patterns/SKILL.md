---
name: frontend-svelte-grader:design-patterns
description: "Svelte 5 and SvelteKit design patterns and anti-patterns used as grading reference: runes patterns, component composition, SvelteKit data loading, form actions, TypeScript integration, and styling patterns. Each anti-pattern maps directly to a grading rubric deduction."
user-invocable: false
---

# Design Patterns — Svelte 5 / SvelteKit

Quick reference for graders. These patterns define what GOOD and BAD Svelte 5 code looks like. Anti-patterns map directly to grading deductions.

## Pattern Categories

| Category | Patterns | Load Reference For |
|----------|----------|-------------------|
| Reactivity | `$state`, `$derived`, `$effect` usage | State Management review |
| Component Composition | Snippets, props interfaces, actions | Component Quality review |
| SvelteKit Data Loading | Universal vs server load, streaming | Performance review |
| Form Patterns | Form actions, `use:enhance` | UX Patterns review |
| TypeScript Integration | `$props()` typing, `$types`, generics | TypeScript review |
| Styling | Tailwind + custom properties hybrid | Styling/CSS review |
| Testing | Behavior-first, `getByRole` queries | Testing Quality review |

## Reactivity Decision Matrix

| Need | Use | Do NOT Use |
|------|-----|------------|
| Local mutable value | `$state` | `writable()` store |
| Value derived from state | `$derived` | `$effect` that sets another `$state` |
| Side effect (DOM, fetch, logging) | `$effect` | `$derived` with mutation |
| Cross-component global state | Svelte store or `$state` in `.svelte.ts` | `$state` in a regular `.ts` file |
| Prop from parent | `$props()` with `interface Props` | `export let` (Svelte 4 pattern) |
| Two-way binding | `$bindable()` in `$props()` | Writable store passed as prop |
| Deep reactive object | `$state` (deep reactive by default) | Manual `$state` per field |

## Component Composition Decision Matrix

| Need | Use | Do NOT Use |
|------|-----|------------|
| Reusable template fragment | Snippet (`{#snippet}`) | Passing markup as prop string |
| Default content placeholder | Snippet as default slot | `<slot>` (Svelte 4) |
| Conditional slot-like content | Named snippet | Multiple boolean props |
| Third-party DOM integration | Svelte action (`use:`) | `onMount` with direct DOM manipulation |
| Dynamic CSS classes | `class:` directive or `clsx` | Ternary string interpolation in `class=` |

## Critical Anti-Pattern Quick Reference

These anti-patterns always map to a grading deduction:

| Anti-Pattern | Severity | Dimension |
|--------------|----------|-----------|
| `$effect` used to set derived state | Major | State Management |
| `$:` reactive declarations (Svelte 4) | Critical | State Management |
| `export let` for props (Svelte 4) | Critical | Component Quality |
| `as any` in component props | Major | TypeScript Usage |
| `<div onclick>` instead of `<button>` | Major | Accessibility |
| No `aria-label` on icon-only buttons | Major | Accessibility |
| Missing `use:enhance` on forms | Major | UX Patterns |
| Snapshot tests for Svelte components | Major | Testing Quality |
| `getByTestId` instead of `getByRole` | Minor | Testing Quality |
| Inline `style=` for static values | Minor | Styling/CSS |
| Prop drilling 3+ levels deep | Minor | State Management |
| `+page.ts` for server-only data | Major | Performance |

## Additional Resources

- **[patterns-reference.md](patterns-reference.md)** — Detailed Svelte 5 patterns with concrete code examples: `$state`/`$derived`/`$effect` correct usage, component composition with snippets, SvelteKit load functions, form actions with progressive enhancement, TypeScript strict patterns. Load when reviewing any dimension that needs pattern verification.
- **[anti-patterns.md](anti-patterns.md)** — Complete anti-pattern catalog with BAD/GOOD code pairs and failure mode explanations. Each anti-pattern includes the exact grading deduction it triggers. Load when you find a suspicious pattern and need to confirm it is a violation and determine its severity.

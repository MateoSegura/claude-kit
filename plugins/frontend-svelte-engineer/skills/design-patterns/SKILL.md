---
name: frontend-svelte-engineer:design-patterns
description: "Svelte 5 runes-specific design patterns and anti-patterns. Covers reactivity patterns ($state/$derived/$effect), data loading patterns (universal vs server load, streaming), component composition (snippets, compound components, headless), error handling, performance patterns, and animation patterns. Includes common Svelte 5 anti-patterns with concrete bad/good code examples. Load this when writing components, implementing features, or reviewing code for correctness."
user-invocable: false
---

# Design Patterns — Svelte 5 / SvelteKit

Quick-reference cheat sheet. See [patterns-reference.md](patterns-reference.md) for code examples with trade-offs. See [anti-patterns.md](anti-patterns.md) for common mistakes with bad/good comparisons.

## Pattern Category Overview

| Category | Patterns | Load Reference When |
|----------|----------|---------------------|
| Reactivity | Derived chains, effect cleanup, fine-grained state, $state.raw | Writing reactive logic, effects |
| Data Loading | Universal vs server load, streaming, parallel requests, form actions | Implementing routes, API calls |
| Component Composition | Snippets, compound components, headless components | Building reusable UI |
| Error Handling | Result types, error boundaries, form validation | Adding error handling |
| Performance | Lazy loading, virtualized lists, memoization | Optimizing components |
| Animation | Svelte transitions, View Transitions API, orchestrated sequences | Adding animations |

## Pattern Decision Matrix

### Reactivity

| Need | Pattern | Avoid |
|------|---------|-------|
| Computed value from state | `$derived(expr)` | `$effect` for computation |
| Complex computed (block needed) | `$derived.by(() => { ... })` | Intermediate `$state` |
| External subscription (DOM, WebSocket) | `$effect` with cleanup return | `onMount` for reactive deps |
| Large array replaced wholesale | `$state.raw` | `$state` with deep proxy |
| Value from parent component | `$props()` | Svelte 4 `export let` |
| Two-way binding from parent | `$bindable()` inside `$props()` | Separate get/set props |

### Data Loading

| Need | Pattern | Notes |
|------|---------|-------|
| Data needed for SEO / initial render | `+page.server.ts` load | SSR-safe |
| Data needs no auth / can be public | `+page.ts` load | Runs on client too |
| Data can load after initial render | Streamed promise in load | Non-critical data |
| Mutation (create/update/delete) | Form action in `+page.server.ts` | Use `use:enhance` for no-reload |
| Multiple independent API calls | `Promise.all` in load | Parallel, not waterfall |

### Component Composition

| Need | Pattern | Notes |
|------|---------|-------|
| Flexible content inside component | `{#snippet name}{/snippet}` + `{@render name()}` | Svelte 5 replacement for slots |
| Default content | `{@render children?.()}` | `children` is a built-in snippet prop |
| Related components sharing state | Context API + compound component | Use Symbol key |
| Reusable behavior without UI | Action function (`use:tooltip`) | Zero rendering overhead |
| Highly configurable UI primitive | Headless component + render prop | Maximum flexibility |

### Error Handling

| Need | Pattern | Notes |
|------|---------|-------|
| Typed function that can fail | `Result<T, E>` discriminated union | No thrown exceptions |
| Route-level error display | `+error.svelte` | Catches load function throws |
| Form validation feedback | `fail(422, { field, error })` in action | Returns to +page.svelte |
| Unexpected errors | `error(500, 'message')` from `@sveltejs/kit` | Shows root +error.svelte |

## Svelte 4 → Svelte 5 Pattern Map

| Svelte 4 | Svelte 5 | Reason |
|----------|----------|--------|
| `export let prop` | `let { prop } = $props()` | Explicit, typed, destructured |
| `$: computed = a + b` | `let computed = $derived(a + b)` | Reactive, not label-based |
| `$: { sideEffect() }` | `$effect(() => { sideEffect() })` | Explicit, with cleanup |
| `on:click={handler}` | `onclick={handler}` | Standard DOM event attributes |
| `<slot />` | `{@render children?.()}` | Explicit render functions |
| `<slot name="title">` | `{#snippet title()}{/snippet}` | Named snippet pattern |
| `createEventDispatcher` | Callback props | Direct function passing |
| `writable()` / `$store` | Module-level `$state` | No reactive context needed |
| `beforeUpdate` / `afterUpdate` | `$effect.pre` / `$effect` | Lifecycle alignment |

## Quick Rules — Always Apply

1. **Never use `$effect` to compute a value** — use `$derived` instead.
2. **Never import `writable`, `readable`, `derived` from `svelte/store`** in Svelte 5 components.
3. **Always return cleanup from `$effect`** when registering event listeners, timers, or subscriptions.
4. **Never mutate `$derived` values** — they are read-only; derive a new value instead.
5. **Never use `$:` reactive declarations** — use `$derived` or `$effect` explicitly.
6. **Use `onclick=` not `on:click=`** — Svelte 5 uses standard attribute syntax.
7. **Always key `{#each}` lists** with `(item.id)` when items can reorder.
8. **Module-level `$state` is SSR-shared** — gate with `browser` or keep in context.

## Additional Resources

- [patterns-reference.md](patterns-reference.md) — Detailed patterns with complete code examples, trade-offs, and when-to-use guidance for all six categories
- [anti-patterns.md](anti-patterns.md) — Common Svelte 5 mistakes with BAD code, why it fails, and GOOD code correction

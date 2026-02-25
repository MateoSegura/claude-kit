---
name: frontend-svelte-debugger:design-patterns
description: "Svelte 5 and SvelteKit design patterns and anti-patterns for diagnostic comparison. Covers reactivity, component composition, routing, state management, hardware IPC, and error handling patterns used to identify correct vs incorrect code during debugging sessions."
user-invocable: false
---

# Design Patterns — Svelte 5 / SvelteKit

Quick reference for diagnosing correct vs incorrect code. See [patterns-reference.md](patterns-reference.md) for full code examples. See [anti-patterns.md](anti-patterns.md) for common mistakes with failure analysis.

## Pattern Categories

| Category | Patterns | When to load reference |
|----------|----------|------------------------|
| Reactivity | `$state` init, `$derived` chains, `$effect` cleanup, `$effect.pre`, `$state.snapshot`, `$state.raw` | Stale data, infinite loops, missed updates |
| Component | Compound components, snippet composition, error boundaries, context services | Prop drilling, context errors, rendering bugs |
| Routing | Load function data flow, form actions, hooks (`handle`, `handleError`), adapter config | 404s, hydration errors, prerender failures |
| State Management | Module-level `$state`, context-bound state, universal stores | Cross-component sync issues, serialization traps |
| Hardware IPC | Tauri `invoke`, `listen`/`emit` event streams, device state machines, reconnect logic | Stale device state, unclosed listeners, event leaks |
| Error Handling | `error()` + `redirect()`, `handleError` hook, error boundaries, try/catch in effects | Unhandled rejections, wrong HTTP status, cascading errors |

## Decision Matrix

| Symptom | First Pattern to Check | Anti-pattern Often Responsible |
|---------|------------------------|-------------------------------|
| UI doesn't update after assignment | `$state` — is it deeply reactive? | Destructuring reactive proxy |
| Effect runs too often / infinite loop | `$derived` instead of `$effect` for sync | Using `$effect` for state sync |
| Value lags by one update | `$effect.pre` for pre-DOM reads | Reading DOM in `$effect` (post-update) |
| Context value undefined in child | `setContext` called before children render | Calling `getContext` outside component init |
| Load data stale after navigation | `invalidate()` or `invalidateAll()` | Returning mutable shared object from `load` |
| Device listener fires after unmount | `$effect` returning cleanup fn | Missing `return unlisten` in `$effect` |
| Hydration mismatch on page load | Server/client HTML must be identical | Accessing `window`/`localStorage` at module scope |
| Form action returns 500 | Return `fail()` from action, not throw | Throwing from form action instead of `fail()` |
| `$derived` returns stale value | Dependencies must be read synchronously | Async call inside `$derived` |
| TypeScript error on `$state` class field | Use `$state` rune in class bodies (Svelte 5.2+) | Using class fields without rune annotation |

## Reactivity Quick Reference

```svelte
<!-- $state: deeply reactive proxy -->
let count = $state(0);
let items = $state<string[]>([]);  // array is deeply reactive

<!-- $state.raw: not reactive internally, only on reassign -->
let raw = $state.raw({ x: 1 });   // raw.x = 2 does NOT trigger update

<!-- $state.snapshot: extract plain value from proxy -->
const plain = $state.snapshot(items);  // for structuredClone, postMessage, etc.

<!-- $derived: memoized computed value, no side effects -->
let doubled = $derived(count * 2);
let complex = $derived.by(() => items.filter(i => i.length > 3));

<!-- $effect: runs after DOM update, returns cleanup -->
$effect(() => {
  const timer = setInterval(() => count++, 1000);
  return () => clearInterval(timer);  // MUST return cleanup
});

<!-- $effect.pre: runs BEFORE DOM update (for measurement) -->
$effect.pre(() => {
  const height = el.offsetHeight;  // safe to read before Svelte patches DOM
});
```

## Component Pattern Quick Reference

```svelte
<!-- Snippet composition (Svelte 5 replacement for slots) -->
{#snippet header(title: string)}
  <h2>{title}</h2>
{/snippet}
{@render header('My Title')}

<!-- Context service: parent sets, children get -->
<!-- Parent: --> setContext('theme', { color: $state('blue') });
<!-- Child:  --> const theme = getContext('theme');

<!-- Error boundary: +error.svelte handles load/action errors -->
<!-- +error.svelte receives: $page.error.message, $page.status -->
```

## Additional resources

- [patterns-reference.md](patterns-reference.md) — Full pattern catalog with 10-30 line code examples, when-to-use guidance, and trade-off analysis for each pattern category
- [anti-patterns.md](anti-patterns.md) — Catalog of common Svelte 5 mistakes with bad code, failure explanation, and corrected code for each

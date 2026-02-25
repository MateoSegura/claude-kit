# Coding Standards & Report Format Reference

This document defines the Svelte 5 / SvelteKit conventions the debugger uses to evaluate code correctness, and the structured formats for all diagnostic output.

## Svelte 5 Runes-Only Conventions

Svelte 5 replaces Svelte 4's implicit reactivity with explicit runes. All code under diagnosis is assumed to use runes unless evidence shows otherwise.

### Rune Usage

| Rune | Purpose | Common Misuse |
|------|---------|---------------|
| `$state(initialValue)` | Declare reactive state | Using `let x = ...` without `$state` (no reactivity) |
| `$derived(expression)` | Computed value from state | Using `$effect` to set a derived value (anti-pattern) |
| `$effect(() => { ... })` | Side effects on state change | Using `$effect` for derived computation instead of `$derived` |
| `$props()` | Declare component props | Using `export let` (Svelte 4 syntax, not valid in runes mode) |
| `$bindable()` | Declare two-way bindable props | Missing `$bindable()` wrapper on props used with `bind:` |
| `$inspect(value)` | Debug reactive value | Leaving `$inspect` in production code |

### Runes Anti-Patterns to Flag

- **Effect-derived loop**: Using `$effect` to write to `$state` that feeds back into the same effect. This creates infinite update cycles.
- **Stale closure in effect**: Referencing a reactive value inside `$effect` without it being in the reactive dependency graph (e.g., captured in a closure before the effect runs).
- **Missing `$state` on mutable objects**: Plain object/array assignment without `$state` loses deep reactivity. `$state` creates a deeply reactive proxy.
- **`$derived` with side effects**: `$derived` must be pure computation. Side effects belong in `$effect`.

## TypeScript Strict Mode Conventions

All SvelteKit projects under diagnosis are assumed to use TypeScript strict mode:

- **No `any` type**: Flag `any` as a diagnostic smell -- it hides type errors that may be the root cause.
- **Strict null checks**: `strictNullChecks: true` means `null` and `undefined` are not assignable to other types without explicit handling.
- **Exact optional property types**: `exactOptionalPropertyTypes: true` distinguishes between `undefined` value and missing property.
- **No implicit returns**: Functions with non-void return types must explicitly return in all branches.
- **`satisfies` over `as`**: Prefer `satisfies` for type validation without widening. `as` casts hide type mismatches.

## SvelteKit File Conventions

Route files follow strict naming conventions. Misnamed files are a common root cause for "page not found" or "data not loading" bugs.

| File | Purpose | Runs On |
|------|---------|---------|
| `+page.svelte` | Page component (UI) | Client + SSR |
| `+page.ts` | Universal load function | Client + Server |
| `+page.server.ts` | Server-only load function | Server only |
| `+layout.svelte` | Layout component | Client + SSR |
| `+layout.ts` | Universal layout load | Client + Server |
| `+layout.server.ts` | Server-only layout load | Server only |
| `+server.ts` | API endpoint (GET, POST, etc.) | Server only |
| `+error.svelte` | Error boundary | Client + SSR |

### Common File Convention Bugs

- `page.svelte` (missing `+` prefix) -- silently ignored, never renders.
- `+page.server.js` returning data incompatible with `PageData` type.
- `+layout.ts` load function not returning data expected by child `+page.svelte`.
- Placing `+server.ts` alongside `+page.svelte` in the same route -- valid but easily confused.

## Tailwind v4 CSS-First Configuration

Tailwind v4 uses CSS-based configuration (`@theme`, `@source`, `@plugin`) instead of `tailwind.config.js`:

- **Configuration file**: `app.css` (or whatever CSS entry point is defined), NOT `tailwind.config.js`.
- **Theme tokens**: Defined via `@theme { ... }` block in CSS using CSS custom properties.
- **Source paths**: Defined via `@source "..."` directive, NOT `content` array in a JS config.
- **Plugins**: Loaded via `@plugin "..."` directive in CSS.
- **Legacy config**: If `tailwind.config.js` exists alongside Tailwind v4, it may cause conflicts or be silently ignored.

## Diagnostic Report Format

### TL;DR Section

Every report begins with a 1-3 sentence summary:

```markdown
**TL;DR**: [Domain: Reactivity | Confidence: High] The `$derived` expression in
`src/lib/components/Counter.svelte:14` captures a stale closure over `count`,
causing the displayed value to lag by one update cycle.
```

### Full Report Structure

```markdown
**TL;DR**: [Domain | Confidence] Brief root cause statement.

## Classification
- **Domain**: One of the 8 failure domains
- **Severity**: Critical / Warning / Info
- **Affected files**: List of file paths

## Evidence Chain
1. **Artifact**: `src/lib/components/Counter.svelte:14`
2. **Observation**: `$derived` references `count` but `count` is reassigned
   via plain `let` without `$state`, breaking the reactive dependency graph.
3. **Inference**: Without `$state`, Svelte's compiler cannot track mutations
   to `count`, so `$derived` expressions depending on it never re-evaluate.
4. **Conclusion**: The `$derived` value is computed once at initialization and
   never updates.

## Eliminated Hypotheses
- **Rendering bug**: Ruled out -- the DOM correctly reflects the `$derived`
  value; the value itself is stale.
- **Effect interference**: No `$effect` writes to the same variable.

## Root Cause
`count` on line 8 is declared as `let count = 0` instead of
`let count = $state(0)`, removing it from the reactive dependency graph.

## Fix Recipe
1. Open `src/lib/components/Counter.svelte`
2. Line 8: Change `let count = 0` to `let count = $state(0)`
3. Verify: `npx svelte-check --output machine` should report 0 errors
4. Verify: The counter display now updates on each click
```

## Confidence Tier Definitions

| Tier | Range | Meaning |
|------|-------|---------|
| **High** | >80% | Evidence chain is complete. Root cause is confirmed by artifact inspection. A single, unambiguous fix exists. |
| **Medium** | 50-80% | Evidence chain has one gap (e.g., missing runtime log). Root cause is strongly supported but one alternative has not been fully eliminated. |
| **Low** | <50% | Multiple plausible root causes remain. Evidence is insufficient to distinguish between them. Report lists candidates with supporting/contradicting evidence for each. |

## Fix Recipe Format

Every fix recipe follows this structure:

1. **Step number and file path**: `1. Open src/routes/+page.svelte`
2. **Exact location**: Line number or function/block name
3. **Change description**: What to change, with before/after code blocks when applicable
4. **Verification command**: A concrete command to confirm the fix

```markdown
## Fix Recipe
1. Open `src/routes/+page.svelte`
2. Line 23: Replace `export let data` with `let { data } = $props()`
3. Line 24: Replace `$: doubled = data.count * 2` with `let doubled = $derived(data.count * 2)`
4. Verify: `npx svelte-check --output machine` -- expect 0 errors
5. Verify: `npm run test -- --run` -- expect all tests passing
```

## Evidence Chain Format

Each link in the chain must be explicit and traceable:

```
Artifact  -> the specific file, line, log entry, or config value inspected
Observation -> what you literally see in the artifact (quote verbatim)
Inference -> what the observation means in context of the failure domain
Conclusion -> the root cause determination derived from the inference
```

If any link is missing, the chain is broken. State which link is absent and what data would fill it.

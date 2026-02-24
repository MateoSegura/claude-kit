# Compiler Errors — Svelte 5 / SvelteKit

Symptom → Cause → Fix patterns for errors produced by `svelte-check`, the Svelte compiler, and TypeScript strict mode.

---

## svelte-check Error Patterns

### error TS2345 — Argument of type X is not assignable to Y

**Symptom**: `error TS2345: Argument of type 'string | null' is not assignable to parameter of type 'string'`

**Cause**: TypeScript strict mode (`strict: true` or `strictNullChecks: true`) requires narrowing nullable types before use. Common in SvelteKit when `params`, `url.searchParams.get()`, or `event.locals` values are `string | null`.

**Fix**:
```typescript
// Before: fails strict null check
const id = params.id;         // type: string | undefined
doSomething(id);              // error: string | undefined not assignable to string

// After: narrow first
const id = params.id;
if (!id) throw error(400, 'Missing id');
doSomething(id);              // type: string — narrowed
```

For optional with default: `const q = url.searchParams.get('q') ?? ''`

---

### error TS2339 — Property does not exist on type

**Symptom**: `error TS2339: Property 'user' does not exist on type 'App.Locals'`

**Cause**: `App.Locals` interface in `src/app.d.ts` is missing the property being set on `event.locals`.

**Fix**:
```typescript
// src/app.d.ts
declare global {
  namespace App {
    interface Locals {
      user: { id: string; email: string } | null;
    }
  }
}
export {};
```

Restart the TypeScript language server after editing `app.d.ts`.

---

### error TS7006 — Parameter 'x' implicitly has an 'any' type

**Symptom**: Inside `.svelte` files, callback parameters inferred as `any`.

**Cause**: Missing type annotation on event handler or array callback; `strict` mode requires explicit types where inference fails.

**Fix**:
```svelte
<!-- Before -->
<input oninput={(e) => (value = e.target.value)} />  <!-- e implicitly any -->

<!-- After -->
<input oninput={(e: Event & { currentTarget: HTMLInputElement }) =>
  (value = (e.currentTarget as HTMLInputElement).value)} />
```

Or use the `on:` directive alternative in Svelte 5 component events.

---

## Rune Compilation Errors

### Cannot use runes in non-rune file

**Symptom**: `Error: Cannot use $state outside a .svelte file or a .svelte.ts/.svelte.js module`

**Cause**: Using `$state`, `$derived`, or `$effect` in a plain `.ts` or `.js` file (not a `.svelte.ts` file).

**Fix**: Rename the file to `.svelte.ts` (or `.svelte.js`). Files using runes must have the `.svelte.ts` extension so the Svelte compiler processes them.

```bash
mv src/lib/store.ts src/lib/store.svelte.ts
```

Update all imports accordingly.

---

### $effect ran too many times / Detected a potentially infinite update cycle

**Symptom**: Svelte runtime warning: `Detected a potentially infinite update cycle in an effect`

**Cause**: An effect reads and writes the same `$state`, creating a feedback loop.

**Diagnostic**:
```svelte
$effect(() => {
  count = count + 1;  // reads count (dependency), then writes count → infinite loop
});
```

**Fix**: Replace with `$derived` if the goal is computed state, or use a flag/condition to prevent re-entry:
```svelte
// For computed values: use $derived
let doubled = $derived(count * 2);

// For true one-shot effects: check before writing
$effect(() => {
  if (someCondition && !alreadyDone) {
    alreadyDone = true;
    triggerAction();
  }
});
```

---

### $props() used outside component

**Symptom**: `Error: $props() can only be used at the top level of a .svelte file`

**Cause**: `$props()` called inside a function, `$effect`, or an imported module rather than at the top level of the `<script>` block.

**Fix**:
```svelte
<!-- BAD -->
<script lang="ts">
  function init() {
    let { name } = $props();  // error: inside function
  }
</script>

<!-- GOOD -->
<script lang="ts">
  let { name } = $props();  // top level only
</script>
```

---

### Snippet type mismatch

**Symptom**: `Type 'Snippet<[]>' is not assignable to type 'Snippet<[string]>'`

**Cause**: Parent component declares a snippet prop with a parameter, but the passed snippet does not declare the matching parameter.

**Fix**:
```svelte
<!-- Component expects Snippet<[string]> -->
<!-- BAD usage -->
{#snippet myRow()}   <!-- missing parameter -->
  <td>static</td>
{/snippet}

<!-- GOOD usage -->
{#snippet myRow(item: string)}
  <td>{item}</td>
{/snippet}
```

---

## TypeScript Strict Mode Failures

### Strict property initialization

**Symptom**: `error TS2564: Property 'el' has no initializer and is not definitely assigned in the constructor`

**Cause**: `bind:this` target typed without accounting for the possibility it's `undefined` before mount.

**Fix**:
```svelte
<!-- Use non-null assertion for bind:this — Svelte guarantees it's set before $effect -->
let el!: HTMLDivElement;  // the ! tells TS it will be assigned

$effect(() => {
  el.focus();  // safe — el is assigned by mount time
});
```

---

### Type error on $page.data

**Symptom**: `Property 'item' does not exist on type 'Record<string, any> & App.PageData'`

**Cause**: `$page.data` is typed as `App.PageData` which must be augmented to include route-specific data.

**Fix**: Type individual page data via `PageData` from `$types`, not via `$page.data`:
```svelte
<script lang="ts">
  import type { PageData } from './$types';
  let { data }: { data: PageData } = $props();  // properly typed from load return
</script>
```

Do not use `$page.data.someProperty` in components where a typed `data` prop is available.

---

## svelte-check Common Warnings

| Warning Code | Message Pattern | Common Cause | Fix |
|-------------|-----------------|-------------|-----|
| `svelte(legacy-component-creation)` | Using `new Component()` | Svelte 4 instantiation pattern | Use `mount()` from `svelte` instead |
| `svelte(non-reactive-update)` | Variable assigned but not reactive | Missing `$state` | Add `$state()` wrapper |
| `svelte(ownership_invalid_binding)` | Binding to prop of another component | Two-way binding on passed prop | Use callback prop or event instead |
| `a11y-no-static-element-interactions` | Static element with event handler | Missing `role` attribute | Add `role="button"` or use `<button>` |
| `a11y-missing-attribute` | `<img>` without `alt` | Missing alt text | Add `alt=""` (decorative) or descriptive text |

---

## Diagnosing Unknown Compiler Errors

1. Run `npx svelte-check --output human` for human-readable output
2. Check the exact file path and line number in the error
3. Temporarily disable `strict` in `tsconfig.json` to isolate TypeScript vs Svelte issues
4. Run `npx svelte-check --ignore src/lib/third-party` to exclude noisy third-party types
5. Check `svelte.config.js` for `vitePlugin: { prebundleSvelteLibraries: true }` if seeing library-related errors

# Dimension Rubrics — Complete Scoring Criteria

Detailed pass/fail criteria for all 8 grading dimensions. Each section covers what to look for, how to score findings, and code examples of passing and failing patterns.

---

## Dimension 1: Component Quality (Weight: 15%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | Pass Evidence | Fail Evidence | Severity |
|-----------|---------------|---------------|----------|
| Props typed via `$props()` with `interface Props` | `const { foo, bar }: Props = $props()` | `export let foo: string` | Critical |
| Component file ≤ 300 lines | File line count ≤ 300 | File > 300 lines | Major (per file) |
| Single responsibility | Component has one clear primary concern | Component handles unrelated concerns (e.g., data fetching + form validation + chart rendering) | Major |
| Snippet usage for complex templates | `{#snippet}` used for reusable template fragments | Repetitive inline markup that could be extracted | Minor |
| No direct DOM manipulation | `use:` actions or `bind:` for DOM refs | `document.getElementById`, `document.querySelector` in `onMount` | Major |
| Exports only what consumers need | Props interface minimal and documented | Unnecessary exports, internal state exposed | Minor |
| Component reusability | Generic props, no hardcoded strings in logic | Business logic hardcoded into component | Major |
| Svelte 5 event syntax | `onclick={handler}` event attributes | `on:click={handler}` (Svelte 4 syntax) | Major |

### Passing Pattern

```svelte
<!-- Good: Svelte 5 component with typed props and snippet -->
<script lang="ts">
  interface Props {
    items: string[];
    onSelect: (item: string) => void;
    placeholder?: string;
  }

  const { items, onSelect, placeholder = 'Select...' }: Props = $props();
  let selected = $state<string | null>(null);

  function handleSelect(item: string) {
    selected = item;
    onSelect(item);
  }
</script>

{#snippet option(item: string)}
  <li role="option" aria-selected={selected === item} onclick={() => handleSelect(item)}>
    {item}
  </li>
{/snippet}

<ul role="listbox">
  {#if items.length === 0}
    <li>{placeholder}</li>
  {:else}
    {#each items as item}
      {@render option(item)}
    {/each}
  {/if}
</ul>
```

### Failing Pattern

```svelte
<!-- BAD: Svelte 4 API, no types, direct DOM manipulation -->
<script>
  export let items;         // Svelte 4: export let
  export let onSelect;

  import { onMount } from 'svelte';

  onMount(() => {
    const el = document.querySelector('.list'); // direct DOM
    el.focus();
  });
</script>

<ul class="list">
  {#each items as item}
    <li on:click={() => onSelect(item)}>{item}</li>  <!-- Svelte 4 event syntax -->
  {/each}
</ul>
```

---

## Dimension 2: State Management (Weight: 15%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | Pass Evidence | Fail Evidence | Severity |
|-----------|---------------|---------------|----------|
| No Svelte 4 reactive declarations | No `$:` labels anywhere | `$: doubled = count * 2` | Critical |
| `$derived` for computed values | `const doubled = $derived(count * 2)` | `$effect(() => { derived = count * 2 })` | Major |
| `$state` instead of writable stores for local state | `let count = $state(0)` | `const count = writable(0)` for component-local state | Minor |
| No prop drilling beyond 2 levels | Context API used for deep trees | Same prop threaded through 3+ component layers | Minor |
| `$effect` has cleanup when needed | `return () => cleanup()` in effects with subscriptions | Subscription started in `$effect` with no cleanup | Major |
| Global state in `.svelte.ts` files | `export let authState = $state(...)` in `.svelte.ts` | `$state` used in regular `.ts` files (does not work) | Major |
| `$bindable()` used sparingly | Only for genuine two-way binding (e.g., form inputs) | `$bindable()` used as shortcut to avoid event callbacks | Minor |
| State colocated with usage | State declared in the component that owns it | Unnecessary hoisting of state to parent | Minor |

### Passing Pattern

```svelte
<script lang="ts">
  // Good: $state for local, $derived for computed, $effect only for true side effects
  let count = $state(0);
  const doubled = $derived(count * 2);
  const isEven = $derived(count % 2 === 0);

  $effect(() => {
    // Only for actual side effects: logging, external sync
    console.log(`Count changed to ${count}`);
    // Cleanup returned for subscriptions/timers
    const id = setTimeout(() => {}, 1000);
    return () => clearTimeout(id);
  });
</script>
```

### Failing Pattern

```svelte
<script lang="ts">
  // BAD: $effect used to compute derived value (use $derived instead)
  let count = $state(0);
  let doubled = $state(0);     // unnecessary $state

  $effect(() => {
    doubled = count * 2;       // anti-pattern: computing inside effect
  });

  // BAD: Svelte 4 reactive declaration
  $: tripled = count * 3;
</script>
```

---

## Dimension 3: Styling/CSS (Weight: 10%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | Pass Evidence | Fail Evidence | Severity |
|-----------|---------------|---------------|----------|
| Tailwind for layout and spacing | `class="flex items-center gap-4 p-6"` | Custom CSS for standard flex/grid layouts | Minor |
| Custom properties for design tokens | `var(--color-brand)`, `var(--spacing-md)` | Magic numbers in CSS (`color: #3b82f6`) | Minor |
| Responsive breakpoints | `sm:`, `md:`, `lg:` Tailwind prefixes | Fixed pixel widths without responsive consideration | Major |
| No inline styles for static values | Dynamic `style` only for runtime-computed values | `style="padding: 16px"` on static elements | Minor |
| Scoped styles avoid global leakage | `:global()` used sparingly and intentionally | Styles in `<style>` that accidentally affect children | Minor |
| No `!important` abuse | Zero or 1 `!important` in entire codebase | Multiple `!important` overrides | Major |
| Design token consistency | Same token used for same spacing throughout | Inconsistent spacing (16px here, 1rem there) | Minor |
| CSS specificity managed | Low-specificity selectors | Deeply nested selectors (`.a .b .c .d`) | Minor |

### Passing Pattern

```svelte
<!-- Good: Tailwind utilities + custom property for brand colors -->
<style>
  :root {
    --color-brand: theme('colors.blue.600');
    --radius-card: 0.75rem;
  }
</style>

<article class="rounded-[var(--radius-card)] bg-white p-6 shadow-sm
                sm:p-8 md:flex md:gap-6">
  <div class="text-[color:var(--color-brand)] font-semibold">
    <!-- content -->
  </div>
</article>
```

### Failing Pattern

```svelte
<!-- BAD: Inline styles for static values, no responsive design -->
<article style="padding: 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
  <div style="color: #2563eb; font-weight: 600;">
    <!-- content -->
  </div>
</article>
```

---

## Dimension 4: Accessibility (Weight: 15%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | WCAG SC | Pass Evidence | Fail Evidence | Severity |
|-----------|---------|---------------|---------------|----------|
| Interactive elements keyboard-operable | 2.1.1 | All interactive UI reachable by Tab key | `<div onclick>` with no `tabindex` | Critical |
| No keyboard trap | 2.1.2 | Focus moves freely, modals have focus trap with Esc | Focus stuck inside element with no escape | Critical |
| Sufficient color contrast | 1.4.3 | 4.5:1 for normal text, 3:1 for large text | Text with contrast ratio < 4.5:1 | Major |
| Non-text content has text alternative | 1.1.1 | `<img alt="...">`, `aria-label` on icon buttons | `<img>` with no `alt`, icon button with no label | Major |
| Semantic HTML | 1.3.1 | `<nav>`, `<main>`, `<button>`, `<h1>`-`<h6>` | `<div class="button">`, `<div class="nav">` | Major |
| ARIA used correctly | 4.1.2 | `aria-expanded`, `aria-controls` match actual state | `aria-hidden="true"` on focusable elements | Major |
| Focus visible | 2.4.11 (WCAG 2.2) | `:focus-visible` styles present | `outline: none` without visible alternative | Major |
| Focus not obscured | 2.4.12 (WCAG 2.2) | Focused component not hidden by sticky headers | Sticky header covers focused input | Minor |
| Form inputs labeled | 1.3.1 | `<label for>` or `aria-labelledby` on every input | `<input>` with `placeholder` only, no label | Major |
| Error identification | 3.3.1 | Error message associated with field via `aria-describedby` | Error shown visually only (color change) | Major |
| Language set | 3.1.1 | `<html lang="en">` in app.html | Missing `lang` attribute | Minor |

### Passing Pattern

```svelte
<!-- Good: Accessible dialog with focus management -->
<script lang="ts">
  interface Props {
    open: boolean;
    onClose: () => void;
    title: string;
  }
  const { open, onClose, title }: Props = $props();

  let dialogEl = $state<HTMLDialogElement | null>(null);

  $effect(() => {
    if (open && dialogEl) {
      dialogEl.showModal();
    } else if (!open && dialogEl) {
      dialogEl.close();
    }
  });
</script>

<dialog
  bind:this={dialogEl}
  aria-labelledby="dialog-title"
  onclose={onClose}
>
  <h2 id="dialog-title">{title}</h2>
  <slot />
  <button onclick={onClose}>Close</button>
</dialog>
```

### Failing Pattern

```svelte
<!-- BAD: Div-based modal, no focus management, no ARIA -->
<script lang="ts">
  export let isOpen = false;    // Svelte 4 API + no a11y
</script>

{#if isOpen}
  <div class="modal-overlay" on:click={close}>      <!-- Svelte 4 event + no keyboard -->
    <div class="modal">
      <div class="close-btn" on:click={close}>×</div>   <!-- div instead of button -->
      <slot />
    </div>
  </div>
{/if}
```

---

## Dimension 5: Performance (Weight: 15%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | Pass Evidence | Fail Evidence | Severity |
|-----------|---------------|---------------|----------|
| Server data in `+page.server.ts` | DB queries, API keys only in `.server.ts` | Private env vars or DB client in `+page.ts` | Major |
| Code splitting via dynamic import | `import('./HeavyComponent.svelte')` for large components | All components eagerly imported regardless of size | Minor |
| `$effect` not used for derived data | `$derived` for computed values | Long `$effect` chains updating reactive state | Major |
| Images have explicit dimensions | `width` and `height` on `<img>` | `<img src>` with no dimensions (causes layout shift) | Major |
| `preload` used appropriately | `data-sveltekit-preload-data` on nav links | No preloading, slow navigation | Minor |
| Streaming for slow data | `stream: true` in load, deferred promises | All data awaited before page renders | Minor |
| No reactive computation in loops | `$derived` computed once | `$derived` or `$effect` inside `{#each}` blocks | Major |
| `svelte:head` for per-page metadata | `<svelte:head>` in page components | `document.title = ...` in `onMount` | Minor |

### Passing Pattern

```typescript
// Good: +page.server.ts for private data, streaming for slow queries
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, fetch }) => {
  // Fast data resolved immediately
  const user = await locals.getUser();

  // Slow data streamed — page renders while this resolves
  const analytics = fetch('/api/analytics').then(r => r.json());

  return {
    user,
    streamed: { analytics }
  };
};
```

### Failing Pattern

```typescript
// BAD: +page.ts with server-only data (exposed to client bundle)
import { DB_CONNECTION_STRING } from '$env/static/private'; // Error: not available in universal load

export const load = async () => {
  // This will fail — $env/static/private not available in universal load
  const data = await fetchFromDB(DB_CONNECTION_STRING);
  return { data };
};
```

---

## Dimension 6: TypeScript Usage (Weight: 10%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | Pass Evidence | Fail Evidence | Severity |
|-----------|---------------|---------------|----------|
| `strict: true` in tsconfig.json | `"strict": true` in compilerOptions | `"strict": false` or missing | Critical |
| No `as any` casts | Zero `as any` in component code | `data as any` to bypass type checking | Major (per instance) |
| `$props()` explicitly typed | `const { foo }: Props = $props()` | `const props = $props()` (untyped) | Major |
| Load function types from `$types` | `import type { PageLoad } from './$types'` | Manual `load: (event: any) => ...` | Minor |
| Generics used where appropriate | `function fetch<T>(url: string): Promise<T>` | `function fetch(url: string): Promise<any>` | Minor |
| No `@ts-ignore` suppression | Zero `@ts-ignore` comments | `// @ts-ignore` to silence errors | Major (per instance) |
| Discriminated unions for variants | `type Status = { state: 'loading' } | { state: 'error'; message: string }` | `state: string` or boolean flags | Minor |
| Event types explicit | `onclick: (e: MouseEvent) => void` in Props | Untyped event handlers | Minor |

### Passing Pattern

```typescript
// Good: Strict TypeScript with $props typed, $types used, generics
import type { PageLoad } from './$types';

interface Props {
  variant: 'primary' | 'secondary' | 'destructive';
  onclick: (e: MouseEvent) => void;
  disabled?: boolean;
  children: import('svelte').Snippet;
}

const { variant, onclick, disabled = false, children }: Props = $props();
```

```typescript
// Good: load function with $types, no any
export const load: PageLoad = async ({ params, fetch }) => {
  const response = await fetch(`/api/posts/${params.slug}`);
  if (!response.ok) throw error(response.status);
  const post: Post = await response.json();
  return { post };
};
```

### Failing Pattern

```typescript
// BAD: No types, as any escape hatch, no $types
export const load = async ({ params, fetch }: any) => {
  const data = await fetch(`/api/posts/${params.slug}`);
  return { post: (await data.json()) as any };
};
```

---

## Dimension 7: Testing Quality (Weight: 10%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | Pass Evidence | Fail Evidence | Severity |
|-----------|---------------|---------------|----------|
| Tests exist | Test files present for components | Zero test files in codebase | Critical |
| Behavior-first queries | `getByRole('button', { name: /submit/i })` | `getByTestId('submit-btn')` | Minor (per instance) |
| User interaction tested | `userEvent.click()`, `userEvent.type()` | Testing state values directly (`expect(state.count).toBe(1)`) | Major |
| No snapshot tests for structure | Assertions on specific content | `expect(container).toMatchSnapshot()` | Major |
| Mocks limited to boundaries | Only external services mocked | Internal functions mocked | Minor |
| Test isolation | Each test independent, no shared mutable state | `beforeEach` mutates shared variable that persists | Minor |
| Accessibility assertions | `expect(el).toHaveAccessibleName(...)` | Only visual text checked | Minor |
| Test naming is descriptive | `it('shows error message when email is invalid')` | `it('test 1')`, `it('works')` | Minor |

### Passing Pattern

```typescript
// Good: Behavior-first test with user interactions
import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm.svelte';

describe('LoginForm', () => {
  it('shows validation error when submitting empty email', async () => {
    const user = userEvent.setup();
    render(LoginForm);

    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Email is required'
    );
  });

  it('calls onSuccess after valid submission', async () => {
    const onSuccess = vi.fn();
    const user = userEvent.setup();
    render(LoginForm, { props: { onSuccess } });

    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(onSuccess).toHaveBeenCalledOnce();
  });
});
```

### Failing Pattern

```typescript
// BAD: Snapshot test + implementation testing
import { render } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import Counter from './Counter.svelte';

it('renders correctly', () => {
  const { container } = render(Counter);
  expect(container).toMatchSnapshot();  // snapshot anti-pattern
});

it('increments count', () => {
  const count = writable(0);
  // Testing internal state, not user behavior
  count.update(n => n + 1);
  expect(get(count)).toBe(1);
});
```

---

## Dimension 8: UX Patterns (Weight: 10%)

**Start score: 100. Apply deductions per finding below.**

### Scoring Criteria

| Criterion | Pass Evidence | Fail Evidence | Severity |
|-----------|---------------|---------------|----------|
| Loading states for async ops | Skeleton loaders or spinners during data fetch | Page blank while data loads, no indicator | Major |
| Error boundaries present | `+error.svelte` at appropriate route levels | No error boundary; unhandled errors break layout | Major |
| Progressive enhancement on forms | `use:enhance` on form elements | Forms only work with JavaScript; no server action fallback | Major |
| Actionable error messages | "Email already in use. Try logging in." | "An error occurred." | Minor |
| Empty states designed | Intentional empty state UI when list is empty | Blank space when list has no items | Minor |
| Optimistic updates | UI updates before server confirms | UI waits for full server round-trip for simple actions | Minor |
| Form validation feedback | Inline validation with `aria-describedby` | Alert on submit only (no inline feedback) | Minor |
| Navigation feedback | `data-sveltekit-preload-data`, loading indicator | No feedback during route transitions | Minor |

### Passing Pattern

```svelte
<!-- Good: Form with use:enhance, loading state, error handling -->
<script lang="ts">
  import { enhance } from '$app/forms';
  import type { ActionData } from './$types';

  interface Props {
    form: ActionData;
  }
  const { form }: Props = $props();

  let isSubmitting = $state(false);
</script>

<form
  method="POST"
  use:enhance={() => {
    isSubmitting = true;
    return async ({ update }) => {
      await update();
      isSubmitting = false;
    };
  }}
>
  <label>
    Email
    <input
      type="email"
      name="email"
      aria-describedby={form?.errors?.email ? 'email-error' : undefined}
      aria-invalid={!!form?.errors?.email}
    />
    {#if form?.errors?.email}
      <span id="email-error" role="alert">{form.errors.email}</span>
    {/if}
  </label>

  <button type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
    {isSubmitting ? 'Submitting...' : 'Submit'}
  </button>
</form>
```

### Failing Pattern

```svelte
<!-- BAD: No use:enhance, no loading state, generic error -->
<script lang="ts">
  let error = $state('');

  async function handleSubmit(e: Event) {
    e.preventDefault();
    try {
      await fetch('/api/submit', { method: 'POST' });
    } catch {
      error = 'An error occurred.';   // Not actionable
    }
    // No loading state
  }
</script>

<form onsubmit={handleSubmit}>
  <input type="email" name="email" />
  <button>Submit</button>   <!-- No disabled state during submission -->
</form>
{#if error}<p>{error}</p>{/if}
```

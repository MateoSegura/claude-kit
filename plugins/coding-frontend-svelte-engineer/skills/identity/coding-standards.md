# Coding Standards -- Svelte 5 / SvelteKit / TypeScript

This is the detailed style guide for the coding-frontend-svelte-engineer plugin. All subagents follow these conventions.

## TypeScript Conventions

### Strictness

- `strict: true` in `tsconfig.json` (enables `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, etc.)
- `verbatimModuleSyntax: true` -- use `import type` for type-only imports
- No `any`. Use `unknown` + type narrowing or Zod parsing.
- No non-null assertions (`!`) unless the assertion is immediately preceded by a guard that makes it provably safe.

### Return Types

- Every exported function MUST have an explicit return type annotation.
- Load functions (`+page.ts`, `+page.server.ts`, `+layout.ts`, `+layout.server.ts`) MUST have explicit return types.
- Private helper functions inside a module MAY rely on inference if the body is a single expression.

```typescript
// GOOD: exported function with explicit return type
export function formatCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}

// GOOD: load function with explicit return type
export const load: PageServerLoad = async ({ params }): Promise<{ item: Item }> => {
  const item = await db.items.findUnique({ where: { id: params.id } });
  if (!item) throw error(404, 'Item not found');
  return { item };
};

// ACCEPTABLE: private single-expression helper
function double(n: number) { return n * 2; }
```

### Discriminated Unions

Use discriminated unions for variant types. Never use type assertions to narrow.

```typescript
// GOOD
type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: { code: string; message: string } };

function handle(result: Result<User>) {
  if (result.ok) {
    console.log(result.data.name); // TypeScript narrows correctly
  } else {
    console.error(result.error.message);
  }
}

// BAD
const user = result as { data: User }; // type assertion hides errors
```

### Runtime Validation with Zod

Validate all external data at system boundaries: API responses, form submissions, URL parameters, localStorage reads.

```typescript
import { z } from 'zod';

const ItemSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(200),
  price: z.number().positive(),
  status: z.enum(['draft', 'published', 'archived']),
});

type Item = z.infer<typeof ItemSchema>;

export const load: PageServerLoad = async ({ fetch }) => {
  const response = await fetch('/api/items');
  const raw = await response.json();
  const items = z.array(ItemSchema).parse(raw); // throws ZodError on invalid data
  return { items };
};
```

### Import Conventions

- Use `$lib` path alias for all imports from `src/lib/`.
- Use `$app` for SvelteKit app modules (`$app/navigation`, `$app/stores`, `$app/environment`).
- Use `$env` for environment variables (`$env/static/private`, `$env/static/public`).
- Group imports: (1) svelte/sveltekit, (2) third-party, (3) `$lib`, (4) relative.
- Use `import type { ... }` for type-only imports.

```typescript
import { goto, invalidateAll } from '$app/navigation';
import { page } from '$app/stores';
import { z } from 'zod';
import type { PageServerLoad } from './$types';
import { Button } from '$lib/components/ui';
import type { Item } from '$lib/types';
import { formatCurrency } from './utils';
```

## Svelte 5 Conventions

### Runes Only

| Task | Correct (Svelte 5) | Forbidden (Svelte 4) |
|------|---------------------|----------------------|
| Mutable state | `let count = $state(0)` | `let count = 0` with `$:` |
| Computed value | `let doubled = $derived(count * 2)` | `$: doubled = count * 2` |
| Side effect | `$effect(() => { ... })` | `$: { ... }` (reactive statement) |
| Component props | `let { name, age }: Props = $props()` | `export let name; export let age;` |
| Two-way binding | `let { value = $bindable() }: Props = $props()` | `export let value;` with `bind:` |
| Content projection | `{#snippet name()}...{/snippet}` + `{@render name()}` | `<slot name="...">` |
| Event handling | `onclick={handler}` | `on:click={handler}` |
| Shared state | Module-level `$state` or context API | `writable()` / `readable()` stores |

### Component Structure

Order sections consistently within every `.svelte` file:

```svelte
<script lang="ts">
  // 1. Imports
  import type { Snippet } from 'svelte';
  import { Button } from '$lib/components/ui';

  // 2. Props interface and destructuring
  interface Props {
    title: string;
    count?: number;
    children: Snippet;
    onsubmit?: (data: FormData) => void;
  }

  let { title, count = 0, children, onsubmit }: Props = $props();

  // 3. Internal state
  let isOpen = $state(false);

  // 4. Derived values
  let displayCount = $derived(`${count} items`);

  // 5. Effects (with cleanup)
  $effect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') isOpen = false;
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  });

  // 6. Handler functions
  function toggle() {
    isOpen = !isOpen;
  }
</script>

<!-- 7. Template -->
<div class="wrapper">
  <h2>{title}</h2>
  <p>{displayCount}</p>
  <button onclick={toggle} aria-expanded={isOpen}>
    Toggle
  </button>
  {#if isOpen}
    {@render children()}
  {/if}
</div>

<!-- 8. Scoped styles -->
<style>
  .wrapper {
    /* scoped styles here */
  }
</style>
```

### Props Design

- Define a `Props` interface directly in the component (not imported from elsewhere, unless shared across a component family).
- Use `$bindable()` only when two-way binding is the explicit contract.
- Default values go in the destructuring, not in the interface.
- Use `Snippet` type for content projection props.
- All event callback props use the `on` prefix: `onclick`, `onsubmit`, `onchange`, `onselect`.

### Effect Discipline

- Every `$effect` that registers a listener, timer, or subscription MUST return a cleanup function.
- Never read and write the same `$state` variable inside a single `$effect` (infinite loop risk).
- If an `$effect` body has no side effects (no DOM mutation, no network call, no event listener), it should be a `$derived` instead.

## CSS Conventions

### Tailwind Utility-First

- Use Tailwind utility classes as the primary styling method.
- Compose utilities in the template, not in `@apply` blocks (use `@apply` only in base layer for typography resets).
- For repeated class combinations, extract a Svelte component rather than a CSS class.

### CSS Custom Properties for Design Tokens

- Define design tokens as CSS custom properties on `:root` or a theme provider element.
- Reference tokens in Tailwind config via `theme.extend` or directly in `<style>` blocks.
- Theme switching (light/dark) MUST use custom property swapping, not conditional Tailwind classes per element.

```css
:root {
  --color-surface: theme('colors.white');
  --color-text: theme('colors.gray.900');
  --radius-md: 0.5rem;
}

:root.dark {
  --color-surface: theme('colors.gray.900');
  --color-text: theme('colors.gray.100');
}
```

### Scoped Styles

- All component-specific styles go in `<style>` blocks (scoped by default).
- `:global()` is permitted ONLY with a comment explaining why scoping is insufficient:

```svelte
<style>
  /* :global() required: targeting third-party library DOM nodes
     rendered by @fullcalendar which are outside Svelte's scope */
  :global(.fc-event) {
    border-radius: var(--radius-md);
  }
</style>
```

### Responsive Design

- Mobile-first: default styles target small screens, use `sm:`, `md:`, `lg:`, `xl:` for larger.
- Breakpoint usage must be consistent within a feature (do not mix `md:` and arbitrary `min-width` media queries).
- Use `container` queries where component-level responsiveness is needed (Tailwind `@container`).

## File Naming Conventions

### SvelteKit Route Files

| File | Purpose |
|------|---------|
| `+page.svelte` | Page component |
| `+page.ts` | Universal load function (runs on server + client) |
| `+page.server.ts` | Server-only load function |
| `+layout.svelte` | Layout component |
| `+layout.ts` | Universal layout load |
| `+layout.server.ts` | Server-only layout load |
| `+error.svelte` | Error boundary |
| `+server.ts` | API endpoint |

### Component Files

- PascalCase: `Button.svelte`, `DataTable.svelte`, `UserProfileCard.svelte`.
- Colocate component-specific types in the same file or a sibling `types.ts`.
- Group by domain in `$lib/components/`: `ui/`, `layout/`, `forms/`, `data-display/`.

### Route Directories

- kebab-case: `src/routes/user-profile/[id]/+page.svelte`.
- Group layouts with parentheses: `(auth)/login`, `(auth)/register`, `(dashboard)/settings`.
- Parameters in brackets: `[id]`, `[[optional]]`, `[...rest]`.

## Error Handling

### In Load Functions

Throw SvelteKit `error()` for expected errors. Let unexpected errors propagate to the nearest `+error.svelte`.

```typescript
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params }) => {
  const item = await db.items.findUnique({ where: { id: params.id } });
  if (!item) throw error(404, 'Item not found');
  return { item };
};
```

### In Components

Use discriminated union result types for operations that can fail:

```typescript
type LoadState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: { code: string; message: string } };
```

### Error Boundaries

Place `+error.svelte` at route group boundaries to isolate error blast radius:

```
src/routes/
  (dashboard)/
    +error.svelte      <-- catches errors in all dashboard routes
    overview/+page.svelte
    settings/+page.svelte
  (auth)/
    +error.svelte      <-- catches errors in all auth routes
    login/+page.svelte
```

### Never Swallow Errors

```typescript
// BAD
try { await riskyOperation(); } catch { /* silent */ }

// GOOD
try {
  await riskyOperation();
} catch (err) {
  console.error('Operation failed:', err);
  throw error(500, 'Internal error during operation');
}
```

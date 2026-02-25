# Patterns Reference — Svelte 5 / SvelteKit

Detailed pattern catalog with concrete code examples. Each pattern includes problem context, solution, when to use, and trade-offs. These are the reference patterns against which graders evaluate submissions.

---

## Category 1: Reactivity Patterns

### Pattern: $state for Local Mutable Values

**Problem/Context:** A component needs a value that changes over time and drives re-renders.

**Solution:**

```svelte
<script lang="ts">
  // Local counter — use $state
  let count = $state(0);
  let name = $state('');

  // Objects are deeply reactive with $state
  let user = $state<{ name: string; age: number }>({ name: '', age: 0 });
  // Mutation is reactive:
  function birthday() {
    user.age += 1; // triggers reactivity
  }
</script>

<button onclick={() => count++}>{count}</button>
```

**When to use:** Any value owned by the current component that changes over time.

**Trade-offs:** `$state` objects are deep reactive proxies — nested mutations are tracked automatically. This is more powerful than Svelte 4's `export let` and eliminates the need for writable stores for component-local state.

---

### Pattern: $derived for Computed Values

**Problem/Context:** A value should always equal a computation over existing state. If you find yourself setting a variable inside an `$effect`, this pattern applies.

**Solution:**

```svelte
<script lang="ts">
  let items = $state<string[]>([]);
  let filter = $state('');

  // Correct: $derived auto-updates, memoized
  const filtered = $derived(
    items.filter(item => item.toLowerCase().includes(filter.toLowerCase()))
  );

  const isEmpty = $derived(filtered.length === 0);

  // For complex derivations, use $derived.by
  const stats = $derived.by(() => {
    const total = items.length;
    const matching = filtered.length;
    const percentage = total > 0 ? Math.round((matching / total) * 100) : 0;
    return { total, matching, percentage };
  });
</script>
```

**When to use:** Any value that can be expressed as a pure function of other reactive values. Rule: if the value has no "own" state (no direct mutations), it should be `$derived`.

**Trade-offs:** `$derived` is lazy and memoized — it only recomputes when dependencies change. Using `$effect` for derived values bypasses memoization and runs every render cycle, adding unnecessary overhead.

---

### Pattern: $effect for True Side Effects

**Problem/Context:** Code must run in response to state changes and has observable effects outside the reactive system (DOM manipulation, external service calls, logging, timers).

**Solution:**

```svelte
<script lang="ts">
  let searchQuery = $state('');
  let results = $state<SearchResult[]>([]);

  // $effect: used for fetching (a true side effect)
  $effect(() => {
    if (!searchQuery) {
      results = [];
      return;
    }

    const controller = new AbortController();

    fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`, {
      signal: controller.signal
    })
      .then(r => r.json())
      .then(data => { results = data; })
      .catch(err => {
        if (err.name !== 'AbortError') console.error(err);
      });

    // Cleanup: abort in-flight request when searchQuery changes
    return () => controller.abort();
  });
</script>
```

**When to use:** External I/O, DOM focus management, subscription setup/teardown, analytics calls. NOT for computing values.

**Trade-offs:** `$effect` runs at least once, always re-runs when any reactive dependency changes, and must always return a cleanup function when it creates subscriptions or timers. Forgetting cleanup causes memory leaks and stale callbacks.

---

### Pattern: Global State in .svelte.ts Files

**Problem/Context:** State needs to be shared across multiple routes or components without prop drilling or SvelteKit stores.

**Solution:**

```typescript
// src/lib/state/auth.svelte.ts
// The .svelte.ts extension makes runes available in non-component files

interface User {
  id: string;
  email: string;
  role: 'admin' | 'user';
}

// Module-level $state — shared across all importers
let currentUser = $state<User | null>(null);
let isLoading = $state(false);

export function getAuthState() {
  return {
    get user() { return currentUser; },
    get isLoading() { return isLoading; },
  };
}

export async function login(email: string, password: string) {
  isLoading = true;
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      headers: { 'Content-Type': 'application/json' }
    });
    currentUser = await response.json();
  } finally {
    isLoading = false;
  }
}
```

```svelte
<!-- Usage in any component -->
<script lang="ts">
  import { getAuthState } from '$lib/state/auth.svelte.ts';
  const auth = getAuthState();
</script>

{#if auth.user}
  <p>Welcome, {auth.user.email}</p>
{/if}
```

**When to use:** Auth state, theme preferences, shopping cart, or any state that genuinely needs to persist across route navigations.

**Trade-offs:** Module-level `$state` is a singleton per module instance. In SSR contexts, this means state is shared across ALL requests — for server-side rendering, use `setContext`/`getContext` with request-scoped state instead.

---

## Category 2: Component Composition Patterns

### Pattern: Typed Props with $props()

**Problem/Context:** Components need explicit, type-safe contracts for their inputs.

**Solution:**

```svelte
<script lang="ts">
  // Define Props interface BEFORE using $props()
  interface Props {
    // Required props
    variant: 'primary' | 'secondary' | 'destructive';
    onclick: (e: MouseEvent) => void;
    children: import('svelte').Snippet;
    // Optional props with defaults
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    class?: string;
  }

  const {
    variant,
    onclick,
    children,
    size = 'md',
    disabled = false,
    class: className = ''
  }: Props = $props();

  const classes = $derived([
    'btn',
    `btn--${variant}`,
    `btn--${size}`,
    className
  ].filter(Boolean).join(' '));
</script>

<button
  {disabled}
  class={classes}
  aria-disabled={disabled}
  {onclick}
>
  {@render children()}
</button>
```

**When to use:** Every Svelte 5 component that accepts external inputs.

---

### Pattern: Snippets for Reusable Template Fragments

**Problem/Context:** A template has repeating structures that should be extracted without creating a full component.

**Solution:**

```svelte
<script lang="ts">
  interface Item {
    id: string;
    label: string;
    count: number;
  }

  interface Props {
    items: Item[];
    emptyMessage?: string;
  }

  const { items, emptyMessage = 'No items yet.' }: Props = $props();
</script>

<!-- Define the snippet once -->
{#snippet itemRow(item: Item)}
  <li class="flex items-center justify-between py-2">
    <span class="font-medium">{item.label}</span>
    <span class="text-sm text-gray-500 tabular-nums">{item.count}</span>
  </li>
{/snippet}

<!-- Use it in multiple places -->
<ul>
  {#if items.length === 0}
    <li class="text-gray-400 py-4 text-center">{emptyMessage}</li>
  {:else}
    {#each items as item (item.id)}
      {@render itemRow(item)}
    {/each}
  {/if}
</ul>
```

**When to use:** When a template fragment is used 2+ times within a component or when a complex fragment would make the template hard to read inline.

---

### Pattern: Svelte Actions for DOM Integration

**Problem/Context:** Third-party libraries or DOM APIs need to be integrated without polluting component logic with imperative code.

**Solution:**

```typescript
// src/lib/actions/tooltip.ts
import type { Action } from 'svelte/action';

interface TooltipOptions {
  content: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

export const tooltip: Action<HTMLElement, TooltipOptions> = (
  node,
  { content, placement = 'top' }
) => {
  // Initialize tooltip (e.g., Floating UI or Tippy.js)
  let instance = createTooltip(node, { content, placement });

  return {
    update({ content: newContent, placement: newPlacement = 'top' }) {
      instance.setContent(newContent);
      instance.setPlacement(newPlacement);
    },
    destroy() {
      instance.destroy();
    }
  };
};
```

```svelte
<script lang="ts">
  import { tooltip } from '$lib/actions/tooltip.ts';
</script>

<button use:tooltip={{ content: 'Save changes', placement: 'top' }}>
  💾
</button>
```

**When to use:** Any time you need to integrate a DOM library, set up ResizeObserver, manage focus traps, or perform imperative DOM operations.

---

## Category 3: SvelteKit Data Loading Patterns

### Pattern: Server Load for Private Data

**Problem/Context:** A page needs data that requires authentication, database access, or server-side secrets.

**Solution:**

```typescript
// src/routes/dashboard/+page.server.ts
import type { PageServerLoad } from './$types';
import { error, redirect } from '@sveltejs/kit';
import { db } from '$lib/server/db';

export const load: PageServerLoad = async ({ locals, params }) => {
  // locals.user set by hooks.server.ts
  if (!locals.user) {
    redirect(302, '/login');
  }

  const projects = await db.project.findMany({
    where: { userId: locals.user.id },
    orderBy: { updatedAt: 'desc' }
  });

  // Return plain objects only (no class instances)
  return {
    projects: projects.map(p => ({
      id: p.id,
      name: p.name,
      updatedAt: p.updatedAt.toISOString()
    }))
  };
};
```

**When to use:** Database queries, auth checks, server-only environment variables, session access. Data returned by `+page.server.ts` is NEVER included in the client bundle.

---

### Pattern: Universal Load for Public Data

**Problem/Context:** A page needs data that is safe to fetch from both server and client.

**Solution:**

```typescript
// src/routes/blog/[slug]/+page.ts
import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params, fetch }) => {
  const response = await fetch(`/api/posts/${params.slug}`);

  if (response.status === 404) {
    error(404, 'Post not found');
  }
  if (!response.ok) {
    error(500, 'Failed to load post');
  }

  const post = await response.json();
  return { post };
};
```

**When to use:** Public API calls, CMS data, anything that can safely run on the client for navigation-based requests. Note: the `fetch` provided by SvelteKit is server-side-aware.

---

### Pattern: Form Actions with Progressive Enhancement

**Problem/Context:** Forms must work without JavaScript and enhance gracefully when JavaScript is available.

**Solution:**

```svelte
<!-- src/routes/contact/+page.svelte -->
<script lang="ts">
  import { enhance } from '$app/forms';
  import type { ActionData } from './$types';

  interface Props {
    form: ActionData;
  }
  const { form }: Props = $props();

  let isSubmitting = $state(false);
</script>

<!-- Works without JS (native form POST), enhances with JS -->
<form
  method="POST"
  action="?/submit"
  use:enhance={({ formElement, formData, action, cancel }) => {
    isSubmitting = true;

    return async ({ result, update }) => {
      isSubmitting = false;
      await update({ reset: result.type === 'success' });
    };
  }}
>
  <label>
    Name
    <input
      name="name"
      type="text"
      value={form?.values?.name ?? ''}
      aria-describedby={form?.errors?.name ? 'name-error' : undefined}
      aria-invalid={!!form?.errors?.name}
    />
    {#if form?.errors?.name}
      <span id="name-error" role="alert" class="text-red-600 text-sm">
        {form.errors.name}
      </span>
    {/if}
  </label>

  <button type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
    {isSubmitting ? 'Sending...' : 'Send'}
  </button>
</form>
```

```typescript
// src/routes/contact/+page.server.ts
import type { Actions } from './$types';
import { fail } from '@sveltejs/kit';

export const actions: Actions = {
  submit: async ({ request }) => {
    const data = await request.formData();
    const name = data.get('name')?.toString();

    if (!name || name.trim().length < 2) {
      return fail(422, {
        values: { name },
        errors: { name: 'Name must be at least 2 characters' }
      });
    }

    await sendContactEmail({ name });
    return { success: true };
  }
};
```

**When to use:** All user-submitted forms. This is the SvelteKit-idiomatic pattern.

---

## Category 4: TypeScript Strict Patterns

### Pattern: Discriminated Unions for State Variants

**Problem/Context:** A component or store has multiple mutually exclusive states, and type narrowing must work correctly.

**Solution:**

```typescript
// Good: discriminated union, TypeScript can narrow correctly
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string };

let postState = $state<AsyncState<Post>>({ status: 'idle' });

async function loadPost(slug: string) {
  postState = { status: 'loading' };
  try {
    const response = await fetch(`/api/posts/${slug}`);
    const data: Post = await response.json();
    postState = { status: 'success', data };
  } catch (err) {
    postState = {
      status: 'error',
      message: err instanceof Error ? err.message : 'Unknown error'
    };
  }
}
```

```svelte
<!-- TypeScript narrows correctly in template -->
{#if postState.status === 'loading'}
  <Spinner />
{:else if postState.status === 'error'}
  <ErrorMessage message={postState.message} />  <!-- 'message' guaranteed -->
{:else if postState.status === 'success'}
  <PostView post={postState.data} />              <!-- 'data' guaranteed -->
{/if}
```

**When to use:** Any async state, form state with server validation, multi-step wizard state.

---

## Category 5: Testing Patterns

### Pattern: Behavior-First Component Testing

**Problem/Context:** Tests must verify what users experience, not implementation details.

**Solution:**

```typescript
import { render, screen, within } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import SearchInput from './SearchInput.svelte';

describe('SearchInput', () => {
  it('calls onSearch with debounced value as user types', async () => {
    const user = userEvent.setup({ delay: null }); // Disable typing delay
    const onSearch = vi.fn();

    render(SearchInput, {
      props: { onSearch, debounceMs: 0 } // 0ms in test
    });

    const input = screen.getByRole('searchbox');
    await user.type(input, 'svelte');

    expect(onSearch).toHaveBeenCalledWith('svelte');
  });

  it('clears the input when clear button is clicked', async () => {
    const user = userEvent.setup();
    render(SearchInput, { props: { initialValue: 'svelte', onSearch: vi.fn() } });

    const input = screen.getByRole('searchbox');
    expect(input).toHaveValue('svelte');

    await user.click(screen.getByRole('button', { name: /clear search/i }));

    expect(input).toHaveValue('');
    expect(input).toHaveFocus(); // Focus returned to input after clear
  });
});
```

**When to use:** All component tests. Query by role first (`getByRole`), then by label (`getByLabelText`), then by text (`getByText`). `getByTestId` is a last resort.

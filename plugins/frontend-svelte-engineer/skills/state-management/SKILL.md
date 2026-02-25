---
name: frontend-svelte-engineer:state-management
description: "State management architecture for Svelte 5 runes at scale. Covers state taxonomy (local, shared module, server, URL, form state), decision matrix for state location, context API patterns, load function data, form actions, URL synchronization, and migration from Svelte 4 stores. Load this when architecting cross-component state, implementing shared stores, or designing data flow."
user-invocable: false
---

# State Management at Scale — Svelte 5 Runes

Quick reference for state architecture decisions. See [reference.md](reference.md) for advanced patterns, typed store factories, async state, optimistic updates, and context injection.

## State Category Taxonomy

| Category | Scope | Mechanism | When to Use |
|----------|-------|-----------|-------------|
| Local component state | One component | `$state` | Values used and updated in one place |
| Shared module state | App-wide singleton | Module-level `$state` | Global app state (auth user, theme, cart) |
| Server state | Data from server | Load function + `invalidate()` | API data, database records |
| URL state | Serializable, shareable | `$page.url.searchParams` | Filters, pagination, search queries |
| Form state | Form lifecycle | Form actions + `use:enhance` | Mutations, multi-step forms |
| Cross-component | Component tree | `setContext` / `getContext` | Dependency injection, compound components |

## Decision Matrix — Where Should State Live?

```
Is the state used by only ONE component?
  YES → $state inside that component (local state)
  NO  ↓

Is the state URL-shareable? (user can bookmark/copy link)
  YES → URL searchParams via $page.url
  NO  ↓

Is it data from the server that needs refreshing?
  YES → Load function + invalidate() (server state)
  NO  ↓

Is it shared by components in a subtree (not app-wide)?
  YES → setContext / getContext (scoped context)
  NO  ↓

Is it truly global (auth, theme, notifications)?
  YES → Module-level $state singleton
```

## Local Component State

```svelte
<script lang="ts">
  // Simple local state
  let count = $state(0);
  let isOpen = $state(false);

  // Object state — mutations are tracked deeply
  let user = $state({ name: '', email: '' });

  // Derived from local state
  let isValid = $derived(user.name.length > 0 && user.email.includes('@'));
</script>
```

## Shared Module State (Global Singleton)

```typescript
// src/lib/stores/auth.svelte.ts
// Module-level $state — one instance, shared across all components

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

let state = $state<AuthState>({
  user: null,
  loading: false,
  error: null,
});

export function getAuth() {
  return state;  // Return the reactive proxy
}

export async function login(email: string, password: string) {
  state.loading = true;
  state.error = null;
  try {
    state.user = await authService.login(email, password);
  } catch (err) {
    state.error = err instanceof Error ? err.message : 'Login failed';
  } finally {
    state.loading = false;
  }
}

export async function logout() {
  await authService.logout();
  state.user = null;
}
```

```svelte
<!-- Any component -->
<script lang="ts">
  import { getAuth, logout } from '$lib/stores/auth.svelte.ts';
  const auth = getAuth();
</script>

{#if auth.user}
  <p>Hello, {auth.user.name}</p>
  <button onclick={logout}>Sign out</button>
{/if}
```

**Critical**: Module-level `$state` is server-shared in SSR. Use only on the client side (check `browser` from `$app/environment`) OR reset per-request.

## Server State (Load Functions)

```typescript
// src/routes/products/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, depends }) => {
  // Register dependency key for invalidation
  depends('app:products');

  const products = await fetch('/api/products').then(r => r.json());
  return { products };
};
```

```svelte
<!-- After mutation, trigger revalidation -->
<script lang="ts">
  import { invalidate } from '$app/navigation';

  async function deleteProduct(id: string) {
    await fetch(`/api/products/${id}`, { method: 'DELETE' });
    await invalidate('app:products');  // Re-runs load function
  }
</script>
```

## URL State (Shareable Filters)

```svelte
<!-- src/routes/products/+page.svelte -->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  // Read from URL
  let search = $derived($page.url.searchParams.get('q') ?? '');
  let category = $derived($page.url.searchParams.get('cat') ?? 'all');

  // Write to URL (replaceState to avoid polluting history)
  function updateFilter(key: string, value: string) {
    const url = new URL($page.url);
    if (value) {
      url.searchParams.set(key, value);
    } else {
      url.searchParams.delete(key);
    }
    goto(url.toString(), { replaceState: true, keepFocus: true, noScroll: true });
  }
</script>

<input
  value={search}
  oninput={(e) => updateFilter('q', e.currentTarget.value)}
  placeholder="Search..."
/>
```

## Context API (Subtree Dependency Injection)

```typescript
// src/lib/context/theme.ts
import { setContext, getContext } from 'svelte';

const THEME_KEY = Symbol('theme');

interface ThemeContext {
  primary: string;
  mode: 'light' | 'dark';
  setMode: (mode: 'light' | 'dark') => void;
}

export function createTheme() {
  let mode = $state<'light' | 'dark'>('light');

  const ctx: ThemeContext = {
    get primary() { return mode === 'light' ? '#1a56db' : '#60a5fa'; },
    get mode() { return mode; },
    setMode: (m) => { mode = m; },
  };

  setContext(THEME_KEY, ctx);
  return ctx;
}

export function useTheme(): ThemeContext {
  return getContext(THEME_KEY);
}
```

```svelte
<!-- Parent: sets up context -->
<script lang="ts">
  import { createTheme } from '$lib/context/theme.ts';
  createTheme();
</script>

<!-- Child (any depth): consumes context -->
<script lang="ts">
  import { useTheme } from '$lib/context/theme.ts';
  const theme = useTheme();
</script>

<button onclick={() => theme.setMode('dark')}>Dark mode</button>
```

## Form State (Progressive Enhancement)

```typescript
// src/routes/contact/+page.server.ts
import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
  submit: async ({ request }) => {
    const data = await request.formData();
    const email = data.get('email') as string;

    if (!email?.includes('@')) {
      return fail(422, { email, error: 'Invalid email address' });
    }

    await sendContactEmail({ email });
    redirect(303, '/contact/success');
  }
};
```

```svelte
<!-- src/routes/contact/+page.svelte -->
<script lang="ts">
  import { enhance } from '$app/forms';
  import type { ActionData } from './$types';

  let { form }: { form: ActionData } = $props();
  let submitting = $state(false);
</script>

<form
  method="POST"
  action="?/submit"
  use:enhance={() => {
    submitting = true;
    return async ({ update }) => {
      await update();
      submitting = false;
    };
  }}
>
  <input name="email" type="email" value={form?.email ?? ''} />
  {#if form?.error}
    <p class="text-red-500">{form.error}</p>
  {/if}
  <button type="submit" disabled={submitting}>
    {submitting ? 'Sending...' : 'Send'}
  </button>
</form>
```

## Svelte 4 → Svelte 5 State Migration

| Svelte 4 | Svelte 5 | Notes |
|----------|----------|-------|
| `writable(value)` | Module-level `$state` | Remove store imports |
| `derived(store, fn)` | `$derived(expr)` | Expression-based, no import |
| `readable(value)` | Module-level `$state` (read-only getter) | Export getter, not setter |
| `$store` subscription | Direct reference to reactive object | No `$` sigil needed |
| `store.subscribe()` | `$effect(() => { ... })` | Only for external integration |
| `store.update()` | Direct mutation | `state.prop = newValue` |

## Additional Resources

- [reference.md](reference.md) — Typed store factories, dispose patterns, derived state chains, async state (loading/error/data), optimistic updates, cross-component communication patterns, advanced URL sync, state debugging

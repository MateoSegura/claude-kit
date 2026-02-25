# Anti-Patterns — Common Svelte 5 Mistakes

## REACTIVITY ANTI-PATTERNS

### Anti-Pattern: Using $effect for Derived Values

**What developers do wrong**: Using `$effect` to compute a value and assign it to another `$state` variable — treating it like Svelte 4's `$:` reactive declaration.

```svelte
<!-- BAD: Unnecessary side effect, creates extra reactive dependency -->
<script lang="ts">
  let items = $state<string[]>([]);
  let count = $state(0);
  let hasItems = $state(false);

  $effect(() => {
    count = items.length;        // Redundant $state + $effect
    hasItems = items.length > 0; // Creates update cycle: items → effect → count/hasItems → render
  });
</script>
```

**Why it fails**: `$effect` runs AFTER the DOM updates, creating an extra render cycle. If the effect triggers another state change, Svelte must re-render again. It also makes the dependency graph harder to reason about. The `count` and `hasItems` state variables are now inconsistently writable from elsewhere.

```svelte
<!-- GOOD: $derived is lazy, memoized, single-render -->
<script lang="ts">
  let items = $state<string[]>([]);

  let count = $derived(items.length);
  let hasItems = $derived(items.length > 0);
</script>
```

---

### Anti-Pattern: Mutating $derived Values

**What developers do wrong**: Trying to push/modify the array/object returned by `$derived`.

```svelte
<!-- BAD: $derived is read-only — mutations silently fail or throw -->
<script lang="ts">
  let todos = $state([
    { id: 1, text: 'Buy groceries', done: false },
    { id: 2, text: 'Walk dog', done: true },
  ]);

  let activeTodos = $derived(todos.filter(t => !t.done));

  function addActive(text: string) {
    activeTodos.push({ id: Date.now(), text, done: false }); // RUNTIME ERROR
  }
</script>
```

**Why it fails**: `$derived` values are read-only proxies. Mutations on derived arrays throw a runtime error: "Cannot add property to a read-only proxy." Even if they didn't throw, the mutation wouldn't persist because `$derived` recomputes from the source state on the next read.

```svelte
<!-- GOOD: Mutate the source state, $derived recomputes automatically -->
<script lang="ts">
  let todos = $state([
    { id: 1, text: 'Buy groceries', done: false },
    { id: 2, text: 'Walk dog', done: true },
  ]);

  let activeTodos = $derived(todos.filter(t => !t.done));

  function addActive(text: string) {
    todos.push({ id: Date.now(), text, done: false }); // Mutate source
    // activeTodos auto-recomputes on next read
  }
</script>
```

---

### Anti-Pattern: Missing $effect Cleanup

**What developers do wrong**: Registering event listeners or subscriptions in `$effect` without returning a cleanup function.

```svelte
<!-- BAD: Memory leak + event fires after component is destroyed -->
<script lang="ts">
  interface Props { targetEl: HTMLElement | null; }
  let { targetEl }: Props = $props();

  $effect(() => {
    if (!targetEl) return;
    targetEl.addEventListener('click', handleClick);
    // No cleanup! Every time targetEl changes, a new listener is added.
    // After component unmounts, listener still fires on targetEl.
  });
</script>
```

**Why it fails**: When `targetEl` changes or the component unmounts, the old event listener is never removed. This causes: (1) memory leaks, (2) the handler fires with stale component state, (3) in long-running apps, a new listener is stacked on every re-run.

```svelte
<!-- GOOD: Return cleanup function from $effect -->
<script lang="ts">
  interface Props { targetEl: HTMLElement | null; }
  let { targetEl }: Props = $props();

  $effect(() => {
    if (!targetEl) return;

    targetEl.addEventListener('click', handleClick);

    return () => {
      targetEl!.removeEventListener('click', handleClick);
    };
  });
</script>
```

---

### Anti-Pattern: Replacing $state Object Reference

**What developers do wrong**: Replacing an entire `$state` object with a new object, losing fine-grained reactivity on dependent components.

```svelte
<!-- BAD: Wholesale object replacement breaks fine-grained tracking -->
<script lang="ts">
  let user = $state({ name: 'Alice', email: 'alice@example.com', role: 'admin' });

  async function refreshUser() {
    const fresh = await fetchUser();
    user = fresh;  // Creates new proxy — components re-render everything
  }

  // Also bad: direct spread creates new reference
  function updateName(name: string) {
    user = { ...user, name };  // Unnecessary full re-render
  }
</script>
```

**Why it fails**: Fine-grained reactivity only tracks which PROPERTIES were read by each component. When you replace the entire object, Svelte can't know which properties changed — it re-renders all subscribers. For `updateName`, only `user.name` changed, but the spread triggers re-renders of everything reading `user.email` and `user.role` too.

```svelte
<!-- GOOD: Mutate properties directly for fine-grained updates -->
<script lang="ts">
  let user = $state({ name: 'Alice', email: 'alice@example.com', role: 'admin' });

  async function refreshUser() {
    const fresh = await fetchUser();
    // Assign individual properties — only components reading changed props re-render
    user.name = fresh.name;
    user.email = fresh.email;
    user.role = fresh.role;
  }

  function updateName(name: string) {
    user.name = name;  // Only re-renders components that read user.name
  }
</script>
```

---

### Anti-Pattern: Reactive $: Declaration (Svelte 4 Legacy)

**What developers do wrong**: Using Svelte 4's label-based reactive declarations in Svelte 5.

```svelte
<!-- BAD: Legacy syntax — not valid in Svelte 5 runes mode -->
<script lang="ts">
  let count = 0;
  $: doubled = count * 2;
  $: {
    console.log('count changed:', count);
  }
  $: if (count > 10) {
    count = 0;
  }
</script>
```

**Why it fails**: In Svelte 5 runes mode (enabled by `lang="ts"` or explicit runes opt-in), `$:` is not valid syntax. The compiler will throw: "Svelte 5 runes mode does not support reactive declarations." Even in Svelte 4 compatibility mode, `$:` is deprecated and should not be used in new code.

```svelte
<!-- GOOD: Svelte 5 runes equivalents -->
<script lang="ts">
  let count = $state(0);
  let doubled = $derived(count * 2);

  $effect(() => {
    console.log('count changed:', count);
  });

  $effect(() => {
    if (count > 10) count = 0;
  });
</script>
```

---

## DATA LOADING ANTI-PATTERNS

### Anti-Pattern: Client-Side Fetch in onMount

**What developers do wrong**: Fetching data in `onMount` instead of using SvelteKit load functions.

```svelte
<!-- BAD: No SSR, no loading state management, no caching, waterfall after nav -->
<script lang="ts">
  import { onMount } from 'svelte';

  let products = $state<Product[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  onMount(async () => {
    try {
      const res = await fetch('/api/products');
      products = await res.json();
    } catch (e) {
      error = 'Failed to load';
    } finally {
      loading = false;
    }
  });
</script>
```

**Why it fails**: (1) `onMount` only runs in the browser — no SSR, hurting SEO and perceived performance. (2) Every navigation to this page re-fetches, even if data is fresh. (3) Manual loading/error state management is repetitive. (4) After server-side navigation, the page renders empty then fills in (flash of empty content).

```svelte
<!-- GOOD: Use SvelteKit load function -->
```

```typescript
// +page.server.ts
export const load: PageServerLoad = async ({ fetch }) => {
  const res = await fetch('/api/products');
  if (!res.ok) error(500, 'Failed to load products');
  return { products: await res.json() as Product[] };
};
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
  let { data } = $props();
</script>

{#each data.products as product (product.id)}
  <ProductCard {product} />
{/each}
```

---

### Anti-Pattern: Secrets in Universal Load

**What developers do wrong**: Using API keys or secrets in `+page.ts` (universal load), which runs on the client.

```typescript
// BAD: +page.ts runs in the browser — API key exposed to users
import { STRIPE_SECRET_KEY } from '$env/static/private';  // TypeScript ERROR
// OR worse:
const apiKey = 'sk_live_xxxx';  // Hardcoded secret visible in JS bundle
```

**Why it fails**: `+page.ts` is a universal file — it runs both server-side (SSR) AND on the client after navigation. The compiled JS bundle is sent to the browser. Any secrets, credentials, or private env vars will be visible in the browser's network tools.

```typescript
// GOOD: Move secrets to +page.server.ts
// src/routes/checkout/+page.server.ts
import { STRIPE_SECRET_KEY } from '$env/static/private';  // Server-only ✓

export const load: PageServerLoad = async () => {
  const paymentIntent = await stripe.paymentIntents.create({
    amount: 1000,
    currency: 'usd',
    // STRIPE_SECRET_KEY used here, never sent to browser
  });

  return {
    clientSecret: paymentIntent.client_secret,  // Safe to send to client
  };
};
```

---

### Anti-Pattern: Not Invalidating After Mutations

**What developers do wrong**: Mutating data (via fetch or form action) without triggering a data reload, leaving stale data in the UI.

```svelte
<!-- BAD: Data mutation not reflected in UI -->
<script lang="ts">
  let { data } = $props();

  async function deleteProduct(id: string) {
    await fetch(`/api/products/${id}`, { method: 'DELETE' });
    // Nothing happens — data.products still shows the deleted product
  }
</script>
```

**Why it fails**: SvelteKit's load functions cache data per navigation. After a mutation, the cached data is stale. The UI shows deleted/outdated records until the user manually navigates away and back.

```svelte
<!-- GOOD option 1: Use form actions (auto-invalidates) -->
<form method="POST" action="?/delete" use:enhance>
  <input type="hidden" name="id" value={product.id} />
  <button type="submit">Delete</button>
</form>
```

```svelte
<!-- GOOD option 2: Programmatic invalidation -->
<script lang="ts">
  import { invalidate } from '$app/navigation';

  async function deleteProduct(id: string) {
    await fetch(`/api/products/${id}`, { method: 'DELETE' });
    await invalidate('app:products');  // Re-runs any load that depends('app:products')
  }
</script>
```

---

## COMPONENT ANTI-PATTERNS

### Anti-Pattern: Prop Drilling Through Many Levels

**What developers do wrong**: Passing props through 4+ component layers when only the deepest component uses them.

```svelte
<!-- BAD: Page → Layout → Section → Container → Widget all pass `user` -->
<!-- Page.svelte -->
<Layout {user}>
  <Section {user}>
    <Container {user}>
      <UserWidget {user} />
    </Container>
  </Section>
</Layout>
```

**Why it fails**: Every intermediate component must declare `user` in its props and pass it down, even though it doesn't use it. Adding new shared state requires touching every layer. Refactoring one component cascades changes throughout.

```svelte
<!-- GOOD: Context API for cross-cutting concerns -->
<!-- Page.svelte or +layout.svelte -->
<script lang="ts">
  import { setContext } from 'svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  setContext('user', data.user);
</script>

<!-- UserWidget.svelte — accesses context directly, no prop drilling -->
<script lang="ts">
  import { getContext } from 'svelte';
  const user = getContext<User>('user');
</script>
```

---

### Anti-Pattern: Using Legacy Store Syntax in Svelte 5

**What developers do wrong**: Importing and using Svelte 4 stores (`writable`, `readable`, `derived`) in new Svelte 5 components.

```svelte
<!-- BAD: Svelte 4 store in a Svelte 5 component -->
<script lang="ts">
  import { writable, derived } from 'svelte/store';

  const count = writable(0);
  const doubled = derived(count, $c => $c * 2);
</script>

<p>{$count}</p>       <!-- The $ sigil required to subscribe -->
<p>{$doubled}</p>
<button onclick={() => count.update(n => n + 1)}>Increment</button>
```

**Why it fails**: While Svelte 5 maintains backward compatibility with stores, mixing paradigms creates confusion. The `$store` subscription sigil is not needed for runes-based state. New developers encountering both patterns in the same codebase waste time understanding both systems. The store pattern also requires manual subscription management that runes handle automatically.

```svelte
<!-- GOOD: Svelte 5 runes — no import, no $ sigil -->
<script lang="ts">
  let count = $state(0);
  let doubled = $derived(count * 2);
</script>

<p>{count}</p>
<p>{doubled}</p>
<button onclick={() => count++}>Increment</button>
```

---

## STYLING ANTI-PATTERNS

### Anti-Pattern: Inline Style Binding for Theming

**What developers do wrong**: Using `style="color: {themeColor}"` for theme values instead of CSS custom properties.

```svelte
<!-- BAD: Inline styles for theming -->
<script lang="ts">
  let theme = $state({ primary: '#1a56db', bg: '#ffffff' });
</script>

<div style="background-color: {theme.bg};">
  <button style="background-color: {theme.primary}; color: white;">
    Click me
  </button>
</div>
```

**Why it fails**: (1) Inline styles override all CSS cascade, making it impossible to apply hover/focus states with Tailwind. (2) Every component that uses theming needs access to the theme state object. (3) No browser caching or optimization. (4) Performance: Svelte must generate a unique style attribute string on every render.

```svelte
<!-- GOOD: CSS custom properties set once at root -->
<script lang="ts">
  // Set once at app root, all children inherit via CSS cascade
  let mode = $state<'light' | 'dark'>('light');
</script>

<div class:dark={mode === 'dark'}>
  <!-- Tailwind dark: variants work automatically -->
  <button class="bg-primary-500 hover:bg-primary-600 text-white dark:bg-primary-400">
    Click me
  </button>
</div>

<style>
  /* CSS custom properties respond to .dark class */
  :global(:root) {
    --color-primary-500: 216 100% 54%;
  }
  :global(.dark) {
    --color-primary-500: 216 100% 70%;
  }
</style>
```

---

### Anti-Pattern: Excessive :global() Usage

**What developers do wrong**: Using `:global()` throughout component styles instead of scoped styles or component composition.

```svelte
<!-- BAD: Reaches into child component internals with :global() -->
<style>
  :global(.product-card) { border-radius: 12px; }
  :global(.product-card .title) { font-size: 1.25rem; }
  :global(.product-card img) { object-fit: cover; }
</style>
```

**Why it fails**: `:global()` removes the scoping guarantees of Svelte's CSS. The styles may accidentally match unrelated elements throughout the app. It creates hidden dependencies between parent and child components. If you rename a class in `ProductCard.svelte`, the parent's `:global()` silently stops working.

```svelte
<!-- GOOD: Pass class props or use component composition -->
<!-- ProductCard.svelte accepts a class prop -->
<script lang="ts">
  interface Props {
    class?: string;
    imageClass?: string;
  }
  let { class: className = '', imageClass = '' }: Props = $props();
</script>

<div class="product-card {className}">
  <img class="object-cover {imageClass}" />
</div>
```

```svelte
<!-- Parent controls appearance through props, not global selectors -->
<ProductCard class="rounded-xl" imageClass="aspect-video" />
```

# Patterns Reference — Detailed Svelte 5 Pattern Catalog

## REACTIVITY PATTERNS

### Pattern: Derived State Chain

**Problem/Context**: Computing values from multiple reactive sources, especially when intermediate values need re-use.

**Solution**:
```svelte
<script lang="ts">
  let items = $state<Item[]>([]);
  let searchQuery = $state('');
  let sortBy = $state<'name' | 'date'>('name');

  // Chain: each step is independently memoized
  let filtered = $derived(
    items.filter(i => i.name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  let sorted = $derived(
    [...filtered].sort((a, b) =>
      sortBy === 'name' ? a.name.localeCompare(b.name) : b.date - a.date
    )
  );

  let count = $derived(filtered.length);  // Depends on filtered, not sorted
</script>

<p>{count} results</p>
{#each sorted as item (item.id)}
  <ItemRow {item} />
{/each}
```

**When to Use**: Any time you need computed values. Always prefer over `$effect` + intermediate `$state`.

**Trade-offs**: Each `$derived` adds a small memory overhead (one reactive node). Chains are lazy — a `$derived` is not recomputed until it is read. If `sorted` is not rendered, its computation is skipped entirely even when `items` changes.

**Related**: Use `$derived.by` when you need a multi-statement computation block.

---

### Pattern: Effect Cleanup

**Problem/Context**: Side effects that register external listeners (DOM events, WebSocket, timers, observers) need to clean up when the component is destroyed or the effect re-runs.

**Solution**:
```svelte
<script lang="ts">
  interface Props {
    targetId: string;
    onResize: (entry: ResizeObserverEntry) => void;
  }
  let { targetId, onResize }: Props = $props();

  $effect(() => {
    const el = document.getElementById(targetId);
    if (!el) return;

    const observer = new ResizeObserver(([entry]) => onResize(entry));
    observer.observe(el);

    // Return cleanup function — called when effect re-runs or component unmounts
    return () => observer.disconnect();
  });
</script>
```

**When to Use**: Any `$effect` that registers listeners, creates timers, or holds external references.

**Trade-offs**: The cleanup function MUST be synchronous. Async cleanup is not supported — use a flag variable instead.

**Related**: `$effect.pre` for effects that need to run before the DOM updates.

---

### Pattern: Fine-Grained Reactivity for Lists

**Problem/Context**: Rendering large lists where items change individually. Naive approach re-renders the entire list on any change.

**Solution**:
```svelte
<script lang="ts">
  // Each todo's properties are independently reactive
  class Todo {
    id = crypto.randomUUID();
    text = $state('');
    done = $state(false);

    constructor(text: string) {
      this.text = text;
    }

    toggle() {
      this.done = !this.done;
    }
  }

  let todos = $state<Todo[]>([]);
</script>

<!-- Keyed by id: only the changed item re-renders -->
{#each todos as todo (todo.id)}
  <div>
    <input
      type="checkbox"
      checked={todo.done}
      onchange={() => todo.toggle()}
    />
    <span class:line-through={todo.done}>{todo.text}</span>
  </div>
{/each}
```

**When to Use**: Lists with > 20 items that update frequently; any list where items are independently mutable.

**Trade-offs**: Class-based state uses more memory per item vs plain objects. The `$state` in class fields only works in Svelte 5 with runes mode.

---

### Pattern: $state.raw for Wholesale Replacement

**Problem/Context**: Large arrays or objects that you replace entirely (not mutate property-by-property). Deep proxy wrapping on every replacement is expensive.

**Solution**:
```svelte
<script lang="ts">
  // $state.raw: shallow reactivity only — tracks reassignment, not mutations
  let rows = $state.raw<DataRow[]>([]);
  let lastUpdated = $state.raw<Date | null>(null);

  async function refresh() {
    const newRows = await fetchAll();
    rows = newRows;            // Triggers re-render
    lastUpdated = new Date();  // Triggers re-render
    // mutations like rows.push() would NOT trigger re-render
  }
</script>
```

**When to Use**: Data tables, chart datasets, paginated results — any state you replace wholesale.

**Trade-offs**: Cannot use fine-grained mutations (`rows[0].name = 'new'` won't be tracked). Must replace the entire reference.

---

## DATA LOADING PATTERNS

### Pattern: Universal vs Server Load Selection

**Problem/Context**: Choosing between `+page.ts` (universal: runs both SSR + client) and `+page.server.ts` (server-only: secrets, DB, cookies).

**Decision tree**:
```
Does the load function need:
  - cookies / session?         → +page.server.ts
  - database access?           → +page.server.ts
  - API keys / secrets?        → +page.server.ts
  - Only public API calls?     → +page.ts
  - Needs to run on client?    → +page.ts
```

```typescript
// +page.server.ts — auth-gated data
import { redirect, error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, params }) => {
  if (!locals.user) redirect(303, '/login');

  const product = await db.products.findById(params.id);
  if (!product) error(404, 'Product not found');

  return { product };
};
```

```typescript
// +page.ts — public data (also runs on client after navigation)
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, params }) => {
  const res = await fetch(`https://api.example.com/products/${params.id}`);
  if (!res.ok) throw new Error('Not found');
  return { product: await res.json() };
};
```

**Trade-offs**: `+page.server.ts` only runs once (SSR); client navigations re-run it on the server. `+page.ts` runs on the server (SSR) AND on the client after navigation — simpler mental model for public data.

---

### Pattern: Streaming Non-Critical Data

**Problem/Context**: A page has critical data (must be present to render) and non-critical data (can appear after). Awaiting all data blocks the initial render.

**Solution**:
```typescript
// +page.server.ts
export const load: PageServerLoad = async ({ params }) => {
  return {
    // Awaited: critical for initial render
    product: await getProduct(params.id),

    // NOT awaited: streams in after HTML is sent to browser
    reviews: getReviews(params.id),
    relatedProducts: getRelated(params.id),
  };
};
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
  let { data } = $props();
</script>

<ProductDetail product={data.product} />  <!-- Renders immediately -->

{#await data.reviews}
  <div class="animate-pulse h-40 bg-surface-100 rounded" />
{:then reviews}
  <ReviewSection {reviews} />
{/await}
```

**When to Use**: Any page with independently fetchable data where some is slower than others.

**Trade-offs**: Requires streaming-capable hosting (adapter-node, adapter-vercel, adapter-cloudflare — NOT adapter-static).

---

### Pattern: Parallel Data Loading

**Problem/Context**: Multiple independent API calls in a load function. Sequential calls create waterfall latency.

**Solution**:
```typescript
// BAD — sequential: total time = A + B + C
export const load: PageServerLoad = async () => {
  const user = await getUser();
  const products = await getProducts();
  const stats = await getStats();
  return { user, products, stats };
};

// GOOD — parallel: total time = max(A, B, C)
export const load: PageServerLoad = async () => {
  const [user, products, stats] = await Promise.all([
    getUser(),
    getProducts(),
    getStats(),
  ]);
  return { user, products, stats };
};
```

**When to Use**: Any load function with 2+ independent data sources.

**Trade-offs**: `Promise.all` is all-or-nothing — if one fails, all fail. Use `Promise.allSettled` if partial failures are acceptable.

---

## COMPONENT COMPOSITION PATTERNS

### Pattern: Render Delegation with Snippets

**Problem/Context**: A component needs to render flexible content defined by the parent. Svelte 5 replaces slots with snippets.

**Solution**:
```svelte
<!-- Card.svelte -->
<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    children: Snippet;
    header?: Snippet;
    footer?: Snippet;
    class?: string;
  }

  let { children, header, footer, class: className = '' }: Props = $props();
</script>

<div class="rounded-lg border p-4 {className}">
  {#if header}
    <header class="mb-3 font-semibold">
      {@render header()}
    </header>
  {/if}

  <div class="content">
    {@render children()}
  </div>

  {#if footer}
    <footer class="mt-3 pt-3 border-t text-sm text-surface-600">
      {@render footer()}
    </footer>
  {/if}
</div>
```

```svelte
<!-- Usage -->
<Card>
  {#snippet header()}
    <h2>Card Title</h2>
  {/snippet}

  <p>Card content goes here.</p>

  {#snippet footer()}
    <button>Action</button>
  {/snippet}
</Card>
```

**When to Use**: Any component needing flexible content areas. Direct replacement for Svelte 4 named slots.

---

### Pattern: Compound Components with Context

**Problem/Context**: Related components (e.g., Tabs + Tab + TabPanel) need to share state without prop drilling.

**Solution**:
```svelte
<!-- Tabs.svelte -->
<script lang="ts">
  import { setContext } from 'svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    defaultTab?: string;
    children: Snippet;
  }

  let { defaultTab = '', children }: Props = $props();

  let activeTab = $state(defaultTab);

  setContext('tabs', {
    get active() { return activeTab; },
    setActive: (id: string) => { activeTab = id; },
  });
</script>

<div class="tabs">{@render children()}</div>
```

```svelte
<!-- Tab.svelte -->
<script lang="ts">
  import { getContext } from 'svelte';

  interface Props {
    id: string;
    label: string;
  }

  let { id, label }: Props = $props();

  const tabs = getContext<{ active: string; setActive: (id: string) => void }>('tabs');
  let isActive = $derived(tabs.active === id);
</script>

<button
  role="tab"
  aria-selected={isActive}
  onclick={() => tabs.setActive(id)}
  class:active={isActive}
>
  {label}
</button>
```

**When to Use**: Accordion, Tabs, Menu, TreeView — any set of components that logically belong together.

**Trade-offs**: Implicit coupling — Tab must be inside Tabs. Document this requirement clearly. Use Symbol key in production to avoid collision.

---

### Pattern: Headless Components (Actions)

**Problem/Context**: Reusable interactive behavior (tooltip, dropdown, drag-and-drop) without prescribing UI markup.

**Solution**:
```typescript
// src/lib/actions/tooltip.ts
export interface TooltipOptions {
  content: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
}

export function tooltip(node: HTMLElement, options: TooltipOptions) {
  let tooltipEl: HTMLElement | null = null;

  function show() {
    tooltipEl = document.createElement('div');
    tooltipEl.className = 'tooltip';
    tooltipEl.textContent = options.content;
    document.body.appendChild(tooltipEl);
    position();
  }

  function hide() {
    tooltipEl?.remove();
    tooltipEl = null;
  }

  function position() {
    if (!tooltipEl) return;
    const rect = node.getBoundingClientRect();
    tooltipEl.style.top = `${rect.top - tooltipEl.offsetHeight - 8}px`;
    tooltipEl.style.left = `${rect.left + rect.width / 2}px`;
  }

  node.addEventListener('mouseenter', show);
  node.addEventListener('mouseleave', hide);

  return {
    update(newOptions: TooltipOptions) {
      options = newOptions;
      if (tooltipEl) tooltipEl.textContent = newOptions.content;
    },
    destroy() {
      hide();
      node.removeEventListener('mouseenter', show);
      node.removeEventListener('mouseleave', hide);
    }
  };
}
```

```svelte
<!-- Usage: any element, any markup -->
<button use:tooltip={{ content: 'Save your changes', placement: 'top' }}>
  Save
</button>
```

**When to Use**: Tooltips, drag-and-drop, click-outside detection, intersection observer tracking, auto-resize textareas.

---

## ERROR HANDLING PATTERNS

### Pattern: Result Type for Typed Errors

**Problem/Context**: Functions that can fail predictably (validation, API calls, file operations). Throwing exceptions loses type information.

**Solution**:
```typescript
// src/lib/types/result.ts
export type Ok<T> = { ok: true; data: T };
export type Err<E = string> = { ok: false; error: E };
export type Result<T, E = string> = Ok<T> | Err<E>;

export const ok = <T>(data: T): Ok<T> => ({ ok: true, data });
export const err = <E = string>(error: E): Err<E> => ({ ok: false, error });
```

```typescript
// src/lib/server/users.ts
import { ok, err, type Result } from '$lib/types/result.ts';

interface CreateUserError {
  field: 'email' | 'username';
  message: string;
}

export async function createUser(
  email: string,
  username: string
): Promise<Result<User, CreateUserError>> {
  const existing = await db.users.findByEmail(email);
  if (existing) {
    return err({ field: 'email', message: 'Email already in use' });
  }

  const user = await db.users.create({ email, username });
  return ok(user);
}
```

```typescript
// Usage: compile-time exhaustive checking
const result = await createUser(email, username);
if (!result.ok) {
  // TypeScript knows result.error has field + message here
  return fail(422, { [result.error.field]: result.error.message });
}
// TypeScript knows result.data is User here
return { user: result.data };
```

---

### Pattern: Route Error Boundaries

**Problem/Context**: Isolating errors to specific route groups so one broken route doesn't take down the whole app.

**Solution**:
```svelte
<!-- src/routes/(app)/+error.svelte -->
<!-- Catches errors only within the (app) group -->
<script lang="ts">
  import { page } from '$app/stores';
</script>

<div class="flex flex-col items-center justify-center min-h-screen">
  <h1 class="text-4xl font-bold text-surface-900">
    {$page.status}
  </h1>
  <p class="text-surface-600 mt-2">{$page.error?.message}</p>
  <a href="/dashboard" class="mt-4 btn-primary">Back to Dashboard</a>
</div>
```

**When to Use**: Create `+error.svelte` at each route group boundary. The most specific `+error.svelte` in the route hierarchy catches the error.

---

## PERFORMANCE PATTERNS

### Pattern: Lazy Component Loading

**Problem/Context**: Heavy components (rich text editors, map widgets, PDF viewers) should not block the initial page load.

**Solution**:
```svelte
<script lang="ts">
  import type { Component } from 'svelte';
  import type { RichEditorProps } from '$lib/components/RichEditor.svelte';

  let editorVisible = $state(false);

  // Module-level promise — only loads once, not per-render
  const EditorModule = import('$lib/components/RichEditor.svelte');
</script>

{#if !editorVisible}
  <button onclick={() => editorVisible = true}>Open Editor</button>
{:else}
  {#await EditorModule}
    <div class="h-64 animate-pulse bg-surface-100 rounded" />
  {:then { default: RichEditor }}
    <RichEditor content={''} />
  {/await}
{/if}
```

---

### Pattern: Virtualized List

**Problem/Context**: Rendering hundreds or thousands of items. DOM with 1000+ nodes causes jank.

**Solution**:
```svelte
<script lang="ts">
  interface Props {
    items: Item[];
    itemHeight: number;
    containerHeight: number;
  }

  let { items, itemHeight, containerHeight }: Props = $props();

  let scrollTop = $state(0);

  let visibleCount = $derived(Math.ceil(containerHeight / itemHeight) + 2);
  let startIndex = $derived(Math.floor(scrollTop / itemHeight));
  let endIndex = $derived(Math.min(startIndex + visibleCount, items.length));
  let visibleItems = $derived(items.slice(startIndex, endIndex));
  let totalHeight = $derived(items.length * itemHeight);
  let offsetY = $derived(startIndex * itemHeight);
</script>

<div
  style="height: {containerHeight}px; overflow-y: auto;"
  onscroll={(e) => { scrollTop = e.currentTarget.scrollTop; }}
>
  <!-- Full height spacer -->
  <div style="height: {totalHeight}px; position: relative;">
    <!-- Only rendered items -->
    <div style="transform: translateY({offsetY}px);">
      {#each visibleItems as item (item.id)}
        <div style="height: {itemHeight}px;">
          <ItemRow {item} />
        </div>
      {/each}
    </div>
  </div>
</div>
```

**When to Use**: Lists with > 100 items. Consider libraries like `svelte-virtual-list` for production use.

---

## ANIMATION PATTERNS

### Pattern: Orchestrated Svelte Transitions

**Problem/Context**: Coordinating enter/exit animations across multiple elements.

**Solution**:
```svelte
<script lang="ts">
  import { fly, fade, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';

  let visible = $state(false);
</script>

{#if visible}
  <!-- Backdrop: fades in/out -->
  <div
    class="fixed inset-0 bg-black/50"
    transition:fade={{ duration: 200 }}
    onclick={() => visible = false}
  />

  <!-- Modal: flies in from below with delay -->
  <div
    class="fixed inset-x-0 bottom-0 rounded-t-2xl bg-white p-6"
    in:fly={{ y: 100, duration: 300, easing: quintOut, delay: 50 }}
    out:fly={{ y: 100, duration: 200 }}
  >
    <slot />
  </div>
{/if}
```

### Pattern: View Transitions API

**Problem/Context**: Smooth page transitions during SvelteKit navigation.

**Solution**:
```typescript
// svelte.config.js — enable view transitions
export default {
  kit: {
    // View transitions are enabled per-navigation
  }
};
```

```typescript
// src/routes/+layout.ts
import { onNavigate } from '$app/navigation';

onNavigate((navigation) => {
  if (!document.startViewTransition) return;

  return new Promise((resolve) => {
    document.startViewTransition(async () => {
      resolve();
      await navigation.complete;
    });
  });
});
```

```css
/* src/app.css — customize the transition */
@keyframes fade-in {
  from { opacity: 0; transform: translateY(4px); }
}
@keyframes fade-out {
  to { opacity: 0; transform: translateY(-4px); }
}

::view-transition-old(root) {
  animation: 150ms ease-in both fade-out;
}
::view-transition-new(root) {
  animation: 200ms ease-out both fade-in;
}
```

**When to Use**: Any SvelteKit app targeting modern browsers (Chrome 111+, Safari 18+, Firefox behind flag as of 2025). Always provide fallback.

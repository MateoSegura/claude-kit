# State Management Reference — Advanced Patterns

## Typed Store Factory Pattern

For reusable reactive state with a consistent interface:

```typescript
// src/lib/stores/create-store.svelte.ts
type StoreState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

interface Store<T> {
  readonly state: StoreState<T>;
  load: () => Promise<void>;
  reset: () => void;
}

export function createStore<T>(fetcher: () => Promise<T>): Store<T> {
  let state = $state<StoreState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  return {
    get state() { return state; },

    async load() {
      state.loading = true;
      state.error = null;
      try {
        state.data = await fetcher();
      } catch (err) {
        state.error = err instanceof Error ? err.message : 'Unknown error';
      } finally {
        state.loading = false;
      }
    },

    reset() {
      state = { data: null, loading: false, error: null };
    }
  };
}
```

```typescript
// Usage: src/lib/stores/products.svelte.ts
import { createStore } from './create-store.svelte.ts';

export const productsStore = createStore(async () => {
  const res = await fetch('/api/products');
  if (!res.ok) throw new Error('Failed to load products');
  return res.json() as Promise<Product[]>;
});
```

```svelte
<script lang="ts">
  import { productsStore } from '$lib/stores/products.svelte.ts';
  import { onMount } from 'svelte';

  const { state } = productsStore;
  onMount(() => productsStore.load());
</script>

{#if state.loading}
  <Spinner />
{:else if state.error}
  <ErrorMessage message={state.error} />
{:else if state.data}
  <ProductList products={state.data} />
{/if}
```

## Disposing Module-Level State

For state that needs cleanup (WebSocket, timers, event listeners):

```typescript
// src/lib/stores/realtime.svelte.ts
import { browser } from '$app/environment';

let ws: WebSocket | null = null;
let messages = $state<Message[]>([]);
let connected = $state(false);

export function getMessages() { return messages; }
export function isConnected() { return connected; }

export function connect(url: string) {
  if (!browser) return;  // Never connect during SSR

  ws = new WebSocket(url);

  ws.onopen = () => { connected = true; };
  ws.onmessage = (e) => {
    messages = [...messages, JSON.parse(e.data)];
  };
  ws.onclose = () => { connected = false; };
}

// Call from onMount's cleanup or layout's onDestroy
export function disconnect() {
  ws?.close();
  ws = null;
}
```

```svelte
<script lang="ts">
  import { connect, disconnect, getMessages } from '$lib/stores/realtime.svelte.ts';
  import { onMount } from 'svelte';

  const messages = getMessages();

  onMount(() => {
    connect('wss://api.example.com/ws');
    return () => disconnect();  // Cleanup on component destroy
  });
</script>
```

## Derived State Chains

Build complex computed state from simpler pieces:

```typescript
// Avoiding diamond dependencies in derived chains
let products = $state<Product[]>([]);
let searchQuery = $state('');
let selectedCategory = $state<string | null>(null);
let sortOrder = $state<'asc' | 'desc'>('asc');

// Each derived depends only on what it needs
let filteredByCategory = $derived(
  selectedCategory
    ? products.filter(p => p.category === selectedCategory)
    : products
);

let filteredBySearch = $derived(
  searchQuery
    ? filteredByCategory.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : filteredByCategory
);

let sortedProducts = $derived(
  [...filteredBySearch].sort((a, b) =>
    sortOrder === 'asc'
      ? a.name.localeCompare(b.name)
      : b.name.localeCompare(a.name)
  )
);

// totalCount depends only on filtered results, not sort order
let totalCount = $derived(filteredBySearch.length);
```

**Key insight**: Structure derivations so each step depends on the minimum necessary state. This avoids re-computing expensive operations when unrelated state changes.

## Async State with Discriminated Unions

Use discriminated unions for type-safe async state instead of separate loading/error/data variables:

```typescript
// src/lib/types/async.ts
export type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string };
```

```svelte
<script lang="ts">
  import type { AsyncState } from '$lib/types/async.ts';

  interface User { id: string; name: string; }

  let userState = $state<AsyncState<User>>({ status: 'idle' });

  async function loadUser(id: string) {
    userState = { status: 'loading' };
    try {
      const res = await fetch(`/api/users/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: User = await res.json();
      userState = { status: 'success', data };
    } catch (err) {
      userState = { status: 'error', error: err instanceof Error ? err.message : 'Unknown' };
    }
  }
</script>

{#if userState.status === 'idle'}
  <button onclick={() => loadUser('123')}>Load User</button>
{:else if userState.status === 'loading'}
  <Spinner />
{:else if userState.status === 'error'}
  <ErrorBanner message={userState.error} />
{:else if userState.status === 'success'}
  <UserCard user={userState.data} />
{/if}
```

## Optimistic Updates

```svelte
<script lang="ts">
  let todos = $state<Todo[]>([]);

  async function toggleTodo(id: string) {
    // 1. Optimistic update — immediate UI feedback
    const todo = todos.find(t => t.id === id)!;
    todo.done = !todo.done;

    try {
      // 2. Server mutation
      await fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ done: todo.done }),
      });
    } catch {
      // 3. Revert on failure
      todo.done = !todo.done;
      // Show error toast
    }
  }
</script>
```

## Cross-Component Communication Patterns

### Event-Based (Parent to Child to Parent)

```svelte
<!-- Child component -->
<script lang="ts">
  interface Props {
    onselect: (item: Item) => void;
  }
  let { onselect }: Props = $props();
</script>

<button onclick={() => onselect(item)}>Select</button>
```

```svelte
<!-- Parent -->
<script lang="ts">
  function handleSelect(item: Item) {
    console.log('Selected:', item);
  }
</script>

<ChildComponent onselect={handleSelect} />
```

### Shared Module State (Any-to-Any)

```typescript
// src/lib/stores/notifications.svelte.ts
let notifications = $state<Notification[]>([]);

export function getNotifications() { return notifications; }

export function addNotification(n: Omit<Notification, 'id'>) {
  const id = crypto.randomUUID();
  notifications = [...notifications, { ...n, id }];

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    notifications = notifications.filter(x => x.id !== id);
  }, 5000);
}
```

### Context (Scoped Subtree)

```typescript
// Typed context with Symbol key (avoids string collision)
const CART_KEY = Symbol('cart');

interface CartContext {
  items: CartItem[];
  add: (product: Product) => void;
  remove: (id: string) => void;
  total: number;
}

export function createCart() {
  let items = $state<CartItem[]>([]);
  let total = $derived(items.reduce((sum, i) => sum + i.price * i.qty, 0));

  const ctx: CartContext = {
    get items() { return items; },
    get total() { return total; },
    add: (product) => {
      const existing = items.find(i => i.id === product.id);
      if (existing) {
        existing.qty++;
      } else {
        items.push({ ...product, qty: 1 });
      }
    },
    remove: (id) => {
      items = items.filter(i => i.id !== id);
    }
  };

  setContext(CART_KEY, ctx);
  return ctx;
}

export function useCart(): CartContext {
  const ctx = getContext<CartContext>(CART_KEY);
  if (!ctx) throw new Error('useCart must be called within a CartProvider');
  return ctx;
}
```

## Advanced URL State Synchronization

For multi-parameter filter state with debouncing:

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  // Read all filter state from URL at once
  let filters = $derived({
    q: $page.url.searchParams.get('q') ?? '',
    category: $page.url.searchParams.get('cat') ?? '',
    page: Number($page.url.searchParams.get('page') ?? '1'),
    sort: $page.url.searchParams.get('sort') ?? 'relevance',
  });

  let debounceTimer: ReturnType<typeof setTimeout>;

  function updateFilters(updates: Partial<typeof filters>) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const url = new URL($page.url);

      for (const [key, value] of Object.entries(updates)) {
        const paramKey = key === 'page' ? 'page' : key === 'category' ? 'cat' : key;
        if (value && value !== '' && value !== 1) {
          url.searchParams.set(paramKey, String(value));
        } else {
          url.searchParams.delete(paramKey);
        }
      }

      // Reset to page 1 when filters change
      if (!('page' in updates)) {
        url.searchParams.delete('page');
      }

      goto(url.toString(), { replaceState: true, keepFocus: true, noScroll: true });
    }, 300);
  }
</script>
```

## State Debugging Techniques

```typescript
// Debug reactive state changes in development
import { dev } from '$app/environment';

if (dev) {
  $effect(() => {
    console.log('state changed:', $state.snapshot(myState));
  });
}
```

```typescript
// $state.snapshot creates a plain (non-reactive) copy for logging/serialization
function logState() {
  const snapshot = $state.snapshot(complexState);
  console.log(JSON.stringify(snapshot, null, 2));
}
```

## SSR Safety for Module-Level State

Module-level `$state` in SvelteKit's SSR is shared across ALL requests on the server. To avoid data leaking between users:

```typescript
// BAD: shared across all SSR requests — user data leaks!
let currentUser = $state<User | null>(null);

// GOOD option 1: Use load functions (per-request)
// GOOD option 2: Gate on browser
import { browser } from '$app/environment';
let currentUser = browser ? $state<User | null>(null) : null;

// GOOD option 3: Store in context (per-request lifecycle)
// See context patterns above
```

## Form State with Multi-Step Wizard

```svelte
<script lang="ts">
  type Step = 'personal' | 'address' | 'review';

  let currentStep = $state<Step>('personal');
  let formData = $state({
    name: '',
    email: '',
    street: '',
    city: '',
    country: '',
  });

  const steps: Step[] = ['personal', 'address', 'review'];
  let stepIndex = $derived(steps.indexOf(currentStep));
  let canGoBack = $derived(stepIndex > 0);
  let canGoForward = $derived(stepIndex < steps.length - 1 && isCurrentStepValid());

  function isCurrentStepValid(): boolean {
    if (currentStep === 'personal') {
      return formData.name.length > 0 && formData.email.includes('@');
    }
    if (currentStep === 'address') {
      return formData.street.length > 0 && formData.city.length > 0;
    }
    return true;
  }

  function next() { if (canGoForward) currentStep = steps[stepIndex + 1]; }
  function back() { if (canGoBack) currentStep = steps[stepIndex - 1]; }
</script>
```

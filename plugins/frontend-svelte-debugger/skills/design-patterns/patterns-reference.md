# Patterns Reference — Svelte 5 / SvelteKit

Detailed pattern catalog with concrete Svelte 5 code examples, when-to-use guidance, and trade-off analysis.

---

## Reactivity Patterns

### $state Initialization

**Problem/Context**: Declaring reactive state that the framework tracks for updates.

**Solution**:
```svelte
<script lang="ts">
  // Primitive: directly reactive
  let count = $state(0);

  // Object: deeply reactive proxy — mutations on nested props trigger updates
  let user = $state({ name: 'Alice', prefs: { theme: 'dark' } });
  user.prefs.theme = 'light';  // triggers update

  // Array: deeply reactive — push/pop/splice all trigger updates
  let items = $state<string[]>([]);
  items.push('new');  // triggers update

  // Class with reactive fields (Svelte 5.2+)
  class Counter {
    value = $state(0);
    increment() { this.value++; }
  }
  const counter = new Counter();
</script>
```

**When-to-Use**: All component-local reactive state. Use `$state.raw` when deep reactivity is costly and you only reassign at the top level.

**Trade-offs**: Deep proxy has ~5-15% overhead vs raw objects for large arrays. For arrays >1000 items that mutate frequently, benchmark `$state.raw` with manual reassignment.

**Related Patterns**: `$state.raw` (shallow-only reactivity), `$state.snapshot` (extract for external APIs)

---

### $state.raw — Shallow Reactivity

**Problem/Context**: You have a large object or array that you always reassign rather than mutate. Deep proxying is wasted overhead.

**Solution**:
```svelte
<script lang="ts">
  // Only reassignment triggers update; internal mutations do NOT
  let config = $state.raw({ width: 800, height: 600, flags: [1, 2, 3] });

  function updateConfig(newWidth: number) {
    // MUST reassign the whole object — mutation won't trigger
    config = { ...config, width: newWidth };
  }
</script>
```

**When-to-Use**: Large config objects, immutable data from an API response, performance-sensitive large arrays.

**Trade-offs**: Faster reads, no mutation tracking. Developer must remember to reassign — partial mutation silently fails to update UI.

---

### $state.snapshot — Extracting Plain Values

**Problem/Context**: Need to pass reactive state to an external API that does not accept a Proxy (e.g., `structuredClone`, `postMessage`, Tauri `invoke`, JSON serialization).

**Solution**:
```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  let device = $state({ id: 'usb-001', config: { baud: 9600 } });

  async function save() {
    // $state.snapshot produces a plain object, safe for JSON/IPC
    const plain = $state.snapshot(device);
    await invoke('save_device_config', { config: plain });
  }

  // Also use for structuredClone
  const copy = structuredClone($state.snapshot(device));
</script>
```

**When-to-Use**: Any time reactive state leaves the Svelte reactivity system.

---

### $derived Chains

**Problem/Context**: Computing values from other reactive state; values should update automatically and be memoized.

**Solution**:
```svelte
<script lang="ts">
  let items = $state<{ name: string; active: boolean }[]>([]);
  let query = $state('');

  // Simple expression
  let activeCount = $derived(items.filter(i => i.active).length);

  // Complex logic: use $derived.by
  let filtered = $derived.by(() => {
    if (!query.trim()) return items;
    const q = query.toLowerCase();
    return items.filter(i => i.name.toLowerCase().includes(q));
  });

  // Chained: derived from another derived (fine — tracks dependencies correctly)
  let hasResults = $derived(filtered.length > 0);
</script>
```

**When-to-Use**: Any computed value derived from `$state`. Prefer over `$effect` for synchronous value computation.

**Trade-offs**: `$derived` is lazy and memoized — only recomputes when accessed AND dependencies changed. `$effect` runs eagerly after every dependency change regardless of reads.

**Related Patterns**: Never use `$derived` with async functions — use `$effect` + `$state` for async data fetching.

---

### $effect with Cleanup

**Problem/Context**: Side effects that must be torn down when the component unmounts or dependencies change (timers, subscriptions, event listeners).

**Solution**:
```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  let deviceData = $state<string | null>(null);

  $effect(() => {
    // Set up subscription
    const unlistenPromise = listen<string>('device-data', (event) => {
      deviceData = event.payload;
    });

    // Return cleanup function — called on unmount or before re-running
    return () => {
      unlistenPromise.then(unlisten => unlisten());
    };
  });
</script>
```

**When-to-Use**: Any subscription, timer, DOM event listener, or resource that needs cleanup. ALWAYS return a cleanup function.

**Trade-offs**: No async callback support — if you need async setup, use a sync outer function with an async IIFE inside, and track the promise for cleanup.

---

### $effect.pre for DOM Measurement

**Problem/Context**: Reading DOM dimensions or positions that must be captured before Svelte patches the DOM in the current flush.

**Solution**:
```svelte
<script lang="ts">
  let el: HTMLElement;
  let prevHeight = $state(0);
  let contentItems = $state<string[]>([]);

  $effect.pre(() => {
    // Runs BEFORE DOM update — safe to read layout
    if (el) {
      prevHeight = el.offsetHeight;
    }
    // contentItems is tracked as a dependency — re-runs when it changes
    contentItems; // explicit read to track dependency
  });
</script>

<div bind:this={el}>
  {#each contentItems as item}
    <p>{item}</p>
  {/each}
</div>
```

**When-to-Use**: FLIP animations, scroll position preservation, layout snapshot before transition.

---

## Component Patterns

### Compound Components via Context

**Problem/Context**: A parent component controls shared state; multiple child components need access without deep prop drilling.

**Solution**:
```svelte
<!-- Tabs.svelte (parent) -->
<script lang="ts">
  import { setContext } from 'svelte';
  let { children } = $props();

  const state = $state({ activeTab: 0 });
  setContext('tabs', {
    get active() { return state.activeTab; },
    select: (i: number) => { state.activeTab = i; }
  });
</script>
<div class="tabs">{@render children()}</div>

<!-- Tab.svelte (child) -->
<script lang="ts">
  import { getContext } from 'svelte';
  let { index, label } = $props<{ index: number; label: string }>();
  const tabs = getContext<{ active: number; select: (i: number) => void }>('tabs');
</script>
<button
  class:active={tabs.active === index}
  onclick={() => tabs.select(index)}
>{label}</button>
```

**When-to-Use**: Tab groups, accordion, select/option pairs, form field groups.

**Trade-offs**: Context is not reactive by default — use getter functions or `$state` objects inside the context value, not primitive copies.

---

### Snippet Composition

**Problem/Context**: Customizable regions within a component (Svelte 5 replacement for named slots).

**Solution**:
```svelte
<!-- Card.svelte -->
<script lang="ts">
  let { header, children, footer }: {
    header?: import('svelte').Snippet;
    children: import('svelte').Snippet;
    footer?: import('svelte').Snippet;
  } = $props();
</script>
<div class="card">
  {#if header}{@render header()}{/if}
  <div class="body">{@render children()}</div>
  {#if footer}{@render footer()}{/if}
</div>

<!-- Usage -->
<Card>
  {#snippet header()}<h2>Title</h2>{/snippet}
  <p>Content goes here</p>
  {#snippet footer()}<button>Action</button>{/snippet}
</Card>
```

**When-to-Use**: Any component with variable layout regions. Snippets can accept parameters (e.g., `{#snippet row(item)}`).

---

### Error Boundaries via +error.svelte

**Problem/Context**: Catching errors from `load` functions and form actions without crashing the entire page.

**Solution**:
```svelte
<!-- src/routes/+error.svelte -->
<script lang="ts">
  import { page } from '$app/state';
</script>

<h1>{page.status} — {page.error?.message ?? 'Unknown error'}</h1>
{#if page.status === 404}
  <p>The page you requested does not exist.</p>
{:else if page.status >= 500}
  <p>An internal error occurred. Please try again.</p>
{/if}
```

**Server-side error throwing**:
```typescript
// +page.server.ts
import { error } from '@sveltejs/kit';
export const load = async ({ params }) => {
  const item = await db.find(params.id);
  if (!item) throw error(404, 'Item not found');
  return { item };
};
```

**When-to-Use**: Any route that may fail to load. Scoped `+error.svelte` files handle errors for their route segment only.

---

## Routing Patterns

### Load Function Data Flow

**Problem/Context**: Fetching data server-side and passing it to the page component.

**Solution**:
```typescript
// +page.server.ts
import type { PageServerLoad } from './$types';
export const load: PageServerLoad = async ({ params, fetch, depends }) => {
  // Mark data as dependent on a custom key for manual invalidation
  depends('app:items');
  const res = await fetch(`/api/items/${params.id}`);
  if (!res.ok) throw error(res.status, await res.text());
  return { item: await res.json() };
};
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
  import type { PageData } from './$types';
  let { data }: { data: PageData } = $props();
  // data.item is available; no need to fetch client-side
</script>
<h1>{data.item.name}</h1>
```

**When-to-Use**: All data that can be fetched before page render. Universal `+page.ts` runs on both server and client; `+page.server.ts` runs server-only.

**Trade-offs**: Server load adds a round trip on client navigation. For data that changes frequently, consider streaming or client-side fetching with SWR pattern.

---

### Form Actions

**Problem/Context**: Handling HTML form submissions with server-side validation and progressive enhancement.

**Solution**:
```typescript
// +page.server.ts
import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
  create: async ({ request, locals }) => {
    const data = await request.formData();
    const name = data.get('name') as string;

    if (!name || name.length < 2) {
      // Use fail() — do NOT throw — to return validation errors
      return fail(422, { name, error: 'Name must be at least 2 characters' });
    }
    await locals.db.create({ name });
    throw redirect(303, '/items');
  }
};
```

**When-to-Use**: Any mutation operation — create, update, delete. Works without JavaScript (progressive enhancement).

---

### Hooks: handle and handleError

**Problem/Context**: Intercepting every server request for auth, logging, or request transformation.

**Solution**:
```typescript
// src/hooks.server.ts
import type { Handle, HandleServerError } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  // Attach session to event.locals before every request
  event.locals.user = await getSession(event.cookies);
  const response = await resolve(event);
  response.headers.set('X-Frame-Options', 'DENY');
  return response;
};

export const handleError: HandleServerError = async ({ error, event }) => {
  // Log and return safe message — never expose internal error to client
  console.error('Server error:', error, event.url.pathname);
  return { message: 'An unexpected error occurred' };
};
```

---

## Hardware IPC Patterns (Tauri)

### Tauri invoke — Request/Response

**Problem/Context**: Calling a Rust backend command from Svelte; handling async results and errors.

**Solution**:
```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  let status = $state<'idle' | 'loading' | 'error'>('idle');
  let result = $state<string | null>(null);

  async function connect(deviceId: string) {
    status = 'loading';
    try {
      // $state.snapshot not needed for primitives; use it for objects
      result = await invoke<string>('connect_device', { deviceId });
      status = 'idle';
    } catch (e) {
      status = 'error';
      console.error('Tauri invoke failed:', e);
    }
  }
</script>
```

**When-to-Use**: One-shot commands: connect, disconnect, read config, send command.

---

### listen/emit — Event Streams

**Problem/Context**: Receiving continuous data from hardware (serial data, BLE notifications) without polling.

**Solution**:
```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';

  let latestReading = $state<number | null>(null);

  $effect(() => {
    // listen() returns a Promise<UnlistenFn>
    const unlistenPromise = listen<number>('sensor-reading', (event) => {
      latestReading = event.payload;
    });

    // MUST clean up — leaked listeners survive component destruction
    return () => {
      unlistenPromise.then(unlisten => unlisten());
    };
  });
</script>
```

**When-to-Use**: Serial data streams, BLE characteristic notifications, progress events.

---

### Device State Machine

**Problem/Context**: Tracking complex device lifecycle (disconnected → connecting → connected → error) without invalid state combinations.

**Solution**:
```svelte
<script lang="ts">
  type DeviceState =
    | { status: 'disconnected' }
    | { status: 'connecting'; deviceId: string }
    | { status: 'connected'; deviceId: string; handle: number }
    | { status: 'error'; reason: string };

  let device = $state<DeviceState>({ status: 'disconnected' });

  async function connect(id: string) {
    device = { status: 'connecting', deviceId: id };
    try {
      const handle = await invoke<number>('open_device', { id });
      device = { status: 'connected', deviceId: id, handle };
    } catch (e) {
      device = { status: 'error', reason: String(e) };
    }
  }
</script>

{#if device.status === 'connected'}
  <p>Connected: {device.deviceId} (handle {device.handle})</p>
{:else if device.status === 'error'}
  <p class="error">{device.reason}</p>
{/if}
```

**When-to-Use**: Any hardware with connection lifecycle; prevents partial state from causing undefined behavior.

---

## Error Handling Patterns

### Structured Error Propagation

**Problem/Context**: Surfacing errors from load functions, actions, and API calls in a way that integrates with SvelteKit's error system.

**Solution**:
```typescript
// Typed error helper
import { error } from '@sveltejs/kit';

// In load function — throws to nearest +error.svelte
export const load = async ({ params }) => {
  const device = await getDevice(params.id).catch(() => null);
  if (!device) throw error(404, { message: `Device ${params.id} not found` });
  if (!device.authorized) throw error(403, { message: 'Not authorized' });
  return { device };
};
```

**When-to-Use**: All server-side error conditions. Client-side errors (in `$effect`, event handlers) should be caught locally and stored in `$state`.

---

### Retry with Exponential Backoff

**Problem/Context**: Transient hardware or network failures that resolve with a retry.

**Solution**:
```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  baseDelayMs = 250
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (e) {
      lastError = e;
      if (attempt < maxAttempts - 1) {
        await new Promise(r => setTimeout(r, baseDelayMs * 2 ** attempt));
      }
    }
  }
  throw lastError;
}

// Usage in Svelte
$effect(() => {
  withRetry(() => invoke('connect_device', { id }))
    .then(handle => { device = { status: 'connected', handle }; })
    .catch(e => { device = { status: 'error', reason: String(e) }; });
});
```

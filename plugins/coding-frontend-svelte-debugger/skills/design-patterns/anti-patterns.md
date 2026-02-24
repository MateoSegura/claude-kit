# Anti-Patterns — Svelte 5 / SvelteKit

Common mistakes developers make when writing Svelte 5 code. Each entry shows what the code looks like, why it fails, and the correct version.

---

## $effect for State Synchronization

**What developers do wrong**: Using `$effect` to keep one piece of `$state` in sync with another.

```svelte
<!-- BAD: $effect for state sync -->
<script lang="ts">
  let firstName = $state('');
  let lastName = $state('');
  let fullName = $state('');  // wrong: this is derived state

  $effect(() => {
    fullName = `${firstName} ${lastName}`;  // runs as a side effect
  });
</script>
```

**Why it fails**: Creates a needless write cycle. `$effect` is scheduled after the DOM update; the `fullName` write triggers another update cycle. If `fullName` is also read during the same effect, you risk an infinite loop. Svelte may warn: "Effect invalidated by state it reads."

```svelte
<!-- GOOD: $derived for computed state -->
<script lang="ts">
  let firstName = $state('');
  let lastName = $state('');
  let fullName = $derived(`${firstName} ${lastName}`);  // memoized, no side effect
</script>
```

---

## Destructuring Reactive $state

**What developers do wrong**: Destructuring a `$state` object into local variables, expecting the variables to remain reactive.

```svelte
<!-- BAD: destructuring breaks reactivity -->
<script lang="ts">
  let user = $state({ name: 'Alice', age: 30 });
  let { name, age } = user;  // name and age are plain values, NOT reactive

  function birthday() {
    age++;  // does NOT update user.age or trigger UI update
  }
</script>
<p>{name}</p>  <!-- never updates after destructuring -->
```

**Why it fails**: Destructuring extracts the VALUE at the time of destructuring, not a reactive reference. The Svelte compiler cannot track mutations on a plain variable that was copied from a proxy.

```svelte
<!-- GOOD: access properties directly on the state object -->
<script lang="ts">
  let user = $state({ name: 'Alice', age: 30 });

  function birthday() {
    user.age++;  // mutates the proxy — triggers update
  }
</script>
<p>{user.name}</p>
```

---

## Async Callback in $effect

**What developers do wrong**: Passing an `async` function directly to `$effect`.

```svelte
<!-- BAD: async effect — cleanup never runs -->
<script lang="ts">
  let data = $state<string | null>(null);

  $effect(async () => {
    const result = await fetch('/api/data').then(r => r.text());
    data = result;
    return () => {
      // This cleanup function is on the Promise returned by async fn,
      // NOT the cleanup function Svelte expects. It NEVER runs.
      console.log('cleanup');
    };
  });
</script>
```

**Why it fails**: `$effect` expects a synchronous function that optionally returns a cleanup function. An `async` function always returns a Promise, so the "return value" Svelte sees is a Promise, not a cleanup function. The cleanup is never called.

```svelte
<!-- GOOD: async IIFE inside sync $effect -->
<script lang="ts">
  let data = $state<string | null>(null);
  let cancelled = false;

  $effect(() => {
    cancelled = false;
    (async () => {
      const result = await fetch('/api/data').then(r => r.text());
      if (!cancelled) data = result;
    })();

    return () => { cancelled = true; };  // cleanup returned synchronously
  });
</script>
```

---

## Stale Closure Capture in $effect

**What developers do wrong**: Capturing a value in a closure before it becomes reactive, so the captured value never updates.

```svelte
<!-- BAD: stale closure in event listener -->
<script lang="ts">
  let count = $state(0);

  $effect(() => {
    // count is captured by value at effect setup time (if effect doesn't re-run)
    window.addEventListener('keydown', () => {
      console.log('count is', count);  // may log stale count
    });
    // No cleanup — listener stacks up on every re-run
  });
</script>
```

**Why it fails**: The listener is added on every effect run but never removed. Each listener captures a different closure scope. The listener added in the first run always sees the `count` from that run.

```svelte
<!-- GOOD: read reactive state inside the handler, remove listener on cleanup -->
<script lang="ts">
  let count = $state(0);

  $effect(() => {
    const handler = () => {
      // Reading $state inside the handler gives the current value
      console.log('count is', count);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });
</script>
```

---

## Unclean $effect Teardown (Tauri Listeners)

**What developers do wrong**: Calling `listen()` inside `$effect` without awaiting and storing the `UnlistenFn`.

```svelte
<!-- BAD: listener leaks on unmount -->
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  let value = $state('');

  $effect(() => {
    // Fire and forget — no cleanup reference
    listen('device-value', e => { value = e.payload; });
    // Effect returns nothing — listener persists after component unmounts
  });
</script>
```

**Why it fails**: `listen()` registers a listener in Tauri's global event system. Without calling the returned `UnlistenFn`, the listener continues firing after the component is destroyed, writing to dead `$state` and causing memory leaks.

```svelte
<!-- GOOD: store the promise, call unlisten in cleanup -->
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  let value = $state('');

  $effect(() => {
    const unlistenPromise = listen<string>('device-value', e => {
      value = e.payload;
    });
    return () => { unlistenPromise.then(u => u()); };
  });
</script>
```

---

## Nested $state Mutation Without Reactivity Awareness

**What developers do wrong**: Treating `$state.raw` objects as if they are deeply reactive.

```svelte
<!-- BAD: mutating $state.raw deeply — no update triggered -->
<script lang="ts">
  let config = $state.raw({ network: { port: 8080, host: 'localhost' } });

  function changePort(p: number) {
    config.network.port = p;  // SILENT — $state.raw does not track nested writes
  }
</script>
<p>Port: {config.network.port}</p>  <!-- never changes in UI -->
```

**Why it fails**: `$state.raw` only tracks reassignment of the top-level variable. Deep mutations are invisible to the reactivity system.

```svelte
<!-- GOOD: reassign the whole object -->
<script lang="ts">
  let config = $state.raw({ network: { port: 8080, host: 'localhost' } });

  function changePort(p: number) {
    config = { ...config, network: { ...config.network, port: p } };
  }
</script>
```

---

## Using onMount Instead of $effect

**What developers do wrong**: Using Svelte 4's `onMount` lifecycle for side effects that depend on reactive state.

```svelte
<!-- BAD: onMount does not re-run when dependencies change -->
<script lang="ts">
  import { onMount } from 'svelte';
  let deviceId = $state('');

  onMount(() => {
    // Runs once on mount — if deviceId changes, this does NOT re-run
    connectToDevice(deviceId);
    // Also: return value from onMount is the cleanup, but only for unmount
  });
</script>
```

**Why it fails**: `onMount` runs exactly once after initial mount. It does not observe `$state` dependencies and will not re-run when `deviceId` changes. This is a Svelte 4 pattern.

```svelte
<!-- GOOD: $effect re-runs when dependencies change -->
<script lang="ts">
  let deviceId = $state('');

  $effect(() => {
    if (!deviceId) return;
    const cleanup = connectToDevice(deviceId);
    return cleanup;  // re-runs and cleans up whenever deviceId changes
  });
</script>
```

Note: `onMount` is still valid for one-time setup that does not depend on reactive state (e.g., initializing a third-party library instance). The bug is using it where reactive re-execution is needed.

---

## Mixing Svelte 4 Reactive Stores with Svelte 5 Runes

**What developers do wrong**: Importing `writable` from `svelte/store` and mixing it with rune-based state.

```svelte
<!-- BAD: store returned from load function — not compatible with runes -->
<!-- +page.ts -->
import { writable } from 'svelte/store';
export const load = () => ({
  items: writable<string[]>([])  // wrong: cannot return writable from load
});

<!-- +page.svelte -->
<script lang="ts">
  let { data } = $props();
  // data.items is a Svelte store, not $state — $derived won't track it
  let count = $derived(data.items.length);  // BUG: stores don't work with $derived
</script>
```

**Why it fails**: SvelteKit's type system forbids returning `Writable` from `load` because it cannot be serialized across the server/client boundary. Even if it worked, Svelte 5's `$derived` does not subscribe to Svelte store contracts.

```svelte
<!-- GOOD: return plain data from load, use $state locally -->
<!-- +page.ts -->
export const load = () => ({
  items: ['a', 'b', 'c'] as string[]  // plain, serializable
});

<!-- +page.svelte -->
<script lang="ts">
  let { data } = $props();
  let items = $state(data.items);  // convert to reactive state locally
  let count = $derived(items.length);
</script>
```

---

## Incorrect Context Usage — getContext Outside Init

**What developers do wrong**: Calling `getContext` after component initialization (e.g., inside an event handler or effect).

```svelte
<!-- BAD: getContext inside effect -->
<script lang="ts">
  import { getContext } from 'svelte';

  $effect(() => {
    const theme = getContext('theme');  // ERROR: called outside component init
  });
</script>
```

**Why it fails**: Svelte's context APIs (`setContext`, `getContext`) are only valid during the synchronous execution of the component's initialization (the `<script>` block top level). Calling them inside `$effect`, event handlers, or async callbacks throws a runtime error.

```svelte
<!-- GOOD: call getContext at top level of <script> -->
<script lang="ts">
  import { getContext } from 'svelte';

  // Called during init — correct
  const theme = getContext<{ color: string }>('theme');

  $effect(() => {
    // Use the already-retrieved context value inside effect
    document.body.style.setProperty('--accent', theme.color);
  });
</script>
```

---

## load Function Waterfall

**What developers do wrong**: Sequentially awaiting multiple independent fetches inside a `load` function.

```typescript
// BAD: sequential awaits — waterfall
export const load = async ({ fetch }) => {
  const user = await fetch('/api/user').then(r => r.json());
  const settings = await fetch('/api/settings').then(r => r.json());  // waits for user
  const devices = await fetch('/api/devices').then(r => r.json());    // waits for settings
  return { user, settings, devices };
};
// Total time: t(user) + t(settings) + t(devices)
```

**Why it fails**: Each `await` blocks execution until the previous request completes. If each request takes 100ms, the total load time is 300ms instead of 100ms.

```typescript
// GOOD: parallel fetches with Promise.all
export const load = async ({ fetch }) => {
  const [user, settings, devices] = await Promise.all([
    fetch('/api/user').then(r => r.json()),
    fetch('/api/settings').then(r => r.json()),
    fetch('/api/devices').then(r => r.json()),
  ]);
  return { user, settings, devices };
};
// Total time: max(t(user), t(settings), t(devices))
```

---

## Throwing Instead of Using fail() in Form Actions

**What developers do wrong**: Throwing an error from a form action instead of returning `fail()`.

```typescript
// BAD: throwing from action
export const actions = {
  create: async ({ request }) => {
    const data = await request.formData();
    if (!data.get('name')) {
      throw new Error('Name is required');  // returns HTTP 500, not 422
    }
  }
};
```

**Why it fails**: Throwing from an action triggers SvelteKit's `handleError` hook and returns a 500 response to the client. The error message may be swallowed or replaced by the generic error handler. Progressive enhancement breaks — the form reloads to an error page instead of showing inline validation.

```typescript
// GOOD: use fail() to return structured validation errors
import { fail } from '@sveltejs/kit';
export const actions = {
  create: async ({ request }) => {
    const data = await request.formData();
    const name = data.get('name') as string;
    if (!name) {
      return fail(422, { name: '', error: 'Name is required' });
    }
    // success path...
  }
};
```

The `fail()` response is available as `form` in the page's `$props()` for inline error display.

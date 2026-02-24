# Reactivity Bugs — Svelte 5

Symptom patterns, root causes, and diagnostic steps for `$state`, `$derived`, `$effect`, context, and stale closure bugs.

---

## $state Mutation Tracking Failures

### Symptom: UI doesn't update after assignment

**Pattern A — Destructured value**:
```svelte
let user = $state({ name: 'Alice' });
let { name } = user;  // name is a plain string copy
name = 'Bob';         // no update — name is not reactive
```
**Diagnosis**: Search for `let { ... } = $state(` or `const { ... } = someStateObj` at component top level. The destructure breaks the proxy chain.

**Fix**: Access properties directly — `user.name = 'Bob'`.

---

**Pattern B — Replaced object loses reference**:
```svelte
let items = $state([{ id: 1, done: false }]);
let item = items[0];  // local reference to element
item.done = true;     // MAY work (proxy) but item reference is not stable after splice/sort
```
**Diagnosis**: Check if the code mutates a locally captured element reference after the parent array has been mutated (splice, sort, filter+reassign).

**Fix**: Mutate via index: `items[0].done = true`.

---

**Pattern C — $state.raw mutated deeply**:
```svelte
let config = $state.raw({ port: 8080 });
config.port = 9090;  // silent — raw does not track nested mutation
```
**Diagnosis**: Search for `$state.raw(` and then check if the code mutates nested properties rather than reassigning.

**Fix**: Reassign: `config = { ...config, port: 9090 }`.

---

## $derived Staleness

### Symptom: Derived value appears stale / doesn't update

**Cause A — Async inside $derived**:
```svelte
// BUG: $derived does not support async
let data = $derived(await fetch('/api').then(r => r.json()));
```
`$derived` runs synchronously. Async expressions cause the derived to freeze at the initial `Promise` value.

**Fix**: Use `$effect` + `$state` for async data:
```svelte
let data = $state<unknown>(null);
$effect(() => {
  fetch('/api').then(r => r.json()).then(v => { data = v; });
});
```

---

**Cause B — Dependency not read synchronously**:
```svelte
let flag = $state(false);
let result = $derived.by(() => {
  if (Math.random() > 0.5) return flag;  // conditional read — sometimes flag isn't tracked
  return 'default';
});
```
**Diagnosis**: Dependencies must be read unconditionally in every execution path of `$derived.by`. Conditional reads may or may not establish the dependency.

**Fix**: Read all dependencies before any branching:
```svelte
let result = $derived.by(() => {
  const f = flag;  // unconditional read establishes dependency
  if (Math.random() > 0.5) return f;
  return 'default';
});
```

---

## $effect Cleanup Leaks

### Symptom: Effect fires after component is destroyed / memory grows over time

**Diagnostic checklist**:
1. Does the `$effect` add an event listener, subscribe to a store, or call `listen()`?
2. Does the `$effect` return a cleanup function?
3. Does the cleanup actually call the correct teardown method?

**Common leak pattern — Tauri event listener**:
```svelte
$effect(() => {
  listen('data', handler);  // listen() returns Promise<UnlistenFn>
  // No return — UnlistenFn never called
});
```

**Fix**:
```svelte
$effect(() => {
  const p = listen('data', handler);
  return () => p.then(u => u());
});
```

**Common leak pattern — setInterval**:
```svelte
$effect(() => {
  setInterval(() => { count++; }, 1000);
  // No clearInterval — timer runs forever
});
```

**Fix**: `return () => clearInterval(timerId);`

---

### Symptom: Effect runs on every render, not just dependency changes

**Cause**: Effect reads a non-reactive value that changes identity on every render (e.g., an inline object or function prop).

```svelte
<!-- Parent -->
<Child config={{ debug: true }} />  <!-- new object on every parent render -->

<!-- Child -->
let { config } = $props();
$effect(() => {
  applyConfig(config);  // runs every time parent re-renders — config is a new object
});
```

**Diagnosis**: Check if `$effect` dependencies include object/array props that are recreated at call sites.

**Fix**: Compare relevant properties, use `$derived` to memoize, or destructure primitives from the prop:
```svelte
let { config } = $props();
let debug = $derived(config.debug);  // primitive — stable identity
$effect(() => { if (debug) console.log('debug mode'); });
```

---

## Context Serialization Traps

### Symptom: Context value is correct in parent but undefined or stale in child

**Cause A — setContext called too late**:
```svelte
<!-- BAD: setContext inside $effect (post-init) -->
$effect(() => {
  setContext('key', { value: someState });  // ERROR at runtime
});
```
`setContext` must be called during synchronous component initialization.

**Fix**: Call `setContext` at the top level of `<script>`.

---

**Cause B — Context value is a primitive (not reactive)**:
```svelte
<!-- Parent -->
let count = $state(0);
setContext('count', count);  // passes the NUMBER 0, not the reactive $state

<!-- Child -->
const count = getContext<number>('count');
// count is always 0 — does not update when parent's count changes
```

**Fix**: Pass a reactive object or getter:
```svelte
<!-- Pattern 1: reactive object in context -->
const ctx = $state({ count: 0 });
setContext('counter', ctx);
// Child: const ctx = getContext<typeof ctx>('counter'); reads ctx.count

<!-- Pattern 2: getter function in context -->
setContext('getCount', () => count);
// Child: const getCount = getContext<() => number>('getCount'); reads getCount()
```

---

## Stale Closure Captures

### Symptom: Event handler or callback uses an outdated value

**Pattern — setTimeout with captured state**:
```svelte
let message = $state('hello');

function sendAfterDelay() {
  const captured = message;  // snapshot at call time
  setTimeout(() => {
    // captured is the value at sendAfterDelay() call time, not now
    sendToServer(captured);
  }, 5000);
}
```
This is often intentional. It becomes a bug when the developer expected `message` to be the current value at timeout execution time.

**Fix for "current value at execution"**:
```svelte
setTimeout(() => {
  sendToServer($state.snapshot(message) or just `message`);  // reads current proxy value
}, 5000);
```

Because `message` is a `$state` proxy, reading it inside the closure reads the current value if the proxy itself is stable. The bug arises when the state variable is REASSIGNED (not mutated) and the closure captured the old reference.

---

### Symptom: Callback inside $effect reads stale $props value

```svelte
let { onSuccess } = $props<{ onSuccess: () => void }>();

$effect(() => {
  const socket = new WebSocket(url);
  socket.onmessage = () => {
    onSuccess();  // onSuccess captured at $effect setup — may be stale if parent re-renders
  };
  return () => socket.close();
});
```

**Fix**: Use a ref-like pattern or access props directly:
```svelte
// The effect should re-run when onSuccess changes — add it as explicit dependency
$effect(() => {
  const handler = onSuccess;  // capture current value inside effect body
  const socket = new WebSocket(url);
  socket.onmessage = () => handler();
  return () => socket.close();
});
// Because onSuccess is read inside the effect, it's a tracked dependency — effect re-runs on change
```

---

## Hardware IPC Specific Reactivity Bugs

### Symptom: Device state shows "connected" after physical disconnect

**Cause**: Tauri event listener for disconnect event is not registered, or was registered but the unlisten was called prematurely.

**Diagnostic**:
1. Verify `listen('device-disconnected', ...)` exists
2. Verify the `UnlistenFn` is not called before component unmount
3. Check if the Tauri backend emits the correct event name

### Symptom: invoke() result updates $state but UI still shows old value

**Cause A**: `invoke()` resolves but the Svelte component has already been unmounted.

**Cause B**: The result is written to a local variable (not `$state`) inside the `.then()` callback.

**Diagnostic**:
```svelte
// BUG: result is plain variable
let result = '';  // not $state
invoke('get_data').then(r => { result = r; });  // no UI update

// FIX: result is $state
let result = $state('');
invoke('get_data').then(r => { result = r; });
```

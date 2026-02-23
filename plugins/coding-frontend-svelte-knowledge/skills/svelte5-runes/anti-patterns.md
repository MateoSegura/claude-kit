# Svelte 5 Runes — Anti-Patterns

## Anti-Pattern 1: $effect for State Synchronization

The most common Svelte 5 mistake: using `$effect` to keep two pieces of state in sync. Always use `$derived` for computed values.

**WRONG:**
```svelte
<script>
  let count = $state(0);
  let doubled = $state(0);
  let isEven = $state(true);

  // BAD: effect to sync state
  $effect(() => {
    doubled = count * 2;
    isEven = count % 2 === 0;
  });
</script>
```

**Why it fails:**
- Creates potential infinite update cycles
- `doubled` and `isEven` become out of sync until the effect microtask runs
- Harder to reason about — the source of truth is unclear
- Effects have overhead (they're async); $derived is synchronous

**RIGHT:**
```svelte
<script>
  let count = $state(0);
  let doubled = $derived(count * 2);
  let isEven = $derived(count % 2 === 0);
</script>
```

**For complex multi-value sync, use $derived.by:**
```svelte
<script>
  let items = $state<number[]>([]);

  let stats = $derived.by(() => ({
    total: items.reduce((a, b) => a + b, 0),
    min: Math.min(...items),
    max: Math.max(...items),
    avg: items.length ? items.reduce((a, b) => a + b, 0) / items.length : 0
  }));
</script>
```

---

## Anti-Pattern 2: Destructuring $state Objects

Destructuring a `$state` object into individual variables breaks reactivity. The destructured variables become plain, non-reactive copies.

**WRONG:**
```svelte
<script>
  let user = $state({ name: 'Alice', age: 30, email: 'alice@example.com' });

  // BAD: destructuring loses reactivity
  let { name, age } = user;
</script>

<!-- name and age are NOT reactive — won't update in template -->
<p>{name} is {age}</p>
```

**Why it fails:**
- `name` and `age` are assigned primitive values (strings, numbers) at the time of destructuring
- Primitives are copied by value — they do not maintain a reference to the reactive proxy
- Reassigning `user.name` will not update the local `name` variable

**RIGHT:**
```svelte
<script>
  let user = $state({ name: 'Alice', age: 30, email: 'alice@example.com' });
</script>

<!-- Access reactive properties directly through the object -->
<p>{user.name} is {user.age}</p>
```

**If you need local aliases, use $derived:**
```svelte
<script>
  let user = $state({ name: 'Alice', age: 30 });
  let name = $derived(user.name); // stays in sync
  let age = $derived(user.age);   // stays in sync
</script>
```

---

## Anti-Pattern 3: Async Reads Inside $effect

Reactive dependencies are only tracked synchronously. Any state read after an `await` is invisible to the dependency tracker.

**WRONG:**
```svelte
<script>
  let userId = $state('user-1');
  let userData = $state(null);

  $effect(async () => {
    const response = await fetch(`/api/users/${userId}`);
    // userId is NOT tracked here — changes to userId won't re-run the effect
    // because the read happens after the await
    userData = await response.json();
  });
</script>
```

**Why it fails:**
- The dependency tracker only runs synchronously before the first `await`
- If `userId` is read after `await`, it is not registered as a dependency
- Effect won't re-run when `userId` changes

**RIGHT:**
```svelte
<script>
  let userId = $state('user-1');
  let userData = $state(null);

  $effect(() => {
    // Read userId SYNCHRONOUSLY before any await — this registers the dependency
    const id = userId;

    // Now use id (a captured plain value) in the async part
    fetch(`/api/users/${id}`)
      .then(r => r.json())
      .then(data => { userData = data; });
  });
</script>
```

**Better pattern — use SvelteKit load functions for data fetching instead of $effect:**
```typescript
// +page.ts — preferred for route-level data
export async function load({ params }) {
  const user = await fetch(`/api/users/${params.id}`).then(r => r.json());
  return { user };
}
```

---

## Anti-Pattern 4: Writing to Tracked State Inside $effect

Writing to state that is also a dependency of the same effect creates infinite loops.

**WRONG:**
```svelte
<script>
  let count = $state(0);

  // INFINITE LOOP: count is read (tracked) AND written in the same effect
  $effect(() => {
    if (count < 10) count++;
  });
</script>
```

**RIGHT:**
```svelte
<script>
  let count = $state(0);

  // Use event handlers or controlled logic instead
  function increment() {
    if (count < 10) count++;
  }
</script>
<button onclick={increment}>{count}</button>
```

---

## Anti-Pattern 5: Creating $state Inside $effect

Creating new state inside an effect creates new reactive values on every run, leading to memory leaks and unpredictable behavior.

**WRONG:**
```svelte
<script>
  let trigger = $state(0);

  $effect(() => {
    trigger; // dependency
    // BAD: creates a new $state on every effect run
    let inner = $state({ value: 0 });
  });
</script>
```

**RIGHT:**
```svelte
<script>
  let trigger = $state(0);
  let inner = $state({ value: 0 }); // declare at top level

  $effect(() => {
    trigger; // dependency
    inner.value = 0; // reset or update existing state
  });
</script>
```

---

## Anti-Pattern 6: Props Mutation Without $bindable

Mutating props directly causes `ownership_invalid_mutation` warnings and undefined behavior. Only mutate props declared with `$bindable`.

**WRONG:**
```svelte
<!-- Child.svelte -->
<script>
  let { user } = $props();

  function updateName(name: string) {
    user.name = name; // BAD: mutating prop owned by parent
  }
</script>
```

**RIGHT with $bindable:**
```svelte
<!-- Child.svelte -->
<script>
  let { user = $bindable() } = $props();
  // Now parent must use bind:user={myUser}
  // And child can mutate user.name safely
</script>
```

**RIGHT with callback prop (preferred for explicit data flow):**
```svelte
<!-- Child.svelte -->
<script>
  let { user, onUpdate }: { user: User; onUpdate: (u: User) => void } = $props();

  function updateName(name: string) {
    onUpdate({ ...user, name }); // send update request to parent
  }
</script>

<!-- Parent.svelte -->
<Child {user} onUpdate={(u) => { myUser = u; }} />
```

---

## Anti-Pattern 7: Module-Level Reactive State (Shared Singleton Bug)

Declaring `$state` at module level in a `.svelte` component creates shared state across ALL instances of that component.

**WRONG:**
```svelte
<!-- Counter.svelte -->
<script>
  // BAD: module-level state — shared across ALL Counter instances
  let count = $state(0);
</script>
```

**Why it fails:**
- Module-level code runs once per import, not once per component instance
- All `<Counter />` instances share the same `count` variable
- Clicking any counter updates all counters

**RIGHT:**
```svelte
<!-- Counter.svelte -->
<script>
  // Instance-level state — each component gets its own count
  let count = $state(0);
  // This is the default — state in <script> (not module script) is per-instance
</script>
```

**When you WANT shared state — use .svelte.ts:**
```typescript
// shared-counter.svelte.ts
let count = $state(0); // intentionally module-level singleton
export const sharedCounter = {
  get count() { return count; },
  increment() { count++; }
};
```

---

## Anti-Pattern 8: Forgetting Cleanup in $effect

Side effects that allocate resources (event listeners, intervals, WebSocket connections) must return cleanup functions or they will leak.

**WRONG:**
```svelte
<script>
  let active = $state(false);

  $effect(() => {
    if (active) {
      // BAD: no cleanup — interval keeps running after active becomes false
      setInterval(() => { tick(); }, 1000);
    }
  });
</script>
```

**RIGHT:**
```svelte
<script>
  let active = $state(false);

  $effect(() => {
    if (!active) return; // early return is fine — no cleanup needed

    const id = setInterval(() => { tick(); }, 1000);
    return () => clearInterval(id); // cleanup runs when active changes or component unmounts
  });
</script>
```

**Common resources needing cleanup:**
```svelte
<script>
  let el: HTMLElement;

  $effect(() => {
    // Event listeners
    const handler = (e: Event) => handleEvent(e);
    el.addEventListener('click', handler);
    return () => el.removeEventListener('click', handler);
  });

  $effect(() => {
    // Intersection Observer
    const obs = new IntersectionObserver(callback);
    obs.observe(el);
    return () => obs.disconnect();
  });

  $effect(() => {
    // WebSocket
    const ws = new WebSocket(url);
    return () => ws.close();
  });
</script>
```

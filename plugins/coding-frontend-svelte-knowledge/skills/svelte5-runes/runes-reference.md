# Svelte 5 Runes — Detailed Reference

## $state Deep Dive

### Deep Reactivity Internals

`$state` with objects/arrays returns a Proxy. This means:
- Property access on nested objects is tracked
- Array methods (`push`, `splice`, `sort`) trigger updates
- The proxy wraps recursively — `$state({ a: { b: { c: 1 } } })` tracks all levels
- Prototype methods are preserved

```svelte
<script>
  let matrix = $state([[1, 2], [3, 4]]);
  matrix[0][1] = 99;   // triggers update — nested array tracked
  matrix.reverse();    // triggers update — array method tracked
</script>
```

### When to Use $state.raw

Use `$state.raw` when:
- The value is a large dataset you always replace, never mutate
- The value contains non-serializable properties (DOM nodes, class instances)
- You need referential equality — proxy objects break `===` checks
- Performance is critical and you don't need granular tracking

```typescript
// Good use of $state.raw: class instances
class AudioPlayer {
  constructor(public src: string) {}
  play() { /* ... */ }
}

let player = $state.raw(new AudioPlayer('/music.mp3'));
// To "update" player:
player = new AudioPlayer('/new-song.mp3'); // reassign
```

### $state.snapshot

Essential when passing reactive state to:
- `JSON.stringify()` — proxies serialize but may have unexpected behavior
- `structuredClone()` — requires plain objects
- Third-party libraries that check `instanceof Object`
- Web Workers via `postMessage`

```typescript
let formData = $state({ name: '', email: '' });

function submitForm() {
  const snapshot = $state.snapshot(formData);
  // snapshot is a plain object — safe to pass anywhere
  fetch('/api/submit', {
    method: 'POST',
    body: JSON.stringify(snapshot)
  });
}
```

## $derived Deep Dive

### Dependency Tracking Rules

- Only synchronous reads inside the expression/function body are tracked
- Reads inside callbacks, timers, or after `await` are NOT tracked
- Use `untrack()` from `'svelte'` to read state without tracking

```typescript
import { untrack } from 'svelte';

let count = $state(0);
let logCount = $state(0);

// logCount changes don't re-run this derived
let value = $derived.by(() => {
  const c = count; // tracked
  untrack(() => { logCount++; }); // not tracked
  return c * 2;
});
```

### Derived Objects Are Not Proxied

Unlike `$state`, values returned from `$derived` are NOT wrapped in proxies. This means derived objects use plain assignment tracking:

```svelte
<script>
  let items = $state([1, 2, 3]);

  // Returns a plain object — NOT a deep reactive proxy
  let stats = $derived({ total: items.length, first: items[0] });

  // stats.total is reactive — but only because the derived recomputes
  // You cannot mutate stats.total directly
</script>
```

### Lazy Evaluation

Derived values are lazy — they recompute only when read, not immediately when dependencies change. This is efficient for expensive computations.

```typescript
// computeExpensiveValue only runs when expensiveResult is actually read
let expensiveResult = $derived.by(() => computeExpensiveValue(inputData));
```

### Overridable Derived (Svelte 5.25+) — Full Pattern

```svelte
<script>
  export interface Post {
    id: string;
    likes: number;
    liked: boolean;
  }

  let { post }: { post: Post } = $props();

  // Derived values that can be temporarily overridden
  let likes = $derived(post.likes);
  let liked = $derived(post.liked);

  async function toggleLike() {
    // Optimistic update — instant UI feedback
    liked = !liked;
    likes += liked ? 1 : -1;

    try {
      await fetch(`/api/posts/${post.id}/like`, { method: 'POST' });
      // Server confirms — $derived will resync on next reactive update
    } catch {
      // Rollback
      liked = !liked;
      likes += liked ? 1 : -1;
    }
  }
</script>
```

## $effect Deep Dive

### When Effects Run

1. After component is mounted to DOM (not during SSR)
2. After reactive dependencies change (in a microtask — batched)
3. Cleanup function from previous run executes first

### $effect vs $effect.pre Timing

```
State changes
     ↓
$effect.pre runs (before DOM update) ← use for reading DOM measurements
     ↓
DOM updates
     ↓
$effect runs (after DOM update) ← default, use for most side effects
```

### Avoiding Infinite Loops

Effects can read AND write state, but writing state that is also a dependency causes loops:

```svelte
// DANGEROUS — infinite loop
$effect(() => {
  count = count + 1; // count is a dep AND is being written
});

// SAFE — write a different piece of state
$effect(() => {
  log = `count is ${count}`; // count is dep, log is not
});
```

### $effect.root for Libraries and Tests

```typescript
// In a .svelte.ts utility file (outside component lifecycle)
export function createReactiveStore<T>(initial: T) {
  let value = $state(initial);

  const destroy = $effect.root(() => {
    $effect(() => {
      // sync to localStorage whenever value changes
      localStorage.setItem('store', JSON.stringify($state.snapshot(value)));
    });
  });

  return {
    get value() { return value; },
    set(v: T) { value = v; },
    destroy
  };
}
```

```typescript
// Testing pattern — create effects in isolation
import { $effect } from 'svelte';

test('counter increments', () => {
  const destroy = $effect.root(() => {
    let count = $state(0);
    let log: number[] = [];

    $effect(() => { log.push(count); });

    count++;
    count++;

    // flush effects
    flushSync();
    expect(log).toEqual([0, 1, 2]);
  });
  destroy();
});
```

### $effect.tracking

Useful for building reactive utilities that behave differently inside vs outside effects:

```typescript
function createSubscriber<T>(subscribe: (callback: (v: T) => void) => () => void) {
  return (getter: () => T) => {
    if ($effect.tracking()) {
      let value = $state<T>(getter());

      $effect(() => {
        const unsubscribe = subscribe((v) => { value = v; });
        return unsubscribe;
      });

      return () => value;
    }
    // Not inside a tracking context — just return current value
    return getter;
  };
}
```

## $props Deep Dive

### Props ID for Accessible Forms

```svelte
<script>
  const uid = $props.id();
</script>

<!-- uid is stable across SSR/CSR hydration -->
<div>
  <label for="{uid}-name">Name</label>
  <input id="{uid}-name" name="name" />
</div>
```

### Forwarding All Props (Spread Pattern)

```svelte
<script>
  // Wrap a native element and forward all HTML attributes
  let { children, class: className = '', ...rest } = $props();
</script>

<button class="btn {className}" {...rest}>
  {@render children?.()}
</button>
```

### $bindable with Fallback Values

```svelte
<script>
  // Bindable with a fallback — works with or without bind:
  let { value = $bindable('') }: { value?: string } = $props();
  // Parent can use either:
  //   <Input value="hello" />     (uncontrolled with fallback)
  //   <Input bind:value={myStr} /> (two-way controlled)
</script>
```

## $inspect and $host

### $inspect — Development Debugging

```svelte
<script>
  let count = $state(0);
  let user = $state({ name: 'Alice' });

  // Logs to console whenever count or user changes
  $inspect(count, user);

  // Custom inspector — use for custom devtools integration
  $inspect(count).with((type, value) => {
    if (type === 'update') {
      myDevtools.log('count changed', value);
    }
  });
  // type is 'init' on first run, 'update' on subsequent runs
</script>
```

`$inspect` only runs in development mode — stripped in production builds.

### $host — Custom Elements

```svelte
<svelte:options customElement="my-counter" />

<script>
  // Access the custom element's host for dispatching custom events
  function dispatchCustomEvent() {
    $host().dispatchEvent(new CustomEvent('counted', {
      detail: count,
      bubbles: true
    }));
  }
</script>
```

## Class-Based Reactive State Pattern

For complex reactive objects with methods, use classes in `.svelte.ts`:

```typescript
// todo-store.svelte.ts
export class TodoStore {
  items = $state<Todo[]>([]);
  filter = $state<'all' | 'done' | 'pending'>('all');

  // Derived computed property
  get filtered() {
    return $derived.by(() => {
      if (this.filter === 'all') return this.items;
      return this.items.filter(t => t.done === (this.filter === 'done'));
    });
  }

  addTodo(text: string) {
    this.items.push({ id: crypto.randomUUID(), text, done: false });
  }

  toggleTodo(id: string) {
    const todo = this.items.find(t => t.id === id);
    if (todo) todo.done = !todo.done;
  }

  removeTodo(id: string) {
    this.items = this.items.filter(t => t.id !== id);
  }
}

// Usage: instantiate once, pass around or use as module singleton
export const todos = new TodoStore();
```

```svelte
<!-- todos.svelte -->
<script>
  import { todos } from './todo-store.svelte.ts';
</script>

{#each todos.filtered as todo}
  <TodoItem {todo} onToggle={() => todos.toggleTodo(todo.id)} />
{/each}
```

## untrack() Utility

Import from `'svelte'` to read state without creating a reactive dependency:

```typescript
import { untrack } from 'svelte';

$effect(() => {
  // This effect only tracks primaryValue
  const pv = primaryValue;

  // Read secondaryValue for its current value but don't track it
  const sv = untrack(() => secondaryValue);

  doSomething(pv, sv);
});
```

## Common Patterns with Runes in .svelte.ts

### Paginated Fetch State

```typescript
// pagination.svelte.ts
export function createPagination(fetchFn: (page: number) => Promise<any[]>) {
  let page = $state(1);
  let items = $state<any[]>([]);
  let loading = $state(false);
  let error = $state<Error | null>(null);
  let hasMore = $state(true);

  async function loadPage(p: number) {
    loading = true;
    error = null;
    try {
      const result = await fetchFn(p);
      items = p === 1 ? result : [...items, ...result];
      hasMore = result.length > 0;
      page = p;
    } catch (e) {
      error = e as Error;
    } finally {
      loading = false;
    }
  }

  return {
    get page() { return page; },
    get items() { return items; },
    get loading() { return loading; },
    get error() { return error; },
    get hasMore() { return hasMore; },
    loadNext: () => loadPage(page + 1),
    refresh: () => loadPage(1)
  };
}
```

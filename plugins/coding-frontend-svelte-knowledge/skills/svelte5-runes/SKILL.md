---
name: coding-frontend-svelte-knowledge:svelte5-runes
description: "Comprehensive reference for Svelte 5 runes system: $state, $derived, $effect, $props, $bindable, $inspect, $host — reactive primitives, anti-patterns, and .svelte.ts shared reactive logic patterns."
user-invocable: false
---

# Svelte 5 Runes Quick Reference

Svelte 5 runes are compiler-recognized function calls that declare reactive behavior. They replace the implicit reactivity of Svelte 4's `let` declarations, `$:` reactive statements, and stores. All rune calls begin with `$`.

## Rune Overview

| Rune | Purpose | Returns |
|------|---------|---------|
| `$state(val)` | Deep reactive state | Proxy (objects/arrays) or primitive |
| `$state.raw(val)` | Reactive state, no deep proxy | Plain value |
| `$state.snapshot(val)` | Snapshot of reactive proxy | Plain object |
| `$derived(expr)` | Computed value from expression | Readonly reactive value |
| `$derived.by(fn)` | Computed value from function | Readonly reactive value |
| `$effect(fn)` | Run side effect on state change | void |
| `$effect.pre(fn)` | Side effect before DOM update | void |
| `$effect.root(fn)` | Non-tracked effect scope | Destroy function |
| `$effect.tracking()` | Check if inside tracking context | boolean |
| `$props()` | Declare component props | Destructured props object |
| `$bindable(fallback?)` | Mark prop as two-way bindable | Prop value |
| `$inspect(...vals)` | Debug log reactive values | void |
| `$host()` | Custom element host element | HTMLElement |

## $state — Deep Reactive State

```svelte
<script>
  let count = $state(0);
  let user = $state({ name: 'Alice', age: 30 }); // deep proxy
  let items = $state(['a', 'b', 'c']);            // array proxy

  // Mutate nested properties directly — UI updates automatically
  user.age += 1;
  items.push('d');
  items[0] = 'z';
</script>
```

**$state.raw** — when you want reactivity on assignment but NOT deep proxying:

```svelte
<script>
  // Good for large arrays/objects you replace wholesale, or non-serializable values
  let data = $state.raw({ rows: [] });
  data.rows.push('x');          // No effect — mutation ignored
  data = { rows: ['x'] };       // Triggers update
</script>
```

**$state.snapshot** — extract a plain object from a proxy (e.g., for JSON.stringify, structuredClone, external libs):

```svelte
<script>
  let pos = $state({ x: 0, y: 0 });
  // Passes plain object, not Proxy — safe for external APIs
  fetch('/api', { body: JSON.stringify($state.snapshot(pos)) });
</script>
```

## $derived — Computed Values

```svelte
<script>
  let count = $state(0);
  let doubled = $derived(count * 2);           // expression form
  let formatted = $derived(`Count: ${count}`);

  // $derived.by for multi-statement logic
  let stats = $derived.by(() => {
    const total = items.reduce((acc, n) => acc + n, 0);
    return { total, avg: total / items.length };
  });
</script>
```

**Overridable derived (Svelte 5.25+)** — for optimistic UI:

```svelte
<script>
  let likes = $derived(post.likes); // tracks post.likes

  async function onclick() {
    likes += 1;        // override immediately (optimistic)
    try {
      await like();    // server call
    } catch {
      likes -= 1;      // rollback on failure
    }
    // after next reactive update, $derived takes back control
  }
</script>
```

## $effect — Side Effects

```svelte
<script>
  let color = $state('#ff3e00');
  let canvas;

  $effect(() => {
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = color;        // tracked — re-runs when color changes
    ctx.fillRect(0, 0, 100, 100);

    // Optional cleanup — runs before next effect or on unmount
    return () => ctx.clearRect(0, 0, 100, 100);
  });
</script>
```

**$effect.pre** — runs BEFORE DOM updates (for reading DOM before paint):

```svelte
<script>
  $effect.pre(() => {
    // runs before DOM update — use for measuring DOM, autoscroll prep
    if (shouldScroll) container.scrollTop = container.scrollHeight;
  });
</script>
```

**$effect.root** — effect scope outside component lifecycle:

```svelte
<script>
  // Create effects that live beyond component or in .svelte.ts files
  const destroy = $effect.root(() => {
    $effect(() => console.log('count:', count));
    return () => console.log('cleanup');
  });
  // Call destroy() to clean up manually
</script>
```

## $props and $bindable

```svelte
<script>
  // Basic props with defaults
  let { title, count = 0, class: className = '' } = $props();

  // Rest props — forward unknown attributes
  let { href, children, ...rest } = $props();

  // TypeScript
  interface Props {
    value: number;
    label?: string;
  }
  let { value, label = 'Default' }: Props = $props();
</script>

<!-- Two-way binding in child component -->
<script>
  let { value = $bindable(0) } = $props();
  // Parent can bind:value={myVar}
</script>
```

## Anti-Patterns

See [anti-patterns.md](anti-patterns.md) for full examples. Key violations:

**1. Using $effect for state synchronization** — always use $derived instead:
```svelte
// WRONG — creates update cycles, harder to reason about
let doubled = $state(0);
$effect(() => { doubled = count * 2; });

// RIGHT
let doubled = $derived(count * 2);
```

**2. Destructuring $state objects loses reactivity**:
```svelte
// WRONG — name and age are no longer reactive
let { name, age } = $state({ name: 'Alice', age: 30 });

// RIGHT — destructure from the reactive object
let user = $state({ name: 'Alice', age: 30 });
// Use user.name and user.age in template
```

**3. Reading state asynchronously inside $effect** — async reads after await are NOT tracked:
```svelte
$effect(async () => {
  await something();
  console.log(count); // NOT tracked — count changes won't re-run this
});
```

## .svelte.ts Files — Shared Reactive Logic

Runes work in `.svelte.ts` files for shared reactive state outside components:

```typescript
// counter.svelte.ts
export function createCounter(initial = 0) {
  let count = $state(initial);
  let doubled = $derived(count * 2);

  return {
    get count() { return count; },
    get doubled() { return doubled; },
    increment() { count++; },
    reset() { count = 0; }
  };
}
```

```svelte
<script>
  // counter.svelte
  import { createCounter } from './counter.svelte.ts';
  const counter = createCounter(10);
</script>
<button onclick={() => counter.increment()}>{counter.count}</button>
```

## Additional Resources

- [runes-reference.md](runes-reference.md) — Complete API details, untrack(), $inspect/$host, class-based reactive state patterns, testing with $effect.root

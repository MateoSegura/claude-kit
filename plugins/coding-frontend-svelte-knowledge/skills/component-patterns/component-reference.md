# Svelte 5 Component Reference — Advanced Patterns

## Render Delegation via Snippet Props

Snippet props allow parent components to control HOW a child renders its content — the child controls WHEN and WHERE it renders:

```svelte
<!-- DataTable.svelte — delegates cell rendering to consumer -->
<script>
  import type { Snippet } from 'svelte';

  interface Column<T> {
    key: keyof T;
    header: string;
    cell?: Snippet<[T]>;
  }

  let {
    rows,
    columns,
    rowKey,
  }: {
    rows: T[];
    columns: Column<T>[];
    rowKey: (row: T) => string;
  } = $props();
</script>

<table>
  <thead>
    <tr>
      {#each columns as col}
        <th>{col.header}</th>
      {/each}
    </tr>
  </thead>
  <tbody>
    {#each rows as row (rowKey(row))}
      <tr>
        {#each columns as col}
          <td>
            {#if col.cell}
              {@render col.cell(row)}
            {:else}
              {row[col.key]}
            {/if}
          </td>
        {/each}
      </tr>
    {/each}
  </tbody>
</table>
```

```svelte
<!-- Consumer -->
<script>
  const columns = [
    { key: 'name', header: 'Name' },
    {
      key: 'status',
      header: 'Status',
      // custom cell snippet — TypeScript knows this is a User snippet
    },
  ];
</script>

<DataTable {rows} {columns} rowKey={(u) => u.id}>
  {#snippet columns[1].cell(user)}
    <span class="badge badge--{user.status}">{user.status}</span>
  {/snippet}
</DataTable>
```

## Dynamic Elements

```svelte
<script>
  let { tag = 'div', children, ...rest }: {
    tag?: 'div' | 'section' | 'article' | 'aside' | 'main';
    children: Snippet;
  } = $props();
</script>

<!-- svelte:element for dynamic HTML elements -->
<svelte:element this={tag} {...rest}>
  {@render children()}
</svelte:element>
```

## Portal Pattern

```svelte
<!-- Portal.svelte — render children in a different DOM node -->
<script>
  import { mount, unmount } from 'svelte';
  import type { Snippet } from 'svelte';

  let { children, target = document.body }: {
    children: Snippet;
    target?: HTMLElement;
  } = $props();
</script>

<!-- Use svelte:boundary or teleport with mount -->
<svelte:window />
```

For portals in Svelte 5, use a wrapper element with `use:action`:

```typescript
// portal.ts
export function portal(node: HTMLElement, target: HTMLElement = document.body) {
  target.appendChild(node);
  return {
    destroy() { node.remove(); }
  };
}
```

```svelte
<div use:portal={document.body} class="modal-overlay">
  {@render children()}
</div>
```

## Transitions and Animations

```svelte
<script>
  import { fade, fly, slide, scale, blur, crossfade } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { cubicOut, elasticOut } from 'svelte/easing';

  let visible = $state(true);
  let items = $state(['a', 'b', 'c']);
</script>

<!-- Simple transition -->
{#if visible}
  <div transition:fade={{ duration: 200 }}>Fades in and out</div>
{/if}

<!-- Directional transition -->
{#if visible}
  <div transition:fly={{ y: -20, duration: 300, easing: cubicOut }}>
    Flies in from above
  </div>
{/if}

<!-- In/out separate transitions -->
{#if visible}
  <div in:slide out:fade={{ duration: 150 }}>
    Different in/out
  </div>
{/if}

<!-- Animate list reordering -->
{#each items as item (item)}
  <div animate:flip={{ duration: 300 }}>
    {item}
  </div>
{/each}
```

### Crossfade (Shared Element Transition)

```svelte
<script>
  import { crossfade } from 'svelte/transition';

  const [send, receive] = crossfade({
    duration: 400,
    fallback: slide
  });

  let items = $state({ todo: ['A', 'B'], done: [] });

  function move(item: string, from: 'todo' | 'done', to: 'todo' | 'done') {
    items[from] = items[from].filter(i => i !== item);
    items[to] = [...items[to], item];
  }
</script>

<div class="lists">
  <ul>
    {#each items.todo as item (item)}
      <li in:receive={{ key: item }} out:send={{ key: item }}>
        {item}
        <button onclick={() => move(item, 'todo', 'done')}>Done</button>
      </li>
    {/each}
  </ul>

  <ul>
    {#each items.done as item (item)}
      <li in:receive={{ key: item }} out:send={{ key: item }}>
        <s>{item}</s>
      </li>
    {/each}
  </ul>
</div>
```

## Spring and Tweened Animations

```svelte
<script>
  import { spring, tweened } from 'svelte/motion';

  // Spring physics — natural, physical feel
  const position = spring({ x: 0, y: 0 }, {
    stiffness: 0.15,
    damping: 0.8
  });

  // Tweened — interpolates over time with easing
  const progress = tweened(0, {
    duration: 400,
    easing: cubicOut
  });

  function moveCircle(e: MouseEvent) {
    position.set({ x: e.clientX, y: e.clientY });
  }

  // Update progress
  async function loadData() {
    await progress.set(100); // resolves when tween completes
  }
</script>

<div
  class="circle"
  style="transform: translate({$position.x}px, {$position.y}px)"
/>
<progress value={$progress} max={100} />
```

Note: `spring` and `tweened` return stores (Svelte 4 compatible). In Svelte 5, subscribe with `$` prefix.

## Lifecycle Functions

```svelte
<script>
  import { onMount, onDestroy, tick, mount, unmount } from 'svelte';

  // onMount — runs after component is added to DOM (client only)
  onMount(() => {
    const observer = new IntersectionObserver(callback);
    observer.observe(el);

    // Return teardown function
    return () => observer.disconnect();
  });

  // onDestroy — runs when component is destroyed
  onDestroy(() => cleanup());

  // tick — wait for pending DOM updates
  async function updateAndMeasure() {
    count++;           // schedule DOM update
    await tick();      // wait for DOM update
    const height = el.offsetHeight; // now correct
  }
</script>
```

**Programmatic mounting (Svelte 5):**

```typescript
import { mount, unmount } from 'svelte';
import MyComponent from './MyComponent.svelte';

// Mount a component outside of Svelte's template
const instance = mount(MyComponent, {
  target: document.getElementById('app')!,
  props: { message: 'Hello' }
});

// Later — destroy it
unmount(instance);
```

## Action Directives (use:)

```typescript
// longpress.ts — reusable action
export function longpress(node: HTMLElement, duration = 500) {
  let timer: ReturnType<typeof setTimeout>;

  function start(e: PointerEvent) {
    timer = setTimeout(() => {
      node.dispatchEvent(new CustomEvent('longpress'));
    }, duration);
  }

  function cancel() { clearTimeout(timer); }

  node.addEventListener('pointerdown', start);
  node.addEventListener('pointerup', cancel);
  node.addEventListener('pointerleave', cancel);

  return {
    update(newDuration: number) { duration = newDuration; },
    destroy() {
      node.removeEventListener('pointerdown', start);
      node.removeEventListener('pointerup', cancel);
      node.removeEventListener('pointerleave', cancel);
    }
  };
}
```

```svelte
<script>
  import { longpress } from './longpress.ts';
</script>

<button use:longpress={800} onlongpress={() => openContextMenu()}>
  Hold me
</button>
```

## Component Metadata (Svelte Options)

```svelte
<svelte:options
  customElement="my-widget"     <!-- Compile as custom element -->
  runes={true}                   <!-- Force runes mode -->
  namespace="svg"                <!-- SVG component -->
  accessors={false}              <!-- Disable prop accessors (Svelte 4 compat) -->
/>
```

## Passing Components as Props

```typescript
// Accept a component constructor as a prop
import type { Component } from 'svelte';

interface Props {
  icon: Component<{ size?: number; color?: string }>;
  label: string;
}

let { icon: Icon, label }: Props = $props();
```

```svelte
<button class="icon-btn">
  <Icon size={20} />
  <span>{label}</span>
</button>
```

## Multiple Instance Isolation Pattern

When you need multiple independent instances of the same reactive logic:

```typescript
// editor.svelte.ts — factory that creates isolated instances
export function createEditor(initialContent: string) {
  let content = $state(initialContent);
  let wordCount = $derived(content.trim().split(/\s+/).filter(Boolean).length);
  let dirty = $state(false);

  return {
    get content() { return content; },
    get wordCount() { return wordCount; },
    get dirty() { return dirty; },
    update(text: string) {
      content = text;
      dirty = true;
    },
    save() { dirty = false; }
  };
}
```

```svelte
<script>
  import { createEditor } from './editor.svelte.ts';

  // Each instance is completely isolated
  const mainEditor = createEditor('Hello');
  const noteEditor = createEditor('Notes...');
</script>
```

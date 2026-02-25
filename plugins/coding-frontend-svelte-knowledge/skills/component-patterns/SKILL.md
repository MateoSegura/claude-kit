---
name: coding-frontend-svelte-knowledge:component-patterns
description: "Svelte 5 component composition patterns: snippets replacing slots, context API for compound components, headless components, generic components, event attributes, state management hierarchy, and TypeScript utility types."
user-invocable: false
---

# Svelte 5 Component Patterns Quick Reference

## Snippets Replace Slots

Svelte 5 replaces slot-based composition with snippets. Slots are deprecated.

```svelte
<!-- Card.svelte -->
<script>
  import type { Snippet } from 'svelte';

  let {
    title,
    children,       // implicit — content between component tags
    footer,         // named snippet passed as prop
    header,         // optional named snippet
  }: {
    title: string;
    children: Snippet;
    footer: Snippet;
    header?: Snippet;
  } = $props();
</script>

<div class="card">
  {#if header}
    <div class="card-header">{@render header()}</div>
  {/if}
  <div class="card-body">{@render children()}</div>
  <div class="card-footer">{@render footer()}</div>
</div>
```

```svelte
<!-- Usage -->
<Card title="My Card">
  <!-- children snippet (implicit) -->
  <p>Body content here</p>

  {#snippet footer()}
    <button>Save</button>
  {/snippet}

  {#snippet header()}
    <h2>Custom Header</h2>
  {/snippet}
</Card>
```

### Typed Snippets with Parameters

```svelte
<!-- List.svelte — generic list with typed snippet -->
<script>
  import type { Snippet } from 'svelte';

  interface Props<T> {
    items: T[];
    renderItem: Snippet<[T, number]>;  // snippet receives item and index
    empty?: Snippet;
  }

  let { items, renderItem, empty }: Props<T> = $props();
</script>

{#if items.length === 0}
  {#if empty}
    {@render empty()}
  {:else}
    <p>No items</p>
  {/if}
{:else}
  {#each items as item, i}
    {@render renderItem(item, i)}
  {/each}
{/if}
```

```svelte
<!-- Usage -->
<script>
  let users = $state([{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }]);
</script>

<List {items}>
  {#snippet renderItem(user, index)}
    <li>{index + 1}. {user.name}</li>
  {/snippet}

  {#snippet empty()}
    <p class="empty">No users found</p>
  {/snippet}
</List>
```

## Reusable Snippets in Same File

```svelte
<script>
  let products = $state([...]);
</script>

{#snippet productCard(product)}
  <div class="product">
    <img src={product.image} alt={product.name} />
    <h3>{product.name}</h3>
    <p>${product.price}</p>
  </div>
{/snippet}

<div class="grid">
  {#each products as product}
    {@render productCard(product)}
  {/each}
</div>

<!-- Reuse in another context -->
<aside>
  <h2>Featured</h2>
  {@render productCard(products[0])}
</aside>
```

## Event Attributes Replace on: Directives

```svelte
<!-- Svelte 5: use event attributes (onclick, oninput, etc.) -->
<button onclick={() => count++}>Increment</button>

<input
  oninput={(e) => (name = e.currentTarget.value)}
  onblur={validate}
  onkeydown={(e) => e.key === 'Enter' && submit()}
/>

<!-- Spread event handlers -->
<script>
  let { onclick, ...rest } = $props();
</script>
<button {onclick} {...rest}>Click me</button>

<!-- Multiple handlers: wrap in function -->
<button onclick={() => { track(); navigate(); }}>Go</button>
```

## Context API for Compound Components

```svelte
<!-- Tabs.svelte — compound component root -->
<script>
  import { setContext } from 'svelte';

  let { children, defaultTab = '' } = $props();

  let activeTab = $state(defaultTab);

  // setContext with reactive getter (not value) so children get live updates
  setContext('tabs', {
    get activeTab() { return activeTab; },
    setTab: (tab: string) => { activeTab = tab; }
  });
</script>

<div class="tabs">{@render children()}</div>
```

```svelte
<!-- TabList.svelte -->
<script>
  import { getContext } from 'svelte';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
  const tabs = getContext<TabsContext>('tabs');
</script>

<div role="tablist">{@render children()}</div>
```

```svelte
<!-- Tab.svelte -->
<script>
  import { getContext } from 'svelte';

  let { id, children }: { id: string; children: Snippet } = $props();
  const { activeTab, setTab } = getContext<TabsContext>('tabs');
</script>

<button
  role="tab"
  aria-selected={activeTab === id}
  onclick={() => setTab(id)}
>
  {@render children()}
</button>
```

### createContext (Svelte 5.40+)

```typescript
// tabs-context.svelte.ts — type-safe context factory
import { createContext } from 'svelte';

export const [getTabsContext, setTabsContext] = createContext<TabsContext>('tabs');
// No manual typing of getContext needed — fully type-safe
```

## Generic Components

```svelte
<!-- Combobox.svelte — typed with generics -->
<script generics="T extends { id: string; label: string }">
  import type { Snippet } from 'svelte';

  let {
    items,
    value = $bindable<T | null>(null),
    renderItem,
    keyExtractor = (item: T) => item.id,
  }: {
    items: T[];
    value?: T | null;
    renderItem?: Snippet<[T]>;
    keyExtractor?: (item: T) => string;
  } = $props();
</script>

{#each items as item}
  <button
    onclick={() => (value = item)}
    aria-pressed={value ? keyExtractor(value) === keyExtractor(item) : false}
  >
    {#if renderItem}
      {@render renderItem(item)}
    {:else}
      {item.label}
    {/if}
  </button>
{/each}
```

## TypeScript Utility Types

```typescript
import type { Component, ComponentProps, ComponentEvents, Snippet } from 'svelte';

// Get the props type of a component
type ButtonProps = ComponentProps<typeof Button>;

// Type a component variable
let modal: Component<ModalProps>;

// Snippet type — Snippet<[ParamType1, ParamType2]>
type RenderRow = Snippet<[User, number]>;

// Dynamic component
<svelte:component this={modal} {...modalProps} />

// Dynamic component (Svelte 5 new syntax)
{@const DynamicComp = isAdmin ? AdminPanel : UserPanel}
<DynamicComp {user} />
```

## State Management Hierarchy

Choose the simplest solution that meets your needs:

| Level | Mechanism | Use When |
|-------|-----------|----------|
| 1 | `$state` in component | State used only in this component |
| 2 | `$derived` | Value computed from other state |
| 3 | Props + callbacks | Parent-child communication |
| 4 | Context API | Ancestor-descendant without prop drilling |
| 5 | `.svelte.ts` module | Cross-component state, no common ancestor |
| 6 | URL params / SvelteKit stores | State that should survive navigation / be bookmarkable |
| 7 | `$page.state` snapshots | Ephemeral UI state tied to history entry |

## Headless Component Pattern (Bits UI / Melt UI)

Use headless component libraries for accessible, unstyled interactive primitives:

```svelte
<script>
  import { Dialog } from 'bits-ui';
</script>

<!-- Bits UI provides ARIA, keyboard, focus trap — you provide styles -->
<Dialog.Root>
  <Dialog.Trigger class="btn">Open Dialog</Dialog.Trigger>

  <Dialog.Portal>
    <Dialog.Overlay class="overlay" />
    <Dialog.Content class="dialog">
      <Dialog.Title>Edit Profile</Dialog.Title>
      <Dialog.Description>Update your profile information.</Dialog.Description>

      <!-- Your content here -->
      <form>...</form>

      <Dialog.Close class="close-btn">Cancel</Dialog.Close>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
```

## Class-Based Reactive State in Components

```svelte
<script>
  class FormState {
    values = $state({ email: '', password: '' });
    errors = $state<Record<string, string>>({});
    submitting = $state(false);

    get isValid() {
      return $derived.by(() =>
        Object.keys(this.errors).length === 0 &&
        this.values.email.length > 0
      );
    }

    setField(field: string, value: string) {
      this.values = { ...this.values, [field]: value };
      delete this.errors[field];
    }

    async submit() {
      this.submitting = true;
      try {
        await fetch('/api/login', {
          method: 'POST',
          body: JSON.stringify($state.snapshot(this.values))
        });
      } finally {
        this.submitting = false;
      }
    }
  }

  const form = new FormState();
</script>

<input
  value={form.values.email}
  oninput={(e) => form.setField('email', e.currentTarget.value)}
/>
<button disabled={!form.isValid || form.submitting} onclick={() => form.submit()}>
  Submit
</button>
```

## Error Boundaries with &lt;svelte:boundary&gt;

```svelte
<svelte:boundary>
  <ComponentThatMightCrash />

  {#snippet failed(error, reset)}
    <div class="error-boundary">
      <p>Something went wrong: {error.message}</p>
      <button onclick={reset}>Retry</button>
    </div>
  {/snippet}
</svelte:boundary>
```

## Additional Resources

- [component-reference.md](component-reference.md) — Render delegation, portal patterns, svelte:element, transition/animation APIs, lifecycle functions (mount, unmount, tick), component metadata

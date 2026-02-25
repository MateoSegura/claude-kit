# Browser Testing Reference

## Why Browser Mode, Not jsdom

| Aspect | jsdom | Browser Mode (Playwright) |
|--------|-------|--------------------------|
| Svelte 5 runes | Fails — runes require browser context | Works — real V8/Blink environment |
| CSS layout queries | Mocked / inaccurate | Real layout engine |
| CSS custom properties | Not evaluated | Fully evaluated |
| Web APIs (ResizeObserver, IntersectionObserver) | Needs polyfills | Natively available |
| `$effect` lifecycle | Unreliable | Matches production exactly |
| Form validation | Partial | Fully spec-compliant |
| `focus()` / `blur()` events | Simulated | Real browser events |
| Debugging | No DevTools | Headed mode + DevTools |

**Rule:** Use browser mode for all `.svelte` component tests. Use Node environment only for pure TypeScript utilities, server-side code, and load functions.

## Handling $effect in Tests

Svelte 5 effects run asynchronously. Two strategies for waiting on effect side-effects:

### Strategy 1: expect.element (Recommended)

`expect.element` auto-retries until the assertion passes or times out. Works for DOM changes triggered by effects.

```typescript
// Counter.svelte — $effect updates a 'doubled' display after count changes
it('shows doubled value after increment', async () => {
  render(Counter, { initial: 5 });
  await page.getByRole('button', { name: 'Increment' }).click();
  // expect.element waits for the DOM to reflect the effect result
  await expect.element(page.getByTestId('doubled')).toHaveText('12');
});
```

### Strategy 2: flushSync (For non-DOM side effects)

Use when testing effects that update non-DOM state (e.g., calling a callback, updating a store):

```typescript
import { flushSync } from 'svelte';

it('notifies parent when form is dirty', () => {
  const onDirty = vi.fn();
  render(ContactForm, { onDirty });
  // Trigger state change
  const input = page.getByLabel('Name');
  // After fill, flushSync ensures effects have run synchronously
  await input.fill('Alice');
  flushSync();
  expect(onDirty).toHaveBeenCalledOnce();
});
```

### Strategy 3: $effect.root for Unit-Level Effect Tests

Use in `.svelte.test.ts` files when testing reactive logic in isolation (not component rendering):

```typescript
// Testing a reactive class / store with $effect
it('auto-saves after debounce', () => {
  const save = vi.fn();
  vi.useFakeTimers();

  const cleanup = $effect.root(() => {
    let content = $state('');

    $effect(() => {
      const value = content; // track dependency
      setTimeout(() => save(value), 500);
    });

    content = 'hello';
    vi.advanceTimersByTime(500);
    expect(save).toHaveBeenCalledWith('hello');
  });

  cleanup();
  vi.useRealTimers();
});
```

## Testing $bindable Props

```svelte
<!-- RangeSlider.svelte -->
<script lang="ts">
  let { value = $bindable(50), min = 0, max = 100 }: {
    value?: number;
    min?: number;
    max?: number;
  } = $props();
</script>
<input type="range" {min} {max} bind:value />
<output>{value}</output>
```

```typescript
// RangeSlider.svelte.test.ts
import { render } from 'vitest-browser-svelte';
import { page } from 'vitest/browser';
import { flushSync } from 'svelte';
import RangeSlider from './RangeSlider.svelte';

it('displays initial value', async () => {
  render(RangeSlider, { value: 75 });
  await expect.element(page.getByRole('slider')).toHaveValue('75');
  await expect.element(page.getByRole('status')).toHaveText('75');
});

it('updates output when slider moves', async () => {
  render(RangeSlider, { value: 50 });
  const slider = page.getByRole('slider');
  // Use fill to set the value directly on range input
  await slider.fill('80');
  await expect.element(page.getByRole('status')).toHaveText('80');
});
```

## Testing Component Events via Callback Props

Svelte 5 uses callback props instead of dispatched events:

```svelte
<!-- Modal.svelte -->
<script lang="ts">
  let { open = false, onclose, title, children }: {
    open?: boolean;
    onclose?: () => void;
    title: string;
    children: Snippet;
  } = $props();
</script>
{#if open}
  <dialog open>
    <h2>{title}</h2>
    {@render children()}
    <button onclick={onclose}>Close</button>
  </dialog>
{/if}
```

```typescript
// Modal.svelte.test.ts
it('calls onclose when close button is clicked', async () => {
  const onclose = vi.fn();
  render(Modal, {
    open: true,
    title: 'Confirm Action',
    onclose,
    children: createRawSnippet(() => ({
      render: () => '<p>Are you sure?</p>',
    })),
  });

  await page.getByRole('button', { name: 'Close' }).click();
  expect(onclose).toHaveBeenCalledOnce();
});
```

## Testing Snippets

Use `createRawSnippet` from Svelte to pass snippets as props in tests:

```typescript
import { createRawSnippet } from 'svelte';
import { render } from 'vitest-browser-svelte';
import Card from './Card.svelte';

it('renders custom header snippet', async () => {
  render(Card, {
    header: createRawSnippet(() => ({
      render: () => '<h2>Custom Header</h2>',
    })),
    children: createRawSnippet(() => ({
      render: () => '<p>Card content</p>',
    })),
  });

  await expect.element(page.getByRole('heading', { name: 'Custom Header' })).toBeVisible();
  await expect.element(page.getByText('Card content')).toBeVisible();
});
```

## Testing Conditional Rendering

```svelte
<!-- Alert.svelte -->
<script lang="ts">
  let { type, message, dismissible = false, ondismiss }: {
    type: 'info' | 'warning' | 'error';
    message: string;
    dismissible?: boolean;
    ondismiss?: () => void;
  } = $props();
</script>
{#if dismissible}
  <button onclick={ondismiss} aria-label="Dismiss">×</button>
{/if}
<p role="alert" class="alert-{type}">{message}</p>
```

```typescript
it('does not show dismiss button when not dismissible', async () => {
  render(Alert, { type: 'info', message: 'Info text' });
  // Query for absence — not.toBeInTheDocument() checks it was never rendered
  await expect.element(page.getByRole('button', { name: 'Dismiss' })).not.toBeInTheDocument();
});

it('shows dismiss button when dismissible', async () => {
  const ondismiss = vi.fn();
  render(Alert, { type: 'error', message: 'Error!', dismissible: true, ondismiss });
  const button = page.getByRole('button', { name: 'Dismiss' });
  await expect.element(button).toBeVisible();
  await button.click();
  expect(ondismiss).toHaveBeenCalledOnce();
});
```

## Testing #each Rendered Lists

```svelte
<!-- TagList.svelte -->
<script lang="ts">
  let { tags }: { tags: string[] } = $props();
</script>
<ul>
  {#each tags as tag}
    <li>{tag}</li>
  {/each}
</ul>
```

```typescript
it('renders all tags', async () => {
  render(TagList, { tags: ['svelte', 'vitest', 'playwright'] });
  const items = page.getByRole('listitem');
  // Check count using .all()
  const allItems = await items.all();
  expect(allItems).toHaveLength(3);
  await expect.element(items.first()).toHaveText('svelte');
});

it('renders empty list when no tags', async () => {
  render(TagList, { tags: [] });
  const list = page.getByRole('list');
  await expect.element(list).toBeInTheDocument();
  const items = await page.getByRole('listitem').all();
  expect(items).toHaveLength(0);
});
```

## Testing Async Components (await blocks / Promises)

```svelte
<!-- UserProfile.svelte -->
<script lang="ts">
  let { userId }: { userId: string } = $props();
  const userPromise = fetchUser(userId); // returns Promise<User>
</script>
{#await userPromise}
  <p>Loading...</p>
{:then user}
  <h1>{user.name}</h1>
{:catch error}
  <p role="alert">Error: {error.message}</p>
{/await}
```

```typescript
it('shows loading state initially', async () => {
  // Use a never-resolving promise to test loading state
  vi.mock('$lib/api', () => ({
    fetchUser: vi.fn(() => new Promise(() => {})), // never resolves
  }));

  render(UserProfile, { userId: '1' });
  await expect.element(page.getByText('Loading...')).toBeVisible();
});

it('shows user name after load', async () => {
  vi.mock('$lib/api', () => ({
    fetchUser: vi.fn().mockResolvedValue({ id: '1', name: 'Alice' }),
  }));

  render(UserProfile, { userId: '1' });
  // expect.element retries until the name appears
  await expect.element(page.getByRole('heading', { name: 'Alice' })).toBeVisible();
});

it('shows error message on failure', async () => {
  vi.mock('$lib/api', () => ({
    fetchUser: vi.fn().mockRejectedValue(new Error('Not found')),
  }));

  render(UserProfile, { userId: 'bad-id' });
  await expect.element(page.getByRole('alert')).toHaveText('Error: Not found');
});
```

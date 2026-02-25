# Vitest Anti-Patterns

Common mistakes that produce brittle, unmaintainable, or misleading tests. Each entry shows the bad pattern and the correct replacement.

---

## 1. Testing Implementation Details

**What developers do wrong:** Spy on internal state or private functions to assert that the implementation works a certain way, rather than asserting the observable behavior.

**BAD:**
```typescript
import { Counter } from '$lib/stores/counter.svelte';

it('increments internal _count', () => {
  const counter = new Counter();
  const spy = vi.spyOn(counter, '_count', 'get');
  counter.increment();
  // Testing the internal field directly — breaks with any refactor
  expect(spy).toHaveBeenCalled();
  expect(counter._count).toBe(1);
});
```

**Why it fails:** `_count` is an implementation detail. If the author renames it to `count`, stores it differently, or wraps it, this test breaks even though the behavior is unchanged. The test is coupled to the implementation, not the contract.

**GOOD:**
```typescript
it('increments the displayed count', () => {
  const counter = new Counter();
  counter.increment();
  // Test the public interface — what callers actually observe
  expect(counter.value).toBe(1);
});
```

---

## 2. Snapshot Abuse on Large DOM Trees

**What developers do wrong:** Call `toMatchSnapshot()` or `toMatchInlineSnapshot()` on an entire component's rendered output, creating a test that passes trivially and fails on any cosmetic change.

**BAD:**
```typescript
it('renders ProductCard', async () => {
  const { container } = render(ProductCard, {
    product: { id: 1, name: 'Widget', price: 9.99, image: '/img.jpg' },
  });
  // This captures every div, class, and attribute — any change fails this test
  expect(container.innerHTML).toMatchSnapshot();
});
```

**Why it fails:** The snapshot captures implementation noise (CSS class names, aria attributes, data-testid values, internal wrapper divs). A reviewer clicking "update snapshot" rarely reads what changed. The test becomes a rubber stamp, not a quality gate.

**GOOD:**
```typescript
it('shows product name and price', async () => {
  render(ProductCard, {
    product: { id: 1, name: 'Widget', price: 9.99, image: '/img.jpg' },
  });
  // Assert only the user-visible contract
  await expect.element(page.getByRole('heading', { name: 'Widget' })).toBeVisible();
  await expect.element(page.getByText('$9.99')).toBeVisible();
});

it('shows the product image with alt text', async () => {
  render(ProductCard, {
    product: { id: 1, name: 'Widget', price: 9.99, image: '/img.jpg' },
  });
  const img = page.getByRole('img', { name: 'Widget' });
  await expect.element(img).toBeVisible();
});
```

---

## 3. Flaky Async Tests with Hardcoded Timeouts

**What developers do wrong:** Use `setTimeout` or `sleep` helpers to wait for async operations, creating tests that are slow on fast machines and flaky on slow ones.

**BAD:**
```typescript
it('shows result after search', async () => {
  render(SearchBox);
  await page.getByRole('textbox').fill('svelte');
  // Arbitrary delay — too short on slow CI, wastes time on fast dev machines
  await new Promise(resolve => setTimeout(resolve, 500));
  expect(document.querySelector('.results')).not.toBeNull();
});
```

**Why it fails:** 500ms is arbitrary. On a loaded CI runner, the request takes 600ms and the test fails. On a fast dev machine, it waits 500ms unnecessarily. The test is non-deterministic.

**GOOD:**
```typescript
it('shows result after search', async () => {
  render(SearchBox);
  await page.getByRole('textbox').fill('svelte');
  // expect.element retries until the element appears or times out
  await expect.element(page.getByRole('listitem')).toBeVisible();
});

// For more complex polling needs:
it('shows result after search (waitFor variant)', async () => {
  render(SearchBox);
  await page.getByRole('textbox').fill('svelte');
  await waitFor(() => {
    expect(document.querySelectorAll('.result')).toHaveLength(3);
  });
});
```

---

## 4. Testing Framework Behavior (Testing Svelte, not Your Code)

**What developers do wrong:** Write tests that verify Svelte's own reactivity system or compilation works correctly, rather than testing the application's behavior.

**BAD:**
```typescript
it('reactivity works', () => {
  // This tests Svelte's runtime, not your component
  let count = $state(0);
  count++;
  expect(count).toBe(1); // Testing that Svelte $state increments — not useful
});

it('compiles $derived', () => {
  // This verifies the Svelte compiler, not your application logic
  let x = $state(2);
  let doubled = $derived(x * 2);
  expect(doubled).toBe(4);
});
```

**Why it fails:** Svelte's own test suite covers this. If `$state` is broken, everything fails. These tests give false confidence — they pass even when your component is wrong.

**GOOD:**
```typescript
// Test YOUR logic that uses Svelte primitives
it('cart total updates when item quantity changes', () => {
  const cart = createCart();
  cart.addItem({ id: 1, price: 10, quantity: 1 });
  cart.updateQuantity(1, 3);
  expect(untrack(() => cart.total)).toBe(30);
});
```

---

## 5. Mocking the Module Under Test

**What developers do wrong:** Mock the module being tested, creating a test that only tests the mock itself and provides zero coverage signal.

**BAD:**
```typescript
vi.mock('$lib/utils/format', () => ({
  formatPrice: vi.fn(() => '$9.99'),  // Mocking what we're testing!
}));

import { formatPrice } from '$lib/utils/format';

it('formatPrice returns formatted price', () => {
  expect(formatPrice(9.99)).toBe('$9.99');
  // This tests the vi.fn mock, not formatPrice
});
```

**Why it fails:** The test is circular — it passes because the mock returns what the assertion expects. No real code runs. Coverage tools report the file as tested, but nothing is actually verified.

**GOOD:**
```typescript
// Import the real module — never mock the module under test
import { formatPrice } from '$lib/utils/format';

it('formats price with dollar sign and 2 decimal places', () => {
  expect(formatPrice(9.99)).toBe('$9.99');
  expect(formatPrice(1000)).toBe('$1,000.00');
});
```

---

## 6. Missing Cleanup in $effect Tests

**What developers do wrong:** Use `$effect.root()` in tests but forget to call the returned cleanup function, causing effects to run across test boundaries.

**BAD:**
```typescript
it('tracks page views', () => {
  // Effect root is never cleaned up — leaks into subsequent tests
  $effect.root(() => {
    let views = $state(0);
    $effect(() => {
      analytics.track('pageview', { count: views });
    });
    views++;
  });
  // No cleanup — effect continues running
});
```

**Why it fails:** The effect from test 1 runs when test 2 mutates state. Subsequent tests see calls to `analytics.track` they did not trigger. Test order starts to matter. Tests fail intermittently.

**GOOD:**
```typescript
it('tracks page views', () => {
  const cleanup = $effect.root(() => {
    let views = $state(0);
    $effect(() => {
      analytics.track('pageview', { count: views });
    });
    flushSync();
    views++;
    flushSync();
    expect(analytics.track).toHaveBeenCalledWith('pageview', { count: 1 });
  });
  cleanup(); // Always call cleanup to destroy the reactive scope
});
```

---

## 7. Shared Mutable State Between Tests

**What developers do wrong:** Create a mutable store or counter at module scope that persists across tests, causing test order to affect results.

**BAD:**
```typescript
// Module-level state — shared across all tests in the file
const store = createUserStore();

describe('UserStore', () => {
  it('starts empty', () => {
    expect(store.users).toHaveLength(0);
  });

  it('adds a user', () => {
    store.add({ id: 1, name: 'Alice' });
    expect(store.users).toHaveLength(1);
  });

  // If these run in reverse order, 'starts empty' fails because 'adds a user' already ran
});
```

**Why it fails:** Tests depend on execution order. Running only the "starts empty" test in isolation passes. Running all tests together may fail. CI reruns fail randomly.

**GOOD:**
```typescript
describe('UserStore', () => {
  let store: ReturnType<typeof createUserStore>;

  // Fresh store for every test — guaranteed isolation
  beforeEach(() => {
    store = createUserStore();
  });

  it('starts empty', () => {
    expect(store.users).toHaveLength(0);
  });

  it('adds a user', () => {
    store.add({ id: 1, name: 'Alice' });
    expect(store.users).toHaveLength(1);
  });
});
```

---

## 8. Missing TypeScript Strict Mode in Test Files

**What developers do wrong:** Write test files without TypeScript strict mode or use `any` types to silence type errors.

**BAD:**
```typescript
// @ts-nocheck  ← suppresses all type checking in the file
const result: any = await loadUsers();  // loses type safety
expect((result as any).users).toHaveLength(1);  // assertion on untyped data
```

**Why it fails:** Type errors in test code often mirror type errors in production code. Suppressing types in tests means bugs slip through undetected. Test files should enforce the same strict typing as production files.

**GOOD:**
```typescript
// No ts-nocheck, no `any` casts
const result = await loadUsers();  // inferred as LoadResult
// TypeScript validates this access — if .users doesn't exist, compile error
expect(result.users).toHaveLength(1);
```

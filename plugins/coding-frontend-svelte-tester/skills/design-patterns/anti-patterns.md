# Test Design Anti-Patterns

Common mistakes that make tests brittle, slow, or misleading. Each entry has a BAD example, explains why it fails, and shows the GOOD replacement.

---

## 1. Testing Implementation Details

**What developers do wrong:** Spy on private state or internal methods to verify how the code works, rather than verifying what it produces.

**BAD:**
```typescript
it('increments internal _count via increment()', () => {
  const counter = new Counter();
  const countGetter = vi.spyOn(counter, '_count' as any, 'get');

  counter.increment();

  // Asserting on a private field and internal call pattern
  expect(countGetter).toHaveBeenCalled();
  expect((counter as any)._count).toBe(1);
});
```

**Why it fails:** `_count` is an implementation detail. If the author renames or restructures the internal storage, this test breaks — even though the component still works correctly. The test is testing the author, not the behavior.

**GOOD:**
```typescript
it('increments the displayed value', async () => {
  render(Counter);
  await page.getByRole('button', { name: 'Increment' }).click();
  // Test the output the user actually sees
  await expect.element(page.getByTestId('count')).toHaveText('1');
});
```

---

## 2. Snapshot Abuse on Large DOM Trees

**What developers do wrong:** Use `toMatchSnapshot()` on an entire component's HTML or a large section of the DOM.

**BAD:**
```typescript
it('renders the ProductCard', async () => {
  const { container } = render(ProductCard, {
    product: { id: 1, name: 'Widget', price: 9.99, inStock: true }
  });
  // Captures 50+ lines of HTML including classes, aria attributes, data-* — all noise
  expect(container.innerHTML).toMatchSnapshot();
});
```

**Why it fails:**
- Fails on any CSS class rename, aria attribute addition, wrapper div change
- Reviewers click "update snapshot" without reading what changed
- The snapshot becomes a rubber-stamp, not a quality gate
- CI fails on minor, intentional UI changes

**GOOD:**
```typescript
it('shows product name and price', async () => {
  render(ProductCard, { product: { id: 1, name: 'Widget', price: 9.99 } });
  // Test user-visible behavior, not HTML structure
  await expect.element(page.getByRole('heading', { name: 'Widget' })).toBeVisible();
  await expect.element(page.getByText('$9.99')).toBeVisible();
});

it('shows out-of-stock badge when unavailable', async () => {
  render(ProductCard, { product: { id: 1, name: 'Widget', price: 9.99, inStock: false } });
  await expect.element(page.getByText('Out of stock')).toBeVisible();
});
```

---

## 3. Test Interdependence (Shared Mutable State)

**What developers do wrong:** Create mutable state at module scope that persists between tests, making test order affect results.

**BAD:**
```typescript
// Module-level mutable state — shared across ALL tests in this file
const store = createUserStore();
const mockUsers = [{ id: 1, name: 'Alice' }];

describe('UserStore', () => {
  it('is empty initially', () => {
    expect(store.users).toHaveLength(0);  // Passes only if run first
  });

  it('adds a user', () => {
    store.add(mockUsers[0]);
    expect(store.users).toHaveLength(1);  // Pollutes subsequent tests
  });

  it('removes a user', () => {
    // If 'adds a user' ran first, store has 1 user — ok
    // If 'is empty initially' ran first, store has 0 users — FAILS
    store.remove(1);
    expect(store.users).toHaveLength(0);
  });
});
```

**Why it fails:** Running tests in isolation or in different order produces different results. Debugging is a nightmare — the test "works on my machine."

**GOOD:**
```typescript
describe('UserStore', () => {
  let store: ReturnType<typeof createUserStore>;

  // Fresh instance before each test — guaranteed isolation
  beforeEach(() => {
    store = createUserStore();
  });

  it('is empty initially', () => {
    expect(store.users).toHaveLength(0);
  });

  it('adds a user', () => {
    store.add({ id: 1, name: 'Alice' });
    expect(store.users).toHaveLength(1);
  });

  it('removes a user', () => {
    store.add({ id: 1, name: 'Alice' });
    store.remove(1);
    expect(store.users).toHaveLength(0);
  });
});
```

---

## 4. Over-Mocking (Mocking What You're Testing)

**What developers do wrong:** Mock the function or module that is the subject of the test.

**BAD:**
```typescript
// We want to test formatCurrency — but we mock it!
vi.mock('$lib/utils/format', () => ({
  formatCurrency: vi.fn().mockReturnValue('$9.99'),
}));
import { formatCurrency } from '$lib/utils/format';

it('formats currency correctly', () => {
  expect(formatCurrency(9.99, 'USD')).toBe('$9.99');
  // This tests the vi.fn mock, not the real implementation
});
```

**Why it fails:** The test is circular. `formatCurrency` always returns `'$9.99'` because the mock says so. The real implementation is never called. Coverage shows the file as "tested" but nothing is verified.

**GOOD:**
```typescript
// Import the REAL module — mocking is for dependencies, not the subject
import { formatCurrency } from '$lib/utils/format';

it.each([
  [9.99, 'USD', '$9.99'],
  [1000, 'USD', '$1,000.00'],
  [9.99, 'EUR', '€9.99'],
])('formats %f %s as %s', (amount, currency, expected) => {
  expect(formatCurrency(amount, currency)).toBe(expected);
});
```

---

## 5. Flaky Async Tests with Hardcoded Timeouts

**What developers do wrong:** Use `setTimeout`, `sleep`, or `new Promise(resolve => setTimeout(resolve, N))` to "wait" for async operations.

**BAD:**
```typescript
it('shows search results', async () => {
  render(SearchBox, { onsearch: vi.fn() });
  await page.getByRole('searchbox').fill('svelte');

  // Arbitrary: too short on slow CI, too long on fast dev machines
  await new Promise(resolve => setTimeout(resolve, 500));

  expect(document.querySelectorAll('.result')).toHaveLength(3);
});
```

**Why it fails:** 500ms is a guess. CI runners under load take 800ms. Fast dev machines execute in 50ms, wasting 450ms. The test is non-deterministic — intermittent failures in CI are common.

**GOOD:**
```typescript
it('shows search results', async () => {
  render(SearchBox, { onsearch: vi.fn() });
  await page.getByRole('searchbox').fill('svelte');

  // expect.element polls automatically — fast when ready, patient when slow
  await expect.element(page.getByRole('listitem').first()).toBeVisible();
  const results = await page.getByRole('listitem').all();
  expect(results).toHaveLength(3);
});
```

---

## 6. Testing Svelte Framework Behavior

**What developers do wrong:** Write tests that verify Svelte's reactivity, compilation, or built-in behaviors rather than application logic.

**BAD:**
```typescript
// Tests the Svelte runtime, not your code
it('$state is reactive', () => {
  const count = $state(0);
  count++;
  expect(count).toBe(1);  // Obviously true — this is Svelte's job to ensure
});

// Tests Svelte's derived computation
it('$derived computes', () => {
  const x = $state(3);
  const doubled = $derived(x * 2);
  expect(doubled).toBe(6);  // Svelte's test suite covers this, not yours
});
```

**Why it fails:** These tests will pass even when your application is completely broken. They test Svelte's runtime, which Svelte's own test suite already covers comprehensively. They provide false confidence.

**GOOD:**
```typescript
// Test YOUR business logic that happens to use $state
it('cart total updates correctly when item quantity changes', () => {
  const cart = createCart();
  cart.addItem({ id: 1, price: 10.00, quantity: 1 });
  cart.updateQuantity(1, 3);
  expect(untrack(() => cart.total)).toBe(30.00);
});
```

---

## 7. Missing Svelte 4 Patterns in Test Setup

**What developers do wrong:** Use Svelte 4 APIs in test files while the component uses Svelte 5 runes.

**BAD:**
```typescript
// BAD: Svelte 4 event dispatching in tests — incompatible with Svelte 5 runes
import { fireEvent } from '@testing-library/svelte';

it('handles click', async () => {
  const { getByRole } = render(Button, { label: 'Submit' });
  fireEvent.click(getByRole('button'));  // Svelte 4 pattern
  expect(handleClick).toHaveBeenCalled();
});

// BAD: createEventDispatcher in component being tested
// If the component uses createEventDispatcher instead of callback props,
// it's using Svelte 4 patterns — both need to be updated.
```

**BAD: Testing with export let (Svelte 4 props)**
```typescript
// If the component you're testing uses this API, it's Svelte 4
// Props in Svelte 5 use $props() rune
render(OldComponent, { on:click: handler }); // event binding syntax invalid
```

**GOOD (Svelte 5):**
```typescript
// Svelte 5: callback props instead of event dispatching
it('handles click via callback prop', async () => {
  const onclick = vi.fn();
  render(Button, { label: 'Submit', onclick });

  await page.getByRole('button', { name: 'Submit' }).click();
  expect(onclick).toHaveBeenCalledOnce();
});
```

---

## 8. Assertions Without Meaning (Testing That Tests Run)

**What developers do wrong:** Write tests that always pass regardless of behavior, providing coverage metrics but no quality signal.

**BAD:**
```typescript
it('loads user profile', async () => {
  render(UserProfile, { userId: '1' });
  // No assertion about what was rendered or what the user sees
  // This test only verifies that render() doesn't throw
});

it('calls onsubmit', async () => {
  const onsubmit = vi.fn();
  render(Form, { onsubmit });
  await page.getByRole('button', { name: 'Submit' }).click();
  expect(onsubmit).toHaveBeenCalled();  // Asserts it was called but not WHAT it was called with
});
```

**Why it fails:** The first test passes even if the component renders a blank screen. The second test passes if `onsubmit` is called with empty data, wrong data, or correct data — no discrimination.

**GOOD:**
```typescript
it('displays user name and email', async () => {
  render(UserProfile, { userId: '1' });
  await expect.element(page.getByRole('heading', { name: 'Alice Smith' })).toBeVisible();
  await expect.element(page.getByText('alice@example.com')).toBeVisible();
});

it('calls onsubmit with form data', async () => {
  const onsubmit = vi.fn();
  render(Form, { onsubmit });
  await page.getByLabel('Name').fill('Alice');
  await page.getByLabel('Email').fill('alice@example.com');
  await page.getByRole('button', { name: 'Submit' }).click();
  // Assert the CONTENT of the call, not just that it happened
  expect(onsubmit).toHaveBeenCalledWith({
    name: 'Alice',
    email: 'alice@example.com',
  });
});
```

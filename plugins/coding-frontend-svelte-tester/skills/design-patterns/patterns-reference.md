# Test Design Patterns Reference

Concrete code examples for each pattern. All examples use Svelte 5 runes and Vitest.

---

## Arrange-Act-Assert (AAA)

Every test follows three phases with a blank line separating each:

```typescript
it('removes item from cart when delete is clicked', async () => {
  // ARRANGE: set up initial state
  const cart = createCart();
  cart.addItem({ id: 1, name: 'Widget', price: 9.99 });
  render(CartItem, { item: cart.items[0], onremove: () => cart.removeItem(1) });

  // ACT: perform the user action
  await page.getByRole('button', { name: 'Remove Widget' }).click();

  // ASSERT: verify the expected outcome
  await expect.element(page.getByRole('listitem', { name: 'Widget' }))
    .not.toBeInTheDocument();
  expect(untrack(() => cart.items)).toHaveLength(0);
});
```

**Rules:**
- One concept per test (one ACT, one ASSERT focus)
- If a test needs multiple acts, split it into multiple tests
- Assertions on DOM use `expect.element()` (auto-retry). Non-DOM assertions use `expect()`.

---

## Given-When-Then (BDD Narrative)

For behavior-facing tests, the BDD form reads more naturally:

```typescript
describe('Shopping cart', () => {
  describe('GIVEN the cart has items', () => {
    let cart: Cart;
    beforeEach(() => {
      cart = createCart();
      cart.addItem({ id: 1, name: 'Widget', price: 10.00 });
      cart.addItem({ id: 2, name: 'Gadget', price: 25.00 });
    });

    describe('WHEN the user applies a 10% coupon', () => {
      beforeEach(() => cart.applyCoupon('SAVE10'));

      it('THEN the total reflects the discount', () => {
        expect(untrack(() => cart.total)).toBe(31.50);
      });

      it('THEN the discount amount is shown separately', () => {
        expect(untrack(() => cart.discount)).toBe(3.50);
      });
    });

    describe('WHEN the user removes all items', () => {
      beforeEach(() => {
        cart.removeItem(1);
        cart.removeItem(2);
      });

      it('THEN the cart shows empty state', () => {
        expect(untrack(() => cart.isEmpty)).toBe(true);
      });
    });
  });
});
```

---

## Builder Pattern for Complex Test Fixtures

Use a builder when a component has many props and tests need slight variations:

```typescript
// tests/builders/product.builder.ts
export interface Product {
  id: number;
  name: string;
  price: number;
  category: string;
  inStock: boolean;
  imageUrl: string;
  rating: number;
  reviewCount: number;
}

export class ProductBuilder {
  private product: Product = {
    id: 1,
    name: 'Test Widget',
    price: 9.99,
    category: 'Electronics',
    inStock: true,
    imageUrl: '/images/placeholder.jpg',
    rating: 4.5,
    reviewCount: 120,
  };

  withId(id: number): this {
    this.product = { ...this.product, id };
    return this;
  }

  withName(name: string): this {
    this.product = { ...this.product, name };
    return this;
  }

  withPrice(price: number): this {
    this.product = { ...this.product, price };
    return this;
  }

  outOfStock(): this {
    this.product = { ...this.product, inStock: false };
    return this;
  }

  withNoReviews(): this {
    this.product = { ...this.product, rating: 0, reviewCount: 0 };
    return this;
  }

  build(): Product {
    return { ...this.product };
  }
}

// Usage:
const inStockProduct = new ProductBuilder().build();
const outOfStockProduct = new ProductBuilder().outOfStock().build();
const expensiveProduct = new ProductBuilder().withPrice(299.99).build();
const newProduct = new ProductBuilder().withNoReviews().withId(42).build();
```

```typescript
// ProductCard.svelte.test.ts
import { ProductBuilder } from '../builders/product.builder';

describe('ProductCard', () => {
  it('shows out-of-stock badge when product is not in stock', async () => {
    render(ProductCard, { product: new ProductBuilder().outOfStock().build() });
    await expect.element(page.getByText('Out of stock')).toBeVisible();
  });

  it('hides add-to-cart when out of stock', async () => {
    render(ProductCard, { product: new ProductBuilder().outOfStock().build() });
    await expect.element(
      page.getByRole('button', { name: 'Add to cart' })
    ).toBeDisabled();
  });

  it('shows rating when product has reviews', async () => {
    const product = new ProductBuilder().build(); // default has reviews
    render(ProductCard, { product });
    await expect.element(page.getByText('4.5')).toBeVisible();
  });

  it('hides rating section when no reviews', async () => {
    render(ProductCard, { product: new ProductBuilder().withNoReviews().build() });
    await expect.element(page.getByRole('img', { name: /stars/i })).not.toBeInTheDocument();
  });
});
```

---

## Factory Pattern for Component Props

A simpler alternative to Builder when you just need default props with overrides:

```typescript
// tests/factories/user.factory.ts
import type { User } from '$lib/types';

let idCounter = 0;

export function createUser(overrides: Partial<User> = {}): User {
  idCounter++;
  return {
    id: idCounter,
    name: `Test User ${idCounter}`,
    email: `user${idCounter}@example.com`,
    role: 'user',
    createdAt: new Date('2024-01-01'),
    ...overrides,
  };
}

export function createAdminUser(overrides: Partial<User> = {}): User {
  return createUser({ role: 'admin', ...overrides });
}

// Reset counter between test files
export function resetUserFactory() { idCounter = 0; }
```

```typescript
// UserProfile.svelte.test.ts
import { createUser, createAdminUser } from '../factories/user.factory';

describe('UserProfile', () => {
  it('shows admin badge for admin users', async () => {
    render(UserProfile, { user: createAdminUser() });
    await expect.element(page.getByText('Admin')).toBeVisible();
  });

  it('hides admin controls for regular users', async () => {
    render(UserProfile, { user: createUser() });
    await expect.element(page.getByRole('button', { name: 'Delete user' }))
      .not.toBeInTheDocument();
  });
});
```

---

## Page Object Model (Playwright E2E)

See [playwright-e2e/patterns-reference.md](../playwright-e2e/patterns-reference.md) for the full Page Object implementation. Key principles:

```typescript
// Locators are defined in the constructor — NOT in test methods
class CheckoutPage {
  constructor(private page: Page) {}

  // Locators as readonly properties
  readonly orderSummary = this.page.getByRole('region', { name: 'Order summary' });
  readonly submitButton = this.page.getByRole('button', { name: 'Place order' });

  // High-level actions — test reads like user intent
  async completeCheckout(cardNumber: string) {
    await this.page.getByLabel('Card number').fill(cardNumber);
    await this.submitButton.click();
    await this.page.waitForURL('/order-confirmation');
  }
}

// Test reads as user intent, not implementation
test('user can complete checkout', async ({ page }) => {
  const checkout = new CheckoutPage(page);
  await page.goto('/checkout');
  await checkout.completeCheckout('4242424242424242');
  await expect(page.getByText('Order confirmed!')).toBeVisible();
});
```

---

## Parameterized Tests with test.each

```typescript
import { describe, it, expect } from 'vitest';
import { formatRelativeTime } from '$lib/utils/date';

describe('formatRelativeTime', () => {
  // Array form — good for simple cases
  it.each([
    [30, 'seconds', 'just now'],
    [59, 'seconds', 'just now'],
    [60, 'seconds', '1 minute ago'],
    [90, 'seconds', '1 minute ago'],
    [120, 'seconds', '2 minutes ago'],
    [3600, 'seconds', '1 hour ago'],
    [86400, 'seconds', '1 day ago'],
    [604800, 'seconds', '1 week ago'],
  ])('%i %s → %s', (amount, unit, expected) => {
    const date = new Date(Date.now() - amount * 1000);
    expect(formatRelativeTime(date)).toBe(expected);
  });

  // Object form — good for complex cases with meaningful labels
  it.each([
    {
      label: 'just happened',
      input: new Date(Date.now() - 10_000),
      expected: 'just now',
    },
    {
      label: 'yesterday',
      input: new Date(Date.now() - 86_400_000),
      expected: '1 day ago',
    },
    {
      label: 'future date',
      input: new Date(Date.now() + 60_000),
      expected: 'in 1 minute',
    },
  ])('$label → $expected', ({ input, expected }) => {
    expect(formatRelativeTime(input)).toBe(expected);
  });
});
```

---

## Custom Matcher Extension

Extend `expect` with domain-specific assertions to reduce duplication:

```typescript
// src/test-utils/matchers.ts
import { expect } from 'vitest';

interface CustomMatchers<R = unknown> {
  toBeValidEmail(): R;
  toHaveValidationError(field: string, message: string): R;
}

declare module 'vitest' {
  interface Assertion<T = any> extends CustomMatchers<T> {}
  interface AsymmetricMatchersContaining extends CustomMatchers {}
}

expect.extend({
  toBeValidEmail(received: string) {
    const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(received);
    return {
      pass: valid,
      message: () => valid
        ? `Expected "${received}" NOT to be a valid email`
        : `Expected "${received}" to be a valid email`,
    };
  },

  toHaveValidationError(
    received: { errors: Record<string, string> },
    field: string,
    message: string
  ) {
    const actual = received.errors?.[field];
    const pass = actual === message;
    return {
      pass,
      message: () => pass
        ? `Expected no validation error for "${field}"`
        : `Expected validation error for "${field}" to be "${message}", got "${actual}"`,
    };
  },
});
```

```typescript
// Usage in tests
it('rejects invalid email', () => {
  const result = validateEmail('not-valid');
  expect(result).toHaveValidationError('email', 'Invalid email format');
});

it('accepts valid email', () => {
  expect('user@example.com').toBeValidEmail();
});
```

---

## Test Doubles — Complete Hierarchy

```typescript
describe('Test double examples', () => {
  // STUB: Replace a dependency with a simple return value
  it('loads user from stub', async () => {
    const getUser = vi.fn().mockResolvedValue({
      id: 1, name: 'Alice', role: 'admin'
    });
    const result = await fetchUserProfile('1', getUser);
    expect(result.displayName).toBe('Alice');
  });

  // SPY: Verify a callback was called with the right arguments
  it('notifies analytics on purchase', async () => {
    const trackEvent = vi.fn();  // spy — no real implementation
    render(BuyButton, { productId: 42, price: 9.99, onpurchase: trackEvent });
    await page.getByRole('button', { name: 'Buy now' }).click();
    expect(trackEvent).toHaveBeenCalledWith({ event: 'purchase', productId: 42, price: 9.99 });
    expect(trackEvent).toHaveBeenCalledTimes(1);
  });

  // MOCK: Replace an entire module
  it('navigates to product page after add to cart', async () => {
    vi.mock('$app/navigation', () => ({ goto: vi.fn() }));
    const { goto } = await import('$app/navigation');

    render(AddToCart, { productId: 42 });
    await page.getByRole('button', { name: 'Add to cart' }).click();
    expect(goto).toHaveBeenCalledWith('/cart');
  });

  // FAKE: Working but simplified implementation
  it('stores items in local cart', () => {
    // In-memory fake replaces the real persistence layer
    const fakeStorage = new Map<string, string>();
    const storage = {
      get: (key: string) => fakeStorage.get(key) ?? null,
      set: (key: string, val: string) => fakeStorage.set(key, val),
      remove: (key: string) => fakeStorage.delete(key),
    };

    const cart = createPersistedCart(storage);
    cart.addItem({ id: 1, name: 'Widget', price: 9.99 });
    expect(fakeStorage.has('cart')).toBe(true);
  });
});
```

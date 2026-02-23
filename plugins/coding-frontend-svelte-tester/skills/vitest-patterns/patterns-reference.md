# Vitest Patterns Reference

Detailed patterns for Vitest in Svelte 5 / SvelteKit projects.

## Mocking SvelteKit Modules

### $app/navigation

```typescript
// src/lib/__tests__/auth.test.ts
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
  invalidate: vi.fn(),
  invalidateAll: vi.fn(),
  pushState: vi.fn(),
  replaceState: vi.fn(),
  preloadData: vi.fn(),
  preloadCode: vi.fn(),
}));

import { goto } from '$app/navigation';
import { logout } from '$lib/auth';

describe('logout', () => {
  beforeEach(() => vi.clearAllMocks());

  it('redirects to /login after logout', async () => {
    await logout();
    expect(goto).toHaveBeenCalledWith('/login');
  });
});
```

### $app/stores

```typescript
vi.mock('$app/stores', () => {
  const { readable, writable } = await import('svelte/store');
  const page = readable({
    url: new URL('http://localhost/'),
    params: {},
    route: { id: '/' },
    status: 200,
    error: null,
    data: {},
    form: null,
    state: {},
  });
  return { page, navigating: readable(null), updated: readable(false) };
});
```

### $app/environment

```typescript
vi.mock('$app/environment', () => ({
  browser: true,
  dev: false,
  building: false,
  version: '1.0.0',
}));
```

### $env/static/public

```typescript
vi.mock('$env/static/public', () => ({
  PUBLIC_API_URL: 'https://api.test.example.com',
  PUBLIC_APP_NAME: 'TestApp',
}));
```

## Mocking fetch

```typescript
describe('fetchUsers', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ id: 1, name: 'Alice' }],
    } as Response);
  });

  afterEach(() => vi.restoreAllMocks());

  it('returns users from API', async () => {
    const users = await fetchUsers();
    expect(users).toHaveLength(1);
    expect(users[0].name).toBe('Alice');
  });

  it('throws on network error', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Network error')
    );
    await expect(fetchUsers()).rejects.toThrow('Network error');
  });
});
```

## Testing SvelteKit Load Functions

```typescript
// src/routes/products/+page.server.ts (the load function)
// src/routes/products/__tests__/page.server.test.ts

import { describe, it, expect, vi } from 'vitest';
import { load } from '../+page.server';
import type { RequestEvent } from '@sveltejs/kit';

vi.mock('$lib/server/db', () => ({
  getProducts: vi.fn().mockResolvedValue([
    { id: 1, name: 'Widget', price: 9.99 },
  ]),
}));

function makeLoadEvent(params: Record<string, string> = {}): RequestEvent {
  return {
    params,
    url: new URL('http://localhost/products'),
    request: new Request('http://localhost/products'),
    locals: {},
    cookies: { get: vi.fn(), set: vi.fn(), delete: vi.fn(), getAll: vi.fn() },
    fetch: global.fetch,
    getClientAddress: () => '127.0.0.1',
    platform: undefined,
    route: { id: '/products' },
    setHeaders: vi.fn(),
    isDataRequest: false,
    isSubRequest: false,
  } as unknown as RequestEvent;
}

describe('load()', () => {
  it('returns products', async () => {
    const result = await load(makeLoadEvent());
    expect(result.products).toHaveLength(1);
    expect(result.products[0].name).toBe('Widget');
  });
});
```

## Testing SvelteKit Form Actions

```typescript
// src/routes/contact/__tests__/page.server.test.ts
import { describe, it, expect, vi } from 'vitest';
import { actions } from '../+page.server';
import { fail } from '@sveltejs/kit';

function makeFormData(fields: Record<string, string>): FormData {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  return fd;
}

function makeRequestEvent(formData: FormData): RequestEvent {
  return {
    request: {
      formData: async () => formData,
    },
    locals: {},
  } as unknown as RequestEvent;
}

describe('contact form action', () => {
  it('returns validation error for empty email', async () => {
    const event = makeRequestEvent(makeFormData({ email: '', message: 'hello' }));
    const result = await actions.default(event);
    expect(result.status).toBe(422);
    expect(result.data.errors.email).toBeDefined();
  });

  it('submits successfully with valid data', async () => {
    const event = makeRequestEvent(
      makeFormData({ email: 'user@example.com', message: 'hello' })
    );
    const result = await actions.default(event);
    expect(result).toBeUndefined(); // success = no return value
  });
});
```

## Testing $state and $derived (Reactive Stores)

Use `.svelte.test.ts` extension to enable runes in test files:

```typescript
// src/lib/__tests__/counter.svelte.test.ts
import { describe, it, expect } from 'vitest';
import { untrack } from 'svelte';
// Test the .svelte.ts store directly
import { createCounter } from '$lib/stores/counter.svelte';

describe('createCounter', () => {
  it('starts at 0', () => {
    const counter = createCounter();
    expect(untrack(() => counter.value)).toBe(0);
  });

  it('increments', () => {
    const counter = createCounter();
    counter.increment();
    expect(untrack(() => counter.value)).toBe(1);
  });

  it('derives doubled value', () => {
    const counter = createCounter();
    counter.increment();
    counter.increment();
    expect(untrack(() => counter.doubled)).toBe(4);
  });
});
```

## Testing $effect with $effect.root

```typescript
// src/lib/__tests__/tracker.svelte.test.ts
import { describe, it, expect, vi } from 'vitest';
import { untrack, flushSync } from 'svelte';

describe('$effect tracking', () => {
  it('runs effect when state changes', () => {
    const cleanup = $effect.root(() => {
      let count = $state(0);
      const log: number[] = [];

      $effect(() => {
        log.push(count);
      });

      // Initial effect run
      flushSync();
      expect(log).toEqual([0]);

      count++;
      flushSync();
      expect(log).toEqual([0, 1]);
    });

    cleanup();
  });
});
```

## Parameterized Tests with test.each

```typescript
import { describe, it, expect } from 'vitest';
import { formatCurrency } from '$lib/utils/format';

describe('formatCurrency', () => {
  it.each([
    [0, 'USD', '$0.00'],
    [1000, 'USD', '$1,000.00'],
    [9.99, 'EUR', '€9.99'],
    [-5.5, 'USD', '-$5.50'],
  ])('formats %d %s as %s', (amount, currency, expected) => {
    expect(formatCurrency(amount, currency)).toBe(expected);
  });

  // Object form (more readable for complex cases)
  it.each([
    { input: null, currency: 'USD', expected: '$0.00', label: 'null input' },
    { input: NaN, currency: 'USD', expected: '$0.00', label: 'NaN input' },
  ])('handles edge case: $label', ({ input, currency, expected }) => {
    expect(formatCurrency(input, currency)).toBe(expected);
  });
});
```

## Async Test Patterns

### waitFor — poll until condition is true

```typescript
import { waitFor } from '@testing-library/dom';

it('loads data asynchronously', async () => {
  // After triggering async operation
  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument();
  }, { timeout: 2000 });
});
```

### expect.element — built-in retry for browser mode

```typescript
// In browser-mode tests, prefer expect.element which auto-retries
it('shows success message after submit', async () => {
  await page.getByRole('button', { name: 'Submit' }).click();
  // Automatically retries until condition is met or timeout
  await expect.element(page.getByText('Success!')).toBeVisible();
});
```

### Async thrown errors

```typescript
it('rejects with AuthError for invalid token', async () => {
  await expect(
    validateToken('invalid-token-xyz')
  ).rejects.toThrow('Invalid token');
});
```

## Timer Mocking with vi.useFakeTimers

```typescript
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { debounce } from '$lib/utils/debounce';

describe('debounce', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('delays execution by specified ms', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 300);

    debounced('a');
    debounced('b');
    debounced('c');

    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(300);
    expect(fn).toHaveBeenCalledTimes(1);
    expect(fn).toHaveBeenCalledWith('c');
  });

  it('resets timer on repeated calls', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 300);

    debounced('first');
    vi.advanceTimersByTime(200);
    debounced('second');
    vi.advanceTimersByTime(200); // only 200ms since second call

    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100); // now 300ms since second call
    expect(fn).toHaveBeenCalledWith('second');
  });
});
```

## Snapshot Testing — When It Is Appropriate

Use snapshots for stable serialized output only (not rendered DOM):

```typescript
// GOOD: Serialized data structures
it('serializes config correctly', () => {
  const config = buildConfig({ debug: true });
  expect(config).toMatchInlineSnapshot(`
    {
      "debug": true,
      "logLevel": "verbose",
      "timeout": 5000,
    }
  `);
});

// GOOD: Small, stable DOM fragments
it('renders badge correctly', async () => {
  render(Badge, { variant: 'success', label: 'Active' });
  const badge = page.getByRole('status');
  await expect.element(badge).toHaveText('Active');
  // Use targeted assertions, not toMatchSnapshot() on the entire document
});

// BAD: toMatchSnapshot() on large component trees — see anti-patterns.md
```

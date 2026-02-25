---
name: coding-frontend-svelte-tester:vitest-patterns
description: "Vitest configuration, test lifecycle, assertion API, mocking patterns, and async testing for Svelte 5 / SvelteKit projects. Covers vi.fn/vi.mock/vi.spyOn, mocking SvelteKit modules, testing $state/$derived/$effect, and parameterized tests."
user-invocable: false
---

# Vitest Patterns for Svelte 5

Core reference for Vitest in Svelte 5 / SvelteKit projects. Use browser mode (vitest-browser-svelte) for component tests, Node environment for utilities and server-side code.

## vitest.config.ts — Multi-Project Setup

```typescript
import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    projects: [
      {
        // Client-side component tests — real browser
        extends: true,
        test: {
          name: 'client',
          include: ['src/**/*.svelte.test.ts', 'src/**/*.browser.test.ts'],
          browser: {
            enabled: true,
            name: 'chromium',
            provider: 'playwright',
            headless: true,
          },
          setupFiles: ['./src/vitest-setup-client.ts'],
        },
      },
      {
        // Unit tests — Node environment
        extends: true,
        test: {
          name: 'unit',
          include: ['src/**/*.test.ts'],
          exclude: ['src/**/*.svelte.test.ts', 'src/**/*.browser.test.ts'],
          environment: 'node',
          setupFiles: ['./src/vitest-setup-unit.ts'],
        },
      },
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'lcov', 'html'],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
      include: ['src/**/*.{ts,svelte}'],
      exclude: [
        'src/**/*.test.ts',
        'src/**/*.spec.ts',
        'src/**/+page.ts',       // SvelteKit route files (tested via E2E)
        'src/**/+layout.ts',
        'src/app.d.ts',
      ],
    },
  },
});
```

## Test File Naming Conventions

| Extension | Environment | Use For |
|-----------|-------------|---------|
| `*.test.ts` | Node | Pure TS utilities, stores, load functions, actions |
| `*.svelte.test.ts` | Browser | Svelte 5 components with runes, browser APIs |
| `*.browser.test.ts` | Browser | Components needing real DOM behavior |
| `*.spec.ts` | Node | Integration-style unit tests |

## Test Lifecycle Hooks

```typescript
import { beforeAll, beforeEach, afterEach, afterAll, describe, it, expect } from 'vitest';

describe('MyFeature', () => {
  beforeAll(async () => { /* runs once before all tests */ });
  beforeEach(() => { /* fresh state per test */ });
  afterEach(() => { /* cleanup per test */ });
  afterAll(async () => { /* teardown once */ });

  it('describes behavior', () => {
    expect(result).toBe(expected);
  });
});
```

## Assertion Quick Reference

```typescript
// Equality
expect(value).toBe(42);          // strict ===
expect(value).toEqual({ a: 1 }); // deep equality
expect(value).toStrictEqual(obj); // deep + prototype check

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();

// Numbers
expect(n).toBeGreaterThan(0);
expect(n).toBeCloseTo(3.14, 2);

// Strings
expect(str).toContain('substring');
expect(str).toMatch(/regex/);

// Arrays / iterables
expect(arr).toContain(item);
expect(arr).toHaveLength(3);
expect(arr).toContainEqual({ id: 1 });

// Errors
expect(() => fn()).toThrow('message');
expect(() => fn()).toThrowError(CustomError);

// Async
await expect(promise).resolves.toBe(value);
await expect(promise).rejects.toThrow('error');

// DOM (browser mode — use expect.element for retry-ability)
await expect.element(locator).toBeVisible();
await expect.element(locator).toHaveText('Hello');
await expect.element(locator).toBeInTheDocument();
await expect.element(locator).toBeDisabled();
```

## Mocking Quick Reference

```typescript
import { vi } from 'vitest';

// Function mock
const fn = vi.fn().mockReturnValue(42);
const fn2 = vi.fn().mockResolvedValue({ data: [] }); // async
expect(fn).toHaveBeenCalledWith(arg1, arg2);
expect(fn).toHaveBeenCalledTimes(2);

// Spy on existing method
const spy = vi.spyOn(obj, 'method').mockReturnValue(value);

// Module mock
vi.mock('$lib/api', () => ({
  fetchUser: vi.fn().mockResolvedValue({ id: 1, name: 'Alice' }),
}));

// Reset / restore
vi.clearAllMocks();   // clear call history
vi.resetAllMocks();   // clear + reset implementations
vi.restoreAllMocks(); // restore original implementations
```

## Decision Matrix — Test Type Selection

| Target | Test Type | Tool |
|--------|-----------|------|
| Pure TS utility function | Unit | Vitest node |
| `.svelte.ts` store with `$state` | Unit | Vitest node (.svelte.test.ts) |
| Svelte component rendering | Component | vitest-browser-svelte |
| Component + user interactions | Component | vitest-browser-svelte |
| SvelteKit load function | Unit | Vitest node |
| SvelteKit form action | Unit | Vitest node (FormData) |
| Full route navigation | E2E | Playwright |
| Accessibility compliance | A11y | vitest-axe / axe-playwright |

## Additional Resources

- **[patterns-reference.md](patterns-reference.md)** — Detailed patterns: mocking SvelteKit modules ($app/*), testing reactive state, async patterns, timers, parameterized tests with `test.each`
- **[anti-patterns.md](anti-patterns.md)** — Common mistakes: implementation testing, snapshot abuse, flaky async, over-mocking, missing cleanup in `$effect` tests

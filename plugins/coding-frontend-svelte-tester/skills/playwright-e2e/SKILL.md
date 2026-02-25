---
name: coding-frontend-svelte-tester:playwright-e2e
description: "Playwright E2E testing for SvelteKit applications. Covers configuration, locator strategies, navigation testing, form actions, page object model, network interception, and SvelteKit-specific patterns including load functions, SSR hydration, and route transitions."
user-invocable: false
---

# Playwright E2E Testing for SvelteKit

E2E tests verify complete user flows through a running SvelteKit application. Use `npx playwright test` — Playwright starts the dev server automatically via `webServer` config.

## playwright.config.ts — SvelteKit Setup

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.e2e.ts',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'mobile', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI,
  },
});
```

## Test File Structure

```typescript
// tests/e2e/products.e2e.ts
import { test, expect } from '@playwright/test';

test.describe('Product catalog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/products');
  });

  test('displays product list', async ({ page }) => {
    await expect(page.getByRole('list', { name: 'Products' })).toBeVisible();
  });
});
```

## Locator Strategies — Priority Order

| Priority | Method | Example |
|----------|--------|---------|
| 1 | `getByRole` | `page.getByRole('button', { name: 'Submit' })` |
| 2 | `getByLabel` | `page.getByLabel('Email address')` |
| 3 | `getByPlaceholder` | `page.getByPlaceholder('Search...')` |
| 4 | `getByText` | `page.getByText('Welcome back')` |
| 5 | `getByAltText` | `page.getByAltText('Product image')` |
| 6 | `getByTestId` | `page.getByTestId('nav-home')` |
| Avoid | CSS selectors | `.btn-primary` — breaks on refactor |
| Avoid | XPath | `//div[@class]` — brittle |

## Common Assertions

```typescript
// Visibility
await expect(locator).toBeVisible();
await expect(locator).toBeHidden();
await expect(locator).not.toBeVisible();

// Content
await expect(locator).toHaveText('Exact text');
await expect(locator).toContainText('partial text');
await expect(locator).toHaveValue('input value');
await expect(locator).toHaveAttribute('href', '/path');

// Count
await expect(locator).toHaveCount(5);

// URL
await expect(page).toHaveURL('/dashboard');
await expect(page).toHaveURL(/\/products\/\d+/);

// Page title
await expect(page).toHaveTitle('My App - Home');
```

## Navigation Patterns

```typescript
// Navigate and wait for load
await page.goto('/products');
await page.goto('/products', { waitUntil: 'networkidle' });

// Client-side navigation (SvelteKit goto)
await page.getByRole('link', { name: 'Products' }).click();
await expect(page).toHaveURL('/products');

// Wait for network quiet after navigation
await page.waitForLoadState('networkidle');

// Wait for specific response
await Promise.all([
  page.waitForResponse(resp => resp.url().includes('/api/products')),
  page.getByRole('button', { name: 'Load more' }).click(),
]);
```

## Waiting Strategies

```typescript
// Built-in auto-wait — Playwright waits for elements to be actionable
await page.getByRole('button').click();    // waits for clickable
await page.getByLabel('Name').fill('text'); // waits for editable

// Explicit waits (use sparingly)
await page.waitForSelector('[data-loaded="true"]');
await page.waitForURL('/dashboard');
await page.waitForResponse(url => url.includes('/api/user'));
await page.waitForLoadState('domcontentloaded'); // | 'load' | 'networkidle'

// Polling assertion
await expect(async () => {
  const count = await page.getByRole('listitem').count();
  expect(count).toBeGreaterThan(0);
}).toPass({ timeout: 5000 });
```

## Test Fixtures

```typescript
// tests/e2e/fixtures.ts
import { test as base } from '@playwright/test';
import { AuthPage } from './pages/AuthPage';
import { ProductsPage } from './pages/ProductsPage';

type Fixtures = {
  authPage: AuthPage;
  productsPage: ProductsPage;
  loggedInPage: { page: Page };
};

export const test = base.extend<Fixtures>({
  authPage: async ({ page }, use) => {
    await use(new AuthPage(page));
  },
  productsPage: async ({ page }, use) => {
    await use(new ProductsPage(page));
  },
  loggedInPage: async ({ page }, use) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('testpassword');
    await page.getByRole('button', { name: 'Log in' }).click();
    await page.waitForURL('/dashboard');
    await use({ page });
  },
});

export { expect } from '@playwright/test';
```

## Additional Resources

- **[patterns-reference.md](patterns-reference.md)** — Page object model, form action testing, load function testing, network interception, authentication flows, file upload/download, multi-tab scenarios
- **[examples.md](examples.md)** — Complete E2E test suites: login flow, CRUD, search/filter, form validation, SSR hydration verification

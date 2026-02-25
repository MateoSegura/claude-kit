# Playwright E2E Patterns Reference

## Page Object Model for SvelteKit Routes

Page objects encapsulate locator selectors and interactions for a single route, making tests resilient to UI changes and reducing duplication.

```typescript
// tests/e2e/pages/ProductsPage.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class ProductsPage {
  readonly url = '/products';
  readonly heading: Locator;
  readonly searchInput: Locator;
  readonly productList: Locator;
  readonly loadMoreButton: Locator;

  constructor(private page: Page) {
    this.heading = page.getByRole('heading', { name: 'Products', level: 1 });
    this.searchInput = page.getByRole('searchbox', { name: 'Search products' });
    this.productList = page.getByRole('list', { name: 'Product results' });
    this.loadMoreButton = page.getByRole('button', { name: 'Load more' });
  }

  async goto() {
    await this.page.goto(this.url);
    await this.heading.waitFor();
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    // Wait for debounce + response
    await this.page.waitForResponse(resp =>
      resp.url().includes('/api/products') && resp.status() === 200
    );
  }

  async getProductNames(): Promise<string[]> {
    const items = await this.productList.getByRole('heading', { level: 3 }).all();
    return Promise.all(items.map(item => item.textContent().then(t => t ?? '')));
  }

  async clickProduct(name: string) {
    await this.productList
      .getByRole('link', { name: new RegExp(name) })
      .click();
  }
}
```

```typescript
// tests/e2e/pages/AuthPage.ts
import { type Page, type Locator } from '@playwright/test';

export class AuthPage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(private page: Page) {
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Log in' });
    this.errorMessage = page.getByRole('alert');
  }

  async login(email: string, password: string) {
    await this.page.goto('/login');
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async loginAndWait(email: string, password: string) {
    await this.login(email, password);
    await this.page.waitForURL('/dashboard');
  }
}
```

## Form Submission Testing

### Native HTML Forms

```typescript
test('contact form submits successfully', async ({ page }) => {
  await page.goto('/contact');

  await page.getByLabel('Name').fill('Alice Smith');
  await page.getByLabel('Email').fill('alice@example.com');
  await page.getByLabel('Message').fill('Hello there!');

  // Wait for the form submission response (SvelteKit form action)
  const [response] = await Promise.all([
    page.waitForResponse(resp =>
      resp.url().includes('/contact') && resp.request().method() === 'POST'
    ),
    page.getByRole('button', { name: 'Send message' }).click(),
  ]);

  expect(response.status()).toBe(200);
  await expect(page.getByText('Message sent successfully')).toBeVisible();
});
```

### SvelteKit Enhanced Form Actions

```typescript
test('login form action redirects on success', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('correctpassword');
  await page.getByRole('button', { name: 'Log in' }).click();

  // SvelteKit form action redirects to dashboard on success
  await expect(page).toHaveURL('/dashboard');
  await expect(page.getByText('Welcome back')).toBeVisible();
});

test('login form shows server validation error', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('wrongpassword');
  await page.getByRole('button', { name: 'Log in' }).click();

  // SvelteKit form action returns ActionFailure — page re-renders with error
  await expect(page).toHaveURL('/login'); // stays on login
  await expect(page.getByRole('alert')).toContainText('Invalid email or password');
});

test('form preserves input values on validation failure', async ({ page }) => {
  await page.goto('/register');

  await page.getByLabel('Email').fill('not-an-email');
  await page.getByLabel('Username').fill('alice');
  await page.getByRole('button', { name: 'Register' }).click();

  // After form action fail(), SvelteKit re-renders with form values preserved
  await expect(page.getByLabel('Email')).toHaveValue('not-an-email');
  await expect(page.getByLabel('Username')).toHaveValue('alice');
  await expect(page.getByText('Invalid email format')).toBeVisible();
});
```

## Load Function Behavior Testing

```typescript
test('product page loads product data', async ({ page }) => {
  await page.goto('/products/42');

  // The page loads via SvelteKit's +page.server.ts load function
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  // Verify the loaded data appears in the page
  await expect(page.getByTestId('product-id')).toHaveText('42');
});

test('products page handles 404 from load function', async ({ page }) => {
  await page.goto('/products/99999');

  // SvelteKit throws error(404) in load — renders error page
  await expect(page).toHaveURL('/products/99999');
  await expect(page.getByRole('heading', { name: /not found/i })).toBeVisible();
});

test('authenticated page redirects unauthenticated users', async ({ page }) => {
  // Not logged in — visit a protected route
  await page.goto('/dashboard');

  // Load function calls redirect(303, '/login')
  await expect(page).toHaveURL('/login');
});
```

## Authentication Flow Patterns

### Session-Based (Cookies)

```typescript
// tests/e2e/fixtures.ts
import { test as base, type BrowserContext } from '@playwright/test';

export const test = base.extend<{ authedContext: BrowserContext }>({
  authedContext: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Perform login once per fixture
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('testpassword');
    await page.getByRole('button', { name: 'Log in' }).click();
    await page.waitForURL('/dashboard');
    await page.close();

    // Context now has the session cookie — reuse for all tests
    await use(context);
    await context.close();
  },
});

// In test file:
test('dashboard shows user name', async ({ authedContext }) => {
  const page = await authedContext.newPage();
  await page.goto('/dashboard');
  await expect(page.getByText('Welcome, Test User')).toBeVisible();
});
```

### Token-Based (localStorage / sessionStorage)

```typescript
test.beforeEach(async ({ page }) => {
  // Inject token before navigation to avoid full login flow
  await page.addInitScript(() => {
    localStorage.setItem('auth_token', 'test-token-xyz');
  });
  await page.goto('/dashboard');
});
```

## Network Request Interception

```typescript
test('shows error state when API fails', async ({ page }) => {
  // Intercept and fail the products API
  await page.route('/api/products', route => {
    route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
  });

  await page.goto('/products');
  await expect(page.getByRole('alert')).toContainText('Failed to load products');
});

test('shows cached data when API is slow', async ({ page }) => {
  // Delay the API response to test loading state
  await page.route('/api/products', async route => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    await route.continue();
  });

  await page.goto('/products');
  await expect(page.getByRole('progressbar')).toBeVisible(); // loading indicator
});

test('fulfills with mock data for repeatable scenarios', async ({ page }) => {
  await page.route('/api/products*', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Widget A', price: 9.99 },
        { id: 2, name: 'Widget B', price: 14.99 },
      ]),
    });
  });

  await page.goto('/products');
  await expect(page.getByRole('listitem')).toHaveCount(2);
});
```

## File Upload / Download Testing

```typescript
test('uploads a file', async ({ page }) => {
  await page.goto('/upload');

  const fileInput = page.getByLabel('Choose file');
  await fileInput.setInputFiles({
    name: 'document.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('PDF content'),
  });

  await page.getByRole('button', { name: 'Upload' }).click();
  await expect(page.getByText('document.pdf uploaded')).toBeVisible();
});

test('downloads a file', async ({ page }) => {
  await page.goto('/reports');

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export CSV' }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe('report.csv');
});
```

## Multi-Tab Scenarios

```typescript
test('share link opens product in new tab', async ({ page, context }) => {
  await page.goto('/products/1');
  const shareButton = page.getByRole('button', { name: 'Share' });

  // Wait for new page to open
  const [newPage] = await Promise.all([
    context.waitForEvent('page'),
    shareButton.click(),
  ]);

  await newPage.waitForLoadState();
  await expect(newPage).toHaveURL(/\/products\/1/);
  await expect(newPage.getByRole('heading', { level: 1 })).toBeVisible();
});
```

## SSR Hydration Verification

```typescript
test('SSR content hydrates without layout shift', async ({ page }) => {
  // Intercept JS to test SSR-only rendering first
  await page.route('**/*.js', route => route.abort());

  await page.goto('/products');

  // Content should be visible from SSR even without JS
  await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
  const items = await page.getByRole('listitem').count();
  expect(items).toBeGreaterThan(0);
});

test('page hydrates and enables interactivity', async ({ page }) => {
  await page.goto('/products');

  // After hydration, interactive elements should be clickable
  const searchInput = page.getByRole('searchbox');
  await expect(searchInput).toBeEnabled();
  await searchInput.fill('widget');
  // Verify client-side filtering works (hydration complete)
  await expect(page.getByRole('listitem')).toHaveCount(2);
});
```

## Visual Regression

```typescript
test('product card looks correct', async ({ page }) => {
  await page.goto('/products/1');
  await expect(page.getByTestId('product-card')).toHaveScreenshot('product-card.png');
});

test('full page screenshot', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png', {
    fullPage: true,
    maxDiffPixels: 50, // allow minor rendering differences
  });
});
```

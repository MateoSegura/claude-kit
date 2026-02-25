# Playwright E2E Examples

Complete test suites for common SvelteKit application patterns.

## Example 1: Login / Authentication Flow

```typescript
// tests/e2e/auth.e2e.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.describe('login page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
    });

    test('displays login form', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'Log in' })).toBeVisible();
      await expect(page.getByLabel('Email')).toBeVisible();
      await expect(page.getByLabel('Password')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Log in' })).toBeVisible();
    });

    test('redirects to dashboard after successful login', async ({ page }) => {
      await page.getByLabel('Email').fill('user@example.com');
      await page.getByLabel('Password').fill('correctpassword');
      await page.getByRole('button', { name: 'Log in' }).click();
      await expect(page).toHaveURL('/dashboard');
    });

    test('shows error for invalid credentials', async ({ page }) => {
      await page.getByLabel('Email').fill('user@example.com');
      await page.getByLabel('Password').fill('wrongpassword');
      await page.getByRole('button', { name: 'Log in' }).click();
      await expect(page.getByRole('alert')).toContainText('Invalid credentials');
      await expect(page).toHaveURL('/login');
    });

    test('shows client-side validation for empty fields', async ({ page }) => {
      await page.getByRole('button', { name: 'Log in' }).click();
      await expect(page.getByText('Email is required')).toBeVisible();
      await expect(page.getByText('Password is required')).toBeVisible();
    });

    test('redirects authenticated users away from login', async ({ page }) => {
      // Set auth cookie first
      await page.context().addCookies([{
        name: 'session',
        value: 'valid-session-token',
        domain: 'localhost',
        path: '/',
      }]);
      await page.goto('/login');
      await expect(page).toHaveURL('/dashboard');
    });
  });

  test.describe('logout', () => {
    test('clears session and redirects to login', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.getByLabel('Email').fill('user@example.com');
      await page.getByLabel('Password').fill('correctpassword');
      await page.getByRole('button', { name: 'Log in' }).click();
      await page.waitForURL('/dashboard');

      // Logout
      await page.getByRole('button', { name: 'Log out' }).click();
      await expect(page).toHaveURL('/login');

      // Verify session is cleared
      await page.goto('/dashboard');
      await expect(page).toHaveURL('/login');
    });
  });
});
```

---

## Example 2: CRUD Operations

```typescript
// tests/e2e/products-crud.e2e.ts
import { test, expect } from '@playwright/test';

test.describe('Product management', () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate
    await page.goto('/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('adminpassword');
    await page.getByRole('button', { name: 'Log in' }).click();
    await page.waitForURL('/dashboard');
  });

  test('creates a new product', async ({ page }) => {
    await page.goto('/products/new');

    await page.getByLabel('Product name').fill('Test Widget');
    await page.getByLabel('Price').fill('19.99');
    await page.getByLabel('Description').fill('A fantastic test widget');
    await page.getByRole('combobox', { name: 'Category' }).selectOption('Electronics');

    await page.getByRole('button', { name: 'Create product' }).click();

    // Should redirect to the new product page
    await expect(page).toHaveURL(/\/products\/\d+/);
    await expect(page.getByRole('heading', { name: 'Test Widget' })).toBeVisible();
  });

  test('edits an existing product', async ({ page }) => {
    await page.goto('/products/1/edit');

    await page.getByLabel('Product name').clear();
    await page.getByLabel('Product name').fill('Updated Widget Name');
    await page.getByRole('button', { name: 'Save changes' }).click();

    await expect(page).toHaveURL('/products/1');
    await expect(page.getByRole('heading', { name: 'Updated Widget Name' })).toBeVisible();
  });

  test('deletes a product with confirmation', async ({ page }) => {
    await page.goto('/products/1');

    // Click delete — triggers confirmation dialog
    await page.getByRole('button', { name: 'Delete product' }).click();
    await expect(page.getByRole('dialog', { name: 'Confirm deletion' })).toBeVisible();

    await page.getByRole('button', { name: 'Yes, delete' }).click();

    // Redirects to products list
    await expect(page).toHaveURL('/products');
    await expect(page.getByText('Product deleted successfully')).toBeVisible();
  });

  test('cancels deletion when user declines', async ({ page }) => {
    await page.goto('/products/1');

    await page.getByRole('button', { name: 'Delete product' }).click();
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Still on the same product page
    await expect(page).toHaveURL('/products/1');
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });
});
```

---

## Example 3: Search with Filtering and Pagination

```typescript
// tests/e2e/search.e2e.ts
import { test, expect } from '@playwright/test';

test.describe('Product search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/products');
    // Wait for initial product list to load
    await expect(page.getByRole('list', { name: 'Products' })).toBeVisible();
  });

  test('filters results as user types', async ({ page }) => {
    const initialCount = await page.getByRole('listitem').count();

    await page.getByRole('searchbox', { name: 'Search products' }).fill('widget');

    // Wait for debounce + results update
    await page.waitForResponse(resp => resp.url().includes('/api/products'));

    const filteredCount = await page.getByRole('listitem').count();
    expect(filteredCount).toBeLessThan(initialCount);
  });

  test('shows no results message for unmatched query', async ({ page }) => {
    await page.getByRole('searchbox').fill('xyznonexistent12345');
    await page.waitForResponse(resp => resp.url().includes('/api/products'));
    await expect(page.getByText('No products found')).toBeVisible();
  });

  test('applies category filter', async ({ page }) => {
    await page.getByRole('combobox', { name: 'Category' }).selectOption('Electronics');
    await page.waitForResponse(resp => resp.url().includes('/api/products'));

    // All visible items should be in the Electronics category
    const categories = await page.getByTestId('product-category').allTextContents();
    expect(categories.every(c => c === 'Electronics')).toBe(true);
  });

  test('resets filters on clear', async ({ page }) => {
    await page.getByRole('searchbox').fill('widget');
    await page.waitForResponse(resp => resp.url().includes('/api/products'));
    const filteredCount = await page.getByRole('listitem').count();

    await page.getByRole('button', { name: 'Clear filters' }).click();
    await page.waitForResponse(resp => resp.url().includes('/api/products'));
    const resetCount = await page.getByRole('listitem').count();

    expect(resetCount).toBeGreaterThan(filteredCount);
  });

  test('navigates to next page', async ({ page }) => {
    await expect(page.getByRole('navigation', { name: 'Pagination' })).toBeVisible();

    const firstPageItems = await page.getByRole('listitem').allTextContents();
    await page.getByRole('button', { name: 'Next page' }).click();
    await page.waitForURL(/[?&]page=2/);

    const secondPageItems = await page.getByRole('listitem').allTextContents();
    expect(secondPageItems).not.toEqual(firstPageItems);
  });
});
```

---

## Example 4: Form Validation with Server Errors

```typescript
// tests/e2e/registration.e2e.ts
import { test, expect } from '@playwright/test';

test.describe('Registration form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('shows all required fields', async ({ page }) => {
    await expect(page.getByLabel('Full name')).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByLabel('Confirm password')).toBeVisible();
  });

  test('validates email uniqueness via server', async ({ page }) => {
    // Use an email known to be taken in the test environment
    await page.getByLabel('Full name').fill('Alice Test');
    await page.getByLabel('Email').fill('existing@example.com');
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByLabel('Confirm password').fill('SecurePass123!');

    await page.getByRole('button', { name: 'Create account' }).click();

    // Server action returns fail() with error
    await expect(page.getByText('Email already in use')).toBeVisible();
    // Form should preserve filled values (SvelteKit form preservation)
    await expect(page.getByLabel('Full name')).toHaveValue('Alice Test');
    await expect(page.getByLabel('Email')).toHaveValue('existing@example.com');
  });

  test('validates password match client-side', async ({ page }) => {
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByLabel('Confirm password').fill('DifferentPass123!');
    await page.getByLabel('Confirm password').blur();

    await expect(page.getByText('Passwords do not match')).toBeVisible();
    // Submit should be disabled when passwords don't match
    await expect(page.getByRole('button', { name: 'Create account' })).toBeDisabled();
  });

  test('registers successfully and redirects', async ({ page }) => {
    const uniqueEmail = `test-${Date.now()}@example.com`;

    await page.getByLabel('Full name').fill('New User');
    await page.getByLabel('Email').fill(uniqueEmail);
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByLabel('Confirm password').fill('SecurePass123!');

    await page.getByRole('button', { name: 'Create account' }).click();

    await expect(page).toHaveURL('/welcome');
    await expect(page.getByText('Account created!')).toBeVisible();
  });
});
```

---

## Example 5: Navigation and SvelteKit Route Transitions

```typescript
// tests/e2e/navigation.e2e.ts
import { test, expect } from '@playwright/test';

test.describe('Application navigation', () => {
  test('main nav links navigate to correct pages', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('link', { name: 'Products' }).click();
    await expect(page).toHaveURL('/products');
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();

    await page.getByRole('link', { name: 'About' }).click();
    await expect(page).toHaveURL('/about');
    await expect(page.getByRole('heading', { name: 'About Us' })).toBeVisible();
  });

  test('browser back navigation works', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Products' }).click();
    await expect(page).toHaveURL('/products');

    await page.goBack();
    await expect(page).toHaveURL('/');
  });

  test('active nav link is marked with aria-current', async ({ page }) => {
    await page.goto('/products');
    const productLink = page.getByRole('link', { name: 'Products' });
    await expect(productLink).toHaveAttribute('aria-current', 'page');
    const homeLink = page.getByRole('link', { name: 'Home' });
    await expect(homeLink).not.toHaveAttribute('aria-current');
  });

  test('404 page shown for unknown routes', async ({ page }) => {
    await page.goto('/this-route-does-not-exist');
    await expect(page.getByRole('heading', { name: /not found/i })).toBeVisible();
  });

  test('loading indicator shows during route transitions', async ({ page }) => {
    // Slow down navigation to capture loading state
    await page.route('/products**', async route => {
      await new Promise(resolve => setTimeout(resolve, 500));
      await route.continue();
    });

    await page.goto('/');
    await page.getByRole('link', { name: 'Products' }).click();

    // Loading indicator should appear during the slow navigation
    await expect(page.getByRole('progressbar')).toBeVisible();

    // Wait for navigation to complete
    await expect(page).toHaveURL('/products');
    await expect(page.getByRole('progressbar')).not.toBeVisible();
  });
});
```

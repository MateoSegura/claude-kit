# Workflow Patterns

Step-by-step workflows for the five core testing activities. Each workflow reflects the decision sequence a senior test engineer follows when working with Svelte 5 / SvelteKit and the Vitest + Playwright + vitest-axe toolchain.

## 1. Unit Test Workflow

For TypeScript utility modules, `.svelte.ts` rune stores, SvelteKit load functions, form actions, and API endpoints.

### Steps

1. **Read the source file.** Identify all exported functions, classes, and constants. Note parameter types, return types, and thrown errors.

2. **Identify the test surface.** For each export:
   - What are the valid inputs? (happy path)
   - What are the invalid inputs? (error path)
   - What are the edge cases? (empty arrays, null, boundary values, concurrent calls)
   - Does it have side effects? (fetch calls, store mutations, file system access)

3. **Create the test file.** Name it `<source-name>.test.ts` in the same directory or `__tests__/`.

4. **Write the `describe` block.** One top-level `describe` per exported function or class. Nest by behavior category:
   ```typescript
   describe('validateEmail', () => {
     describe('with valid input', () => { /* ... */ });
     describe('with invalid input', () => { /* ... */ });
     describe('edge cases', () => { /* ... */ });
   });
   ```

5. **Write tests using Arrange-Act-Assert.**
   ```typescript
   it('returns true for a standard email address', () => {
     // Arrange
     const email = 'user@example.com';

     // Act
     const result = validateEmail(email);

     // Assert
     expect(result).toBe(true);
   });
   ```

6. **Mock external dependencies only.** If the function calls `fetch`, mock `fetch`. If it imports from `$app/environment`, mock that module. Never mock the function under test.

7. **Run the tests.** `npx vitest run <test-file> --reporter=verbose`

8. **Check coverage.** `npx vitest run <test-file> --coverage` -- verify the source file meets the 80% threshold across all four categories.

9. **Add tests for uncovered branches.** Coverage report shows uncovered lines. Each uncovered branch typically needs one test per branch path.

### When Testing `.svelte.ts` Rune Stores

- Import the store and call it like a function (Svelte 5 rune stores are just functions returning reactive objects)
- Use `$state` in test setup when you need reactive test variables
- Use `flushSync` from `svelte` to synchronously apply reactive updates before asserting
- Test the public API of the store (exported reactive properties and methods), not internal `$state` values

## 2. Component Test Workflow

For `.svelte` components using vitest-browser-svelte in Vitest browser mode.

### Steps

1. **Read the component file.** Identify:
   - Props interface (`$props()` destructuring)
   - Rendered states (loading, error, empty, populated, disabled)
   - User interactions (clicks, form inputs, keyboard events)
   - Callback props (Svelte 5 `onclick`, `onsubmit`, custom callbacks)
   - Snippets (Svelte 5 replacement for slots)
   - Conditional rendering branches (`{#if}`, `{#each}`, `{#await}`)

2. **Create the test file.** Name it `<ComponentName>.test.ts`.

3. **Set up imports.**
   ```typescript
   import { render } from 'vitest-browser-svelte';
   import { page } from '@vitest/browser/context';
   import ComponentName from './ComponentName.svelte';
   ```

4. **Write rendering tests first.** Test every visible state the component can be in:
   ```typescript
   describe('rendering', () => {
     it('displays the default state', async () => {
       render(ComponentName, { props: defaultProps() });
       await expect.element(page.getByRole('heading')).toHaveTextContent('Title');
     });

     it('displays the loading spinner when loading is true', async () => {
       render(ComponentName, { props: { ...defaultProps(), loading: true } });
       await expect.element(page.getByRole('progressbar')).toBeVisible();
     });
   });
   ```

5. **Write interaction tests.** Use Playwright locators via `page` for user actions:
   ```typescript
   describe('user interactions', () => {
     it('calls onsubmit with form data when submitted', async () => {
       const onsubmit = vi.fn();
       render(Form, { props: { onsubmit } });

       await page.getByLabel('Name').fill('Alice');
       await page.getByRole('button', { name: 'Submit' }).click();

       expect(onsubmit).toHaveBeenCalledOnce();
     });
   });
   ```

6. **Write prop reactivity tests.** Use `rerender` to simulate parent prop changes:
   ```typescript
   it('updates displayed count when count prop changes', async () => {
     const { rerender } = render(Counter, { props: { count: 0 } });
     await expect.element(page.getByText('Count: 0')).toBeVisible();

     await rerender({ count: 10 });
     await expect.element(page.getByText('Count: 10')).toBeVisible();
   });
   ```

7. **Write snippet tests** (if component accepts snippets):
   ```typescript
   import { createRawSnippet } from 'svelte';

   it('renders the header snippet', async () => {
     const header = createRawSnippet(() => ({
       render: () => '<span>Custom Header</span>',
     }));
     render(Card, { props: { header } });
     await expect.element(page.getByText('Custom Header')).toBeVisible();
   });
   ```

8. **Run and verify.** `npx vitest run <test-file> --browser --reporter=verbose`

### Key Rules for Component Tests

- Always query by accessible role or label first (`getByRole`, `getByLabelText`), fall back to `getByText`, never use `getByTestId` unless there is no accessible alternative.
- Use `async/await` for all element queries and interactions -- browser mode is async.
- Use `expect.element()` for browser-mode element assertions.
- Never access `component.$$.ctx` or any Svelte internals.

## 3. E2E Test Workflow

For multi-page user flows using Playwright against a running SvelteKit dev server.

### Steps

1. **Identify the user flow.** E2E tests cover cross-page journeys: login -> dashboard -> create item -> verify item appears. Each test file covers one coherent flow.

2. **Create or update the page object.** For each route involved in the flow, create a page object class in `tests/pages/`:
   ```typescript
   // tests/pages/login-page.ts
   import type { Page } from '@playwright/test';

   export class LoginPage {
     constructor(private page: Page) {}

     async goto() {
       await this.page.goto('/login');
     }

     async login(email: string, password: string) {
       await this.page.getByLabel('Email').fill(email);
       await this.page.getByLabel('Password').fill(password);
       await this.page.getByRole('button', { name: 'Sign in' }).click();
     }

     async expectError(message: string) {
       await expect(this.page.getByRole('alert')).toHaveText(message);
     }
   }
   ```

3. **Create the test file.** Name it `<flow-name>.spec.ts` in the `tests/` directory.

4. **Write the test using page objects.**
   ```typescript
   import { test, expect } from '@playwright/test';
   import { LoginPage } from './pages/login-page';
   import { DashboardPage } from './pages/dashboard-page';

   test.describe('Authentication flow', () => {
     test('redirects to dashboard after successful login', async ({ page }) => {
       const loginPage = new LoginPage(page);
       await loginPage.goto();
       await loginPage.login('user@example.com', 'password123');

       const dashboard = new DashboardPage(page);
       await dashboard.expectVisible();
       await expect(page).toHaveURL('/dashboard');
     });

     test('shows error for invalid credentials', async ({ page }) => {
       const loginPage = new LoginPage(page);
       await loginPage.goto();
       await loginPage.login('user@example.com', 'wrong');
       await loginPage.expectError('Invalid credentials');
     });
   });
   ```

5. **Handle network requests** when testing against real APIs:
   ```typescript
   // Intercept and mock API responses
   await page.route('/api/users', async (route) => {
     await route.fulfill({
       json: [{ id: '1', name: 'Test User' }],
     });
   });
   ```

6. **Run E2E tests.** `npx playwright test <test-file> --reporter=list`

7. **Review traces on failure.** `npx playwright show-trace trace.zip`

### Key Rules for E2E Tests

- Always use page objects for route interactions. Direct locator chains in tests become unmaintainable.
- Use `getByRole` and `getByLabel` locators. Avoid CSS selectors and XPath.
- Wait for navigation implicitly with `expect(page).toHaveURL()` rather than explicit `waitForNavigation`.
- Each E2E test must be independent -- use test fixtures or API calls for setup, not other tests.

## 4. A11y Audit Workflow

For WCAG 2.2 AA compliance verification using vitest-axe (component level) and axe-playwright (page level).

### Steps

1. **Identify components that need a11y testing.** Priority order:
   - Interactive components (buttons, forms, dialogs, menus, dropdowns)
   - Navigation components (nav bars, breadcrumbs, tab panels)
   - Content components that use ARIA (alerts, toasts, live regions)
   - Data display components (tables, lists with interaction)

2. **Write component-level a11y tests.**
   ```typescript
   import { render } from 'vitest-browser-svelte';
   import { axe } from 'vitest-axe';
   import 'vitest-axe/extend-expect';
   import Dialog from './Dialog.svelte';

   describe('Dialog accessibility', () => {
     it('has no WCAG 2.2 AA violations when open', async () => {
       const { container } = render(Dialog, {
         props: { open: true, title: 'Confirm action' },
       });
       const results = await axe(container, {
         tags: ['wcag2a', 'wcag2aa', 'wcag22aa'],
       });
       expect(results).toHaveNoViolations();
     });

     it('traps focus within the dialog', async () => {
       render(Dialog, { props: { open: true, title: 'Focus test' } });
       // Tab through all focusable elements and verify focus stays inside
       await page.keyboard.press('Tab');
       // ... assert focused element is inside dialog
     });

     it('closes with Escape key', async () => {
       const onclose = vi.fn();
       render(Dialog, { props: { open: true, title: 'Escape test', onclose } });
       await page.keyboard.press('Escape');
       expect(onclose).toHaveBeenCalledOnce();
     });

     it('returns focus to trigger element on close', async () => {
       // Test that focus management follows WCAG 2.2 requirement
     });
   });
   ```

3. **Write page-level a11y tests** for full routes:
   ```typescript
   // tests/a11y/dashboard.spec.ts
   import { test, expect } from '@playwright/test';
   import AxeBuilder from '@axe-core/playwright';

   test.describe('Dashboard page accessibility', () => {
     test('has no WCAG 2.2 AA violations', async ({ page }) => {
       await page.goto('/dashboard');
       const results = await new AxeBuilder({ page })
         .withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
         .analyze();

       expect(results.violations).toEqual([]);
     });
   });
   ```

4. **Test keyboard navigation patterns.** For each interactive component:
   - Tab order follows visual order
   - All interactive elements are reachable via Tab
   - Enter/Space activates buttons and links
   - Arrow keys navigate within composite widgets (menus, tab panels, radio groups)
   - Escape closes overlays and returns focus

5. **Test screen reader semantics.** Verify:
   - Headings form a logical hierarchy (`h1` > `h2` > `h3`)
   - Form fields have associated labels (`getByLabel` must find them)
   - Images have alt text (or `role="presentation"` for decorative)
   - Live regions announce dynamic content (`aria-live="polite"` or `role="alert"`)

6. **Run a11y tests.** Component-level: `npx vitest run **/*.a11y.test.ts`. Page-level: `npx playwright test tests/a11y/`.

### When to Disable axe Rules

Only disable specific axe rules when there is a documented, accepted exception. Always include the rationale:

```typescript
const results = await axe(container, {
  rules: {
    // Disabled: color contrast is handled by CSS custom properties
    // that axe cannot evaluate statically. Manual verification done.
    'color-contrast': { enabled: false },
  },
});
```

## 5. Coverage Gap-Filling Workflow

For systematically raising coverage from current levels to the 80% target.

### Steps

1. **Run the full suite with coverage.**
   ```bash
   npx vitest run --coverage --reporter=json --outputFile=coverage-report.json
   ```

2. **Identify files below threshold.** Parse the coverage summary and list every file below 80% in any category (statements, branches, functions, lines). Sort by lowest coverage first.

3. **Categorize the gaps.** For each under-covered file:
   - **Uncovered branches**: Usually `if/else`, ternary operators, early returns, error paths, and `{#if}/{:else}` template branches
   - **Uncovered functions**: Exported functions with zero calls in tests, event handlers, lifecycle callbacks
   - **Uncovered statements**: Often setup code, configuration objects, type guard functions
   - **Uncovered lines**: Lines inside uncovered branches or functions

4. **Prioritize by risk.** Fill gaps in this order:
   1. Error handling paths (catch blocks, error boundaries, validation failures)
   2. User-facing interaction handlers (click, submit, keyboard events)
   3. Conditional rendering branches (different states the user sees)
   4. Utility function edge cases
   5. Configuration and setup code (lowest risk, fill last)

5. **Write targeted tests for each gap.** One test per uncovered branch path. Use the uncovered line numbers from the coverage report to identify exactly which conditions to exercise.

6. **Re-run coverage after each batch.** Verify the numbers move up. If a gap resists coverage, it may be dead code -- flag it for removal rather than writing a test for unreachable code.

7. **Stop at 80%.** Do not pursue 100%. Report the final coverage numbers in a summary table:

   | Category | Before | After | Target |
   |----------|--------|-------|--------|
   | Statements | 62% | 83% | 80% |
   | Branches | 55% | 81% | 80% |
   | Functions | 70% | 85% | 80% |
   | Lines | 63% | 82% | 80% |

### Exclusions

Some code legitimately should not count toward coverage:
- Generated type guard functions (from Zod schemas, etc.)
- Development-only code (`if (dev)` blocks)
- Platform-specific fallbacks that cannot run in the test environment

Exclude these in `vitest.config.ts`:
```typescript
coverage: {
  exclude: [
    'src/**/*.generated.ts',
    'src/lib/dev-tools/**',
  ],
}
```

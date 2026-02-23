# vitest-axe Reference

## Installation and Setup

```bash
pnpm add -D vitest-axe
# For E2E a11y:
pnpm add -D @axe-core/playwright
```

### Option A: Extend in Setup File (Recommended)

```typescript
// src/vitest-setup-client.ts
import 'vitest-axe/extend-expect';
```

```typescript
// vitest.config.ts
test: {
  browser: { ... },
  setupFiles: ['./src/vitest-setup-client.ts'],
}
```

### Option B: Manual Extension Per Test File

```typescript
import * as matchers from 'vitest-axe/matchers';
import { expect } from 'vitest';
expect.extend(matchers);
```

### TypeScript Types

When using Option B, augment Vitest's types:

```typescript
// vitest.d.ts or src/vitest-augment.d.ts
import 'vitest';
import type { AxeMatchers } from 'vitest-axe/matchers';

declare module 'vitest' {
  export interface Assertion extends AxeMatchers {}
  export interface AsymmetricMatchersContaining extends AxeMatchers {}
}
```

## axe() Function API

```typescript
import { axe } from 'vitest-axe';

// Basic usage
const results = await axe(container);

// With axe options
const results = await axe(container, {
  runOnly: {
    type: 'tag',
    values: ['wcag2aa', 'wcag22aa'],
  },
  rules: {
    'color-contrast': { enabled: true },
    'landmark-one-main': { enabled: false },  // disable with justification
  },
  elementRef: true,  // include element references in results
});
```

## toHaveNoViolations Matcher

```typescript
// Basic assertion
expect(results).toHaveNoViolations();

// toHaveNoViolations returns detailed output on failure:
// Expected: No violations
// Received:
//   Rule: color-contrast (serious)
//   Description: Elements must have sufficient color contrast
//   Nodes: 3 elements
//   - Element: <button class="btn-light">
//     Impact: serious
//     Fix: Ensure the contrast ratio is at least 4.5:1
```

## Disabling Specific Rules with Rationale

When disabling rules, always include a comment explaining why — to prevent silent suppression of real issues:

```typescript
const results = await axe(container, {
  rules: {
    // Disabled: color-contrast is handled by our design system tokens.
    // All colors are validated at the design system level before usage.
    // See: docs/design/color-tokens.md
    'color-contrast': { enabled: false },

    // Disabled: landmark-one-main is not required for component-level tests.
    // This rule checks the full page structure — covered in E2E a11y tests.
    'landmark-one-main': { enabled: false },

    // Disabled: skip-link only makes sense at the page level.
    'skip-link': { enabled: false },
  },
});
```

## Testing Color Contrast Programmatically

```typescript
it('primary button meets color contrast requirements', async () => {
  render(Button, { variant: 'primary', label: 'Submit' });

  const results = await axe(document.body, {
    runOnly: { type: 'rule', values: ['color-contrast'] },
  });

  expect(results).toHaveNoViolations();
});

it('disabled button state meets color contrast', async () => {
  render(Button, { variant: 'primary', label: 'Submit', disabled: true });

  // Note: WCAG 2.1 exempts disabled UI components from contrast requirements
  // but best practice still aims for 3:1 ratio for readability
  const results = await axe(document.body, {
    runOnly: { type: 'rule', values: ['color-contrast'] },
  });
  expect(results).toHaveNoViolations();
});
```

## Testing ARIA Live Region Announcements

Live regions require a real browser to test properly (JSDOM does not dispatch live region events):

```typescript
it('announces status updates to screen readers', async () => {
  render(StatusBanner, { status: 'idle' });

  // Verify aria-live attribute is present and correct
  const statusRegion = page.getByRole('status');
  await expect.element(statusRegion).toHaveAttribute('aria-live', 'polite');
  await expect.element(statusRegion).toHaveAttribute('aria-atomic', 'true');
});

it('error messages use assertive live region', async () => {
  render(ErrorMessage, { message: 'Form submission failed' });

  const alert = page.getByRole('alert');
  // role="alert" implicitly has aria-live="assertive"
  await expect.element(alert).toBeVisible();
  await expect.element(alert).toHaveText('Form submission failed');

  // Verify axe doesn't flag the implementation
  const results = await axe(document.body);
  expect(results).toHaveNoViolations();
});
```

## Testing Focus Management

### Focus Trap in Modal

```typescript
it('traps focus within open modal', async () => {
  render(Modal, {
    open: true,
    title: 'Confirm Action',
    children: createRawSnippet(() => ({
      render: () => '<button>Option A</button><button>Option B</button>',
    })),
  });

  // Initial focus should be inside modal
  const dialog = page.getByRole('dialog', { name: 'Confirm Action' });
  await expect.element(dialog).toBeVisible();

  // Tab through all focusable elements
  await userEvent.keyboard('{Tab}');
  // Focus should still be inside modal (not outside)
  const activeElement = page.getByRole('button').first();
  await expect.element(activeElement).toBeFocused();
});
```

### Focus Restoration After Dismiss

```typescript
it('returns focus to trigger after modal closes', async () => {
  render(TriggerAndModal, {});

  const trigger = page.getByRole('button', { name: 'Open dialog' });
  await trigger.click();

  await expect.element(page.getByRole('dialog')).toBeVisible();

  // Close modal
  await page.getByRole('button', { name: 'Close' }).click();

  // Focus should return to trigger
  await expect.element(trigger).toBeFocused();
});
```

### Focus After Route Change (SvelteKit)

```typescript
// tests/e2e/focus-management.e2e.ts
import { test, expect } from '@playwright/test';

test('focus moves to main content after navigation', async ({ page }) => {
  await page.goto('/');

  // Navigate via SvelteKit client-side routing
  await page.getByRole('link', { name: 'Products' }).click();
  await page.waitForURL('/products');

  // SvelteKit should move focus to the h1 or a skip-nav target
  // Test that focus is not stuck on the nav link
  const activeElement = page.locator(':focus');
  await expect(activeElement).not.toHaveRole('link');
});
```

## axe-playwright Integration

```typescript
// tests/e2e/a11y-audit.e2e.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('WCAG 2.2 AA audit', () => {
  const routes = ['/', '/products', '/about', '/contact'];

  for (const route of routes) {
    test(`${route} passes automated a11y audit`, async ({ page }) => {
      await page.goto(route);
      await page.waitForLoadState('networkidle');

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2aa', 'wcag21aa', 'wcag22aa'])
        .analyze();

      // Attach detailed violation report to Playwright report
      if (results.violations.length > 0) {
        const violationSummary = results.violations.map(v =>
          `${v.id} (${v.impact}): ${v.description}\n` +
          v.nodes.slice(0, 2).map(n => `  - ${n.html}`).join('\n')
        ).join('\n\n');

        test.info().annotations.push({
          type: 'A11y Violations',
          description: violationSummary,
        });
      }

      expect(results.violations).toEqual([]);
    });
  }

  test('modal dialog passes a11y audit when open', async ({ page }) => {
    await page.goto('/products/1');
    await page.getByRole('button', { name: 'Delete' }).click();
    // Wait for modal to fully open
    await expect(page.getByRole('dialog')).toBeVisible();

    const results = await new AxeBuilder({ page })
      .include('[role="dialog"]')  // audit only the modal
      .withTags(['wcag2aa', 'wcag22aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });

  test('form passes a11y audit in error state', async ({ page }) => {
    await page.goto('/contact');
    // Submit without filling in fields to trigger error state
    await page.getByRole('button', { name: 'Send' }).click();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2aa', 'wcag22aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
```

## Configuring axe for Component Test Suite

A helper function to standardize axe configuration across all component tests:

```typescript
// src/test-utils/a11y.ts
import { axe, type AxeResults } from 'vitest-axe';

export const wcag22Options = {
  runOnly: {
    type: 'tag' as const,
    values: ['wcag2aa', 'wcag21aa', 'wcag22aa'],
  },
};

export async function auditComponent(
  container: Element = document.body
): Promise<AxeResults> {
  return axe(container, wcag22Options);
}

// Usage:
import { auditComponent } from '$test-utils/a11y';

it('passes WCAG 2.2 AA', async () => {
  render(MyComponent, { ... });
  const results = await auditComponent();
  expect(results).toHaveNoViolations();
});
```

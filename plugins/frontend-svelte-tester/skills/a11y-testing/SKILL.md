---
name: frontend-svelte-tester:a11y-testing
description: "Accessibility testing for Svelte 5 components and SvelteKit pages. Covers vitest-axe setup, axe-core rule sets, WCAG 2.2 AA criteria, component-level audits, keyboard navigation testing, and automated a11y verification patterns."
user-invocable: false
---

# Accessibility Testing

Automated accessibility testing catches ~30-40% of WCAG 2.2 AA issues. Combine component-level vitest-axe audits with Playwright page-level checks and manual keyboard/screen reader testing.

## Setup

```bash
pnpm add -D vitest-axe axe-playwright
```

```typescript
// src/vitest-setup-client.ts
import 'vitest-axe/extend-expect';  // adds toHaveNoViolations to expect
```

```typescript
// tsconfig.json — include setup file
{
  "include": ["src/vitest-setup-client.ts"]
}
```

## vitest-axe Core Pattern

```typescript
import { describe, it, expect } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { axe } from 'vitest-axe';
import { page } from 'vitest/browser';
import Button from './Button.svelte';

describe('Button accessibility', () => {
  it('has no WCAG 2.2 AA violations', async () => {
    render(Button, { label: 'Submit form' });
    // Get the rendered container's HTML
    const container = document.querySelector('[data-vitest-browser-container]')
      ?? document.body;
    const results = await axe(container, {
      runOnly: {
        type: 'tag',
        values: ['wcag2aa', 'wcag22aa'],
      },
    });
    expect(results).toHaveNoViolations();
  });
});
```

## axe Rule Sets

| Tag | What It Checks |
|-----|---------------|
| `wcag2a` | WCAG 2.0 Level A |
| `wcag2aa` | WCAG 2.0 Level AA (includes 2a) |
| `wcag21aa` | WCAG 2.1 Level AA additions |
| `wcag22aa` | WCAG 2.2 Level AA additions |
| `best-practice` | Common best practices beyond WCAG |
| `experimental` | Experimental rules (may have false positives) |
| `ACT` | W3C ACT rules |

**Recommended combination for WCAG 2.2 AA:**
```typescript
runOnly: { type: 'tag', values: ['wcag2aa', 'wcag21aa', 'wcag22aa'] }
```

## Component A11y Test Pattern

```typescript
// Every interactive component should have an a11y test
it('passes WCAG 2.2 AA automated audit', async () => {
  render(Component, props);
  const results = await axe(document.body, {
    runOnly: { type: 'tag', values: ['wcag2aa', 'wcag21aa', 'wcag22aa'] },
  });
  expect(results).toHaveNoViolations();
});
```

## Keyboard Navigation Testing

```typescript
import { userEvent } from 'vitest/browser';

it('modal is keyboard accessible', async () => {
  const onclose = vi.fn();
  render(Modal, { open: true, title: 'Dialog', onclose });

  // Focus should be trapped inside modal
  const closeButton = page.getByRole('button', { name: 'Close' });
  await expect.element(closeButton).toBeFocused();

  // Escape closes the modal
  await userEvent.keyboard('{Escape}');
  expect(onclose).toHaveBeenCalledOnce();
});

it('dropdown menu is navigable by keyboard', async () => {
  render(DropdownMenu, { items: ['Item 1', 'Item 2', 'Item 3'] });

  const trigger = page.getByRole('button', { name: 'Open menu' });
  await trigger.focus();
  await userEvent.keyboard('{Enter}');  // open menu

  await expect.element(page.getByRole('menu')).toBeVisible();

  await userEvent.keyboard('{ArrowDown}');
  await expect.element(page.getByRole('menuitem', { name: 'Item 1' })).toBeFocused();

  await userEvent.keyboard('{ArrowDown}');
  await expect.element(page.getByRole('menuitem', { name: 'Item 2' })).toBeFocused();
});
```

## Playwright Page-Level A11y (axe-playwright)

```typescript
// tests/e2e/a11y.e2e.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage passes WCAG 2.2 AA', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(results.violations).toEqual([]);
});
```

## Decision Matrix — Automated vs Manual Testing

| Issue Type | Automated Detection | Manual Required |
|------------|-------------------|-----------------|
| Missing alt text | Yes (axe) | Sometimes (content quality) |
| Color contrast | Partial (axe) | Yes (for complex backgrounds) |
| Keyboard navigation | Partial | Yes (complete flow testing) |
| Focus order | No | Yes |
| Screen reader announcements | No | Yes |
| Cognitive accessibility | No | Yes |
| Touch target size | Partial (axe best-practice) | Yes |
| Motion / animation safety | No | Yes |

## Additional Resources

- **[vitest-axe-reference.md](vitest-axe-reference.md)** — Full vitest-axe API, disabling specific rules with rationale, testing color contrast, aria-live regions, focus management, axe-playwright integration
- **[audit-checklist.md](audit-checklist.md)** — WCAG 2.2 AA automated audit checklist organized by criterion, per-component verification matrix, Svelte-specific a11y pitfalls

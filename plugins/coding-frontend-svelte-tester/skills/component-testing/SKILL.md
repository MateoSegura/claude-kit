---
name: coding-frontend-svelte-tester:component-testing
description: "Component testing for Svelte 5 using vitest-browser-svelte in real browser mode. Covers render API, page locators, userEvent, DOM assertions, and testing Svelte 5 runes ($state, $props, $effect, $bindable) and snippets in a real browser environment."
user-invocable: false
---

# Component Testing with vitest-browser-svelte

Component tests run in a real browser (Chromium) via Playwright provider. Use `.svelte.test.ts` extension to enable runes in test files.

## Setup

```bash
pnpm add -D vitest-browser-svelte @vitest/browser playwright
```

```typescript
// src/vitest-setup-client.ts
/// <reference types="vitest/browser" />
/// <reference types="@vitest/browser-playwright" />
import 'vitest-axe/extend-expect'; // optional: for a11y assertions
```

## Core Imports

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { page, userEvent } from 'vitest/browser';
import MyComponent from './MyComponent.svelte';
```

## render() API

```typescript
// Basic render — returns screen with locator methods
const screen = render(Component, props);

// With initial props
const screen = render(Counter, { initialCount: 5 });

// Access DOM via page locators (preferred — auto-retry)
const button = page.getByRole('button', { name: 'Increment' });
const heading = page.getByRole('heading', { level: 1 });
const input = page.getByLabel('Email address');
const text = page.getByText('Hello world');
const testId = page.getByTestId('submit-btn');

// Or via screen (same locators, scoped to rendered component)
const button = screen.getByRole('button', { name: 'Increment' });
```

## Locator Hierarchy (Prefer Accessibility-First)

| Priority | Query | When to Use |
|----------|-------|-------------|
| 1 | `getByRole(role, { name })` | Most interactive elements |
| 2 | `getByLabel(text)` | Form inputs with labels |
| 3 | `getByPlaceholder(text)` | Inputs without visible labels |
| 4 | `getByText(text)` | Non-interactive display text |
| 5 | `getByAltText(text)` | Images |
| 6 | `getByTitle(text)` | Elements with title attribute |
| 7 | `getByTestId(id)` | Last resort — stable test IDs |

## Assertions — Use expect.element for Retry-ability

```typescript
// DOM assertions with automatic retry until condition met or timeout
await expect.element(locator).toBeVisible();
await expect.element(locator).toBeInTheDocument();
await expect.element(locator).toBeDisabled();
await expect.element(locator).toBeEnabled();
await expect.element(locator).toHaveText('Expected text');
await expect.element(locator).toHaveValue('input value');
await expect.element(locator).toHaveAttribute('aria-expanded', 'true');
await expect.element(locator).toHaveClass('active');
await expect.element(locator).not.toBeInTheDocument();
```

## User Interactions

```typescript
// Click
await page.getByRole('button', { name: 'Submit' }).click();

// Type / fill
await page.getByLabel('Email').fill('user@example.com');

// Clear + type
await page.getByLabel('Search').clear();
await page.getByLabel('Search').fill('new value');

// Keyboard
await userEvent.keyboard('{Tab}');
await userEvent.keyboard('{Enter}');
await userEvent.keyboard('{Escape}');

// Select
await page.getByRole('combobox', { name: 'Country' }).selectOption('US');

// Check/uncheck
await page.getByRole('checkbox', { name: 'Agree' }).check();
await page.getByRole('checkbox', { name: 'Agree' }).uncheck();
```

## Testing $props Reactivity

```typescript
// Button.svelte — accepts label and onclick callback props
// test: Button.svelte.test.ts

it('calls onclick callback when clicked', async () => {
  const onclick = vi.fn();
  render(Button, { label: 'Click me', onclick });
  await page.getByRole('button', { name: 'Click me' }).click();
  expect(onclick).toHaveBeenCalledOnce();
});

it('shows updated label when prop changes', async () => {
  const { rerender } = render(Button, { label: 'Initial' });
  await expect.element(page.getByRole('button', { name: 'Initial' })).toBeVisible();
  // Note: vitest-browser-svelte does not expose rerender — re-render with new props
  // by calling render again (cleanup happens before each test automatically)
});
```

## Multiple Instances / Disambiguating

```typescript
// When multiple matching elements exist, use .first(), .nth(), .last(), or .all()
const links = page.getByRole('link', { name: 'View details' });
await expect.element(links.first()).toBeVisible();
await expect.element(links.nth(1)).toBeVisible();

const allButtons = await page.getByRole('button').all();
expect(allButtons).toHaveLength(3);
```

## Additional Resources

- **[browser-testing-reference.md](browser-testing-reference.md)** — Browser mode vs jsdom rationale, handling `$effect` with `flushSync`, testing `$bindable` props, conditional rendering, async components, snippets
- **[examples.md](examples.md)** — Complete test files: form component, data table, modal, navigation menu, search with debounce, `$state` counter

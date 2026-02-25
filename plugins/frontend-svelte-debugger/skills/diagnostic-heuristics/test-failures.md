# Test Failures — Svelte 5 / SvelteKit

Patterns for diagnosing Vitest component test failures, Playwright timing issues, and assertion mismatch categories.

---

## Vitest Component Test Lifecycle

### Setup Requirements

For `@testing-library/svelte` with Vitest, the setup file must be registered:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  }
});
```

```typescript
// src/test/setup.ts
import '@testing-library/svelte/vitest';  // registers auto-cleanup
import '@testing-library/jest-dom';        // extends expect with DOM matchers
```

**Symptom**: `cleanup is not a function` or "component not unmounted between tests"

**Cause**: Missing `import '@testing-library/svelte/vitest'` in setup file. Without it, components accumulate across tests.

---

### Symptom: `render` throws "document is not defined"

**Cause**: `environment` in `vitest.config.ts` is not set to `'jsdom'` or `'happy-dom'`.

**Fix**:
```typescript
test: {
  environment: 'jsdom',  // or 'happy-dom' (faster but less compatible)
}
```

Or add a file-level override with the `@vitest-environment` comment:
```typescript
// @vitest-environment jsdom
import { render } from '@testing-library/svelte';
```

---

### Symptom: Reactive state doesn't update during test

**Cause**: Svelte's DOM updates are batched and applied asynchronously. Asserting immediately after a state change may read the pre-update DOM.

```typescript
// BAD: asserts before DOM update
const { getByText } = render(Counter);
fireEvent.click(getByText('Increment'));
expect(getByText('Count: 1')).toBeInTheDocument();  // may fail — DOM not yet updated
```

**Fix**: Use `await` with `act` or `waitFor`:
```typescript
import { render, fireEvent, screen, waitFor } from '@testing-library/svelte';

const { getByText } = render(Counter);
await fireEvent.click(getByText('Increment'));  // fireEvent from @testing-library auto-flushes
await waitFor(() => {
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

`@testing-library/svelte`'s `fireEvent` automatically calls `tick()` after each event. For manual state changes, call `await tick()` from `svelte`.

---

### Symptom: $effect does not run in test

**Cause**: `$effect` runs after component mount and after each reactive update. In Vitest with JSDOM, the effect scheduling may behave differently from a real browser.

**Fix**: Use `waitFor` to poll for expected DOM state rather than asserting synchronously. If testing `$effect` behavior specifically, ensure the component is mounted and a tick has passed:

```typescript
import { tick } from 'svelte';
import { render } from '@testing-library/svelte';

const { ... } = render(MyComponent, { props: { url: 'ws://localhost' } });
await tick();  // allow $effect to run
// now assert
```

---

### Symptom: Context not available in test

**Cause**: Testing a component that calls `getContext()` without providing the context in the test.

**Fix**: Wrap the component under test in a wrapper component that provides the context, or use the `options.context` parameter:

```typescript
import { render } from '@testing-library/svelte';
import Child from './Child.svelte';

render(Child, {
  context: new Map([
    ['theme', { color: 'blue' }]
  ])
});
```

---

## Playwright Timing Issues

### Symptom: `waitForSelector` times out on element that should exist

**Cause A — Navigation not awaited**:
```typescript
// BAD: doesn't wait for navigation to complete
await page.click('a[href="/dashboard"]');
await expect(page.locator('h1')).toHaveText('Dashboard');  // fails — page still loading
```

**Fix**:
```typescript
await Promise.all([
  page.waitForNavigation(),
  page.click('a[href="/dashboard"]')
]);
// or use waitForURL
await page.click('a[href="/dashboard"]');
await page.waitForURL('/dashboard');
```

---

**Cause B — SSR race condition**: Page hydrates after initial load; an element exists in server HTML but an event handler isn't attached yet.

**Fix**: Use `page.waitForFunction` to check for interactivity:
```typescript
await page.waitForFunction(() => {
  const btn = document.querySelector('button[data-testid="submit"]');
  return btn && !btn.disabled;
});
```

---

### Symptom: Playwright test flaky — passes 9/10 times

**Cause**: Test depends on network timing (API response), animation completion, or WebSocket message arrival without proper wait.

**Fix**: Replace hardcoded `waitForTimeout` with condition-based waits:
```typescript
// BAD: arbitrary timeout
await page.waitForTimeout(1000);
await expect(page.locator('.status')).toHaveText('Connected');

// GOOD: wait for the condition
await expect(page.locator('.status')).toHaveText('Connected', { timeout: 5000 });
```

---

## Assertion Mismatch Categories

### Category 1: Test bug — test is checking wrong thing

**Indicators**:
- Test fails on a trivially correct component
- Selector does not match the component's actual HTML structure
- Expected value hardcoded with wrong case/whitespace

**Diagnostic**: Use `screen.debug()` or `console.log(document.body.innerHTML)` to inspect actual rendered HTML.

---

### Category 2: App bug — component behavior is wrong

**Indicators**:
- Test was passing before a recent change
- Multiple tests fail simultaneously
- Failure reproduces in browser (not just test environment)

**Diagnostic**: Add `screen.debug()` after the failing assertion to inspect state. Check recent git changes to the component.

---

### Category 3: Test environment mismatch

**Indicators**:
- Test passes in browser mode but fails in JSDOM
- Test fails in CI but passes locally
- Error references Node.js-only or browser-only APIs

**Diagnostic**:
- JSDOM/happy-dom limitations: no layout engine, no CSS parsing, no `canvas`, limited `IntersectionObserver`
- Use `vitest-browser-svelte` for tests that require real browser behavior
- CI differences: check Node.js version, missing environment variables, different locale

---

### Category 4: Snapshot mismatch

**Symptom**: Snapshot test fails after intentional UI change.

**Diagnostic**: Was the change intentional? If yes, update snapshots. If no, investigate what changed.

**Fix**: `npx vitest --update-snapshots` (intentional change) OR revert the code change that caused the unintended snapshot diff.

---

## Test Failure Quick Reference

| Symptom | Category | First Action |
|---------|----------|-------------|
| `document is not defined` | Environment | Add `environment: 'jsdom'` to vitest config |
| Element not found / timeout | Timing | Add `await waitFor(...)` or `await tick()` |
| `getContext` returns undefined | Context | Pass context via `render(Component, { context })` |
| Assertion passes locally, fails CI | Env mismatch | Check env vars, Node version, missing `setup.ts` |
| Snapshot mismatch after UI change | Snapshot | Update with `--update-snapshots` if intentional |
| Effect doesn't fire | Scheduling | Add `await tick()` after mount |
| Multiple test failures after one change | App bug | Identify the regression with `git bisect` |

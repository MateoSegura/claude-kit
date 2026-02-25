# Component Testing Examples

Complete test files for common Svelte 5 component patterns.

## Example 1: $state Counter Component

```svelte
<!-- src/lib/components/Counter.svelte -->
<script lang="ts">
  let { initial = 0, step = 1, onchange }: {
    initial?: number;
    step?: number;
    onchange?: (value: number) => void;
  } = $props();

  let count = $state(initial);
  let doubled = $derived(count * 2);

  function increment() {
    count += step;
    onchange?.(count);
  }

  function decrement() {
    count -= step;
    onchange?.(count);
  }
</script>

<div>
  <button onclick={decrement} aria-label="Decrement">-</button>
  <output data-testid="count">{count}</output>
  <button onclick={increment} aria-label="Increment">+</button>
  <small data-testid="doubled">Doubled: {doubled}</small>
</div>
```

```typescript
// src/lib/components/Counter.svelte.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { page } from 'vitest/browser';
import Counter from './Counter.svelte';

describe('Counter', () => {
  it('renders with default initial value of 0', async () => {
    render(Counter);
    await expect.element(page.getByTestId('count')).toHaveText('0');
  });

  it('renders with provided initial value', async () => {
    render(Counter, { initial: 10 });
    await expect.element(page.getByTestId('count')).toHaveText('10');
  });

  it('increments count on + button click', async () => {
    render(Counter, { initial: 5 });
    await page.getByRole('button', { name: 'Increment' }).click();
    await expect.element(page.getByTestId('count')).toHaveText('6');
  });

  it('decrements count on - button click', async () => {
    render(Counter, { initial: 5 });
    await page.getByRole('button', { name: 'Decrement' }).click();
    await expect.element(page.getByTestId('count')).toHaveText('4');
  });

  it('updates doubled display after increment', async () => {
    render(Counter, { initial: 3 });
    await page.getByRole('button', { name: 'Increment' }).click();
    await expect.element(page.getByTestId('doubled')).toHaveText('Doubled: 8');
  });

  it('uses custom step size', async () => {
    render(Counter, { initial: 0, step: 5 });
    await page.getByRole('button', { name: 'Increment' }).click();
    await expect.element(page.getByTestId('count')).toHaveText('5');
  });

  it('calls onchange with new value after increment', async () => {
    const onchange = vi.fn();
    render(Counter, { initial: 0, onchange });
    await page.getByRole('button', { name: 'Increment' }).click();
    expect(onchange).toHaveBeenCalledWith(1);
  });

  it('calls onchange with new value after decrement', async () => {
    const onchange = vi.fn();
    render(Counter, { initial: 5, onchange });
    await page.getByRole('button', { name: 'Decrement' }).click();
    expect(onchange).toHaveBeenCalledWith(4);
  });
});
```

---

## Example 2: Form Component with Validation

```typescript
// src/lib/components/LoginForm.svelte.test.ts
import { describe, it, expect, vi } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { page } from 'vitest/browser';
import LoginForm from './LoginForm.svelte';

describe('LoginForm', () => {
  describe('initial state', () => {
    it('renders email and password fields', async () => {
      render(LoginForm);
      await expect.element(page.getByLabel('Email')).toBeVisible();
      await expect.element(page.getByLabel('Password')).toBeVisible();
    });

    it('renders submit button as enabled', async () => {
      render(LoginForm);
      await expect.element(page.getByRole('button', { name: 'Log in' })).toBeEnabled();
    });
  });

  describe('validation', () => {
    it('shows error for invalid email format', async () => {
      render(LoginForm);
      await page.getByLabel('Email').fill('not-an-email');
      await page.getByLabel('Email').blur();
      await expect.element(page.getByText('Enter a valid email address')).toBeVisible();
    });

    it('shows error for short password', async () => {
      render(LoginForm);
      await page.getByLabel('Password').fill('abc');
      await page.getByLabel('Password').blur();
      await expect.element(page.getByText('Password must be at least 8 characters')).toBeVisible();
    });

    it('does not show errors for valid inputs before blur', async () => {
      render(LoginForm);
      await page.getByLabel('Email').fill('user@example.com');
      // No blur — no error yet
      await expect.element(page.getByText('Enter a valid email address')).not.toBeInTheDocument();
    });
  });

  describe('submission', () => {
    it('calls onsubmit with credentials when form is valid', async () => {
      const onsubmit = vi.fn();
      render(LoginForm, { onsubmit });
      await page.getByLabel('Email').fill('user@example.com');
      await page.getByLabel('Password').fill('securepassword');
      await page.getByRole('button', { name: 'Log in' }).click();
      expect(onsubmit).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'securepassword',
      });
    });

    it('disables submit button while submitting', async () => {
      const onsubmit = vi.fn(() => new Promise(() => {})); // never resolves
      render(LoginForm, { onsubmit });
      await page.getByLabel('Email').fill('user@example.com');
      await page.getByLabel('Password').fill('securepassword');
      await page.getByRole('button', { name: 'Log in' }).click();
      await expect.element(page.getByRole('button', { name: 'Log in' })).toBeDisabled();
    });
  });
});
```

---

## Example 3: Search with Debounce

```typescript
// src/lib/components/SearchBox.svelte.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { page } from 'vitest/browser';
import SearchBox from './SearchBox.svelte';

describe('SearchBox', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('shows placeholder text', async () => {
    render(SearchBox, { placeholder: 'Search products...' });
    await expect.element(page.getByPlaceholder('Search products...')).toBeVisible();
  });

  it('calls onsearch after debounce delay', async () => {
    const onsearch = vi.fn();
    render(SearchBox, { onsearch, debounceMs: 300 });
    await page.getByRole('searchbox').fill('svelte');
    expect(onsearch).not.toHaveBeenCalled(); // not yet
    vi.advanceTimersByTime(300);
    expect(onsearch).toHaveBeenCalledWith('svelte');
  });

  it('cancels previous debounce on rapid typing', async () => {
    const onsearch = vi.fn();
    render(SearchBox, { onsearch, debounceMs: 300 });
    const input = page.getByRole('searchbox');
    await input.fill('a');
    vi.advanceTimersByTime(200);
    await input.fill('ab');
    vi.advanceTimersByTime(200);
    await input.fill('abc');
    vi.advanceTimersByTime(300);
    expect(onsearch).toHaveBeenCalledTimes(1);
    expect(onsearch).toHaveBeenCalledWith('abc');
  });

  it('shows clear button when input has value', async () => {
    render(SearchBox, { onsearch: vi.fn() });
    await page.getByRole('searchbox').fill('test');
    await expect.element(page.getByRole('button', { name: 'Clear search' })).toBeVisible();
  });

  it('clears input and calls onsearch with empty string when clear is clicked', async () => {
    const onsearch = vi.fn();
    render(SearchBox, { onsearch });
    await page.getByRole('searchbox').fill('test');
    vi.advanceTimersByTime(300);
    vi.clearAllMocks();
    await page.getByRole('button', { name: 'Clear search' }).click();
    await expect.element(page.getByRole('searchbox')).toHaveValue('');
    expect(onsearch).toHaveBeenCalledWith('');
  });
});
```

---

## Example 4: Navigation Menu

```typescript
// src/lib/components/NavMenu.svelte.test.ts
import { describe, it, expect, vi } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { page, userEvent } from 'vitest/browser';
import NavMenu from './NavMenu.svelte';

const items = [
  { href: '/', label: 'Home' },
  { href: '/about', label: 'About' },
  { href: '/contact', label: 'Contact' },
];

describe('NavMenu', () => {
  it('renders all nav items', async () => {
    render(NavMenu, { items });
    const links = await page.getByRole('link').all();
    expect(links).toHaveLength(3);
  });

  it('renders correct href for each item', async () => {
    render(NavMenu, { items });
    await expect.element(page.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/');
    await expect.element(page.getByRole('link', { name: 'About' })).toHaveAttribute('href', '/about');
  });

  it('marks active item with aria-current', async () => {
    render(NavMenu, { items, currentPath: '/about' });
    await expect.element(
      page.getByRole('link', { name: 'About' })
    ).toHaveAttribute('aria-current', 'page');
  });

  it('does not mark non-active items with aria-current', async () => {
    render(NavMenu, { items, currentPath: '/about' });
    await expect.element(
      page.getByRole('link', { name: 'Home' })
    ).not.toHaveAttribute('aria-current');
  });

  describe('mobile menu', () => {
    it('hides nav links behind hamburger on mobile', async () => {
      render(NavMenu, { items, mobile: true });
      // Menu hidden by default
      await expect.element(page.getByRole('navigation')).toHaveAttribute('data-open', 'false');
    });

    it('opens menu when hamburger is clicked', async () => {
      render(NavMenu, { items, mobile: true });
      await page.getByRole('button', { name: 'Open menu' }).click();
      await expect.element(page.getByRole('navigation')).toHaveAttribute('data-open', 'true');
    });

    it('closes menu when Escape is pressed', async () => {
      render(NavMenu, { items, mobile: true });
      await page.getByRole('button', { name: 'Open menu' }).click();
      await userEvent.keyboard('{Escape}');
      await expect.element(page.getByRole('navigation')).toHaveAttribute('data-open', 'false');
    });
  });
});
```

---

## Example 5: Data Table

```typescript
// src/lib/components/DataTable.svelte.test.ts
import { describe, it, expect, vi } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { page } from 'vitest/browser';
import DataTable from './DataTable.svelte';

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'email', label: 'Email', sortable: false },
  { key: 'role', label: 'Role', sortable: true },
];

const rows = [
  { id: 1, name: 'Alice', email: 'alice@example.com', role: 'Admin' },
  { id: 2, name: 'Bob', email: 'bob@example.com', role: 'User' },
  { id: 3, name: 'Carol', email: 'carol@example.com', role: 'User' },
];

describe('DataTable', () => {
  it('renders column headers', async () => {
    render(DataTable, { columns, rows });
    await expect.element(page.getByRole('columnheader', { name: 'Name' })).toBeVisible();
    await expect.element(page.getByRole('columnheader', { name: 'Email' })).toBeVisible();
    await expect.element(page.getByRole('columnheader', { name: 'Role' })).toBeVisible();
  });

  it('renders one row per data item', async () => {
    render(DataTable, { columns, rows });
    // thead row + 3 data rows
    const dataRows = await page.getByRole('row').all();
    expect(dataRows).toHaveLength(4); // 1 header + 3 data
  });

  it('shows empty state when rows is empty', async () => {
    render(DataTable, { columns, rows: [], emptyMessage: 'No users found' });
    await expect.element(page.getByText('No users found')).toBeVisible();
  });

  it('shows loading spinner when loading is true', async () => {
    render(DataTable, { columns, rows: [], loading: true });
    await expect.element(page.getByRole('progressbar')).toBeVisible();
  });

  it('calls onsort with column key and direction when sortable header clicked', async () => {
    const onsort = vi.fn();
    render(DataTable, { columns, rows, onsort });
    await page.getByRole('columnheader', { name: 'Name' }).click();
    expect(onsort).toHaveBeenCalledWith({ key: 'name', direction: 'asc' });
    await page.getByRole('columnheader', { name: 'Name' }).click();
    expect(onsort).toHaveBeenCalledWith({ key: 'name', direction: 'desc' });
  });

  it('does not call onsort when non-sortable header is clicked', async () => {
    const onsort = vi.fn();
    render(DataTable, { columns, rows, onsort });
    await page.getByRole('columnheader', { name: 'Email' }).click();
    expect(onsort).not.toHaveBeenCalled();
  });
});
```

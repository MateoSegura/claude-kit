# Test Coding Standards

Complete style guide for test code in the coding-frontend-svelte-tester plugin. All test code must follow these conventions for consistency across unit, component, E2E, and a11y test files.

## File Naming and Placement

### Naming Conventions

| Source File | Test File | Example |
|-------------|-----------|---------|
| `Button.svelte` | `Button.test.ts` | Component test |
| `utils.ts` | `utils.test.ts` | Unit test |
| `auth.svelte.ts` | `auth.svelte.test.ts` | Runes store test |
| `+page.server.ts` | `page-server-load.test.ts` | Load function test |
| `+server.ts` | `api-endpoint.test.ts` | API route test |
| Route `/dashboard` | `dashboard.spec.ts` | E2E test (Playwright) |
| Component a11y | `Button.a11y.test.ts` | A11y audit test |

### Placement Rules

- **Unit and component tests**: Colocate with source in the same directory, OR place in a sibling `__tests__/` directory. Choose one convention per project and stick to it.
- **E2E tests**: Always in the project root `tests/` or `e2e/` directory, matching the Playwright config's `testDir`.
- **Test utilities and helpers**: In `tests/utils/` or `src/test-utils/`.
- **Test fixtures**: In `tests/fixtures/` or colocated `__fixtures__/` directories.
- **Page objects**: In `tests/pages/` for E2E page object classes.

### File Extensions

- `.test.ts` -- Vitest tests (unit, component, a11y)
- `.spec.ts` -- Playwright E2E tests
- Never `.test.js` or `.spec.js` -- TypeScript strict mode is mandatory

## describe/it Block Organization

### Structure

```typescript
describe('ComponentName', () => {
  // Shared setup
  beforeEach(() => {
    // Fresh state for each test
  });

  afterEach(() => {
    // Cleanup (if needed)
  });

  describe('rendering', () => {
    it('displays the default state', async () => { /* ... */ });
    it('displays the loading state', async () => { /* ... */ });
    it('displays the error state', async () => { /* ... */ });
    it('displays the empty state', async () => { /* ... */ });
  });

  describe('user interactions', () => {
    it('submits the form when submit button is clicked', async () => { /* ... */ });
    it('clears the input when reset button is clicked', async () => { /* ... */ });
  });

  describe('prop changes', () => {
    it('updates displayed name when name prop changes', async () => { /* ... */ });
  });

  describe('accessibility', () => {
    it('has no WCAG 2.2 AA violations', async () => { /* ... */ });
    it('is keyboard navigable', async () => { /* ... */ });
  });
});
```

### Naming Rules

- `describe` blocks: Use the component name or module name at the top level. Use behavioral categories for nesting (`rendering`, `user interactions`, `prop changes`, `accessibility`, `error handling`).
- `it` descriptions: Present tense, from the user's perspective. Start with a verb: `displays`, `submits`, `navigates`, `prevents`, `shows`, `hides`, `updates`, `calls`.
- Never use `test()` -- always `it()` for consistency.
- Never use `it.skip()` in committed code. Use `it.todo()` for planned tests with a description of what the test will cover.

### Grouping Order

Within a `describe` block, order nested groups:
1. `rendering` -- default and variant states
2. `user interactions` -- clicks, inputs, form submissions
3. `prop changes` -- reactive updates from parent
4. `accessibility` -- WCAG compliance, keyboard nav
5. `error handling` -- invalid input, network failures, edge cases

## Assertion Patterns

### Preferred Matchers

| Scenario | Matcher | Example |
|----------|---------|---------|
| Element visible | `toBeVisible()` | `await expect.element(page.getByText('Hello')).toBeVisible()` |
| Element not present | `not.toBeInTheDocument()` | `expect(page.getByText('Error').query()).not.toBeInTheDocument()` |
| Text content | `toHaveTextContent()` | `await expect.element(heading).toHaveTextContent('Dashboard')` |
| Attribute value | `toHaveAttribute()` | `await expect.element(link).toHaveAttribute('href', '/home')` |
| Function called | `toHaveBeenCalledWith()` | `expect(onsubmit).toHaveBeenCalledWith(expected)` |
| Thrown error | `toThrow()` | `expect(() => validate(bad)).toThrow('Invalid')` |
| Array contains | `toContainEqual()` | `expect(items).toContainEqual({ id: 1 })` |
| Object shape | `toMatchObject()` | `expect(result).toMatchObject({ status: 'ok' })` |
| A11y clean | `toHaveNoViolations()` | `expect(axeResults).toHaveNoViolations()` |

### Assertion Anti-Patterns

```typescript
// BAD: Snapshot of entire component render
expect(container).toMatchSnapshot();

// GOOD: Targeted assertions on specific elements
await expect.element(page.getByRole('heading')).toHaveTextContent('Welcome');
await expect.element(page.getByRole('button')).toBeVisible();

// BAD: Truthy check hides the actual value on failure
expect(result).toBeTruthy();

// GOOD: Specific assertion with clear failure message
expect(result).toBe('expected-value');

// BAD: Testing internal state
expect(component.$$.ctx[0]).toBe(5);

// GOOD: Testing visible output
await expect.element(page.getByText('Count: 5')).toBeVisible();
```

## Mock Conventions

### Mock Placement

```typescript
// Module-level mocks (hoisted by Vitest)
vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
  invalidateAll: vi.fn(),
}));

vi.mock('$app/stores', () => ({
  page: { subscribe: vi.fn() },
}));

describe('MyComponent', () => {
  // Import after mocking
  let goto: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    vi.clearAllMocks();
    const nav = await import('$app/navigation');
    goto = nav.goto as ReturnType<typeof vi.fn>;
  });
});
```

### Mock Rules

1. **Mock at the module boundary**, not at the function level inside a module. Use `vi.mock('module-path')` to replace entire modules.
2. **Reset all mocks in `beforeEach`** with `vi.clearAllMocks()`. Never let mock state leak between tests.
3. **Type your mocks**. Use `ReturnType<typeof vi.fn>` or explicit type annotations. Never use `any` for mock return types.
4. **Mock only external dependencies**: SvelteKit modules (`$app/*`, `$env/*`), fetch calls, third-party APIs. Never mock the module under test.
5. **Use `vi.spyOn` for observation only**: When you need to verify a call was made to a real function without replacing its behavior.

### Common SvelteKit Mocks

```typescript
// $app/navigation
vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
  invalidate: vi.fn(),
  invalidateAll: vi.fn(),
  preloadData: vi.fn(),
  beforeNavigate: vi.fn(),
  afterNavigate: vi.fn(),
}));

// $app/environment
vi.mock('$app/environment', () => ({
  browser: true,
  dev: true,
  building: false,
  version: 'test',
}));

// fetch in load functions
const mockFetch = vi.fn().mockResolvedValue(
  new Response(JSON.stringify({ data: [] }), { status: 200 })
);
```

## Fixture and Test Data Patterns

### Test Data Factories

For components with complex props, use factory functions instead of inline objects:

```typescript
// tests/factories/user.ts
interface UserProps {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
  avatar?: string;
}

export function createUser(overrides: Partial<UserProps> = {}): UserProps {
  return {
    id: crypto.randomUUID(),
    name: 'Test User',
    email: 'test@example.com',
    role: 'user',
    ...overrides,
  };
}

// In tests:
const admin = createUser({ role: 'admin', name: 'Admin User' });
const guest = createUser({ role: 'guest' });
```

### Factory Rules

1. Every factory returns a valid default object with no required overrides.
2. Use `Partial<T>` for the overrides parameter.
3. Factories live in `tests/factories/` and export named functions prefixed with `create`.
4. One factory per domain type (user, product, order, etc.).
5. Use factories whenever a prop object has 4+ properties.

### Fixture Files

Static fixture data (JSON responses, large datasets) goes in `tests/fixtures/`:

```
tests/
  fixtures/
    users.json           # Mock API response data
    products.json        # Large dataset for table tests
    form-scenarios.ts    # Parameterized form input cases
```

```typescript
// tests/fixtures/form-scenarios.ts
export const validFormInputs = [
  { email: 'user@example.com', password: 'Str0ng!Pass', expected: 'success' },
  { email: 'admin@co.org', password: 'An0ther!One', expected: 'success' },
] as const;

export const invalidFormInputs = [
  { email: '', password: 'x', expected: 'Email is required' },
  { email: 'bad', password: 'x', expected: 'Invalid email format' },
  { email: 'a@b.com', password: '', expected: 'Password is required' },
] as const;
```

## TypeScript Standards in Tests

### Required Practices

- All test files use `.test.ts` or `.spec.ts` extension
- No `// @ts-ignore` or `// @ts-nocheck` comments
- No `as any` type casts -- use `as unknown as SpecificType` if genuinely needed, with a comment explaining why
- Mock return types must be explicitly typed or inferred from `vi.fn<T>()`
- Use `satisfies` for compile-time validation of test data against interfaces
- Import types with `import type { ... }` for type-only imports

### Type Patterns for Test Setup

```typescript
// Typing mock functions
const onchange = vi.fn<(value: string) => void>();

// Typing render props
const props: ComponentProps<typeof SearchInput> = {
  placeholder: 'Search...',
  onchange,
};

// Typing factory returns
function createProps(
  overrides: Partial<ComponentProps<typeof Card>> = {}
): ComponentProps<typeof Card> {
  return { title: 'Default', ...overrides };
}
```

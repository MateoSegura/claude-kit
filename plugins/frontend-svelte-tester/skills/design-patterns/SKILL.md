---
name: frontend-svelte-tester:design-patterns
description: "Test design patterns and anti-patterns for Svelte 5 / SvelteKit projects. Quick-reference decision matrices for test structure, fixture building, doubles (stub/mock/spy), and common mistakes that produce brittle or misleading tests."
user-invocable: false
---

# Test Design Patterns for Svelte 5

Quick reference. See [patterns-reference.md](patterns-reference.md) for code examples. See [anti-patterns.md](anti-patterns.md) for what to avoid.

## Pattern Overview

| Pattern | Description | Use When |
|---------|-------------|----------|
| Arrange-Act-Assert | Structure each test in 3 phases | Every test |
| Given-When-Then | BDD narrative for behavior tests | User-facing features |
| Builder / Test Data Builder | Fluent API for complex test objects | Complex props, form data |
| Factory | Function returning default test objects | Repeated setup with overrides |
| Page Object Model | Class encapsulating route locators | Playwright E2E tests |
| Parameterized (test.each) | Run test with multiple input sets | Pure functions, validation |
| Custom Matcher | extend expect() with domain matchers | Repeated assertion patterns |
| Test Double Hierarchy | stub / spy / mock with clear intent | Isolating dependencies |

## Decision Matrix — Test Structure

| Question | Pattern | Avoid |
|----------|---------|-------|
| Testing a pure function with many inputs? | `test.each` | Copy-paste tests |
| Testing component rendering with various props? | Factory + `test.each` | Snapshot |
| Testing async user interaction? | `expect.element` auto-retry | `setTimeout` waits |
| Testing a multi-step user flow? | Page Object Model | Inline selectors |
| Need complex nested object as prop? | Builder pattern | Inline object literals everywhere |
| Verifying a callback was invoked? | Spy (`vi.fn()`) | Implementation spying |
| Replacing a module dependency? | Mock (`vi.mock()`) | Mocking the module under test |
| Providing a stub return value? | Stub (`vi.fn().mockReturnValue()`) | Real network calls |

## Test Double Hierarchy

| Type | What It Does | When to Use |
|------|-------------|-------------|
| **Stub** | Returns predefined value, no call verification | Replacing external data sources |
| **Spy** | Records calls, lets real implementation run | Verifying callbacks were invoked |
| **Mock** | Replaces module entirely, verify interactions | Replacing heavy dependencies ($app/navigation) |
| **Fake** | Working implementation (e.g., in-memory store) | When mock is too complex to maintain |

```typescript
// Stub — just return a value
const getUser = vi.fn().mockReturnValue({ id: 1, name: 'Alice' });

// Spy — track calls, real implementation still runs
const spy = vi.spyOn(analytics, 'track');

// Mock — replace entire module
vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

// Fake — real but simplified implementation
const fakeStorage = { data: new Map(), get: (k) => fakeStorage.data.get(k), set: (k,v) => fakeStorage.data.set(k,v) };
```

## Test Naming Conventions

```typescript
// Pattern: "describe [subject], it [behavior under conditions]"

describe('validateEmail', () => {
  it('returns valid:true for correctly formatted email')
  it('returns valid:false for email without @')
  it('returns valid:false for empty string')
});

// Component tests: describe [ComponentName], it [what user sees/can do]
describe('Counter', () => {
  it('shows 0 as initial count')
  it('increments count when + button is clicked')
  it('decrements count when - button is clicked')
});

// E2E: plain English describing the user's goal
test('user can log in with valid credentials')
test('user sees error message when entering wrong password')
test('user is redirected to login when session expires')
```

## AAA Principle at a Glance

```typescript
it('increments count', async () => {
  // ARRANGE — set up the state and render
  render(Counter, { initial: 5 });

  // ACT — perform the action being tested
  await page.getByRole('button', { name: 'Increment' }).click();

  // ASSERT — verify the expected outcome
  await expect.element(page.getByTestId('count')).toHaveText('6');
});
```

## Additional Resources

- **[patterns-reference.md](patterns-reference.md)** — Code examples for every pattern: AAA, Given-When-Then, Builder, Factory, Page Object Model, test.each, custom matchers, test doubles
- **[anti-patterns.md](anti-patterns.md)** — Implementation testing, snapshot abuse, test interdependence, over-mocking, flaky async, testing framework behavior — each with BAD/GOOD code examples

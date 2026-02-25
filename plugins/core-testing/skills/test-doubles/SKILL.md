---
name: core-testing:test-doubles
description: "Mocks, stubs, fakes, spies — when to use each, over-mocking dangers, dependency injection, and test isolation strategies"
user-invocable: false
---

# Test Doubles Quick Reference

## Taxonomy of Test Doubles

A **test double** is any object that stands in for a real dependency during testing. There are distinct types with different purposes:

| Double | What it does | Typical use |
|--------|-------------|-------------|
| **Stub** | Returns canned data, no verification | Provide indirect input to the system under test |
| **Mock** | Verifies that specific calls were made | Assert on interactions and collaboration |
| **Spy** | Records calls for later inspection | Verify interactions without prescribing them upfront |
| **Fake** | Working implementation, simplified | Replace slow/complex dependencies (in-memory DB, local file store) |
| **Dummy** | Passed around but never used | Fill required parameters that are irrelevant to the test |

## When to Use Each

### Stubs — Control Indirect Inputs

Use when you need to control what a dependency returns, but you do not care how it was called.

```
// Stub: always returns a fixed exchange rate
currencyService.getRate("USD", "EUR") -> returns 0.85

// Test: verify that the ORDER uses the rate correctly
order = createOrder(100, "USD", "EUR", currencyService)
assert order.convertedTotal == 85.0
```

### Mocks — Verify Interactions

Use when the **interaction itself** is the important behavior.

```
// Mock: verify that an email was sent with specific content
emailService.expect("send").with(to: "user@example.com", subject: "Welcome")

// Test: registration should trigger welcome email
userService.register("user@example.com")
emailService.verify()  // Fails if send() was not called correctly
```

### Spies — Record for Later Assertion

Use when you want to observe interactions without pre-declaring expectations.

```
// Spy: record all calls
logger = createSpy()

// Test: run the operation
processOrder(order, logger)

// Assert after the fact
assert logger.calls.contains("info", "Order processed: #123")
assert logger.calls.count("error") == 0
```

### Fakes — Functional Substitutes

Use when a real implementation is too slow, complex, or unavailable, but you need realistic behavior.

```
// Fake: in-memory database implementing the same interface
fakeDB = InMemoryDatabase()
fakeDB.insert("users", {id: 1, name: "Alice"})

// Test: uses the same interface as real DB
repo = UserRepository(fakeDB)
user = repo.findById(1)
assert user.name == "Alice"
```

### Dummies — Placeholder Values

Use when a parameter is required but irrelevant to the test.

```
// Dummy: never actually used in this test path
dummyLogger = NullLogger()

// Test: only cares about the calculation, not logging
calculator = Calculator(dummyLogger)
assert calculator.add(2, 3) == 5
```

## The Dangers of Over-Mocking

**Symptoms:**
- Tests break on every refactor even though behavior is unchanged
- Tests pass but production is broken (mocks hide integration bugs)
- Tests are harder to read than the code they test
- Mock setup is 30+ lines for a 3-line assertion

**Root causes:**
- Mocking types you do not own (third-party APIs, language builtins)
- Mocking everything instead of using real collaborators
- Verifying implementation details (call order, exact arguments) rather than outcomes
- Deep mocking chains (mock returns mock returns mock)

**Guideline**: If you mock more than 2-3 dependencies in a single test, the code under test may have too many responsibilities.

## Sociable vs Solitary Unit Tests

| Approach | Description | Trade-off |
|----------|-------------|-----------|
| **Solitary** | Replace all collaborators with test doubles | Fast, isolated, but may miss integration issues |
| **Sociable** | Use real collaborators, only double external boundaries | Slower, but higher confidence in collaboration |

**The pragmatic middle ground**: Use real collaborators within the same module. Double at architectural boundaries (network, file system, database, external APIs).

## Dependency Injection for Testability

**Constructor injection** (preferred):

```
class OrderService:
    constructor(paymentGateway, inventoryService, emailService):
        self.payment = paymentGateway
        self.inventory = inventoryService
        self.email = emailService
```

In production: inject real implementations. In tests: inject stubs/fakes.

**Why injection matters**: Without it, the class creates its own dependencies internally, making them impossible to replace in tests without resorting to monkey-patching or reflection hacks.

## Test Isolation Strategies

1. **Fresh fixtures per test**: Each test creates its own data. No shared mutable state between tests.
2. **Database transactions**: Wrap each test in a transaction and roll back after. Fast, clean.
3. **Containerized services**: Spin up a fresh database/queue per test suite. Slower but realistic.
4. **Deterministic time**: Inject a clock interface. Never call `now()` directly.
5. **Deterministic randomness**: Inject a seeded RNG. Never call `random()` directly.

## Decision Flowchart

```
Is the dependency EXTERNAL (network, DB, file system)?
├── YES → Use a Fake or Stub at the boundary
│         (or a real instance in a container for integration tests)
└── NO → Is it in the SAME module?
    ├── YES → Use the real implementation (sociable test)
    └── NO → Is the interaction the BEHAVIOR you're testing?
        ├── YES → Use a Mock or Spy
        └── NO → Use a Stub to control inputs
```

## Additional Resources

- [doubles-reference.md](doubles-reference.md) — Extended patterns for test double management, mock lifecycle, fake maintenance, contract testing with doubles, and anti-patterns in mock-heavy codebases

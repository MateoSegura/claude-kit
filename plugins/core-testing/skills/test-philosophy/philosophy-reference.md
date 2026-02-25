# Test Philosophy — Extended Reference

Detailed reference material covering test economics, organizational patterns, testing maturity, and common strategic anti-patterns.

## Test Economics

### The Cost of Bugs Over Time

```
Cost to fix
    ^
    |                                          ████ Production
    |                                   ████
    |                            ████
    |                     ████
    |              ████
    |       ████
    |████
    +----------------------------------------------→ Phase
     Design  Code  Unit   Integration  QA  Staging  Production
              Test  Test
```

Bugs found later cost exponentially more to fix. A design error caught in code review costs minutes; the same error found in production costs hours to days plus customer impact.

### Test ROI Framework

For any proposed test, evaluate:

```
ROI = (Bug_Prevention_Value + Refactoring_Safety + Documentation_Value)
      / (Write_Cost + Maintenance_Cost + Execution_Cost)
```

**High ROI tests:**
- Cover code that changes frequently
- Cover code with high bug density history
- Cover code with high business impact
- Are stable despite refactoring (test behavior, not implementation)
- Run fast (seconds, not minutes)

**Low ROI tests:**
- Cover stable code that never changes
- Test trivial logic
- Break on every refactor (tightly coupled to implementation)
- Take minutes to run
- Require complex setup that obscures intent

## The Test Pyramid in Depth

### Unit Tests

**Definition**: Test a single unit of behavior in isolation from external systems.

**Characteristics:**
- Execute in milliseconds
- No network, file system, or database access
- Deterministic — same result every run
- Test one logical concept per test

**What makes a good unit test (F.I.R.S.T.):**
- **Fast**: Milliseconds, not seconds
- **Independent**: No test depends on another test
- **Repeatable**: Same result in any environment
- **Self-validating**: Pass or fail, no manual inspection
- **Timely**: Written close to the code it tests

**Common unit test patterns:**
- Arrange-Act-Assert (AAA)
- Given-When-Then (GWT)
- Setup-Exercise-Verify-Teardown (four-phase test)

```
// Arrange-Act-Assert pattern
test "discount applies to order total":
    // Arrange
    order = Order([Item(50.00), Item(30.00)])
    discount = PercentageDiscount(10)

    // Act
    discountedTotal = discount.apply(order)

    // Assert
    assert discountedTotal == 72.00
```

### Integration Tests

**Definition**: Test the collaboration between components or with external systems.

**What they verify:**
- Database queries return expected results
- HTTP clients handle responses and errors correctly
- Message queues deliver and consume messages
- File I/O reads and writes correctly
- Component wiring is correct

**Boundary integration patterns:**
- **Contract tests**: Verify that provider and consumer agree on API shape
- **Component tests**: Test a service with real dependencies but fake external services
- **Gateway tests**: Test the adapter layer to an external system

```
// Integration test: repository with real database
test "user repository saves and retrieves":
    db = createTestDatabase()
    repo = UserRepository(db)

    repo.save(User(name: "Alice", email: "alice@example.com"))

    found = repo.findByEmail("alice@example.com")
    assert found.name == "Alice"
```

### End-to-End Tests

**Definition**: Test the system as a whole, from the user's perspective.

**When E2E tests are essential:**
- Critical user journeys (signup, checkout, payment)
- Cross-service workflows
- Authentication/authorization flows
- Data flows across system boundaries

**When to avoid E2E tests:**
- Validating business logic (use unit tests)
- Testing error messages (use component tests)
- Covering edge cases (use lower-level tests)

**Making E2E tests reliable:**
- Use deterministic test data (seed the database, do not depend on existing state)
- Wait for conditions, do not use sleep
- Isolate test environments
- Clean up after each test
- Keep the suite small — 10-20 critical paths, not hundreds

## Testing Maturity Model

### Level 1: Ad-Hoc

- Tests exist but are not maintained
- No CI/CD integration
- Manual testing is the primary quality gate
- Test coverage is unknown

### Level 2: Repeatable

- Unit tests for critical paths
- Tests run in CI on every push
- Test failures block merges
- Coverage is measured but not targeted

### Level 3: Defined

- Testing strategy documented (pyramid ratios, what to test)
- Integration tests for external boundaries
- Test data management strategy exists
- Coverage thresholds on new code

### Level 4: Managed

- Mutation testing on critical modules
- Contract tests between services
- Performance/load testing automated
- Test quality is reviewed in code reviews

### Level 5: Optimizing

- Property-based testing for core algorithms
- Chaos engineering in staging/production
- Tests inform architecture decisions
- Continuous improvement of test suite ROI

## Property-Based Testing — Extended

### Choosing Properties

**Invariant properties**: Something that must always be true.

```
// Invariant: a sorted list is always in non-decreasing order
for any list L:
    sorted = sort(L)
    for i in 0..sorted.length-1:
        assert sorted[i] <= sorted[i+1]
```

**Round-trip properties**: encode/decode, serialize/deserialize, write/read.

```
// Round-trip: JSON serialization
for any valid config C:
    assert fromJSON(toJSON(C)) == C
```

**Idempotency properties**: Applying an operation twice yields the same result as once.

```
// Idempotency: normalizing a URL
for any URL u:
    assert normalize(normalize(u)) == normalize(u)
```

**Commutativity properties**: Order does not matter.

```
// Commutativity: merging configs
for any configs A, B:
    assert merge(A, B) == merge(B, A)  // only if your merge is commutative
```

**Oracle properties**: Compare against a known-correct (but slow) implementation.

```
// Oracle: fast sort vs reference sort
for any list L:
    assert quickSort(L) == bubbleSort(L)
```

### Shrinking

When a property-based test finds a failing input, the framework **shrinks** it to the minimal failing case. This is one of the greatest advantages over example-based testing — you get the simplest reproduction case automatically.

```
// Framework finds: [42, -17, 0, 99, -3, 8, 55] fails the property
// After shrinking: [-1, 0] — minimal case that still fails
```

## Testing Anti-Patterns

### Ice Cream Cone (Inverted Pyramid)

```
  ██████████████  Manual tests
   ████████████   E2E tests
    ██████████    Integration
      ██████      Unit
```

Too many slow, expensive tests at the top. Test suite is slow, flaky, and expensive to maintain. Fix: invest in unit and integration tests, remove redundant E2E tests.

### Cupcake Anti-Pattern

Every team/service has its own full E2E suite testing the same user journeys. N services means N redundant E2E suites. Fix: shared E2E suite for critical paths, service-level contract tests.

### Test-After (Wishful Testing)

Write all the code, then write tests to cover it. Tests tend to mirror the implementation rather than specify behavior. Fix: write tests first, or at minimum write tests before the PR review.

### Mock-Heavy Tests

Every dependency is mocked, including value objects and simple collaborators. Tests pass but the real system fails. Fix: mock at boundaries, use real objects for in-process collaborators.

### Flaky Test Tolerance

Flaky tests are retried instead of fixed. Team learns to ignore test failures. Fix: quarantine flaky tests, fix or delete within one sprint.

### Test-Per-Method

One test file per source file, one test per method. Tests are coupled to implementation structure rather than behavior. Fix: organize tests by behavior ("when X happens, Y should result"), not by code structure.

## Organizational Testing Patterns

### Testing Quadrants (Brian Marick)

```
                Business-Facing
                     │
    Functional       │     Exploratory
    Acceptance    Q2 │ Q3  Usability
    Tests            │     Sessions
                     │
  ───────────────────┼───────────────────
                     │
    Unit          Q1 │ Q4  Performance
    Integration      │     Security
    Tests            │     Load Tests
                     │
                Technology-Facing
```

- **Q1** (technology-facing, support programming): Unit + integration tests. Automated. Developer-written.
- **Q2** (business-facing, support programming): Functional acceptance tests. Automated. Team-written.
- **Q3** (business-facing, critique product): Exploratory testing, usability. Manual. QA/UX-driven.
- **Q4** (technology-facing, critique product): Performance, security, load. Automated. Specialist-driven.

### Shift-Left Testing

Move testing earlier in the development cycle:
- Static analysis in the IDE (before code is written)
- Unit tests at code time
- Integration tests at PR time
- Contract tests before deployment
- E2E tests in staging
- Monitoring in production

### Testing in a Microservices Architecture

- **Service-level tests**: Each service owns its test suite (unit + integration)
- **Contract tests**: Consumer and provider agree on API contracts
- **E2E tests**: Minimal — only critical cross-service journeys
- **Synthetic monitoring**: Automated health checks in production
- **Chaos testing**: Verify resilience by injecting failures between services

## The Testing Trophy Model — Extended

Kent C. Dodds' testing trophy emphasizes integration tests for modern web applications:

**Static analysis** (base): TypeScript, ESLint, formatters — catch entire categories of bugs with zero runtime cost.

**Unit tests** (small): Pure functions, utilities, complex logic — fast, focused.

**Integration tests** (largest section): Test realistic user flows through multiple components with minimal mocking — best ROI for most applications.

**E2E tests** (top): Full browser tests for critical paths — expensive, keep minimal.

The trophy model works well for web applications where most bugs live in the integration between components, not in isolated units. It does not replace the pyramid for all contexts — embedded systems, compilers, and data pipelines may still benefit from a bottom-heavy approach.

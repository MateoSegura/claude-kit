---
name: core-testing:tdd-bdd
description: "Red-green-refactor cycle, outside-in vs inside-out TDD, BDD with Given-When-Then, and acceptance test driven development"
user-invocable: false
---

# TDD/BDD Quick Reference

## Test-Driven Development (TDD)

### The Red-Green-Refactor Cycle

```
    ┌──────────┐
    │   RED    │  Write a failing test
    │  (fail)  │  (the simplest test that does not pass)
    └────┬─────┘
         │
    ┌────▼─────┐
    │  GREEN   │  Write the minimum code to pass
    │  (pass)  │  (no more, no less)
    └────┬─────┘
         │
    ┌────▼─────┐
    │ REFACTOR │  Improve the code
    │  (clean) │  (tests must stay green)
    └────┬─────┘
         │
         └──────→ back to RED
```

**Rules of TDD** (Robert C. Martin):
1. Write no production code except to pass a failing test
2. Write only enough of a test to demonstrate a failure
3. Write only enough production code to pass the test

### TDD Micro-Cycle Example

```
// Step 1: RED — write the simplest failing test
test "new cart has zero items":
    cart = ShoppingCart()
    assert cart.itemCount() == 0

// Step 2: GREEN — write the minimum code
class ShoppingCart:
    function itemCount():
        return 0

// Step 3: RED — next failing test
test "adding an item increases count":
    cart = ShoppingCart()
    cart.add(Item("Widget"))
    assert cart.itemCount() == 1

// Step 4: GREEN — make it pass
class ShoppingCart:
    items = []
    function add(item):
        items.append(item)
    function itemCount():
        return items.length

// Step 5: REFACTOR — if needed (not yet)
// Step 6: RED — next test...
```

### Inside-Out vs Outside-In TDD

**Inside-Out (Classic / Chicago School)**:
- Start from domain objects, work outward to boundaries
- Build small, tested units, compose them into larger structures
- Rarely uses mocks — relies on real collaborators
- Natural for domain-heavy code

```
// Build order: Domain -> Service -> Controller
1. Test & build Money value object
2. Test & build Product entity (uses Money)
3. Test & build Cart (uses Product, Money)
4. Test & build CartService (uses Cart)
5. Test & build CartController (uses CartService)
```

**Outside-In (London School / Mockist)**:
- Start from the outermost layer (API, UI), work inward
- Mock inner layers that do not exist yet
- Drives design from user-facing behavior
- Natural for behavior-first design

```
// Build order: Controller -> Service -> Domain
1. Test CartController with mocked CartService
2. Test CartService with mocked Cart repository
3. Test Cart domain logic with real objects
```

**Which to choose:**

| Scenario | Recommended approach |
|----------|---------------------|
| Rich domain logic | Inside-out |
| API/UI-first design | Outside-in |
| Greenfield with unclear domain | Outside-in to discover interfaces |
| Well-understood domain | Inside-out to build solid foundation |
| Team new to TDD | Inside-out (fewer mocks, easier to learn) |

## Behavior-Driven Development (BDD)

### Given-When-Then

BDD structures tests as **specifications of behavior** using natural-language templates:

```
Feature: Shopping cart checkout

  Scenario: Applying a discount code
    Given a cart with items totaling 100.00
    And a valid discount code "SAVE20" for 20% off
    When the customer applies the discount code
    Then the cart total should be 80.00
    And the discount code should be marked as used
```

**Given** — establish the precondition (arrange)
**When** — perform the action (act)
**Then** — verify the outcome (assert)
**And/But** — continue the previous clause

### BDD Anti-Patterns

- **Incidental details**: Including irrelevant setup data ("Given a user named John born on 1990-01-15 at 14:30 UTC...") — include only what matters to the scenario
- **Imperative steps**: "Given I click the login button, then I type my password..." — use declarative steps ("Given I am logged in")
- **Testing implementation**: "Then the database should contain a row..." — test observable behavior ("Then my order appears in order history")
- **Too many scenarios**: 50 scenarios for one feature — extract common patterns, use scenario outlines for data-driven variation

### Scenario Outlines (Data-Driven BDD)

```
Scenario Outline: Shipping cost calculation
    Given an order weighing <weight> kg
    And the destination is <zone>
    When shipping cost is calculated
    Then the cost should be <expected_cost>

    Examples:
    | weight | zone     | expected_cost |
    | 1.0    | domestic | 5.00          |
    | 1.0    | europe   | 12.00         |
    | 5.0    | domestic | 10.00         |
    | 5.0    | europe   | 25.00         |
```

## Acceptance Test Driven Development (ATDD)

**ATDD** extends BDD by making acceptance tests the starting point for feature development:

```
1. Team (dev + QA + product) writes acceptance criteria together
2. Criteria are expressed as executable specifications
3. Development begins — acceptance tests fail (red)
4. Inner TDD loop: unit tests drive implementation
5. When unit tests pass, check if acceptance tests pass
6. Refactor until acceptance + unit tests are green
```

**The double loop**:

```
Outer loop: Acceptance test (RED → ... → GREEN)
  Inner loop: Unit test (red → green → refactor)
  Inner loop: Unit test (red → green → refactor)
  Inner loop: Unit test (red → green → refactor)
Outer loop: Acceptance test GREEN ✓
```

## When TDD Helps vs When It Is Overhead

**TDD shines when**:
- Complex business logic with many edge cases
- Algorithm design — tests clarify expected behavior incrementally
- Collaborative code with many consumers — tests document the contract
- Bug fixes — write a failing test that reproduces the bug, then fix
- Refactoring — existing tests provide a safety net

**TDD is overhead when**:
- Exploratory prototyping — you will throw the code away
- UI layout work — visual testing is more effective
- One-time scripts — faster to verify manually
- Trivial glue code — the test is more complex than the code
- Rapidly changing requirements — tests become maintenance burden before the design stabilizes

**Pragmatic approach**: Use TDD for core logic and skip it for scaffolding. Retrofit tests on stabilized code that started as a prototype.

## Additional Resources

- [tdd-reference.md](tdd-reference.md) — Extended patterns for TDD kata progressions, refactoring under test, test list planning, transformation priority premise, and BDD automation strategies

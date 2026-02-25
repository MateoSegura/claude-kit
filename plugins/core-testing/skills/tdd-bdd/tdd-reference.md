# TDD/BDD — Extended Reference

Detailed reference material covering TDD kata progressions, refactoring under test, test list planning, the transformation priority premise, and BDD automation strategies.

## TDD Kata Progressions

Katas are small exercises for practicing TDD mechanics. Progress from simple to complex:

### Level 1 — Value Transformations

Practice the red-green-refactor cycle on pure functions with no dependencies.

**FizzBuzz Kata:**
```
// Test list:
// 1 → "1"
// 2 → "2"
// 3 → "Fizz"
// 5 → "Buzz"
// 15 → "FizzBuzz"

// RED: first test
test "returns string of number":
    assert fizzbuzz(1) == "1"

// GREEN: simplest implementation
function fizzbuzz(n):
    return toString(n)

// RED: next test
test "returns Fizz for multiples of 3":
    assert fizzbuzz(3) == "Fizz"

// GREEN: add conditional
function fizzbuzz(n):
    if n % 3 == 0: return "Fizz"
    return toString(n)

// Continue: add Buzz, FizzBuzz...
```

### Level 2 — State and Collections

Practice with objects that maintain state.

**Stack Kata:**
```
// Test list:
// new stack is empty
// push one, pop returns it
// push two, pop returns last pushed (LIFO)
// pop empty stack raises error
// peek returns top without removing
```

**String Calculator Kata:**
```
// Test list:
// "" → 0
// "1" → 1
// "1,2" → 3
// "1\n2,3" → 6
// custom delimiter: "//;\n1;2" → 3
// negative numbers throw exception
```

### Level 3 — Collaborators and Design

Practice outside-in TDD with mock objects.

**Banking Kata:**
```
// Test list:
// deposit increases balance
// withdrawal decreases balance
// print statement shows date, amount, balance
// statement is in reverse chronological order

// Outside-in: start with the acceptance test
test "print statement after deposits and withdrawal":
    account = Account()
    account.deposit(1000, date: "2024-01-10")
    account.deposit(2000, date: "2024-01-13")
    account.withdraw(500, date: "2024-01-14")
    statement = account.printStatement()

    assert statement == """
    Date       | Amount | Balance
    2024-01-14 | -500   | 2500
    2024-01-13 | 2000   | 3000
    2024-01-10 | 1000   | 1000
    """
```

## The Test List

Before writing any test, create a **test list** — a plain-text list of behaviors to test. This is your roadmap.

```
// Shopping Cart — Test List
// -------------------------
// [ ] new cart has zero items and zero total
// [ ] adding an item increases count by 1
// [ ] adding an item adds its price to total
// [ ] adding same item twice increases quantity
// [ ] removing an item decreases count
// [ ] removing last instance of item removes it entirely
// [ ] clearing cart resets to zero items
// [ ] 10% discount applies when total exceeds 100
// [ ] discount does not stack with other discounts
// [ ] cannot add item with negative price
// [ ] cannot add item with zero quantity
```

**How to use the test list:**
1. Write the full list before coding
2. Start with the simplest test
3. Cross off tests as you implement them
4. Add new tests as you discover edge cases
5. The list is a living document, not a contract

## Refactoring Under Test

### The Refactoring Cycle

```
1. Tests are GREEN
2. Identify a code smell (duplication, long method, etc.)
3. Apply one small refactoring
4. Run tests — must stay GREEN
5. Repeat from step 2
```

**Critical rule**: Never refactor and change behavior at the same time. Refactoring means changing structure without changing behavior. New behavior requires new tests.

### Common Refactoring Moves (With Safety Net)

**Extract Method:**
```
// Before
function processOrder(order):
    // validate
    if order.items.length == 0: raise EmptyOrderError
    if order.total < 0: raise NegativeTotalError
    // calculate
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * 0.1
    total = subtotal + tax
    // save
    db.save(order, total)

// After (extract validation and calculation)
function processOrder(order):
    validateOrder(order)
    total = calculateTotal(order)
    db.save(order, total)

function validateOrder(order):
    if order.items.length == 0: raise EmptyOrderError
    if order.total < 0: raise NegativeTotalError

function calculateTotal(order):
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * 0.1
    return subtotal + tax
```

Tests remain unchanged — they test the public behavior of `processOrder`, which has not changed.

**Replace Conditional with Polymorphism:**
```
// Before
function calculateShipping(order):
    if order.type == "standard":
        return order.weight * 1.0
    elif order.type == "express":
        return order.weight * 2.5
    elif order.type == "overnight":
        return order.weight * 5.0

// After
interface ShippingStrategy:
    function calculate(order): number

class StandardShipping implements ShippingStrategy:
    function calculate(order): return order.weight * 1.0

class ExpressShipping implements ShippingStrategy:
    function calculate(order): return order.weight * 2.5

class OvernightShipping implements ShippingStrategy:
    function calculate(order): return order.weight * 5.0
```

Existing tests pass because the observable behavior is identical.

### Characterization Tests

When refactoring legacy code without tests:

```
1. Write tests that capture CURRENT behavior (even if buggy)
2. These are "characterization tests" — they characterize what the code does now
3. Refactor with these tests as a safety net
4. After refactoring, decide which behaviors are bugs
5. Write new tests for correct behavior, fix the bugs
```

```
// Characterization test — captures current (possibly wrong) behavior
test "legacy discount calculation":
    // We discovered this returns 9.5 instead of expected 10.0
    // Document the current behavior first
    assert legacyDiscount(100, 0.1) == 9.5  // Rounding bug?

// After refactoring, fix the bug:
test "discount calculation rounds correctly":
    assert discount(100, 0.1) == 10.0
```

## Transformation Priority Premise (Robert C. Martin)

When going from RED to GREEN, apply the **simplest transformation** that makes the test pass. Transformations are ordered from simple to complex:

```
Priority   Transformation            Example
────────   ──────────────            ───────
1          {} → nil                  Return nothing
2          nil → constant            Return a fixed value
3          constant → variable       Return a parameter
4          unconditional → selection Add an if/else
5          value → list              Single value → collection
6          statement → recursion     Loop → recursive call
7          selection → iteration     If → while/for
8          value → mutated value     Transform a value
9          expression → function     Inline → extracted function
```

**Principle**: Prefer higher-priority (simpler) transformations. Lower-priority transformations suggest you may need more intermediate tests.

```
// Example: implementing factorial

// Test 1: factorial(0) == 1
// Transformation: {} → constant (return 1)
function factorial(n): return 1

// Test 2: factorial(1) == 1
// Still passes with constant — no change needed

// Test 3: factorial(2) == 2
// Transformation: constant → variable (return n)
// But wait — factorial(0) would fail.
// Transformation: unconditional → selection
function factorial(n):
    if n == 0: return 1
    return n

// Test 4: factorial(3) == 6
// Transformation: value → mutated value + selection → iteration
function factorial(n):
    if n == 0: return 1
    return n * factorial(n - 1)
```

## BDD Automation Strategies

### Step Definition Organization

```
// Feature file (business language)
Feature: User registration

  Scenario: Successful registration
    Given no user exists with email "new@example.com"
    When I register with email "new@example.com" and password "secure123"
    Then a user account should be created
    And a welcome email should be sent to "new@example.com"

// Step definitions (glue code)
Given "no user exists with email {string}":
    function(email):
        database.deleteUserByEmail(email)

When "I register with email {string} and password {string}":
    function(email, password):
        response = api.post("/register", {email, password})
        context.response = response

Then "a user account should be created":
    function():
        assert context.response.status == 201

Then "a welcome email should be sent to {string}":
    function(email):
        assert emailService.lastSentTo() == email
```

### Keeping Scenarios Declarative

```
// BAD — imperative (UI automation script)
Scenario: Login
    Given I navigate to "/login"
    And I type "user@example.com" into the "email" field
    And I type "password123" into the "password" field
    And I click the "Login" button
    Then I should see the text "Dashboard"

// GOOD — declarative (business intent)
Scenario: Login
    Given a registered user with email "user@example.com"
    When the user logs in with valid credentials
    Then they should see their dashboard
```

**Rule of thumb**: If a non-technical stakeholder cannot understand the scenario, it is too imperative.

### Living Documentation

BDD scenarios serve as executable documentation:

```
1. Scenarios are written in business language
2. They are automated and run in CI
3. If a scenario fails, the documented behavior is broken
4. Scenarios are always up-to-date (because they are tests)
5. New team members read scenarios to understand the system
```

## When TDD Helps — Extended Guide

### TDD for Bug Fixes

```
1. Reproduce the bug manually
2. Write a failing test that demonstrates the bug
3. Verify the test fails for the right reason
4. Fix the code
5. Verify the test passes
6. The test prevents the bug from recurring
```

This is one of the highest-ROI uses of TDD. Every bug fix comes with a regression test.

### TDD for Algorithm Design

TDD excels at incremental algorithm development:

```
// Roman numeral converter — test-driven
test "1 → I":     assert toRoman(1) == "I"
test "2 → II":    assert toRoman(2) == "II"
test "3 → III":   assert toRoman(3) == "III"
test "4 → IV":    assert toRoman(4) == "IV"
test "5 → V":     assert toRoman(5) == "V"
test "9 → IX":    assert toRoman(9) == "IX"
test "10 → X":    assert toRoman(10) == "X"
// Each test drives the next generalization
```

### TDD for API Design

Writing tests first forces you to think about the API from the consumer's perspective:

```
// Before writing the implementation, the test reveals:
// - What the constructor signature should be
// - What methods are needed
// - What the return types are
// - How errors are surfaced

test "rate limiter allows requests within limit":
    limiter = RateLimiter(maxRequests: 5, windowSeconds: 60)
    for i in 1..5:
        assert limiter.allowRequest(clientId: "user1") == true

test "rate limiter rejects requests beyond limit":
    limiter = RateLimiter(maxRequests: 5, windowSeconds: 60)
    for i in 1..5:
        limiter.allowRequest(clientId: "user1")
    assert limiter.allowRequest(clientId: "user1") == false
```

## When TDD Is Overhead — Extended Guide

### Exploratory Spikes

When you do not know what you are building yet:

```
1. Time-box a spike (2-4 hours)
2. Write throwaway code without tests
3. Learn what the solution should look like
4. Throw away the spike
5. Re-implement with TDD, now that you understand the problem
```

**Critical**: Actually throw away the spike. "Temporary" code has a way of becoming permanent.

### UI Layout and Styling

Visual output is better verified by visual tools:
- Screenshot comparison tools
- Storybook / component catalogs
- Manual QA for aesthetics

TDD is valuable for UI **logic** (state management, validation, conditional rendering) but not for visual appearance.

### Rapidly Changing Requirements

If requirements change daily, tests written today are deleted tomorrow. In this phase:
- Focus on integration tests that verify end-to-end flows
- Keep unit test scope narrow (domain logic only)
- Accept that some throwaway code will not have tests
- Add comprehensive tests once requirements stabilize

## Double Loop TDD (ATDD + TDD)

```
OUTER LOOP (acceptance test — minutes to hours)
┌──────────────────────────────────────────────┐
│ Write acceptance test (RED)                   │
│ ┌──────────────────────────────────┐          │
│ │ INNER LOOP (unit test — seconds) │          │
│ │ Write unit test (red)            │          │
│ │ Make it pass (green)             │          │
│ │ Refactor (clean)                 │          │
│ │ Repeat...                        │          │
│ └──────────────────────────────────┘          │
│ Acceptance test passes (GREEN)                │
│ Refactor                                      │
└──────────────────────────────────────────────┘
Next acceptance test...
```

**Outer loop**: Defines WHAT the system should do (business behavior).
**Inner loop**: Defines HOW the system implements it (technical design).

The outer loop keeps you focused on user value. The inner loop keeps your code clean and well-designed.

## Common TDD Mistakes

### Writing Too Big a Test

Jumping from "new cart is empty" to "full checkout with discount, tax, and shipping" skips too many intermediate steps. Each test should require only a small code change.

### Skipping the Refactor Step

Red-green without refactoring accumulates technical debt. The refactor step is where design emerges. Never skip it.

### Testing Private Methods

If you feel the need to test a private method, it is a sign the method should be extracted into its own class with a public interface.

### Gold-Plating the First Test

Do not write the "perfect" test first. Start with the simplest case and let the design emerge through the cycle.

### Ignoring the Test List

Jumping to the interesting test instead of working through the list in order. The simple tests build the foundation for complex ones.

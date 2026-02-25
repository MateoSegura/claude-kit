# Test Doubles — Extended Reference

Detailed reference material covering test double lifecycle, contract testing with doubles, fake maintenance, and anti-patterns in mock-heavy codebases.

## Test Double Lifecycle Management

### Setup and Teardown

Every test double has a lifecycle: create, configure, use, verify (if mock), dispose.

```
test "order service sends confirmation email":
    // CREATE — instantiate the double
    emailService = createMock(EmailService)

    // CONFIGURE — set expectations or return values
    emailService.expect("sendConfirmation")
                .with(orderId: "ORD-123", email: "user@example.com")
                .returns(success)

    // USE — inject into system under test and exercise
    orderService = OrderService(emailService)
    orderService.completeOrder("ORD-123")

    // VERIFY — check expectations were met
    emailService.verifyAllExpectations()

    // DISPOSE — clean up (usually automatic with test framework)
```

### Strict vs Loose Mocks

**Strict mocks** fail on any unexpected call:
```
mock = createStrictMock(PaymentGateway)
mock.expect("charge").with(100.00).returns(success)
mock.refund(50.00)  // FAILS — unexpected call
```

**Loose mocks** ignore unexpected calls:
```
mock = createLooseMock(PaymentGateway)
mock.expect("charge").with(100.00).returns(success)
mock.refund(50.00)  // Ignored — returns default value
```

**Guidance**: Default to loose mocks. Strict mocks create brittle tests that break when innocuous calls are added. Only use strict mocks when verifying that a specific interaction does NOT happen.

### Argument Matchers

Instead of exact values, use matchers for flexibility:

```
// Exact match — brittle
mock.expect("send").with("user@example.com", "Subject", "Body")

// Matcher-based — flexible
mock.expect("send").with(
    anyString(),                    // any email
    containing("Order"),            // subject contains "Order"
    matchingRegex("Total: \\$\\d+") // body matches pattern
)
```

**Use exact matching** for values central to the test's purpose. **Use matchers** for incidental values.

## Fake Maintenance

Fakes are the most powerful but most expensive test doubles. They require ongoing maintenance.

### In-Memory Database Fake

```
class InMemoryUserStore implements UserStore:
    users = {}

    function save(user):
        users[user.id] = copy(user)

    function findById(id):
        if id not in users:
            return null
        return copy(users[id])  // Return copy to prevent aliasing

    function findByEmail(email):
        for user in users.values():
            if user.email == email:
                return copy(user)
        return null

    function delete(id):
        if id not in users:
            raise NotFoundError(id)
        remove users[id]
```

### Fake Fidelity

A fake must behave like the real implementation for the scenarios your tests exercise. Common fidelity gaps:

| Gap | Example | Fix |
|-----|---------|-----|
| Missing error cases | Fake never throws timeout | Add configurable failure injection |
| Different semantics | Fake uses exact match, real uses fuzzy | Match real behavior |
| Missing constraints | Fake allows duplicate keys, real does not | Add constraint checking |
| Concurrency behavior | Fake is not thread-safe, real is | Add synchronization or document limitation |

### Contract Tests for Fakes

Run the same test suite against both the real implementation and the fake to verify they behave identically:

```
// Shared contract test suite
function userStoreContractTests(createStore):
    test "save and retrieve":
        store = createStore()
        store.save(User(id: 1, name: "Alice"))
        assert store.findById(1).name == "Alice"

    test "find returns null for missing":
        store = createStore()
        assert store.findById(999) == null

    test "delete removes user":
        store = createStore()
        store.save(User(id: 1, name: "Alice"))
        store.delete(1)
        assert store.findById(1) == null

// Run against both implementations
userStoreContractTests(() => InMemoryUserStore())
userStoreContractTests(() => PostgresUserStore(testDbConnection))
```

If a contract test passes against the fake but fails against the real implementation (or vice versa), the fake is out of sync.

## Contract Testing Between Services

### Consumer-Driven Contract Testing

The **consumer** defines what it expects from the provider. The provider verifies it can fulfill those expectations.

```
// Consumer side: "I expect GET /users/123 to return {name, email}"
contract "user-service":
    interaction "get user by id":
        request:
            method: GET
            path: /users/123
        response:
            status: 200
            body:
                name: type(string)
                email: type(string)

// Provider side: verify this contract is fulfilled
providerTest "fulfills user-service contract":
    startProvider()
    verifyContract("user-service")  // Replays interactions, checks responses
```

### Provider Contract Testing

The **provider** publishes its contract. Consumers verify they can work with it.

Useful when the provider is a shared platform service with many consumers.

## Dependency Injection Patterns

### Constructor Injection

```
class OrderProcessor:
    constructor(
        paymentGateway: PaymentGateway,
        inventoryService: InventoryService,
        notificationService: NotificationService
    ):
        self.payment = paymentGateway
        self.inventory = inventoryService
        self.notification = notificationService
```

**Advantages**: Dependencies are explicit, visible in the constructor signature. Cannot create an instance without providing all dependencies.

### Factory/Builder for Complex Setup

When a class has many dependencies, use a builder to reduce test boilerplate:

```
class OrderProcessorBuilder:
    payment = defaultStubPaymentGateway()
    inventory = defaultStubInventoryService()
    notification = defaultStubNotificationService()

    function withPayment(pg):
        payment = pg
        return self

    function withInventory(inv):
        inventory = inv
        return self

    function build():
        return OrderProcessor(payment, inventory, notification)

// Test only cares about payment — other dependencies use defaults
test "rejects expired credit card":
    payment = createStub(PaymentGateway)
    payment.when("charge").thenReturn(CardExpiredError)

    processor = OrderProcessorBuilder().withPayment(payment).build()
    result = processor.process(order)
    assert result.status == "payment_failed"
```

### Interface Segregation for Testability

If a class depends on a large interface but uses only one method, define a smaller interface:

```
// BAD: depends on entire UserService (20 methods)
class EmailSender:
    constructor(userService: UserService)
    function sendWelcome(userId):
        user = userService.findById(userId)  // Only method used
        send(user.email, "Welcome!")

// GOOD: depends on minimal interface
interface UserLookup:
    function findById(id): User

class EmailSender:
    constructor(userLookup: UserLookup)
    function sendWelcome(userId):
        user = userLookup.findById(userId)
        send(user.email, "Welcome!")

// Test: only need to stub one method
stub = createStub(UserLookup)
stub.when("findById").with(1).thenReturn(User(email: "a@b.com"))
```

## Anti-Patterns in Mock-Heavy Codebases

### The Mockery Maze

**Symptom**: Mock returns a mock that returns a mock.

```
// BAD: deep mock chain
mockDb.when("getConnection").thenReturn(mockConnection)
mockConnection.when("prepareStatement").thenReturn(mockStatement)
mockStatement.when("executeQuery").thenReturn(mockResultSet)
mockResultSet.when("next").thenReturn(true)
mockResultSet.when("getString").thenReturn("Alice")
```

**Fix**: This code needs a repository abstraction. Test the repository with a real database (integration test), then stub the repository in higher-level tests.

### The Verification Overload

**Symptom**: Test verifies exact call sequence and argument details.

```
// BAD: testing implementation, not behavior
mock.verify("save").calledOnce()
mock.verify("save").calledWith(User(name: "Alice", createdAt: exactly(timestamp)))
mock.verify("save").calledBefore("sendEmail")
mock.verify("sendEmail").calledOnce()
mock.verify("sendEmail").calledWith(subject: "Welcome")
```

**Fix**: Verify the observable outcome, not the internal steps.

```
// GOOD: verify what the user sees
result = service.register("Alice")
assert result.success == true
assert emailInbox.contains(subject: "Welcome")
```

### The Mock That Knows Too Much

**Symptom**: Mock setup replicates the implementation logic.

```
// BAD: mock duplicates the discount calculation
mockPricing.when("calculateDiscount")
    .with(order)
    .thenReturn(order.total * 0.1)  // Duplicates the 10% logic
```

**Fix**: Use a simple stub with a fixed return value. The test should verify what happens with a given discount, not recalculate it.

```
// GOOD: fixed return value
mockPricing.when("calculateDiscount").thenReturn(10.00)
// Test: verify the order applies the 10.00 discount correctly
```

### The Untested Mock

**Symptom**: Mock behavior diverges from real implementation over time. Tests pass, production breaks.

**Fix**: Contract tests (run same assertions against real and fake). Periodically review mock configurations against actual API contracts.

## Test Double Selection Guide

```
What are you trying to do?
│
├── Provide canned data to the SUT?
│   └── STUB
│
├── Verify a specific interaction happened?
│   ├── Need to verify during the test? → MOCK
│   └── Want to inspect after the test? → SPY
│
├── Replace a slow/complex system with a working substitute?
│   └── FAKE
│
├── Fill a required parameter that is irrelevant?
│   └── DUMMY
│
└── Unsure?
    └── Start with a STUB. Upgrade to MOCK only if
        the interaction is the behavior you are testing.
```

## Test Double Maintenance Checklist

- [ ] Each mock/stub is configured with the minimum needed for the test
- [ ] No mock chains deeper than one level
- [ ] Fakes have contract tests verifying parity with real implementations
- [ ] Argument matchers are used for incidental values, exact values for important ones
- [ ] Mock verification focuses on observable behavior, not call sequences
- [ ] Test setup is under 10 lines (use builders for complex scenarios)
- [ ] When a real dependency API changes, corresponding doubles are updated

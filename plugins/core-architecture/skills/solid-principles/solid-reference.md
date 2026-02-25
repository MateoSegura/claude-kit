# SOLID Principles — Detailed Reference

Extended examples, edge cases, and real-world scenarios for each SOLID principle.

---

## Single Responsibility — Deep Dive

### Identifying Violations

**Smell: "And" in the name.** `UserValidatorAndSaver`, `OrderProcessorAndNotifier` — the "and" reveals two responsibilities.

**Smell: Multiple reasons to change.** Ask: "Who would request a change to this class?" If the answer is "the DBA, the UI team, and the security team," the class has at least three responsibilities.

**Smell: Unrelated imports.** A class that imports both `database` and `email` and `pdfGenerator` has too many concerns.

### Practical Example: Report Generation

**Violation:**

```
class ReportGenerator:
    method generate(data):
        // 1. Query database
        rows = db.query("SELECT * FROM sales WHERE ...")

        // 2. Apply business rules
        filtered = rows.filter(r => r.amount > threshold)
        totals = calculateTotals(filtered)

        // 3. Format as HTML
        html = "<html><body><h1>Sales Report</h1>"
        for row in filtered:
            html += "<tr><td>" + row.name + "</td></tr>"
        html += "</body></html>"

        // 4. Send via email
        smtp.send(to: "boss@company.com", body: html)
```

**Fix:**

```
class SalesDataRepository:
    method getSales(criteria): ...

class SalesAnalyzer:
    method analyze(rows):
        filtered = rows.filter(r => r.amount > threshold)
        return { filtered, totals: calculateTotals(filtered) }

class HtmlReportFormatter:
    method format(analysisResult): ...

class ReportDelivery:
    method deliver(report, recipients): ...

class ReportOrchestrator:
    constructor(repository, analyzer, formatter, delivery): ...
    method generateAndSend(criteria, recipients):
        data = this.repository.getSales(criteria)
        analysis = this.analyzer.analyze(data)
        report = this.formatter.format(analysis)
        this.delivery.deliver(report, recipients)
```

Each class has one reason to change. The orchestrator composes them.

### Granularity Judgment

SRP does not mean "one method per class." The right granularity depends on the rate of change:

- If formatting and delivery always change together, they can live in one class.
- If your project has one report type and will never have more, the violation is harmless.
- Split when you feel the pain: merge conflicts, test setup complexity, or shotgun surgery.

---

## Open/Closed — Deep Dive

### Extension Mechanisms

| Mechanism | When to Use | Trade-off |
|-----------|-------------|-----------|
| Strategy pattern | Multiple algorithms for one operation | One interface + N implementations |
| Decorator pattern | Adding behavior around existing operations | Wrapping adds indirection |
| Plugin/registry | Runtime-discovered extensions | Registry lookup overhead |
| Template method | Fixed algorithm with customizable steps | Inheritance coupling |
| Event/hook system | Decoupled extension points | Harder to trace execution flow |

### Practical Example: Payment Processing

**Violation:**

```
class PaymentProcessor:
    method process(payment):
        if payment.method == "credit_card":
            chargeCard(payment)
        else if payment.method == "paypal":
            callPaypalApi(payment)
        else if payment.method == "crypto":
            sendCryptoTransaction(payment)
        // Adding Apple Pay requires editing this class
```

**Fix — Registry Pattern:**

```
class PaymentProcessor:
    constructor():
        this.handlers = {}

    method register(methodName, handler):
        this.handlers[methodName] = handler

    method process(payment):
        handler = this.handlers[payment.method]
        if not handler:
            throw UnknownPaymentMethod(payment.method)
        return handler.process(payment)

// Registration (composition root):
processor = new PaymentProcessor()
processor.register("credit_card", new CreditCardHandler(stripe))
processor.register("paypal", new PaypalHandler(paypalClient))
processor.register("crypto", new CryptoHandler(wallet))
// Adding Apple Pay: processor.register("apple_pay", new ApplePayHandler(...))
```

Core `PaymentProcessor` never changes. New payment methods are added by registration.

---

## Liskov Substitution — Deep Dive

### Contract Rules

A subtype must satisfy:

1. **Preconditions cannot be strengthened.** If the base accepts any positive number, the subtype cannot require only even numbers.
2. **Postconditions cannot be weakened.** If the base guarantees a sorted result, the subtype must also return sorted.
3. **Invariants must be preserved.** If the base guarantees balance >= 0, the subtype cannot allow negative balances.
4. **No new exceptions.** If the base never throws `IOException`, the subtype should not either (unless the base declares it possible).

### Practical Example: Collection Types

**Violation:**

```
class MutableList:
    method add(item): ...
    method remove(item): ...
    method get(index): ...

class ReadOnlyList extends MutableList:
    method add(item): throw "Cannot add to read-only list"
    method remove(item): throw "Cannot remove from read-only list"
    method get(index): ...  // this one works
```

Client code that calls `list.add(item)` breaks if given a `ReadOnlyList`.

**Fix:**

```
interface Readable:
    method get(index)
    method size()

interface Writable extends Readable:
    method add(item)
    method remove(item)

class MutableList implements Writable: ...
class ReadOnlyList implements Readable: ...

// Functions that only read accept Readable
function printAll(list: Readable): ...

// Functions that write accept Writable
function addDefaults(list: Writable): ...
```

### The "Is-A" Test is Insufficient

"A square IS a rectangle" is true in geometry but false in OOP when rectangles have independent width/height setters. Behavioral compatibility matters more than taxonomic relationships.

---

## Interface Segregation — Deep Dive

### Identifying Fat Interfaces

**Smell: Implementations with empty or throwing methods.** If multiple implementors stub out the same methods, the interface is too broad.

**Smell: Clients importing but not using.** If a class depends on `UserService` but only calls `getUser()`, while `UserService` also exposes `deleteUser()`, `resetPassword()`, `exportData()` — the client depends on more than it needs.

### Role-Based Interfaces

Split interfaces by the role the client plays:

```
// Fat interface
interface UserService:
    method getUser(id)
    method createUser(data)
    method deleteUser(id)
    method resetPassword(id)
    method exportUserData(id)
    method getLoginHistory(id)

// Role-based splits
interface UserReader:
    method getUser(id)

interface UserWriter:
    method createUser(data)
    method deleteUser(id)

interface UserAdmin:
    method resetPassword(id)
    method exportUserData(id)
    method getLoginHistory(id)

// Display component only needs UserReader
class UserProfile:
    constructor(reader: UserReader): ...

// Admin panel needs UserAdmin + UserWriter
class AdminDashboard:
    constructor(writer: UserWriter, admin: UserAdmin): ...
```

### Pragmatic Limit

Do not split to one-method interfaces by default. Group methods by client usage patterns. If three methods are always used together, keep them in one interface.

---

## Dependency Inversion — Deep Dive

### The Composition Root

All concrete wiring happens in one place — the composition root (main function, DI container config, module initializer). Business logic never instantiates its own dependencies.

```
// Composition root (application entry point)
function main():
    // Infrastructure
    dbPool = createConnectionPool(config.databaseUrl)
    httpClient = createHttpClient(config.timeout)
    cache = createRedisClient(config.redisUrl)

    // Repositories (low-level, implement abstractions)
    userRepo = new SqlUserRepository(dbPool)
    orderRepo = new SqlOrderRepository(dbPool)

    // Services (high-level, depend on abstractions)
    userService = new UserService(userRepo, cache)
    orderService = new OrderService(orderRepo, userService)
    notificationService = new NotificationService(httpClient)

    // Application (composes services)
    app = new Application(userService, orderService, notificationService)
    app.start()
```

### Constructor Injection vs Service Locator

| Approach | Pros | Cons |
|----------|------|------|
| Constructor injection | Explicit dependencies, compile-time safety, easy to test | Verbose constructors |
| Service locator | Less constructor noise | Hidden dependencies, hard to test, runtime failures |

**Prefer constructor injection.** Service locators hide dependencies and make testing harder.

### When DI Is Overkill

- **Leaf functions**: A utility that formats dates does not need injected dependencies.
- **Value objects**: Immutable data holders have no dependencies to invert.
- **Infrastructure at boundaries**: The composition root itself must use `new` — that is its job.

---

## Applying SOLID Together

The principles reinforce each other:

- **SRP + DIP**: Extracting responsibilities creates small classes. DIP ensures they depend on abstractions.
- **OCP + Strategy**: New behaviors are added via new strategy implementations, not code edits.
- **LSP + ISP**: Narrow interfaces make substitution easier because subtypes have fewer contracts to satisfy.

### Warning Signs That SOLID Is Being Over-Applied

- More interfaces than implementations (1:1 ratio with no variation planned)
- Layers of indirection with no behavioral difference
- Simple operations requiring navigation through 5+ files
- Test setup that is more complex than the code under test

SOLID is a tool for managing complexity. If the complexity of applying SOLID exceeds the complexity it removes, scale back.

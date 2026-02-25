# Design Patterns — Anti-Patterns

Common structural mistakes that hurt maintainability, testability, and extensibility. Each entry shows the problem, why it fails, and the correct approach.

---

## Anti-Pattern 1: God Class

**What happens:** All business logic, data access, validation, and side effects live in a single class.

```
// BAD: UserService does everything — 1000+ lines
class UserService:
    constructor(db, cache, emailClient, paymentClient, auditLog):
        // 5+ dependencies = too many responsibilities
        ...

    method createUser(data):
        // Validates inline
        if not isValidEmail(data.email): throw "Bad email"
        // Queries DB directly
        existing = db.query("SELECT * FROM users WHERE email = ?", [data.email])
        if existing: throw "Email taken"
        // Writes DB directly
        user = db.insert("users", data)
        // Sends email inline
        emailClient.send(data.email, "Welcome!")
        // Updates cache inline
        cache.set("user:" + user.id, user)
        // Logs audit inline
        auditLog.record("user.created", user.id)
        return user
```

**Why it fails:** Impossible to test one concern in isolation. Cannot swap email provider without touching user creation. Merge conflicts when multiple developers work on the same file. Grows unboundedly.

**Fix:** Extract responsibilities into collaborators.

```
// GOOD: Single responsibility per class
class UserService:
    constructor(repository, validator, eventBus):
        ...

    method createUser(data):
        this.validator.validate(data)
        user = this.repository.save(new User(data))
        this.eventBus.publish(new UserCreated(user))
        return user

// Side effects handled by independent event listeners
class WelcomeEmailListener:
    method onUserCreated(event): emailClient.sendWelcome(event.email)

class CacheInvalidationListener:
    method onUserCreated(event): cache.set("user:" + event.userId, event.user)
```

---

## Anti-Pattern 2: Anemic Domain Model

**What happens:** Domain objects are pure data containers with no behavior. All logic lives in service classes.

```
// BAD: Order is just a data bag
class Order:
    id, status, items, total

// Service contains ALL business logic
class OrderService:
    method shipOrder(order):
        if order.status != "confirmed":
            throw "Cannot ship"
        if order.total <= 0:
            throw "Invalid total"
        order.status = "shipped"
        order.shippedAt = now()
```

**Why it fails:** Business rules are scattered across multiple services. Domain objects cannot enforce their own invariants. Adding a new rule requires finding all services that touch `order.status`.

**Fix:** Put behavior in the domain object.

```
// GOOD: Rich domain model
class Order:
    id, status, items, total, events

    method ship():
        if this.status != "confirmed":
            throw InvalidStateError("Cannot ship order in " + this.status)
        this.status = "shipped"
        this.shippedAt = now()
        this.events.add(new OrderShipped(this.id))

    method cancel():
        if this.status in ["shipped", "delivered"]:
            throw InvalidStateError("Cannot cancel " + this.status + " order")
        this.status = "cancelled"

// Service delegates to domain
class OrderService:
    method shipOrder(orderId):
        order = repository.findById(orderId)
        order.ship()  // domain enforces rules
        repository.save(order)
        eventBus.publishAll(order.events)
```

---

## Anti-Pattern 3: Circular Dependencies

**What happens:** Module A depends on Module B, and Module B depends on Module A.

```
// BAD: Mutual dependency
class OrderService:
    constructor(userService): ...
    method placeOrder(userId, items):
        user = this.userService.getUser(userId)
        ...
        this.userService.updateOrderCount(userId)

class UserService:
    constructor(orderService): ...
    method getRecentOrders(userId):
        return this.orderService.getOrdersForUser(userId)
```

**Why it fails:** Cannot construct either without the other (chicken-and-egg). Changes cascade in both directions. Cannot test either in isolation.

**Fix:** Break the cycle with events or extract a shared interface.

```
// GOOD: Event-based decoupling
class OrderService:
    constructor(userRepository, eventBus): ...
    method placeOrder(userId, items):
        user = this.userRepository.findById(userId)
        order = Order.create(user, items)
        this.eventBus.publish(new OrderPlaced(order))
        return order

class UserService:
    constructor(userRepository, orderRepository): ...
    method getRecentOrders(userId):
        return this.orderRepository.findByUserId(userId)

// OrderPlaced event updates user stats — no circular dependency
class OrderStatsListener:
    method onOrderPlaced(event):
        userRepository.incrementOrderCount(event.userId)
```

---

## Anti-Pattern 4: Service Locator

**What happens:** Instead of injecting dependencies through constructors, code pulls them from a global registry at runtime.

```
// BAD: Service locator hides dependencies
class OrderService:
    method placeOrder(data):
        userRepo = ServiceLocator.get("UserRepository")
        orderRepo = ServiceLocator.get("OrderRepository")
        mailer = ServiceLocator.get("Mailer")
        // Dependencies are hidden — cannot tell from constructor what this class needs
```

**Why it fails:** Dependencies are invisible from the outside. Tests must configure the global locator. Runtime failures if a service is not registered. Harder to reason about what a class needs.

**Fix:** Constructor injection.

```
// GOOD: Explicit constructor injection
class OrderService:
    constructor(userRepo: UserRepository, orderRepo: OrderRepository, mailer: Mailer):
        this.userRepo = userRepo
        this.orderRepo = orderRepo
        this.mailer = mailer
    // Dependencies are visible, mockable, and compile-time checked
```

---

## Anti-Pattern 5: Premature Abstraction

**What happens:** Developer creates interfaces, factories, and strategy patterns for code that has only one implementation and no planned variation.

```
// BAD: One implementation, no variation
interface IUserRepository: ...
interface IUserRepositoryFactory: ...
interface IUserService: ...
interface IUserServiceFactory: ...
interface IUserValidator: ...
interface IUserValidatorFactory: ...

class UserRepository implements IUserRepository: ...
class UserRepositoryFactory implements IUserRepositoryFactory: ...
class UserService implements IUserService: ...
class UserServiceFactory implements IUserServiceFactory: ...
// 12 files for a CRUD that could be 1 class
```

**Why it fails:** Adds complexity without benefit. More files to navigate, more indirection to trace, more code to maintain. The abstraction may not even match future needs.

**Fix:** Start concrete. Extract an interface when a second implementation appears.

```
// GOOD: Start concrete
class UserService:
    constructor(db): ...
    method createUser(data):
        // Direct implementation — simple and clear
        validate(data)
        return this.db.insert("users", data)

// Extract interface LATER when a second implementation is needed:
// - InMemoryUserService for testing
// - CachedUserService for performance
```

**Rule of thumb:** Three similar instances justify an abstraction. One does not.

---

## Anti-Pattern 6: Leaky Abstraction Abuse

**What happens:** An abstraction layer claims to hide implementation details but forces callers to understand the underlying system.

```
// BAD: Repository exposes SQL concepts
interface UserRepository:
    method findByQuery(sqlWhere: string, params: list): list<User>
    method executeRaw(sql: string): any
    method getConnection(): DatabaseConnection
```

**Why it fails:** Callers must write SQL, defeating the purpose of the abstraction. Changing from SQL to NoSQL requires rewriting all callers. The repository is a thin wrapper adding no value.

**Fix:** Express operations in domain terms.

```
// GOOD: Domain-level operations
interface UserRepository:
    method findById(id): User
    method findByEmail(email): User
    method findActive(): list<User>
    method save(user): User
    method delete(id): boolean
```

---

## Anti-Pattern 7: Temporal Coupling

**What happens:** Methods must be called in a specific order, but nothing enforces it.

```
// BAD: Must call init() before process(), close() after process()
service = new DataProcessor()
service.init()        // forgot this? Runtime crash
service.configure(opts)
service.process(data)
service.close()       // forgot this? Resource leak
```

**Why it fails:** Callers must remember the correct sequence. Forgetting a step causes silent bugs or resource leaks.

**Fix:** Enforce the sequence through the API.

```
// GOOD: Builder/fluent API enforces order
result = DataProcessor.create(opts)
    .process(data)
    // .close() called automatically via resource management

// Or use lifecycle management
function withProcessor(opts, callback):
    processor = new DataProcessor(opts)  // init in constructor
    try:
        return callback(processor)
    finally:
        processor.close()

withProcessor(opts, proc => proc.process(data))
```

---

## Anti-Pattern 8: Feature Envy

**What happens:** A method in one class uses more data and methods from another class than from its own.

```
// BAD: OrderPrinter reaches into Order's internals
class OrderPrinter:
    method printReceipt(order):
        subtotal = 0
        for item in order.items:
            lineTotal = item.price * item.quantity
            subtotal += lineTotal
            print(item.name + ": " + lineTotal)
        tax = subtotal * order.taxRate
        shipping = order.weight * order.shippingRatePerKg
        total = subtotal + tax + shipping
        print("Total: " + total)
```

**Why it fails:** `OrderPrinter` knows too much about `Order`'s internal structure. If `Order` changes (different tax calculation, bundled shipping), `OrderPrinter` breaks.

**Fix:** Ask the object that owns the data to do the calculation.

```
// GOOD: Order provides calculated values
class Order:
    method subtotal(): return sum(item.lineTotal() for item in this.items)
    method tax(): return this.subtotal() * this.taxRate
    method shipping(): return this.weight * this.shippingRatePerKg
    method total(): return this.subtotal() + this.tax() + this.shipping()

class OrderPrinter:
    method printReceipt(order):
        for item in order.items:
            print(item.name + ": " + item.lineTotal())
        print("Total: " + order.total())
```

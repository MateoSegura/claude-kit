# Design Patterns — Complete Reference

Full implementations in pseudocode. Each pattern includes problem statement, solution, complete example, and trade-off analysis.

---

## Repository Pattern — Full Implementation

**Problem:** Business logic is tightly coupled to data access technology. Changing databases, ORMs, or query strategies requires editing business logic.

**Solution:** Define a collection-like interface for data access. Business logic calls `repository.findById()`, not `db.query("SELECT ...")`.

```
// Abstract repository interface
interface Repository<T>:
    method findById(id): T or null
    method findAll(criteria: Criteria): list<T>
    method save(entity: T): T
    method delete(id): boolean

// Concrete implementation for SQL
class SqlUserRepository implements Repository<User>:
    constructor(connection):
        this.connection = connection

    method findById(id):
        row = this.connection.query(
            "SELECT * FROM users WHERE id = ?", [id]
        )
        return row ? User.fromRow(row) : null

    method findAll(criteria):
        query = this.buildQuery(criteria)
        rows = this.connection.query(query.sql, query.params)
        return rows.map(row => User.fromRow(row))

    method save(user):
        if user.id:
            this.connection.execute(
                "UPDATE users SET name=?, email=? WHERE id=?",
                [user.name, user.email, user.id]
            )
        else:
            user.id = this.connection.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                [user.name, user.email]
            )
        return user

    method delete(id):
        affected = this.connection.execute(
            "DELETE FROM users WHERE id = ?", [id]
        )
        return affected > 0

// In-memory implementation for testing
class InMemoryUserRepository implements Repository<User>:
    store = {}

    method findById(id):
        return this.store.get(id)

    method save(user):
        if not user.id:
            user.id = generateId()
        this.store[user.id] = user
        return user

    method delete(id):
        return this.store.remove(id) != null
```

**When to use:** Any service layer that interacts with persistence. Essential when you want testable business logic or might swap storage backends.

**Trade-off:** Extra abstraction layer. Skip it for simple CRUD with no business logic.

---

## Unit of Work — Full Implementation

**Problem:** A business operation touches multiple repositories. Each needs to share one transaction, committing or rolling back atomically.

**Solution:** Unit of Work wraps a transaction and exposes repositories. All repos share the same connection/session.

```
class UnitOfWork:
    constructor(transactionManager):
        this.manager = transactionManager
        this.transaction = null

    method begin():
        this.transaction = this.manager.beginTransaction()
        // Expose repositories sharing this transaction
        this.users = new SqlUserRepository(this.transaction)
        this.orders = new SqlOrderRepository(this.transaction)
        this.inventory = new SqlInventoryRepository(this.transaction)

    method commit():
        this.transaction.commit()

    method rollback():
        this.transaction.rollback()

    method close():
        this.transaction.close()

// Usage with try/finally for safety
function transferFunds(fromId, toId, amount):
    uow = new UnitOfWork(transactionManager)
    uow.begin()
    try:
        fromAccount = uow.accounts.findById(fromId)
        toAccount = uow.accounts.findById(toId)

        if fromAccount.balance < amount:
            throw InsufficientFundsError()

        fromAccount.withdraw(amount)
        toAccount.deposit(amount)

        uow.accounts.save(fromAccount)
        uow.accounts.save(toAccount)
        uow.commit()
    catch error:
        uow.rollback()
        throw error
    finally:
        uow.close()
```

---

## Factory Pattern — Full Implementation

**Problem:** Object creation varies by type, configuration, or runtime conditions. Direct instantiation spreads creation logic across the codebase.

**Solution:** Centralize creation logic in a factory.

```
// Interface
interface NotificationSender:
    method send(recipient, message): boolean

// Implementations
class EmailSender implements NotificationSender:
    constructor(smtpConfig): ...
    method send(recipient, message):
        smtp.send(to: recipient.email, body: message)
        return true

class SmsSender implements NotificationSender:
    constructor(twilioConfig): ...
    method send(recipient, message):
        twilio.send(to: recipient.phone, body: message)
        return true

class PushSender implements NotificationSender:
    constructor(firebaseConfig): ...
    method send(recipient, message):
        firebase.push(to: recipient.deviceToken, body: message)
        return true

// Factory
class NotificationFactory:
    constructor(config):
        this.senders = {
            "email": new EmailSender(config.smtp),
            "sms":   new SmsSender(config.twilio),
            "push":  new PushSender(config.firebase),
        }

    method create(channel): NotificationSender:
        sender = this.senders[channel]
        if not sender:
            throw UnknownChannelError(channel)
        return sender

// Usage
factory = new NotificationFactory(appConfig)
sender = factory.create(user.preferredChannel)
sender.send(user, "Your order shipped")
```

---

## Strategy Pattern — Full Implementation

**Problem:** Multiple algorithms for the same operation, with if/else chains selecting between them.

**Solution:** Define a strategy interface. Swap implementations at runtime.

```
// Strategy interface
interface CompressionStrategy:
    method compress(data: bytes): bytes
    method decompress(data: bytes): bytes
    method name(): string

// Implementations
class GzipCompression implements CompressionStrategy:
    method compress(data): return gzip.compress(data)
    method decompress(data): return gzip.decompress(data)
    method name(): return "gzip"

class LZ4Compression implements CompressionStrategy:
    method compress(data): return lz4.compress(data)
    method decompress(data): return lz4.decompress(data)
    method name(): return "lz4"

class NoCompression implements CompressionStrategy:
    method compress(data): return data
    method decompress(data): return data
    method name(): return "none"

// Context that uses a strategy
class FileArchiver:
    constructor(strategy: CompressionStrategy):
        this.strategy = strategy

    method archive(files):
        for file in files:
            data = readFile(file)
            compressed = this.strategy.compress(data)
            writeFile(file + "." + this.strategy.name(), compressed)

// Select strategy based on configuration
strategies = {
    "gzip": new GzipCompression(),
    "lz4":  new LZ4Compression(),
    "none": new NoCompression(),
}
archiver = new FileArchiver(strategies[config.compression])
```

---

## Observer / Event Bus — Full Implementation

**Problem:** When an entity changes state, multiple subsystems need to react (send emails, update caches, log audits). Direct calls create tight coupling.

**Solution:** Publish events. Subscribers react independently.

```
// Event types
class UserCreated:
    userId, email, name

class OrderPlaced:
    orderId, userId, total

// Event bus
class EventBus:
    handlers = {}  // eventType -> list of handler functions

    method subscribe(eventType, handler):
        if eventType not in this.handlers:
            this.handlers[eventType] = []
        this.handlers[eventType].add(handler)

    method publish(event):
        eventType = type(event)
        for handler in this.handlers.get(eventType, []):
            try:
                handler(event)
            catch error:
                log.error("Handler failed", handler: handler.name, error: error)

// Subscribers — each is independent
class WelcomeEmailHandler:
    method handle(event: UserCreated):
        emailService.sendWelcome(event.email, event.name)

class AuditLogHandler:
    method handle(event: UserCreated):
        auditLog.record("user.created", event.userId)

class AnalyticsHandler:
    method handle(event: UserCreated):
        analytics.track("signup", {userId: event.userId})

// Wiring
bus = new EventBus()
bus.subscribe(UserCreated, welcomeEmailHandler.handle)
bus.subscribe(UserCreated, auditLogHandler.handle)
bus.subscribe(UserCreated, analyticsHandler.handle)

// Publishing
function createUser(data):
    user = userRepository.save(new User(data))
    bus.publish(new UserCreated(user.id, user.email, user.name))
    return user
```

**Trade-off:** Decoupled but harder to trace execution flow. Use structured logging with correlation IDs to maintain observability.

---

## Decorator Pattern — Full Implementation

**Problem:** Adding cross-cutting behavior (logging, caching, retry, metrics) to multiple services without modifying their code.

```
interface HttpClient:
    method request(method, url, body): Response

class BaseHttpClient implements HttpClient:
    method request(method, url, body):
        return http.send(method, url, body)

class LoggingHttpClient implements HttpClient:
    constructor(wrapped: HttpClient): ...
    method request(method, url, body):
        log.info("HTTP request", method: method, url: url)
        response = this.wrapped.request(method, url, body)
        log.info("HTTP response", status: response.status, duration: elapsed)
        return response

class RetryHttpClient implements HttpClient:
    constructor(wrapped: HttpClient, maxRetries: 3): ...
    method request(method, url, body):
        for attempt in 1..this.maxRetries:
            try:
                return this.wrapped.request(method, url, body)
            catch error:
                if attempt == this.maxRetries: throw error
                sleep(exponentialBackoff(attempt))

class CachingHttpClient implements HttpClient:
    constructor(wrapped: HttpClient, cache, ttl): ...
    method request(method, url, body):
        if method == "GET":
            cached = this.cache.get(url)
            if cached: return cached
        response = this.wrapped.request(method, url, body)
        if method == "GET" and response.status == 200:
            this.cache.set(url, response, this.ttl)
        return response

// Compose: base -> retry -> cache -> logging
client = new LoggingHttpClient(
    new CachingHttpClient(
        new RetryHttpClient(
            new BaseHttpClient()
        , 3)
    , cache, 300)
)
```

---

## Mediator Pattern — Full Implementation

**Problem:** Multiple objects need to communicate, but direct references create a web of dependencies.

**Solution:** All communication goes through a central mediator.

```
interface Mediator:
    method send(request): response

class RequestMediator implements Mediator:
    handlers = {}  // requestType -> handler

    method register(requestType, handler):
        this.handlers[requestType] = handler

    method send(request):
        handler = this.handlers[type(request)]
        if not handler:
            throw NoHandlerError(type(request))
        return handler.handle(request)

// Request/response types
class GetUserRequest:
    userId

class CreateOrderRequest:
    userId, items

// Handlers
class GetUserHandler:
    constructor(userRepository): ...
    method handle(request: GetUserRequest):
        return this.userRepository.findById(request.userId)

class CreateOrderHandler:
    constructor(orderRepository, inventoryService): ...
    method handle(request: CreateOrderRequest):
        order = Order.create(request.userId, request.items)
        this.inventoryService.reserve(request.items)
        return this.orderRepository.save(order)

// Wiring
mediator = new RequestMediator()
mediator.register(GetUserRequest, getUserHandler)
mediator.register(CreateOrderRequest, createOrderHandler)

// Usage — caller does not know which handler processes the request
user = mediator.send(new GetUserRequest(userId: "123"))
order = mediator.send(new CreateOrderRequest(userId: "123", items: cart))
```

---

## CQRS — Command Query Responsibility Segregation

**Problem:** A single model optimized for writes (normalized, consistent) performs poorly for reads (denormalized, fast). Complex queries require joins across many tables.

**Solution:** Separate the write model (commands) from the read model (queries).

```
// Command side — rich domain model
class PlaceOrderCommand:
    userId, items, shippingAddress

class PlaceOrderHandler:
    constructor(orderRepository, eventBus): ...
    method handle(command):
        order = Order.create(command.userId, command.items, command.shippingAddress)
        order.validate()
        this.orderRepository.save(order)
        this.eventBus.publish(new OrderPlaced(order))

// Query side — flat, denormalized read model
class OrderSummaryQuery:
    userId, status, page, pageSize

class OrderSummaryQueryHandler:
    constructor(readDb): ...
    method handle(query):
        // Query against denormalized view — no joins, fast
        return this.readDb.query(
            "SELECT * FROM order_summaries WHERE user_id = ? AND status = ? LIMIT ? OFFSET ?",
            [query.userId, query.status, query.pageSize, query.page * query.pageSize]
        )

// Sync read model from write events
class OrderProjection:
    constructor(readDb): ...
    method onOrderPlaced(event):
        this.readDb.insert("order_summaries", {
            orderId: event.orderId,
            userId: event.userId,
            total: event.total,
            status: "placed",
            itemCount: event.items.length,
            createdAt: now()
        })
```

**When to use:** Systems with high read/write asymmetry (many more reads than writes), complex reporting, or event-sourced systems.

**When to skip:** Simple CRUD applications. The infrastructure overhead of maintaining two models is not justified if reads and writes are roughly balanced and queries are simple.

---

## Specification Pattern

**Problem:** Complex query conditions are scattered across repository methods (`findActiveUsers`, `findPremiumUsersCreatedAfter`, etc.), leading to method explosion.

**Solution:** Encapsulate query criteria as composable objects.

```
interface Specification<T>:
    method isSatisfiedBy(entity: T): boolean
    method toQuery(): QueryFragment

class ActiveUserSpec implements Specification<User>:
    method isSatisfiedBy(user): return user.isActive
    method toQuery(): return QueryFragment("active = true")

class PremiumUserSpec implements Specification<User>:
    method isSatisfiedBy(user): return user.tier == "premium"
    method toQuery(): return QueryFragment("tier = 'premium'")

class CreatedAfterSpec implements Specification<User>:
    constructor(date): ...
    method isSatisfiedBy(user): return user.createdAt > this.date
    method toQuery(): return QueryFragment("created_at > ?", [this.date])

// Composition
class AndSpec implements Specification<T>:
    constructor(left, right): ...
    method isSatisfiedBy(entity): return this.left.isSatisfiedBy(entity) and this.right.isSatisfiedBy(entity)
    method toQuery(): return this.left.toQuery().and(this.right.toQuery())

// Usage — compose conditions without new repository methods
spec = new AndSpec(
    new ActiveUserSpec(),
    new AndSpec(
        new PremiumUserSpec(),
        new CreatedAfterSpec("2025-01-01")
    )
)
users = userRepository.findAll(spec)
```

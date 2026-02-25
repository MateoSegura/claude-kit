---
name: core-architecture:design-patterns
description: "Language-agnostic design patterns — GoF creational, structural, and behavioral patterns plus modern patterns (repository, unit of work, specification, CQRS, mediator). Pseudocode examples and decision guidance."
user-invocable: false
---

# Design Patterns

Quick reference for selecting and applying design patterns. All examples use pseudocode. See companion files for full implementations and anti-patterns.

## Additional resources

- [patterns-reference.md](patterns-reference.md) — Full implementations: repository, unit of work, factory, strategy, observer, decorator, mediator, CQRS
- [anti-patterns.md](anti-patterns.md) — Common structural mistakes: god class, anemic domain, circular dependencies, service locator abuse

---

## Pattern Categories

| Category | Patterns | When to Reach For Them |
|----------|----------|------------------------|
| Creational | Factory, Abstract Factory, Builder, Singleton, Prototype | Object creation is complex or must vary at runtime |
| Structural | Adapter, Decorator, Facade, Proxy, Composite | Composing objects or adapting interfaces |
| Behavioral | Strategy, Observer, Command, State, Chain of Responsibility, Mediator | Varying behavior, decoupled communication, state transitions |
| Modern | Repository, Unit of Work, Specification, CQRS, Event Sourcing | Data access abstraction, complex queries, audit trails |

---

## Decision Matrix

| Need | Pattern | Trade-off |
|------|---------|-----------|
| Abstract data access from business logic | Repository | Extra layer; worth it for testability |
| Atomic multi-entity operations | Unit of Work | Shared transaction scope |
| Create objects by type at runtime | Factory | Indirection; good for plugins |
| Build objects with many optional parameters | Builder | More code; clearer than telescoping constructors |
| Swap algorithms at runtime | Strategy | More types; eliminates if/else chains |
| React to state changes without coupling | Observer | Decoupled but harder to trace |
| Undo/redo, queued operations | Command | Enables replay and logging |
| Complex conditional object behavior | State | State classes replace switch statements |
| Wrap behavior around existing objects | Decorator | Composable; can nest deeply |
| Simplify a complex subsystem | Facade | Hides complexity |
| Separate read and write models | CQRS | Justified for high-read/write asymmetry |
| Chain handlers for a request | Chain of Responsibility | Flexible pipeline |

---

## Creational Patterns

**Factory:** Create objects without specifying the concrete class.

```
function createLogger(config):
    match config.target:
        "console" -> return new ConsoleLogger()
        "file"    -> return new FileLogger(config.path)
        "remote"  -> return new RemoteLogger(config.endpoint)
```

**Builder:** Construct complex objects step by step.

```
query = new QueryBuilder()
    .select("name", "email").from("users")
    .where("active", true).orderBy("created_at", "desc")
    .limit(20).build()
```

**Singleton:** Ensure one instance. Prefer creating it once in the composition root and injecting it rather than using a true singleton.

---

## Structural Patterns

**Adapter:** Bridge incompatible interfaces.

```
class LegacyPaymentAdapter implements PaymentProvider:
    constructor(gateway: LegacyPaymentGateway): ...
    method charge(amount, card):
        result = this.gateway.makePayment(amount.toCents(), card.tokenize())
        return Receipt.fromLegacy(result)
```

**Decorator:** Add behavior dynamically without changing the interface.

```
// Compose: file -> compress -> encrypt
source = new EncryptionDecorator(
    new CompressionDecorator(new FileDataSource("data.bin")), key)
```

**Facade:** Simplify a complex subsystem behind one method.

```
class VideoConverter:
    method convert(filename, format):
        // Orchestrates VideoFile, CodecFactory, BitrateReader internally
        return new File(result)
```

---

## Behavioral Patterns

**Strategy:** Encapsulate interchangeable algorithms.

```
class Sorter:
    constructor(strategy: SortStrategy): ...
    method sort(data): return this.strategy.sort(data)

sorter = new Sorter(new QuickSort())   // swap algorithm at runtime
```

**Observer:** Notify multiple objects about state changes.

```
bus.subscribe(OrderPlaced, emailService)
bus.subscribe(OrderPlaced, inventoryService)
// Both react independently when OrderPlaced is published
```

**Command:** Encapsulate requests as objects. Enables queuing and undo.

```
class MoveCommand implements Command:
    method execute(): this.editor.move(this.dx, this.dy)
    method undo():    this.editor.move(-this.dx, -this.dy)
```

**State:** Replace conditionals with state objects.

```
class PendingState implements OrderState:
    method next(order): order.setState(new ConfirmedState())
    method cancel(order): order.setState(new CancelledState())
// Order delegates to current state: order.next() / order.cancel()
```

---

## Modern Patterns

**Repository:** Abstract data access behind a collection-like interface.

```
interface UserRepository:
    method findById(id): User
    method findByEmail(email): User
    method save(user): void
    method delete(id): void
```

**Unit of Work:** Coordinate multiple repos in a single transaction.

```
uow.begin()
    userRepo.save(newUser)
    orderRepo.save(newOrder)
uow.commit()  // all or nothing
```

**CQRS:** Separate read and write models.

| Aspect | Command Side | Query Side |
|--------|-------------|------------|
| Model | Rich domain objects | Flat DTOs / projections |
| Store | Normalized relational | Denormalized views |
| Optimization | Write consistency | Read performance |

See [patterns-reference.md](patterns-reference.md) for full implementations of all patterns.

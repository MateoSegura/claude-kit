# Clean Architecture — Detailed Reference

Full layer breakdowns, project structure examples, and migration strategies.

---

## Project Structure — Hexagonal Layout

A typical project organized by hexagonal architecture:

```
src/
├── domain/                    # Inner core — no external dependencies
│   ├── entities/
│   │   ├── Order
│   │   ├── Customer
│   │   └── Product
│   ├── value-objects/
│   │   ├── Money
│   │   ├── Email
│   │   └── Address
│   ├── events/
│   │   ├── OrderPlaced
│   │   └── OrderCancelled
│   ├── services/
│   │   └── PricingService      # Domain service (stateless business rules)
│   └── errors/
│       ├── ValidationError
│       └── InvalidStateError
│
├── application/               # Use cases — depends on domain only
│   ├── ports/                 # Interfaces for infrastructure
│   │   ├── OrderRepository     # Driven port
│   │   ├── PaymentGateway      # Driven port
│   │   └── NotificationService # Driven port
│   ├── use-cases/
│   │   ├── PlaceOrder
│   │   ├── CancelOrder
│   │   └── GetOrderDetails
│   └── dto/
│       ├── PlaceOrderCommand
│       ├── OrderSummaryResult
│       └── CancelOrderCommand
│
├── adapters/                  # Outer layer — implements ports
│   ├── driving/               # Primary adapters (entry points)
│   │   ├── rest/
│   │   │   ├── OrderController
│   │   │   └── CustomerController
│   │   ├── cli/
│   │   │   └── OrderCli
│   │   └── messaging/
│   │       └── OrderEventConsumer
│   └── driven/                # Secondary adapters (infrastructure)
│       ├── persistence/
│       │   ├── SqlOrderRepository
│       │   └── SqlCustomerRepository
│       ├── payment/
│       │   ├── StripePaymentAdapter
│       │   └── PaypalPaymentAdapter
│       └── notification/
│           ├── EmailNotificationAdapter
│           └── SlackNotificationAdapter
│
└── config/                    # Composition root — wires everything
    ├── DependencyContainer
    └── AppBootstrap
```

### Key Observations

- `domain/` has zero imports from `application/`, `adapters/`, or `config/`.
- `application/ports/` defines interfaces. `adapters/driven/` implements them.
- `config/` is the only place that knows about all concrete classes.
- Adding a new entry point (GraphQL, gRPC) means adding a new driving adapter — no changes to domain or use cases.

---

## Project Structure — Layered (Simpler Alternative)

For smaller projects where hexagonal is overkill:

```
src/
├── models/          # Domain entities and value objects
├── services/        # Business logic (use cases)
├── repositories/    # Data access (abstractions + implementations)
├── controllers/     # HTTP/CLI handlers
└── config/          # Wiring and configuration
```

This still respects the dependency rule (controllers -> services -> repositories -> models) without the full hexagonal ceremony.

---

## Entities vs Value Objects

| Aspect | Entity | Value Object |
|--------|--------|-------------|
| Identity | Has a unique ID | Defined by its attributes |
| Equality | Compared by ID | Compared by value |
| Mutability | Mutable (state changes over time) | Immutable |
| Lifecycle | Created, modified, persisted | Created, used, discarded |
| Example | `Order`, `User`, `Product` | `Money`, `Email`, `Address`, `DateRange` |

```
// Entity: identity matters
order1 = new Order(id: "abc")
order2 = new Order(id: "abc")
order1 == order2  // true (same ID)

// Value object: attributes matter
money1 = new Money(100, "USD")
money2 = new Money(100, "USD")
money1 == money2  // true (same value)

money3 = money1.add(new Money(50, "USD"))
// money1 is unchanged (immutable), money3 is new Money(150, "USD")
```

### Value Object Benefits

- Immutability prevents accidental mutation bugs
- Self-validating (reject invalid states in constructor)
- Encapsulate behavior related to the value

```
class Email:
    constructor(address):
        if not isValidFormat(address):
            throw ValidationError("Invalid email: " + address)
        this.address = address.toLowerCase()

    method domain():
        return this.address.split("@")[1]

    method equals(other):
        return this.address == other.address
```

---

## Domain Events

Domain events capture something meaningful that happened in the domain. They are published by entities and consumed by application services or event handlers.

```
// Domain event — immutable record of what happened
class OrderSubmitted:
    orderId, customerId, total, submittedAt

// Entity publishes events
class Order:
    events = []

    method submit():
        // Business rule enforcement
        if this.items.isEmpty():
            throw ValidationError("Cannot submit empty order")
        this.status = "submitted"
        this.events.add(new OrderSubmitted(
            orderId: this.id,
            customerId: this.customerId,
            total: this.total,
            submittedAt: now()
        ))

// Use case collects and dispatches events
class SubmitOrderUseCase:
    method execute(command):
        order = this.orderRepo.findById(command.orderId)
        order.submit()
        this.orderRepo.save(order)
        for event in order.events:
            this.eventBus.publish(event)
```

### Event Handling Strategies

| Strategy | Consistency | Complexity |
|----------|-------------|------------|
| **In-process, same transaction** | Strong | Low |
| **In-process, after commit** | Eventual | Medium |
| **Outbox pattern (DB + worker)** | Guaranteed delivery | High |
| **External message broker** | Eventual, at-least-once | High |

Start with in-process events. Move to outbox or message broker only when you need cross-service communication or guaranteed delivery.

---

## Aggregate Boundaries

An aggregate is a cluster of entities and value objects treated as a single unit for data changes. One entity is the aggregate root — all external access goes through it.

```
// Order is the aggregate root
// OrderItem and ShippingAddress are internal to the aggregate
class Order:                    // Aggregate root
    id
    items: list<OrderItem>      // Internal entity
    shippingAddress: Address    // Internal value object
    status

    method addItem(product, quantity):
        // Aggregate root enforces invariants
        if this.status != "draft":
            throw InvalidStateError("Cannot modify")
        item = new OrderItem(product, quantity)
        this.items.add(item)
        this.recalculateTotal()

// External code CANNOT access OrderItem directly
// BAD:  order.items[0].quantity = 5
// GOOD: order.updateItemQuantity(itemId, 5)
```

### Aggregate Design Rules

1. **Reference other aggregates by ID, not by object.** `Order.customerId` (ID), not `Order.customer` (object).
2. **One aggregate per transaction.** If you need to update two aggregates atomically, consider merging them or using eventual consistency.
3. **Keep aggregates small.** Large aggregates cause contention and performance problems.

---

## Anti-Corruption Layer

When integrating with external systems or legacy code, use an anti-corruption layer (ACL) to prevent their models from leaking into your domain.

```
// External payment API returns its own format
externalResponse = {
    "txn_id": "PAY-123",
    "amt_cents": 5000,
    "curr": "USD",
    "stat": "OK"
}

// Anti-corruption layer translates to domain model
class PaymentGatewayAdapter implements PaymentGateway:
    method authorize(amount, method):
        externalResult = this.stripeApi.charge(
            amount: amount.toCents(),
            currency: amount.currency,
            source: method.token
        )
        // Translate external model to domain model
        return PaymentResult(
            transactionId: externalResult.txn_id,
            amount: Money.fromCents(externalResult.amt_cents, externalResult.curr),
            success: externalResult.stat == "OK"
        )
```

The domain never sees `txn_id` or `amt_cents`. It only works with `PaymentResult`, `Money`, and other domain types.

---

## Migration Strategy: Monolith to Clean Architecture

For existing codebases, migrate incrementally:

### Phase 1: Extract Domain

1. Identify core business rules scattered across controllers and services.
2. Move them into domain entities with behavior.
3. Keep existing infrastructure in place.

### Phase 2: Define Ports

1. Create interfaces for data access (repository ports).
2. Create interfaces for external services (gateway ports).
3. Existing implementations become the first adapters.

### Phase 3: Introduce Use Cases

1. Extract controller logic into use case classes.
2. Controllers become thin adapters that call use cases.
3. Use cases depend on ports, not concrete implementations.

### Phase 4: Clean Up

1. Move framework-specific code to the adapter layer.
2. Ensure domain has zero framework imports.
3. Add integration tests for adapters, unit tests for domain and use cases.

### Rules for Migration

- **Do not rewrite.** Refactor incrementally.
- **One boundary at a time.** Extract the most painful coupling first.
- **Tests before refactoring.** Write characterization tests to preserve behavior.
- **Ship between phases.** Each phase should produce a deployable, tested state.

---

## Common Mistakes

### Mistake: Domain Model Mirrors Database Schema

```
// BAD: Domain entity is just a table row
class User:
    id, first_name, last_name, email, password_hash,
    created_at, updated_at, is_deleted, role_id,
    last_login_at, login_count, failed_login_attempts
```

Domain entities should model business concepts, not database columns. Persistence details (timestamps, soft-delete flags, login tracking) belong in the infrastructure layer.

### Mistake: Use Cases Return Domain Entities

```
// BAD: Controller gets full domain entity
result = submitOrder.execute(command)
response = { id: result.id, items: result.items, ... }
// Domain internals leak through API response
```

Use cases should return DTOs tailored to the caller's needs, not raw domain entities.

### Mistake: Shared Domain Across Microservices

Each microservice should have its own domain model. Sharing domain entities across services creates tight coupling. Use events and contracts (API schemas) at service boundaries instead.

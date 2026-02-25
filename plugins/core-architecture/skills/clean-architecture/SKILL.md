---
name: core-architecture:clean-architecture
description: "Clean architecture styles — hexagonal/ports-and-adapters, onion architecture, dependency rule, layer boundaries. When to use and when it is overkill."
user-invocable: false
---

# Clean Architecture

Architectural styles that enforce separation between business logic and infrastructure. The core idea: **dependencies point inward**.

## Additional resources

- [architecture-reference.md](architecture-reference.md) — Full layer breakdowns, project structure examples, entity vs value object, domain events, aggregate design, migration strategies

---

## The Dependency Rule

> Source code dependencies must point inward. Nothing in an inner circle can know anything about something in an outer circle.

```
Frameworks & Drivers (outermost)
  └── Interface Adapters
        └── Application / Use Cases
              └── Domain / Entities (innermost)
```

**Domain** knows nothing about databases, HTTP, or frameworks. **Use cases** orchestrate domain objects but do not know how data is stored. **Adapters** translate between use cases and the outside world.

---

## Architecture Variants

| Style | Inner Core | Outer Shell |
|-------|------------|-------------|
| **Hexagonal (Ports & Adapters)** | Domain + ports (interfaces) | Adapters (implementations) |
| **Onion Architecture** | Domain model | Infrastructure at the edge |
| **Clean Architecture** (Uncle Bob) | Entities + use cases | Controllers, gateways, presenters |

All three express the same dependency rule. Terminology differs but the principle is identical.

---

## Hexagonal Architecture

- **Port:** Interface defined by the core (`OrderRepository`, `PaymentGateway`).
- **Driving adapter (primary):** Calls into the core (REST controller, CLI, message consumer).
- **Driven adapter (secondary):** Called by the core through a port (SQL repository, Stripe adapter).

---

## Layer Responsibilities

**Domain (innermost):** Entities, value objects, domain events, domain services. No framework imports, no database references, no HTTP concepts.

```
class Order:
    method submit():
        if this.items.isEmpty(): throw ValidationError("Empty order")
        this.status = "submitted"
        return new OrderSubmitted(this.id, this.total)
```

**Application (use cases):** Orchestrates domain objects. Defines port interfaces. No framework knowledge.

```
class SubmitOrderUseCase:
    constructor(orderRepo: OrderRepository, paymentGateway: PaymentGateway): ...
    method execute(command):
        order = this.orderRepo.findById(command.orderId)
        event = order.submit()
        this.paymentGateway.authorize(order.total, command.paymentMethod)
        this.orderRepo.save(order)
```

**Adapters (outermost):** Controllers, repository implementations, API clients. Translates between external formats and domain types.

---

## Dependency Violations — How to Spot

| Violation | Example | Fix |
|-----------|---------|-----|
| Domain imports framework | `@Injectable()` on entity | Remove framework decorator |
| Domain references DB | `@Column()` on entity fields | Separate persistence models |
| Use case knows HTTP | Returns `HttpResponse` | Return plain DTO |
| Inner layer creates outer | `new SqlRepository()` in use case | Inject via constructor |

---

## Testing Strategy

| Layer | Test Type | Infrastructure Needed |
|-------|-----------|----------------------|
| Domain | Unit tests | None — pure logic |
| Use cases | Unit tests + mocked ports | None |
| Adapters | Integration tests | Real DB, real HTTP |

---

## When to Use

Use clean architecture when 2+ apply:
- Complex business rules (not just CRUD)
- Multiple entry points share business logic
- Infrastructure may change
- Long-lived project maintained by a team
- Testability of business logic is a priority

**Skip it when:** Pure CRUD, prototype, small codebase (< 5k lines), or time-to-market dominates.

See [architecture-reference.md](architecture-reference.md) for project structure examples, aggregate design, anti-corruption layers, and incremental migration strategies.

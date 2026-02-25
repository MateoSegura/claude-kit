---
name: core-architecture:solid-principles
description: "SOLID principles — Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. Practical examples showing violations and fixes in pseudocode."
user-invocable: false
---

# SOLID Principles

Five foundational design principles for writing maintainable, extensible, and testable software.

## Additional resources

- [solid-reference.md](solid-reference.md) — Deep dives with extended examples, edge cases, and real-world scenarios for each principle

---

## Quick Reference

| Principle | One-Liner | Violation Smell |
|-----------|-----------|-----------------|
| **S** — Single Responsibility | A class has one reason to change | God class, "and" in class name |
| **O** — Open/Closed | Open for extension, closed for modification | if/else chains for new types |
| **L** — Liskov Substitution | Subtypes must be substitutable for their base | Overrides that throw "not supported" |
| **I** — Interface Segregation | No client depends on methods it does not use | Fat interfaces, empty method stubs |
| **D** — Dependency Inversion | Depend on abstractions, not concretions | Direct instantiation, hard-coded infra |

---

## S — Single Responsibility

A module should have one, and only one, reason to change.

**Violation:** `UserService.createUser()` validates, persists, sends email, and logs.

**Fix:** Extract each concern into a collaborator. `UserService` orchestrates; `Validator`, `Repository`, `Notifier` each own one responsibility.

---

## O — Open/Closed

Software entities should be open for extension but closed for modification.

**Violation:** Adding a new discount type requires editing a function's if/else chain.

**Fix:** Use a strategy map. Register new strategies without modifying existing code.

```
discountStrategies = { "regular": RegularDiscount, "premium": PremiumDiscount }
// Adding "vip": register VipDiscount — no existing code changes
```

---

## L — Liskov Substitution

Objects of a supertype should be replaceable with subtypes without breaking correctness.

**Violation:** `Square extends Rectangle` breaks when `setWidth` and `setHeight` are called independently.

**Fix:** Use separate types or make shapes immutable. Behavioral compatibility matters more than "is-a" taxonomy.

---

## I — Interface Segregation

Clients should not be forced to depend on interfaces they do not use.

**Violation:** `Robot implements Worker` but must stub `eat()` and `sleep()`.

**Fix:** Split into `Workable`, `Feedable`, `Restable`. `Robot` implements only `Workable`.

---

## D — Dependency Inversion

High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Violation:** `OrderService` instantiates `new MySQLDatabase()` and `new SmtpMailer()`.

**Fix:** Inject `OrderRepository` and `Notifier` abstractions via constructor. Wire concretes in the composition root.

```
// Composition root:
service = new OrderService(new PostgresRepo(pool), new EmailNotifier(smtp))
```

---

## When SOLID Is Overkill

- **Scripts and one-off tools**: A 50-line script does not need interface segregation.
- **Prototypes**: Coupling is acceptable while exploring. Refactor when the design stabilizes.
- **Simple CRUD**: If a service just maps HTTP to database with no business logic, one class is fine.
- **Performance-critical paths**: Abstraction adds indirection. Measure before abstracting.

Apply SOLID when you feel the pain of its absence — not preemptively.

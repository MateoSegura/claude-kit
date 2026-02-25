# core-architecture

> **Role:** Knowledge companion · **Version:** 0.0.1

General-purpose software architecture — SOLID principles, design patterns, clean architecture, and API design for any software project.

This is a **universal knowledge plugin** providing language-agnostic architecture reference material. It can be loaded as a companion by any role plugin regardless of tech stack.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `solid-principles` | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion — with practical violation/fix examples in pseudocode |
| `design-patterns` | GoF creational (factory, builder, singleton, prototype), structural (adapter, decorator, facade, proxy, composite), behavioral (strategy, observer, command, state, mediator, chain of responsibility) — plus modern patterns (repository, unit of work, specification, CQRS, event sourcing) |
| `clean-architecture` | Hexagonal/ports-and-adapters, onion architecture, dependency rule, layer boundaries, entity vs value object, domain events, aggregate design, anti-corruption layer, migration strategies |
| `api-design` | REST conventions, GraphQL vs REST vs gRPC tradeoffs, API versioning strategies, pagination patterns (offset, cursor, keyset), error response conventions, idempotency, rate limiting, webhooks, authentication patterns |

---

## Auto-Loading

This plugin can be declared as a companion by any role plugin to inject architecture knowledge into its agent context. It is domain-agnostic and applies to any software project.

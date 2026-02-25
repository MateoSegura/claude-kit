---
name: core-architecture:identity
description: "Domain overview for universal software architecture knowledge. Auto-loaded for all domain tasks."
user-invocable: false
---

# Software Architecture — Domain Knowledge

This plugin provides language-agnostic reference material for software architecture decisions. It covers foundational principles (SOLID), proven design patterns (GoF and modern), architectural styles (clean architecture, hexagonal), and API design best practices.

## What this plugin contains

- **SOLID principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion — with violation examples and fixes
- **Design patterns**: Creational (factory, builder, singleton, prototype), Structural (adapter, decorator, facade, proxy, composite), Behavioral (strategy, observer, command, state, mediator, chain of responsibility) — plus modern patterns (repository, unit of work, specification, CQRS)
- **Clean architecture**: Hexagonal/ports-and-adapters, onion architecture, dependency rule, layer boundaries, when to use vs when it is overkill
- **API design**: REST principles, GraphQL vs REST vs gRPC tradeoffs, versioning strategies, pagination patterns, error response conventions, idempotency

## What this plugin does NOT contain

- No language-specific implementations — patterns are shown in pseudocode or multi-language snippets
- No agent definitions — agents belong in role plugins
- No slash commands — workflow orchestration belongs in role plugins
- No persona or communication style — role plugins define their own identity
- No hooks or enforcement rules — role plugins own those

## Usage

This is a companion plugin loaded alongside role plugins. It centralizes architecture knowledge so that all role variants share a single, consistent reference base. The content is language-agnostic and applies to any software project.

## Additional resources

- For SOLID principles with practical examples, see [solid-principles/SKILL.md](../solid-principles/SKILL.md) and [solid-reference.md](../solid-principles/solid-reference.md)
- For GoF and modern design patterns, see [design-patterns/SKILL.md](../design-patterns/SKILL.md) and [patterns-reference.md](../design-patterns/patterns-reference.md)
- For architectural styles and layer boundaries, see [clean-architecture/SKILL.md](../clean-architecture/SKILL.md) and [architecture-reference.md](../clean-architecture/architecture-reference.md)
- For REST, GraphQL, gRPC, and API conventions, see [api-design/SKILL.md](../api-design/SKILL.md) and [api-reference.md](../api-design/api-reference.md)

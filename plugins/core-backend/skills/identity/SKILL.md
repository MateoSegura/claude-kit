---
name: core-backend:identity
description: "Domain overview for language-agnostic backend development knowledge. Auto-loaded for all backend domain tasks."
user-invocable: false
---

# Backend Systems -- Domain Knowledge

This plugin provides language-agnostic reference material for building production backend systems. It covers distributed systems patterns, database design, authentication and authorization, API protocol selection, and message queue architectures, with emphasis on resilience, correctness, and scalability.

## What this plugin contains

- **Distributed systems**: Circuit breakers, retries with exponential backoff, service discovery, event-driven architecture, saga pattern, CQRS, eventual consistency, idempotency, distributed tracing
- **Database patterns**: Connection pooling, migration strategies, ORM vs query builder vs raw SQL tradeoffs, indexing strategy, N+1 problem, read replicas, sharding concepts, transaction isolation levels
- **Authentication and authorization**: OAuth 2.0 flows, JWT structure and validation, session-based vs token-based auth, RBAC vs ABAC, API key management, refresh token rotation
- **API protocols**: gRPC (protobuf, streaming modes, interceptors), GraphQL (schema design, resolvers, N+1, subscriptions), WebSockets, Server-Sent Events -- when to use each
- **Message queues**: Pub/sub vs point-to-point, message brokers (Redis Streams, RabbitMQ, Kafka concepts), dead letter queues, exactly-once delivery challenges, event schemas and versioning

## What this plugin does NOT contain

- No agent definitions -- agents belong in role plugins (engineer, grader, tester)
- No slash commands -- workflow orchestration belongs in role plugins
- No persona or communication style -- role plugins define their own identity
- No hooks or enforcement rules -- role plugins own those
- No language-specific code -- all examples use pseudocode or are framework-agnostic

## Usage

This is a companion plugin loaded alongside role plugins such as `cloud-python-engineer` or any backend-focused team. It centralizes domain knowledge so that all role variants share a single, consistent reference base.

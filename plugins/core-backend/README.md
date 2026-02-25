# core-backend

> **Role:** Knowledge companion · **Version:** 0.0.1

Language-agnostic backend development knowledge -- distributed systems, database patterns, authentication, API protocols, and message queues.

This plugin is **auto-loaded as a companion** by any plugin with `domain: "backend"` in its `ctl.json`. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `distributed-systems` | Circuit breakers, retries with exponential backoff, service discovery, event-driven architecture, saga pattern, CQRS, eventual consistency, idempotency, outbox pattern, distributed tracing |
| `database-patterns` | Connection pooling, migration strategies, ORM vs query builder vs raw SQL tradeoffs, indexing strategy, N+1 problem, read replicas, sharding concepts, transaction isolation levels |
| `auth-patterns` | OAuth 2.0 flows (authorization code, client credentials, PKCE), JWT structure and validation, session-based vs token-based auth, RBAC vs ABAC, API key management, refresh token rotation |
| `api-protocols` | gRPC (protobuf, streaming modes, interceptors), GraphQL (schema design, resolvers, N+1, subscriptions), REST conventions, WebSockets, Server-Sent Events -- when to use each |
| `message-queues` | Pub/sub vs point-to-point, message brokers (Redis Streams, RabbitMQ, Kafka), dead letter queues, exactly-once delivery challenges, event schemas and versioning, consumer groups |

---

## Auto-Loading

Plugins with `"domain": "backend"` in their `ctl.json` automatically load this companion and inject all its skills into their agent context at launch. This includes:

- `cloud-python-engineer`
- `cloud-python-grader`
- `cloud-python-tester`
- `cloud-python-debugger`
- Any future backend-focused team plugins

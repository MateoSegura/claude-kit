---
name: cloud-python-knowledge:identity
description: "Domain overview for Python cloud-backend knowledge. Auto-loaded for all domain tasks."
user-invocable: false
---

# Python Cloud-Backend Systems -- Domain Knowledge

This plugin provides Python-specific reference material for building production distributed systems in Python 3.11+. It covers async HTTP/gRPC services, containerization, Kubernetes orchestration, and Python design patterns, with emphasis on type safety, resilience patterns, and observability.

Language-agnostic backend concepts live in the `core-backend` plugin (auto-loaded via domain). This plugin focuses exclusively on Python implementations.

## Domain Scope

- **Runtime**: Python 3.11+ with `asyncio` as the primary concurrency model
- **Web frameworks**: FastAPI 0.100+, Starlette, uvicorn ASGI server
- **Data validation**: Pydantic v2 models, discriminated unions, custom validators
- **Database**: SQLAlchemy 2.0 async ORM, Alembic migrations, asyncpg, aiosqlite
- **RPC**: gRPC via grpcio, protobuf code generation with grpcio-tools and buf
- **HTTP clients**: httpx async client, connection pooling, retry strategies
- **Message brokers**: aio-pika (RabbitMQ), aiokafka (Kafka), redis.asyncio Streams
- **Resilience**: tenacity retries, pybreaker circuit breakers, idempotent request handling
- **Observability**: structlog structured logging, OpenTelemetry traces/metrics, Prometheus client
- **Containerization**: Docker multi-stage builds, uv/pip dependency caching, Compose service graphs
- **Orchestration**: Kubernetes manifests, health probes, HPA scaling, ConfigMap/Secret management

## Expertise Areas

This knowledge base covers Python-specific implementation details for production cloud services. Key expertise areas include:

- **Async-first design**: Correct `asyncio` event loop management, task cancellation semantics, `asyncio.TaskGroup` (3.11+), structured concurrency patterns, and pitfalls around blocking calls in async contexts
- **Type-safe data modeling**: Pydantic v2 model validators, discriminated unions, custom serializers, `model_config` settings, and schema generation for OpenAPI
- **Database access**: SQLAlchemy 2.0 async sessions, connection pooling with `create_async_engine`, Alembic migration patterns, and the repository/unit-of-work pattern for transactional boundaries
- **Service communication**: gRPC streaming modes (unary, server-stream, client-stream, bidirectional), protobuf message evolution, interceptor chains, and deadline propagation
- **Resilience engineering**: Retry policies with tenacity (exponential backoff, jitter), circuit breakers with pybreaker, bulkhead isolation via semaphores, and outbox-pattern for transactional messaging
- **Observability**: Structured logging with structlog, distributed tracing with OpenTelemetry Python SDK, Prometheus metrics via `prometheus-client`, and health check endpoint conventions

## Skill Reference Map

This plugin contains **skills only** — no agents, no commands. Skills are loaded by companion role plugins that reference them in agent frontmatter. Each skill directory contains a `SKILL.md` entry point (auto-loaded) and supplemental reference files (loaded on demand via Read).

| Skill | What It Provides |
|-------|-----------------|
| `python-backend` | asyncio event loop, async/await concurrency, FastAPI/Starlette, httpx, Pydantic v2, dependency injection, middleware patterns |
| `grpc-protocols` | grpcio service definitions, protobuf stubs, all four streaming modes, interceptors, error handling, deadlines, health checking |
| `distributed-systems` | tenacity retries, pybreaker circuit breakers, aio-pika (RabbitMQ), aiokafka, redis.asyncio Streams, SQLAlchemy outbox, idempotency |
| `containers-orchestration` | Multi-stage Dockerfiles with python:3.12-slim, uv caching, Compose with asyncpg/redis, K8s manifests, health probes, HPA, uvicorn config |
| `design-patterns` | SQLAlchemy repository/unit of work, FastAPI Depends DI, factory/strategy with ABC, asyncio observer, structlog, OpenTelemetry SDK, graceful shutdown |

## What this plugin does NOT contain

- No agent definitions — agents belong in role plugins (engineer, grader, tester, debugger)
- No slash commands — workflow orchestration belongs in role plugins
- No role-specific identity or persona — each role plugin defines its own
- No language-agnostic concepts — those live in `core-backend`, `core-architecture`, `core-devops`, `core-security`, `core-testing`

## Core plugin companions

This plugin works alongside these core knowledge plugins (auto-loaded via `domain: "backend"`):

- `core-backend` — Language-agnostic distributed systems, database patterns, auth, API protocols, message queues
- `core-architecture` — Design pattern theory, SOLID, DDD, hexagonal architecture
- `core-devops` — Generic Docker, Kubernetes, CI/CD concepts
- `core-security` — Security patterns and vulnerability prevention
- `core-testing` — Testing strategies and patterns

When a role plugin references a concept covered by a core plugin, this knowledge plugin provides the Python-specific implementation while the core plugin supplies the underlying theory. For example, `core-backend` covers generic circuit breaker theory; this plugin's `distributed-systems` skill covers the pybreaker configuration, state callbacks, and integration with FastAPI exception handlers.

## Python Version and Tooling Assumptions

All patterns in this knowledge base target **Python 3.11+** as the minimum runtime. Key version-specific features that skills rely on:

- `asyncio.TaskGroup` for structured concurrency (3.11)
- `ExceptionGroup` and `except*` syntax for multi-error handling (3.11)
- `tomllib` for pyproject.toml parsing (3.11)
- `type` statement and generic syntax `class Foo[T]:` (3.12)
- **uv** as the preferred package installer and resolver for Docker builds and local development

## Additional resources

- For Python naming, formatting, and type annotation conventions, see [coding-standards.md](coding-standards.md)
- For common workflows (project setup, build, test, containerize, deploy), see [workflow-patterns.md](workflow-patterns.md)

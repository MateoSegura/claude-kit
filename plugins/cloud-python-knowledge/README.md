# cloud-python-knowledge

> **Role:** Knowledge companion · **Version:** 0.1.1

Shared domain knowledge for modern Python cloud-backend development — asyncio, FastAPI, gRPC, Docker, Kubernetes, distributed systems patterns, and design patterns.

This plugin is **auto-loaded as a companion** by the engineer, grader, tester, and debugger plugins. Do not launch it directly. Language-agnostic backend concepts are provided by the `core-backend` plugin (auto-loaded via `domain: "backend"`).

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `python-backend` | Core Python backend patterns: asyncio event loop, async/await concurrency, type hints, FastAPI/Starlette, httpx, Pydantic v2, dependency injection, middleware |
| `grpc-protocols` | Python gRPC with grpcio: protobuf definitions, service stubs, all four streaming modes, interceptors, error handling, deadlines, metadata, health checking, grpcio-tools |
| `distributed-systems` | Python distributed systems libraries: tenacity retries, pybreaker circuit breakers, aio-pika (RabbitMQ), aiokafka, redis.asyncio Streams, SQLAlchemy outbox, FastAPI idempotency |
| `containers-orchestration` | Docker and Kubernetes for Python: multi-stage Dockerfiles with python:3.12-slim, uv caching, Compose with asyncpg/redis, K8s manifests, health probes, HPA, uvicorn config |
| `design-patterns` | Python design pattern implementations: SQLAlchemy repository/unit of work, FastAPI Depends DI, factory/strategy with ABC, asyncio observer, structlog, OpenTelemetry Python SDK, graceful shutdown |

---

## Core Plugin Companions

All `cloud-python-*` plugins set `domain: "backend"`, which auto-loads these core knowledge plugins for language-agnostic concepts:

- `core-backend` — Distributed systems, database patterns, auth, API protocols, message queues
- `core-architecture` — Design pattern theory, SOLID, DDD, hexagonal architecture
- `core-devops` — Generic Docker, Kubernetes, CI/CD concepts
- `core-security` — Security patterns and vulnerability prevention
- `core-testing` — Testing strategies and patterns

---

## Auto-Loading

The following plugins declare this plugin as a companion and automatically inject all its skills into their agent context at launch:

- `cloud-python-engineer`
- `cloud-python-grader`
- `cloud-python-tester`
- `cloud-python-debugger`

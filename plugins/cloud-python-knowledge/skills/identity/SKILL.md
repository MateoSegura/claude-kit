---
name: cloud-python-knowledge:identity
description: "Domain overview for Python cloud-backend knowledge. Auto-loaded for all domain tasks."
user-invocable: false
---

# Python Cloud-Backend Systems -- Domain Knowledge

This plugin provides Python-specific reference material for building production distributed systems in Python 3.11+. It covers async HTTP/gRPC services, containerization, Kubernetes orchestration, and Python design patterns, with emphasis on type safety, resilience patterns, and observability.

Language-agnostic backend concepts live in the `core-backend` plugin (auto-loaded via domain). This plugin focuses exclusively on Python implementations.

## What this plugin contains

- **Python backend patterns**: asyncio event loop, async/await concurrency, type hints, FastAPI/Starlette, httpx, Pydantic v2, dependency injection, middleware
- **gRPC with grpcio**: protobuf definitions, service stubs, streaming patterns, interceptors, error handling
- **Python distributed systems**: tenacity retries, pybreaker circuit breakers, aio-pika, aiokafka, redis.asyncio, outbox with SQLAlchemy
- **Python design patterns**: SQLAlchemy repository/unit of work, FastAPI Depends DI, structlog, OpenTelemetry Python SDK, asyncio graceful shutdown
- **Python containers**: Dockerfiles with python:3.12-slim, uv/pip caching, Compose, uvicorn configuration

## What this plugin does NOT contain

- No agent definitions -- agents belong in role plugins (engineer, grader, tester)
- No slash commands -- workflow orchestration belongs in role plugins
- No language-agnostic concepts -- those live in `core-backend`, `core-architecture`, `core-devops`, `core-security`, `core-testing`

## Core plugin companions

This plugin works alongside these core knowledge plugins (auto-loaded via `domain: "backend"`):

- `core-backend` -- Language-agnostic distributed systems, database patterns, auth, API protocols, message queues
- `core-architecture` -- Design pattern theory, SOLID, DDD, hexagonal architecture
- `core-devops` -- Generic Docker, Kubernetes, CI/CD concepts
- `core-security` -- Security patterns and vulnerability prevention
- `core-testing` -- Testing strategies and patterns

## Additional resources

- For Python naming, formatting, and type annotation conventions, see [coding-standards.md](coding-standards.md)
- For common workflows (project setup, build, test, containerize, deploy), see [workflow-patterns.md](workflow-patterns.md)

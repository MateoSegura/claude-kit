---
name: cloud-python-knowledge:identity
description: "Domain overview for Python cloud-backend knowledge. Auto-loaded for all domain tasks."
user-invocable: false
---

# Python Cloud-Backend Systems -- Domain Knowledge

This plugin provides reference material for building production distributed systems in Python 3.11+. It covers the full stack from async HTTP/gRPC services through containerization and Kubernetes orchestration, with emphasis on type safety, resilience patterns, and observability.

## What this plugin contains

- **Language fundamentals**: Python 3.11+ asyncio patterns, strict type annotations (mypy/pyright), structured concurrency
- **Web frameworks**: FastAPI, Starlette, httpx client patterns, middleware, dependency injection
- **RPC and messaging**: gRPC with grpcio/protobuf, service definitions, streaming patterns
- **Containerization**: Dockerfile best practices, multi-stage builds, distroless/slim images
- **Orchestration**: Kubernetes manifests, Helm charts, health probes, resource limits, HPA
- **Concurrency**: asyncio event loops, threading, multiprocessing, work queues, graceful shutdown
- **Resilience**: Circuit breakers, retries with backoff, timeouts, bulkheads, service discovery
- **Observability**: Structured logging, OpenTelemetry tracing, Prometheus metrics
- **Testing**: pytest, pytest-asyncio, testcontainers, fixture patterns, integration test strategies
- **Safety**: Error handling conventions, input validation (Pydantic), defensive coding patterns

## What this plugin does NOT contain

- No agent definitions -- agents belong in role plugins (engineer, grader, tester)
- No slash commands -- workflow orchestration belongs in role plugins
- No persona or communication style -- role plugins define their own identity
- No hooks or enforcement rules -- role plugins own those

## Usage

This is a companion plugin loaded alongside role plugins such as `cloud-python-engineer` or `cloud-python-grader`. It centralizes domain knowledge so that all role variants share a single, consistent reference base.

## Additional resources

- For Python naming, formatting, and type annotation conventions, see [coding-standards.md](coding-standards.md)
- For common workflows (project setup, build, test, containerize, deploy), see [workflow-patterns.md](workflow-patterns.md)

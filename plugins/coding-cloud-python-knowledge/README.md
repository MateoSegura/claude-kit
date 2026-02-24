# coding-cloud-python-knowledge

> **Role:** Knowledge companion · **Version:** 0.0.1

Shared domain knowledge for modern Python cloud-backend development — asyncio, FastAPI, gRPC, Docker, Kubernetes, distributed systems patterns, and design patterns.

This plugin is **auto-loaded as a companion** by the engineer, grader, tester, and debugger plugins. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `python-backend` | Core Python backend patterns: asyncio event loop, async/await concurrency, type hints, FastAPI/Starlette, httpx, Pydantic v2, dependency injection, middleware |
| `grpc-protocols` | gRPC and Protocol Buffers: protobuf definitions, service stubs, all four streaming modes, interceptors, error handling, deadlines, metadata, health checking, grpcio-tools |
| `distributed-systems` | Distributed systems patterns: circuit breakers, retries with exponential backoff, service discovery, event-driven architecture, message queues, saga pattern, CQRS, eventual consistency |
| `containers-orchestration` | Docker and Kubernetes: multi-stage Dockerfiles, slim images, uv caching, Compose, K8s Deployments, Services, ConfigMaps, Secrets, health probes, resource limits, HPA, Helm charts |
| `design-patterns` | Python design patterns: repository, unit of work, dependency injection, factory, strategy, observer, structured logging, OpenTelemetry tracing, graceful shutdown, connection pooling |

---

## Auto-Loading

The following plugins declare this plugin as a companion and automatically inject all its skills into their agent context at launch:

- `coding-cloud-python-engineer`
- `coding-cloud-python-grader`
- `coding-cloud-python-tester`
- `coding-cloud-python-debugger`

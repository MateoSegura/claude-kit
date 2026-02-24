# coding-cloud-python-engineer

> **Role:** Engineer · **Version:** 1.0.0

Python cloud-backend engineer — scaffolds microservices, writes FastAPI endpoints, gRPC methods, Alembic migrations, background workers, and K8s manifests for modern distributed systems.

```bash
claude-kit --kit coding-cloud-python-engineer
# or load the full team:
claude-kit --kit coding-cloud-python
```

**Companion auto-loaded:** `coding-cloud-python-knowledge` (asyncio, FastAPI, gRPC, Docker, Kubernetes, design patterns)

---

## Agents

| Agent | Description |
|-------|-------------|
| `service-scaffolder` | Scaffolds complete new Python microservices from scratch. Creates pyproject.toml (uv), src/ package layout, FastAPI app factory, Pydantic BaseSettings, multi-stage Dockerfile, docker-compose.yml, Alembic setup, health checks, structlog + OpenTelemetry bootstrap, and CI stubs. Use when the user needs to create a new service, initialize a new project, or bootstrap a microservice skeleton. |
| `endpoint-writer` | Adds HTTP/REST endpoints to existing FastAPI services. Generates router modules, Pydantic request/response schemas, Depends() dependency injection, service-layer calls, proper HTTP status codes, OpenAPI documentation, and structured error handling. Use when the user needs new API endpoints, CRUD resources, or HTTP route modifications. |
| `grpc-writer` | Adds gRPC service methods to Python backends. Generates and updates .proto files following Google API Design Guide, compiles Python stubs, implements async servicers, adds interceptors for logging/auth/tracing, wires services into the gRPC server, and configures gRPC health checking. Use when the user needs gRPC endpoints, protobuf definitions, or inter-service RPC communication. |
| `migration-writer` | Generates Alembic database migrations for SQLAlchemy 2.0 models. Reads model definitions, produces upgrade/downgrade scripts, handles complex operations (data migrations, enum changes, foreign key constraints, index creation), and validates migration chain integrity. Use when the user needs database schema changes, new migrations, or migration troubleshooting. |
| `worker-writer` | Scaffolds background workers and async task processors. Generates Celery tasks, Dramatiq actors, Kafka/NATS/Redis Streams consumers, and pure asyncio workers with graceful shutdown, dead-letter handling, retry policies (tenacity), circuit breakers, and OpenTelemetry instrumentation. Use when the user needs background job processing, event consumers, scheduled tasks, or message queue workers. |
| `manifest-writer` | Generates Kubernetes manifests and Dockerfiles for Python microservices. Produces Deployment, Service, ConfigMap, Secret, HPA, Ingress, PodDisruptionBudget, init containers (Alembic migrations), Kustomize overlays, and multi-stage Dockerfiles with uv. Cloud-agnostic and production-ready. Use when the user needs to containerize a service, create K8s deployment configs, or set up Kustomize environments. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-cloud-python-engineer:engineer` | Primary entry point for all cloud Python engineering workflows. Routes service scaffolding, HTTP endpoints, gRPC methods, database migrations, background workers, and Kubernetes manifests to the appropriate specialist subagent. |

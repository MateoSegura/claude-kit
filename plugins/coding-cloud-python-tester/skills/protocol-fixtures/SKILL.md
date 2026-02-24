---
name: coding-cloud-python-tester:protocol-fixtures
description: "Protocol-specific test fixtures for Python cloud services: HTTP/FastAPI async testing, in-process gRPC server fixtures, NATS test server, Kafka testcontainer, Celery eager mode, and Redis pub/sub testing patterns."
---

# Protocol Fixtures — Decision Matrix

Choose the right fixture strategy based on what protocol the service exposes.

## Protocol Selection Matrix

| Protocol | Service Type | Test Approach | Fixture File |
|----------|-------------|---------------|-------------|
| HTTP REST | FastAPI, Starlette | `httpx.AsyncClient` with `ASGITransport` | [http-fastapi.md](http-fastapi.md) |
| HTTP REST (sync) | Flask, Django | `TestClient` from `starlette.testclient` | [http-fastapi.md](http-fastapi.md) |
| gRPC | protobuf services | In-process server + local channel | [grpc-fixtures.md](grpc-fixtures.md) |
| NATS pub/sub | Event streaming | Embedded `nats-server` or testcontainer | [messaging-fixtures.md](messaging-fixtures.md) |
| Kafka | Event streaming | `KafkaContainer` (testcontainers) | [messaging-fixtures.md](messaging-fixtures.md) |
| Celery tasks | Background workers | Eager mode for unit; real worker for integration | [messaging-fixtures.md](messaging-fixtures.md) |
| Redis pub/sub | Lightweight messaging | `RedisContainer` + subscribe loop | [messaging-fixtures.md](messaging-fixtures.md) |
| GraphQL | GraphQL services | `httpx.AsyncClient` against ASGI app | [http-fastapi.md](http-fastapi.md) |
| WebSocket | Real-time streaming | FastAPI `websocket_connect` helper | [http-fastapi.md](http-fastapi.md) |

## Quick Fixture Selection Rules

**Use HTTP fixtures when:**
- The service exposes an HTTP API (REST, GraphQL, WebSocket)
- Testing API contracts or request/response schemas
- Overriding dependencies to isolate business logic from infrastructure

**Use gRPC fixtures when:**
- The service exposes a `.proto`-defined gRPC interface
- Testing service method contracts and protobuf message handling
- Validating streaming RPC behavior

**Use messaging fixtures when:**
- The service consumes or produces events (NATS, Kafka)
- Testing Celery task logic or task chains
- Verifying Redis pub/sub notification flows

## Dependency Override Pattern (All HTTP Protocols)

```python
# Core pattern: override any FastAPI dependency with a test double
app.dependency_overrides[get_db] = lambda: test_db_session
app.dependency_overrides[get_cache] = lambda: test_redis_client
app.dependency_overrides[get_current_user] = lambda: fake_user

# Always clean up after test
app.dependency_overrides.clear()
```

## Additional Resources

- [http-fastapi.md](http-fastapi.md) — httpx.AsyncClient, ASGITransport, TestClient, dependency overrides, WebSocket testing
- [grpc-fixtures.md](grpc-fixtures.md) — In-process gRPC server, channel setup, protobuf message factories, streaming RPCs
- [messaging-fixtures.md](messaging-fixtures.md) — NATS server, Kafka testcontainer, Celery eager mode, Redis pub/sub

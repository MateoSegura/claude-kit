# Workflow Patterns -- Cloud-Native Python Backend

This document provides detailed step-by-step workflows for the most common tasks performed by the coding-cloud-python-engineer agents. Each workflow reflects how a senior Python backend engineer thinks through the problem.

## Workflow 1: Scaffold a New Microservice

When creating a new service from scratch.

### Steps

1. **Create project structure**

   ```bash
   mkdir -p src/service_name/{routers,schemas,models,repositories,services,workers,proto}
   mkdir -p tests k8s alembic/versions
   touch src/service_name/__init__.py
   touch src/service_name/{main,config,deps,telemetry}.py
   ```

2. **Initialize uv project**

   ```bash
   uv init --name service-name
   uv add fastapi uvicorn[standard] pydantic pydantic-settings
   uv add sqlalchemy[asyncio] asyncpg alembic
   uv add structlog opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
   uv add httpx redis
   uv add --dev ruff mypy pytest pytest-asyncio
   ```

3. **Write config.py with pydantic-settings**

   Define `ServiceSettings(BaseSettings)` with all env vars. Group by concern: database, redis, telemetry, service. Use `model_config = SettingsConfigDict(env_prefix="SVC_")`.

4. **Write telemetry.py bootstrap**

   Initialize `TracerProvider` with `OTLPSpanExporter(endpoint=settings.otlp_endpoint)`. Register as global provider. Export `tracer = trace.get_tracer(__name__)`.

5. **Write main.py with application factory**

   Create `create_app() -> FastAPI` with async lifespan context manager. Wire up routers, exception handlers, CORS middleware, and telemetry init in lifespan startup.

6. **Write health router**

   `GET /healthz` returns `{"status": "ok"}`. `GET /readyz` checks database connectivity and returns 200/503.

7. **Write deps.py**

   Async generator for `AsyncSession`. Factory functions for each repository. All return typed results.

8. **Write Dockerfile (multi-stage)**

   Builder: `python:3.12-slim`, install uv, copy lockfile, `uv sync --frozen`.
   Runtime: `python:3.12-slim`, copy virtualenv from builder, copy source, non-root user, `CMD ["uvicorn", "service_name.main:create_app", "--factory", "--host", "0.0.0.0"]`.

9. **Write Kubernetes manifests**

   Deployment with resource limits, liveness/readiness probes, env from ConfigMap/Secret. Service with ClusterIP.

10. **Run validation**

    ```bash
    ruff check . && ruff format --check . && mypy --strict src/
    ```

### Decision Points

- **Database choice**: PostgreSQL unless the data model is document-oriented (MongoDB) or purely cache/session (Redis). Document the choice in a comment in `config.py`.
- **Async vs sync Celery**: Use async NATS/Kafka consumers by default. Only use Celery if integrating with an existing Celery-based system. Document why in `workers/__init__.py`.

## Workflow 2: Add a CRUD Endpoint

When adding a new resource endpoint to an existing service.

### Steps

1. **Define schemas in `schemas/<resource>.py`**

   ```python
   class CreateItemRequest(BaseModel):
       model_config = ConfigDict(strict=True)
       name: str = Field(min_length=1, max_length=255)
       price_cents: int = Field(gt=0)

   class ItemResponse(BaseModel):
       id: UUID
       name: str
       price_cents: int
       created_at: datetime
   ```

2. **Define or update ORM model in `models/<resource>.py`**

   Use `Mapped[]` type hints on every column. Add indexes for query patterns you know will exist. Add `__repr__` for debugging.

3. **Generate Alembic migration**

   ```bash
   alembic revision --autogenerate -m "add items table"
   ```

   Review the migration. Verify: correct column types, indexes present, foreign keys have `ondelete` behavior, no data loss on existing tables.

4. **Write repository in `repositories/<resource>.py`**

   Methods: `get_by_id`, `list_paginated`, `create`, `update`, `delete`. Each returns a Pydantic model or raises `RecordNotFoundError`. Accept `AsyncSession` via constructor.

5. **Write domain service in `services/<resource>.py` (if business logic exists)**

   Orchestrate validation, repository calls, and event publishing. Keep handlers thin -- all logic lives here.

6. **Write router in `routers/<resource>.py`**

   ```python
   router = APIRouter(prefix="/items", tags=["items"])

   @router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
   async def create_item(
       request: CreateItemRequest,
       repo: ItemRepository = Depends(get_item_repo),
   ) -> ItemResponse:
       ...
   ```

7. **Register router in `main.py`**

   ```python
   app.include_router(item_router)
   ```

8. **Add telemetry and logging**

   Wrap the handler body with `with tracer.start_as_current_span("create_item"):`. Log the business event: `logger.info("item_created", item_id=..., name=...)`.

9. **Validate**

   ```bash
   ruff check src/service_name/routers/<resource>.py
   mypy --strict src/service_name/
   ```

### Decision Points

- **Pagination**: Use cursor-based pagination (keyset) for large datasets, offset-based for small admin UIs. Document the choice in the repository docstring.
- **Soft delete vs hard delete**: Default to soft delete (`deleted_at` timestamp) for auditable resources. Hard delete only for ephemeral or GDPR-mandated purge. Document in the model.

## Workflow 3: Implement a gRPC Service

When adding gRPC alongside or instead of HTTP.

### Steps

1. **Define the `.proto` file in `proto/`**

   Follow Google API Design Guide:
   - Service name matches the domain concept (`OrderService`)
   - Methods use standard verbs (`CreateOrder`, `GetOrder`, `ListOrders`)
   - Request/response messages are per-method (`CreateOrderRequest`, `CreateOrderResponse`)
   - Use `google.protobuf.Timestamp` for datetime fields

2. **Generate Python stubs**

   ```bash
   python -m grpc_tools.protoc \
       -I proto/ \
       --python_out=src/service_name/proto/ \
       --grpc_python_out=src/service_name/proto/ \
       --mypy_out=src/service_name/proto/ \
       proto/order_service.proto
   ```

   Or with betterproto:
   ```bash
   python -m grpc_tools.protoc \
       -I proto/ \
       --python_betterproto_out=src/service_name/proto/ \
       proto/order_service.proto
   ```

3. **Write the servicer class in `services/grpc_<resource>.py`**

   ```python
   class OrderServicer(OrderServiceBase):
       def __init__(self, repo: OrderRepository, publisher: EventPublisher) -> None:
           self._repo = repo
           self._publisher = publisher

       async def CreateOrder(
           self, request: CreateOrderRequest, context: grpc.aio.ServicerContext
       ) -> CreateOrderResponse:
           # Proto -> Pydantic
           validated = CreateOrderSchema.model_validate(...)
           # Domain logic
           order = await self._repo.create(validated)
           # Pydantic -> Proto
           return CreateOrderResponse(id=str(order.id), ...)
   ```

4. **Add interceptors for telemetry**

   Write a `TelemetryInterceptor` that creates spans from gRPC metadata, propagates trace context.

5. **Wire into the server in `main.py`**

   ```python
   server = grpc.aio.server(interceptors=[TelemetryInterceptor()])
   add_OrderServiceServicer_to_server(servicer, server)
   server.add_insecure_port("[::]:50051")
   ```

6. **Validate types**

   ```bash
   mypy --strict src/service_name/services/grpc_order.py
   ```

### Decision Points

- **betterproto vs grpcio stubs**: Use betterproto for cleaner Pythonic API if the project does not need reflection or advanced gRPC features. Document in `proto/README.md`.
- **Unary vs streaming**: Default to unary RPCs. Use server streaming only for large result sets or real-time feeds. Document latency expectations as comments on the proto method.

## Workflow 4: Add an Async Message Consumer

When the service needs to consume events from NATS, Kafka, or a Celery queue.

### Steps

1. **Define the event schema in `schemas/events.py`**

   ```python
   class OrderCreatedEvent(BaseModel):
       model_config = ConfigDict(strict=True)
       event_id: UUID
       order_id: UUID
       customer_id: UUID
       total_cents: int
       occurred_at: datetime
   ```

2. **Write the consumer in `workers/<consumer_name>.py`**

   ```python
   async def handle_order_created(raw_message: bytes) -> None:
       try:
           event = OrderCreatedEvent.model_validate_json(raw_message)
       except ValidationError:
           logger.error("malformed_event", raw=raw_message[:200])
           return  # ACK to avoid redelivery; route to DLQ if configured

       async with get_session() as session:
           repo = InventoryRepository(session)
           await repo.reserve_stock(event.order_id, event.total_cents)
           await session.commit()

       logger.info("stock_reserved", order_id=str(event.order_id))
   ```

3. **Wire the consumer to the transport layer**

   For NATS:
   ```python
   nc = await nats.connect(settings.nats_url)
   js = nc.jetstream()
   sub = await js.subscribe("orders.created", cb=handle_order_created)
   ```

   For Kafka:
   ```python
   consumer = AIOKafkaConsumer("orders.created", bootstrap_servers=settings.kafka_brokers)
   await consumer.start()
   async for msg in consumer:
       await handle_order_created(msg.value)
   ```

4. **Add OpenTelemetry context propagation**

   Extract trace context from message headers/metadata. Create a child span linked to the producer span.

5. **Add dead-letter queue handling**

   On repeated processing failures (configurable retry count), publish the raw message to `<topic>.dlq` with error metadata.

6. **Validate**

   ```bash
   mypy --strict src/service_name/workers/
   ```

### Decision Points

- **NATS vs Kafka**: NATS for low-latency, at-most-once or exactly-once with JetStream. Kafka for high-throughput, ordered, durable event streams. Document in the consumer module docstring.
- **Retry strategy**: Exponential backoff with jitter for transient failures. Immediate DLQ for deserialization failures. Document max retries as a config parameter.

## Workflow 5: Write a Multi-Stage Dockerfile

When containerizing a Python service for production.

### Steps

1. **Builder stage**

   ```dockerfile
   FROM python:3.12-slim AS builder

   ENV PYTHONDONTWRITEBYTECODE=1
   COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

   WORKDIR /app
   COPY pyproject.toml uv.lock ./
   RUN uv sync --frozen --no-dev --no-editable

   COPY src/ ./src/
   ```

2. **Runtime stage**

   ```dockerfile
   FROM python:3.12-slim AS runtime

   ENV PYTHONDONTWRITEBYTECODE=1 \
       PYTHONUNBUFFERED=1

   RUN groupadd -r app && useradd -r -g app app

   WORKDIR /app
   COPY --from=builder /app/.venv /app/.venv
   COPY --from=builder /app/src /app/src

   ENV PATH="/app/.venv/bin:$PATH"
   USER app

   EXPOSE 8000
   CMD ["uvicorn", "service_name.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Validate**

   ```bash
   docker build -t service-name:dev .
   docker run --rm service-name:dev python -c "import service_name; print('ok')"
   ```

### Decision Points

- **Base image**: `python:3.12-slim` for smallest production image. Use `python:3.12` (full) only if C extensions need compilation toolchains at runtime. Document in Dockerfile comment.
- **uv install method**: Copy the uv binary from the official image (`COPY --from=ghcr.io/astral-sh/uv:latest`). This avoids curl/pip bootstrapping and keeps the builder layer deterministic.

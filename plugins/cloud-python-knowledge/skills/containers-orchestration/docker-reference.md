# Docker Reference — Python Services

Complete Dockerfile patterns, optimization techniques, and Compose configurations.

---

## Dockerfile Patterns

### Pattern 1: Standard Multi-Stage with pip + venv

```dockerfile
# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps in base (cached across builder/runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# --- Builder ---
FROM base AS builder

# Build tools only in builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
# Cache bust only when requirements.txt changes
RUN pip install --upgrade pip==24.0 && \
    pip install --requirement requirements.txt

# --- Runtime ---
FROM base AS runtime

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -s /sbin/nologin appuser

WORKDIR /app
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./

USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"

ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 2: uv Package Manager (Recommended for Speed)

```dockerfile
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.5 AS uv-binary

FROM python:3.12-slim AS builder
COPY --from=uv-binary /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first (layer cached until lock file changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# Copy source and install project
COPY src/ ./src/
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN useradd -r -u 1001 appuser
WORKDIR /app
COPY --from=builder --chown=appuser /app/src ./src/
USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 3: Distroless Runtime (Minimal Attack Surface)

```dockerfile
FROM python:3.12-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ /app/src/

# Google Distroless — no shell, no package manager
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
# Note: no shell available — CMD must be exec form
CMD ["/opt/venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Layer Optimization Rules

| Rule | Reason |
|------|--------|
| Copy `requirements.txt` before source code | Dependencies change less often; cache preserved on code changes |
| `apt-get install` in a single RUN | Fewer layers; `rm -rf /var/lib/apt/lists/*` in same RUN |
| Use `--no-install-recommends` | Avoids pulling in optional packages (saves ~50-200 MB) |
| Set `ENV` in base stage | Inherited by all subsequent stages |
| Use `--mount=type=cache` with BuildKit | Pip/uv cache persisted across builds without adding to image |
| Multi-arch with `buildx` | Enables building `linux/amd64` from M-series Mac |

---

## .dockerignore

```
# Version control
.git
.gitignore

# Python artifacts
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
.venv/
venv/

# Tests and dev files
tests/
.pytest_cache/
.coverage
htmlcov/

# Docker artifacts
Dockerfile*
docker-compose*.yml
.dockerignore

# IDE and OS
.vscode/
.idea/
*.swp
.DS_Store

# CI/CD
.github/
.gitlab-ci.yml
```

---

## Docker Compose — Full Development Stack

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build:
      context: .
      target: runtime
      args:
        PYTHON_VERSION: "3.12"
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/appdb
      REDIS_URL: redis://redis:6379/0
      LOG_LEVEL: DEBUG
      DEBUG: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./src:/app/src:ro   # hot-reload (ro = read-only to prevent accidental writes)
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--reload", "--log-level", "debug"]
    restart: unless-stopped

  worker:
    build: { context: ., target: runtime }
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/appdb
      REDIS_URL: redis://redis:6379/0
    depends_on: [db, redis]
    command: ["python", "-m", "src.worker"]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command:
      - redis-server
      - --maxmemory 512mb
      - --maxmemory-policy allkeys-lru
      - --appendonly yes
    volumes:
      - redisdata:/data

  # Optional: local Kafka
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      CLUSTER_ID: "Mk3OEYBSD38oPmkdljPEoQ=="
    ports:
      - "9092:9092"

volumes:
  pgdata:
  redisdata:
```

---

## Image Size Reference

| Base Image | Size | Notes |
|-----------|------|-------|
| `python:3.12` | ~1.0 GB | Full Debian, all tools |
| `python:3.12-slim` | ~130 MB | Minimal Debian, no extras |
| `python:3.12-alpine` | ~55 MB | Musl libc — many wheels don't work |
| `gcr.io/distroless/python3-debian12` | ~50 MB | No shell, most secure |

**Recommendation:** Use `python:3.12-slim` for builder and runtime. Alpine breaks binary wheels (psycopg2, numpy, etc.) and requires musl-compatible builds.

---

## Build Commands Reference

```bash
# Standard build
docker build -t api:dev .

# Target a specific stage
docker build --target builder -t api:deps-only .

# Build with BuildKit (caching, secrets)
DOCKER_BUILDKIT=1 docker build -t api:latest .

# Multi-platform build and push
docker buildx create --use --name multiarch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag my-registry.io/api:1.0.0 \
  --push .

# Inspect layers and size
docker history api:latest
dive api:latest   # requires 'dive' tool

# Run with env file
docker run --env-file .env -p 8000:8000 api:latest

# Exec into running container (debug)
docker exec -it <container_id> /bin/bash

# Compose commands
docker compose up -d               # start in background
docker compose logs -f api         # follow logs
docker compose ps                  # status
docker compose down -v             # stop and remove volumes
docker compose build --no-cache    # rebuild from scratch
```

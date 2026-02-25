# Docker Reference -- Language-Agnostic Patterns

Complete Dockerfile patterns, optimization techniques, and Compose configurations for any technology stack.

---

## Multi-Stage Build Patterns

### Pattern 1: Compiled Language (Go, Rust, C++)

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.22 AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot AS runtime
COPY --from=builder /app /app
EXPOSE 8080
CMD ["/app"]
```

Key: compiled languages produce a single binary, enabling scratch or distroless runtime images.

### Pattern 2: Interpreted Language (Node.js, Python, Ruby)

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-slim AS builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --production
COPY src/ ./src/

FROM node:20-slim AS runtime
RUN useradd -r -u 1001 appuser
WORKDIR /app
COPY --from=builder /build/node_modules ./node_modules
COPY --from=builder /build/src ./src
USER appuser
EXPOSE 3000
CMD ["node", "src/index.js"]
```

Key: runtime still needs the language runtime, but build tools and dev dependencies stay in the builder stage.

### Pattern 3: Static Asset Build (Frontend)

```dockerfile
FROM node:20-slim AS builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.25-alpine AS runtime
COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Key: build tools produce static files; runtime is just a web server.

---

## Layer Optimization Rules

| Rule | Reason |
|------|--------|
| Copy dependency manifests before source code | Dependencies change less often; cache preserved on code changes |
| Combine `apt-get update && install` in a single RUN | Fewer layers; cache cleanup in same RUN |
| Use `--no-install-recommends` for apt | Avoids optional packages (saves 50-200 MB) |
| Set ENV in the base stage | Inherited by all subsequent stages |
| Use `--mount=type=cache` with BuildKit | Package manager cache persists across builds without being in the image |
| Order COPY by change frequency | Least-changing files first for maximum cache reuse |

### BuildKit Cache Mounts

```dockerfile
# Package manager caches (never baked into image)
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y build-essential

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

RUN --mount=type=cache,target=/root/.npm \
    npm ci
```

---

## .dockerignore Template

```
# Version control
.git
.gitignore

# Build artifacts and dependencies
node_modules/
dist/
build/
target/
out/
*.o
*.a

# Test and coverage
tests/
test/
__tests__/
coverage/
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
Thumbs.db

# CI/CD
.github/
.gitlab-ci.yml
.circleci/

# Documentation
*.md
LICENSE
docs/

# Environment files (prevent secret leakage)
.env
.env.*
```

---

## Docker Compose Patterns

### Multi-Service Development Stack

```yaml
services:
  app:
    build:
      context: .
      target: runtime
      args:
        BUILD_ENV: development
    ports: ["8080:8080"]
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/appdb
      REDIS_URL: redis://redis:6379
      LOG_LEVEL: debug
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
    volumes:
      - ./src:/app/src    # hot-reload in dev
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command:
      - redis-server
      - --maxmemory 256mb
      - --maxmemory-policy allkeys-lru
    volumes:
      - redisdata:/data

  # Message broker
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"     # AMQP
      - "15672:15672"   # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest

volumes:
  pgdata:
  redisdata:
```

### Compose Overrides for Environment Separation

```yaml
# docker-compose.yml -- base (production-like)
services:
  app:
    image: registry.example.com/app:latest
    ports: ["8080:8080"]

# docker-compose.override.yml -- auto-loaded for local dev
services:
  app:
    build: { context: ., target: runtime }
    volumes:
      - ./src:/app/src
    environment:
      DEBUG: "true"

# docker-compose.test.yml -- test environment
services:
  app:
    build: { context: ., target: runtime }
    command: ["run-tests"]
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/testdb
```

```bash
# Local dev (uses base + override automatically)
docker compose up

# Test environment
docker compose -f docker-compose.yml -f docker-compose.test.yml up

# Production-like
docker compose -f docker-compose.yml up
```

---

## Image Size Reference

| Image type | Typical size | Notes |
|-----------|-------------|-------|
| Full OS (ubuntu, debian) | 200-800 MB | All tools, easy debugging |
| Slim variants | 50-150 MB | Minimal OS, no extras |
| Alpine variants | 5-50 MB | Musl libc; some binaries incompatible |
| Distroless | 2-50 MB | No shell, no package manager, most secure |
| Scratch | 0 MB + binary | Only for statically linked binaries |

**Recommendations:**
- Use slim variants for most workloads (good balance of size and compatibility)
- Use distroless for security-critical services in production
- Use Alpine with caution (musl libc causes compatibility issues with some libraries)
- Use scratch only for single-binary Go/Rust applications

---

## Security Best Practices

| Practice | Implementation |
|----------|---------------|
| Non-root user | `RUN useradd -r -u 1001 appuser && USER appuser` |
| Read-only filesystem | `readOnlyRootFilesystem: true` in K8s securityContext |
| No privilege escalation | `allowPrivilegeEscalation: false` in K8s |
| Drop all capabilities | `capabilities: { drop: ["ALL"] }` in K8s |
| Scan images for CVEs | `trivy image`, `docker scout cves`, or Snyk |
| Pin base image digests | `FROM node:20-slim@sha256:abc123...` for reproducibility |
| Use COPY not ADD | ADD auto-extracts archives and fetches URLs (unexpected behavior) |
| No secrets in images | Use build secrets (`--mount=type=secret`) or runtime injection |

---

## Build Commands Reference

```bash
# Standard build
docker build -t app:dev .

# Target a specific stage
docker build --target builder -t app:deps-only .

# Build with BuildKit
DOCKER_BUILDKIT=1 docker build -t app:latest .

# Multi-platform build and push
docker buildx create --use --name multiarch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag registry.example.com/app:1.0.0 \
  --push .

# Inspect layers and size
docker history app:latest
dive app:latest

# Run with env file
docker run --env-file .env -p 8080:8080 app:latest

# Compose commands
docker compose up -d                # start in background
docker compose logs -f app          # follow logs
docker compose ps                   # status
docker compose down -v              # stop and remove volumes
docker compose build --no-cache     # rebuild from scratch
```

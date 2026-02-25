---
name: coding-cloud-python-knowledge:containers-orchestration
description: "Docker and Kubernetes reference for Python backend services: multi-stage Dockerfiles, slim images, pip/uv caching, Compose, K8s Deployments, Services, ConfigMaps, Secrets, health probes, resource limits, HPA, and Helm charts. Load when writing Dockerfiles, K8s manifests, or deployment configurations for Python services."
user-invocable: false
---

# Containers & Orchestration — Quick Reference

## Additional resources

- [docker-reference.md](docker-reference.md) — Dockerfile patterns, multi-stage builds, uv/pip optimization, Compose, image scanning
- [kubernetes-reference.md](kubernetes-reference.md) — Full manifest patterns: Deployment, Service, Ingress, ConfigMap, Secret, HPA, PodDisruptionBudget, Helm

---

## Dockerfile Quick Reference — Python Multi-Stage

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Builder stage — install dependencies into venv
FROM base AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Runtime stage — copy only venv and source
FROM base AS runtime
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY src/ ./src/
RUN useradd -r -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Key rules:**
- Always use `python:3.12-slim` (not full, not alpine — glibc required by many wheels)
- Virtual environment in a separate directory makes `COPY --from=builder` clean
- Run as non-root user (`useradd -r` = system user, no home dir)
- `--workers 1` with uvicorn inside K8s — scaling via pod replicas, not workers

---

## uv-Based Build (10x faster than pip)

```dockerfile
FROM ghcr.io/astral-sh/uv:0.5 AS uv
FROM python:3.12-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY src/ ./src/
RUN useradd -r -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Docker Compose — Local Development

```yaml
# docker-compose.yml
services:
  api:
    build: { context: ., target: runtime }
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/mydb
      REDIS_URL: redis://redis:6379
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
    volumes:
      - ./src:/app/src  # hot-reload in dev
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--reload"]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--maxmemory", "256mb", "--maxmemory-policy", "allkeys-lru"]

volumes: { pgdata: {} }
```

---

## Kubernetes Deployment Quick Reference

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels: { app: api }
spec:
  replicas: 3
  selector:
    matchLabels: { app: api }
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }  # zero-downtime
  template:
    metadata:
      labels: { app: api }
    spec:
      containers:
        - name: api
          image: my-registry/api:1.2.3
          ports: [{ containerPort: 8000 }]
          envFrom:
            - configMapRef: { name: api-config }
            - secretRef: { name: api-secrets }
          resources:
            requests: { cpu: "100m", memory: "128Mi" }
            limits: { cpu: "500m", memory: "512Mi" }
          livenessProbe:
            httpGet: { path: /health/live, port: 8000 }
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet: { path: /health/ready, port: 8000 }
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 3
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]  # drain connections
      terminationGracePeriodSeconds: 30
```

---

## K8s ConfigMap and Secret

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: api-config }
data:
  LOG_LEVEL: "INFO"
  REDIS_URL: "redis://redis-svc:6379"
  MAX_CONNECTIONS: "20"

---
# secret.yaml — base64 encoded values
apiVersion: v1
kind: Secret
metadata: { name: api-secrets }
type: Opaque
data:
  DATABASE_URL: cG9zdGdyZXNxbCsuLi4=  # base64(postgresql+asyncpg://...)
  SECRET_KEY: bXlzZWNyZXRrZXk=
```

**Production rule:** Use External Secrets Operator or Vault Agent to inject secrets from AWS Secrets Manager / GCP Secret Manager. Never commit base64 secrets to git.

---

## HPA Quick Reference

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: api-hpa }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 60 }
    - type: Resource
      resource:
        name: memory
        target: { type: Utilization, averageUtilization: 80 }
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0      # scale up immediately
      policies: [{ type: Pods, value: 4, periodSeconds: 15 }]
    scaleDown:
      stabilizationWindowSeconds: 300    # wait 5 min before scaling down
```

**Rules:**
- Always set `resources.requests.cpu` in the Deployment — HPA requires it
- Set `minReplicas: 2` for high availability
- `stabilizationWindowSeconds: 300` on scale-down prevents flapping

---

## Image Build Commands

```bash
# Build and tag
docker build --target runtime -t my-service:$(git rev-parse --short HEAD) .

# Multi-platform (for M1/M2 Mac → Linux amd64 clusters)
docker buildx build --platform linux/amd64 -t my-registry/api:latest --push .

# Scan for vulnerabilities
docker scout cves my-registry/api:latest

# Check image size
docker images my-service --format "{{.Repository}}:{{.Tag}}\t{{.Size}}"

# K8s apply
kubectl apply -f k8s/
kubectl rollout status deployment/api
kubectl rollout undo deployment/api   # rollback if needed
```

---
name: core-devops:containerization
description: "Docker and Kubernetes fundamentals: multi-stage builds, layer caching, minimal images, .dockerignore, Docker Compose, K8s Deployments, Services, ConfigMaps, Secrets, Ingress, health probes, resource limits, HPA. Load when writing Dockerfiles, K8s manifests, or container configurations."
user-invocable: false
---

# Containerization -- Quick Reference

## Additional resources

- [docker-reference.md](docker-reference.md) -- Dockerfile patterns, multi-stage builds, layer optimization, Compose, image scanning
- [kubernetes-reference.md](kubernetes-reference.md) -- Full manifest patterns: Deployment, Service, Ingress, ConfigMap, Secret, HPA, PDB, Helm

---

## Dockerfile Quick Reference -- Language-Agnostic Multi-Stage

```dockerfile
# syntax=docker/dockerfile:1
# --- Builder stage: install dependencies and compile ---
FROM <base-image> AS builder

WORKDIR /build
COPY <dependency-manifest> .
RUN <install-dependencies>

COPY src/ ./src/
RUN <compile-or-build>

# --- Runtime stage: minimal image with only what's needed ---
FROM <minimal-base-image> AS runtime

COPY --from=builder /build/output /app
RUN useradd -r -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app
EXPOSE <port>
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD <health-check-command>

CMD ["<entrypoint>"]
```

**Key rules:**
- Always use multi-stage builds -- builder has compilers/tools, runtime has only the binary/app
- Use slim or distroless base images for runtime (not full OS images)
- Run as non-root user (create a system user with `useradd -r`)
- Copy dependency manifests before source code to maximize layer caching
- Clean up package manager caches in the same RUN layer

---

## Docker Compose -- Local Development

```yaml
services:
  app:
    build: { context: ., target: runtime }
    ports: ["8080:8080"]
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/mydb
    depends_on:
      db: { condition: service_healthy }
    volumes:
      - ./src:/app/src    # hot-reload in dev

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

volumes: { pgdata: {} }
```

---

## Kubernetes Deployment Quick Reference

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  labels: { app: app }
spec:
  replicas: 3
  selector:
    matchLabels: { app: app }
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    metadata:
      labels: { app: app }
    spec:
      containers:
        - name: app
          image: registry.example.com/app:1.0.0
          ports: [{ containerPort: 8080 }]
          envFrom:
            - configMapRef: { name: app-config }
            - secretRef: { name: app-secrets }
          resources:
            requests: { cpu: "100m", memory: "128Mi" }
            limits: { cpu: "500m", memory: "512Mi" }
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet: { path: /ready, port: 8080 }
            initialDelaySeconds: 10
            periodSeconds: 5
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
      terminationGracePeriodSeconds: 30
```

---

## Health Probes

| Probe | Purpose | Failure action |
|-------|---------|----------------|
| Liveness | Is the process alive and not deadlocked? | K8s kills and restarts the pod |
| Readiness | Can the process serve traffic? | K8s removes pod from Service endpoints |
| Startup | Has the process finished initializing? | K8s waits before starting liveness/readiness checks |

**Rules:**
- Liveness: lightweight check (process is responsive)
- Readiness: check downstream dependencies (database, cache connections)
- Startup: use for slow-starting applications to avoid premature kills
- Never share the same endpoint for liveness and readiness

---

## Resource Limits

```yaml
resources:
  requests:     # guaranteed allocation; used by scheduler and HPA
    cpu: "100m"       # 0.1 CPU core
    memory: "128Mi"   # 128 MiB
  limits:       # hard ceiling; pod killed if exceeded (memory) or throttled (CPU)
    cpu: "500m"       # 0.5 CPU core
    memory: "512Mi"   # 512 MiB
```

**Rules:**
- Always set both `requests` and `limits`
- `requests.cpu` is required for HPA to function
- Set memory limits to 2-4x requests to allow burst
- CPU limits throttle (slow); memory limits kill (OOMKilled)
- Monitor actual usage and right-size based on metrics

---

## Image Build Commands

```bash
# Build and tag with git SHA
docker build --target runtime -t my-app:$(git rev-parse --short HEAD) .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t registry/app:latest --push .

# Scan for vulnerabilities
docker scout cves registry/app:latest
trivy image registry/app:latest

# K8s operations
kubectl apply -f k8s/
kubectl rollout status deployment/app
kubectl rollout undo deployment/app
```

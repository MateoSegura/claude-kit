# Python Cloud-Backend Workflow Patterns

## 1. New Service Setup

1. Create project structure:
   ```
   service-name/
   ├── src/service_name/
   │   ├── __init__.py
   │   ├── main.py          # FastAPI app with lifespan
   │   ├── config.py         # Pydantic Settings class
   │   ├── routes/           # Route modules
   │   ├── services/         # Business logic
   │   ├── models/           # Pydantic models
   │   └── repositories/     # Data access
   ├── tests/
   ├── proto/                # If gRPC
   ├── Dockerfile
   ├── pyproject.toml
   ├── requirements.txt      # Or use pyproject.toml with pip-tools
   └── k8s/                  # Kubernetes manifests
   ```
2. Initialize `pyproject.toml` with `ruff`, `mypy`, and `pytest` configuration sections.
3. Create `config.py` with `pydantic_settings.BaseSettings` for all environment variables.
4. Create `main.py` with FastAPI app, lifespan handler for startup/shutdown, and health endpoints.
5. Add `Dockerfile` with multi-stage build (builder + runtime).
6. Add `k8s/` with Deployment, Service, ConfigMap, and HorizontalPodAutoscaler manifests.
7. Verify: `ruff check .`, `mypy --strict .`, `pytest`.

## 2. Build and Lint

1. Install dependencies:
   ```bash
   python -m pip install -e ".[dev]"
   ```
2. Run formatter:
   ```bash
   ruff format .
   ```
3. Run linter with auto-fix:
   ```bash
   ruff check --fix .
   ```
4. Run type checker:
   ```bash
   mypy --strict src/
   # or: pyright
   ```
5. If proto files changed, regenerate:
   ```bash
   python -m grpc_tools.protoc -I proto/ \
     --python_out=src/service_name/pb \
     --grpc_python_out=src/service_name/pb \
     --pyi_out=src/service_name/pb \
     proto/*.proto
   ```
6. Fix any issues before proceeding to test.

## 3. Test

1. Run unit tests:
   ```bash
   pytest tests/unit/ -v --tb=short
   ```
2. Run integration tests (requires Docker for testcontainers):
   ```bash
   pytest tests/integration/ -v --tb=short
   ```
3. Run full suite with coverage:
   ```bash
   pytest --cov=src/service_name --cov-report=term-missing --cov-fail-under=80
   ```
4. For async tests, ensure `pytest-asyncio` is configured with `mode = "auto"` in `pyproject.toml`:
   ```toml
   [tool.pytest-asyncio]
   mode = "auto"
   ```
5. Review coverage report. Focus on untested business logic paths, not boilerplate.

## 4. Containerize

1. Build the image:
   ```bash
   docker build -t service-name:local .
   ```
2. Verify the image runs:
   ```bash
   docker run --rm -p 8000:8000 \
     -e DATABASE_URL=sqlite:///dev.db \
     service-name:local
   ```
3. Check image size (should be under 200MB for a typical Python service):
   ```bash
   docker images service-name:local --format "{{.Size}}"
   ```
4. Scan for vulnerabilities:
   ```bash
   docker scout cves service-name:local
   # or: trivy image service-name:local
   ```
5. Tag for registry push:
   ```bash
   docker tag service-name:local registry.example.com/service-name:$(git rev-parse --short HEAD)
   docker push registry.example.com/service-name:$(git rev-parse --short HEAD)
   ```

## 5. Deploy to Kubernetes

1. Validate manifests:
   ```bash
   kubectl apply --dry-run=client -f k8s/
   ```
2. Apply to target namespace:
   ```bash
   kubectl apply -f k8s/ -n target-namespace
   ```
3. Watch rollout:
   ```bash
   kubectl rollout status deployment/service-name -n target-namespace --timeout=120s
   ```
4. Verify health:
   ```bash
   kubectl get pods -n target-namespace -l app.kubernetes.io/name=service-name
   kubectl logs -n target-namespace -l app.kubernetes.io/name=service-name --tail=50
   ```
5. Check readiness:
   ```bash
   kubectl exec -n target-namespace deploy/service-name -- \
     python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/ready').read())"
   ```
6. If rollout fails, check events and rollback:
   ```bash
   kubectl describe deployment/service-name -n target-namespace
   kubectl rollout undo deployment/service-name -n target-namespace
   ```

## 6. Add a Resilience Pattern (Circuit Breaker / Retry)

1. Identify the external dependency call (HTTP, gRPC, database).
2. Wrap the call with a retry policy using `tenacity`:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=0.5, max=10),
       retry=retry_if_exception_type(httpx.TransportError),
   )
   async def call_external_service(client: httpx.AsyncClient, url: str) -> dict:
       response = await client.get(url, timeout=5.0)
       response.raise_for_status()
       return response.json()
   ```
3. For circuit breakers, use `pybreaker` or implement a lightweight state machine:
   - Closed (normal) -> Open (after N consecutive failures) -> Half-Open (after cooldown)
4. Always set explicit timeouts on every external call -- never rely on library defaults.
5. Add metrics: count retries, record circuit state transitions, histogram of call durations.
6. Test the pattern: use `pytest` fixtures that simulate transient failures and verify retry/circuit behavior.

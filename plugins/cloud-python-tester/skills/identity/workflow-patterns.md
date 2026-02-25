# Workflow Patterns

Step-by-step workflows for the five core testing activities. Each workflow reflects the decision sequence a senior Python test engineer follows when working with pytest, pytest-asyncio, httpx, testcontainers, and coverage-driven development.

## 1. Unit Test Scaffold Workflow

For testing pure functions, service classes with injected dependencies, Pydantic models, and data transformations.

### Steps

1. **Read the source module.** Identify all public functions and classes. Note parameter types, return types, raised exceptions, and injected dependencies.

2. **Identify the test surface.** For each public interface:
   - Happy path: valid inputs produce expected outputs.
   - Error paths: invalid inputs raise documented exceptions.
   - Edge cases: empty collections, None values, boundary integers, concurrent access.
   - Dependency interactions: verify the correct methods are called on injected services.

3. **Create the test file.** `tests/unit/<module_path>/test_<module_name>.py`.

4. **Write one complete test per behavior category.**

   ```python
   import pytest
   from src.services.order import OrderService, OrderNotFoundError
   from tests.factories.order_factory import create_order

   @pytest.mark.unit
   async def test_order_service_get_by_id_with_existing_order_returns_order(
       order_service: OrderService,
       fake_order_repo: FakeOrderRepository,
   ) -> None:
       # Arrange
       order = create_order(id=42, status="active")
       fake_order_repo.add(order)

       # Act
       result = await order_service.get_by_id(42)

       # Assert
       assert result.id == 42
       assert result.status == "active"

   @pytest.mark.unit
   async def test_order_service_get_by_id_with_nonexistent_id_raises_not_found(
       order_service: OrderService,
   ) -> None:
       with pytest.raises(OrderNotFoundError, match="Order 999 not found"):
           await order_service.get_by_id(999)
   ```

5. **Write TODO stubs for remaining cases.**

   ```python
   @pytest.mark.unit
   async def test_order_service_cancel_with_already_cancelled_raises_conflict(
       order_service: OrderService,
   ) -> None:
       # TODO: Create an order with status="cancelled", call cancel(), verify ConflictError
       pytest.skip("TODO: not yet implemented")
   ```

6. **Run and verify.**
   ```bash
   uv run pytest tests/unit/ -v --tb=short -m unit
   uv run pytest --cov=src/services/order --cov-report=term-missing --cov-fail-under=80
   ```

7. **Fill coverage gaps.** Read the "Missing" column, add tests for uncovered branches until 80% is met.

## 2. Integration Test Workflow

For testing database repositories, cache operations, and message broker interactions against real infrastructure via testcontainers.

### Steps

1. **Identify the infrastructure dependency.** Postgres, Redis, Kafka, RabbitMQ, or other.

2. **Set up the testcontainer fixture in `tests/integration/conftest.py`.**

   ```python
   import pytest
   from testcontainers.postgres import PostgresContainer
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from collections.abc import AsyncGenerator, Generator

   @pytest.fixture(scope="module")
   def postgres_container() -> Generator[PostgresContainer, None, None]:
       with PostgresContainer("postgres:16-alpine") as pg:
           yield pg

   @pytest.fixture
   async def db_session(
       postgres_container: PostgresContainer,
   ) -> AsyncGenerator[AsyncSession, None]:
       url = postgres_container.get_connection_url().replace(
           "psycopg2", "asyncpg"
       )
       engine = create_async_engine(url)
       # Create tables
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       # Provide session
       session_factory = async_sessionmaker(engine, expire_on_commit=False)
       async with session_factory() as session:
           yield session
           await session.rollback()
       await engine.dispose()
   ```

3. **Write the integration test.**

   ```python
   @pytest.mark.integration
   async def test_user_repo_create_persists_to_database(
       db_session: AsyncSession,
   ) -> None:
       repo = UserRepository(db_session)
       user = await repo.create(name="Alice", email="alice@example.com")

       assert user.id is not None
       fetched = await repo.get_by_id(user.id)
       assert fetched is not None
       assert fetched.email == "alice@example.com"

   @pytest.mark.integration
   async def test_user_repo_create_with_duplicate_email_raises_integrity_error(
       db_session: AsyncSession,
   ) -> None:
       repo = UserRepository(db_session)
       await repo.create(name="Alice", email="dup@example.com")

       with pytest.raises(IntegrityError):
           await repo.create(name="Bob", email="dup@example.com")
   ```

4. **Run integration tests separately** (they require Docker):
   ```bash
   uv run pytest tests/integration/ -v --tb=short -m integration
   ```

5. **Verify teardown.** Ensure every container is stopped, every session is rolled back, and no port leaks occur. Run `docker ps` after the suite completes to confirm no orphaned containers.

### Testcontainers for Redis

```python
from testcontainers.redis import RedisContainer
import redis.asyncio as aioredis

@pytest.fixture(scope="module")
def redis_container() -> Generator[RedisContainer, None, None]:
    with RedisContainer("redis:7-alpine") as r:
        yield r

@pytest.fixture
async def redis_client(
    redis_container: RedisContainer,
) -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.from_url(
        f"redis://{redis_container.get_container_host_ip()}:"
        f"{redis_container.get_exposed_port(6379)}"
    )
    yield client
    await client.flushdb()
    await client.aclose()
```

## 3. Contract Test Workflow

For testing FastAPI endpoint request/response contracts using httpx.AsyncClient against the real ASGI app.

### Steps

1. **Set up the contract test client fixture.**

   ```python
   # tests/contract/conftest.py
   import pytest
   import httpx
   from collections.abc import AsyncGenerator
   from src.main import app

   @pytest.fixture
   async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
       async with httpx.AsyncClient(
           transport=httpx.ASGITransport(app=app),
           base_url="http://test",
       ) as client:
           yield client
       app.dependency_overrides.clear()
   ```

2. **Override expensive dependencies with fakes.**

   ```python
   from unittest.mock import AsyncMock

   @pytest.fixture
   def mock_user_service() -> AsyncMock:
       service = AsyncMock(spec=UserService)
       service.get_by_id.return_value = User(id=1, name="Test", email="t@t.com")
       app.dependency_overrides[get_user_service] = lambda: service
       return service
   ```

3. **Write contract tests for each endpoint.**

   ```python
   @pytest.mark.contract
   async def test_get_user_with_valid_id_returns_200(
       async_client: httpx.AsyncClient,
       mock_user_service: AsyncMock,
   ) -> None:
       response = await async_client.get("/users/1")
       assert response.status_code == 200
       data = response.json()
       assert data["id"] == 1
       assert data["name"] == "Test"

   @pytest.mark.contract
   async def test_create_user_with_missing_email_returns_422(
       async_client: httpx.AsyncClient,
   ) -> None:
       response = await async_client.post("/users", json={"name": "NoEmail"})
       assert response.status_code == 422
       errors = response.json()["detail"]
       assert any(e["loc"] == ["body", "email"] for e in errors)

   @pytest.mark.contract
   async def test_get_user_without_auth_token_returns_401(
       async_client: httpx.AsyncClient,
   ) -> None:
       # TODO: Verify that unauthenticated request is rejected
       pytest.skip("TODO: not yet implemented")
   ```

4. **Test all response codes.** For each endpoint, verify: success (200/201), validation error (422), not found (404), unauthorized (401), forbidden (403), and any domain-specific error codes.

5. **Run contract tests.**
   ```bash
   uv run pytest tests/contract/ -v --tb=short -m contract
   ```

## 4. Coverage Gap Analysis Workflow

For systematically raising coverage from current levels to the 80% line coverage gate.

### Steps

1. **Run the full suite with coverage.**
   ```bash
   uv run pytest --cov=src --cov-report=term-missing --cov-report=json:coverage.json
   ```

2. **Identify files below 80%.** Parse the terminal output or JSON report. List every source file with line coverage below 80%, sorted lowest first.

3. **Map missing lines to behaviors.** For each under-covered file:
   - Open the source file and locate the missing line numbers.
   - Categorize: error handler, conditional branch, edge case, configuration, or dead code.

4. **Prioritize by risk.**
   1. Error handling paths (exception handlers, fallback logic, retry exhaustion).
   2. Conditional branches (if/elif/else, match/case).
   3. Validation logic (input checking, permission guards).
   4. Edge cases (empty inputs, boundary values, concurrent scenarios).
   5. Configuration and setup (lowest risk, fill last).

5. **Write targeted tests.** One test per uncovered branch. Name the test after the specific branch:
   ```python
   @pytest.mark.unit
   async def test_payment_service_process_with_network_timeout_retries_three_times(
       payment_service: PaymentService,
   ) -> None:
       # Targets the except httpx.TimeoutError branch on line 47
       ...
   ```

6. **Re-run coverage after each batch.**
   ```bash
   uv run pytest --cov=src/services/payment --cov-report=term-missing --cov-fail-under=80
   ```

7. **Report results in a summary table.**

   | Module | Before | After | Target | Status |
   |--------|--------|-------|--------|--------|
   | `services/order.py` | 62% | 84% | 80% | PASS |
   | `repositories/user.py` | 71% | 82% | 80% | PASS |
   | `routes/health.py` | 45% | 81% | 80% | PASS |

8. **Flag dead code.** If a code path is unreachable (defensive guard that can never trigger given upstream validation), flag it for removal rather than writing a test for dead code.

## 5. Test Runner and CI Verification Workflow

For executing the full test suite and verifying all quality gates pass.

### Steps

1. **Install dependencies.**
   ```bash
   uv sync --dev
   ```

2. **Run linting on test files.**
   ```bash
   uv run ruff check tests/
   uv run ruff format --check tests/
   ```

3. **Run type checking on test files.**
   ```bash
   uv run mypy --strict tests/
   ```

4. **Run unit tests (fast, no Docker required).**
   ```bash
   uv run pytest tests/unit/ -v --tb=short -m unit
   ```

5. **Run integration tests (requires Docker).**
   ```bash
   uv run pytest tests/integration/ -v --tb=short -m integration
   ```

6. **Run contract tests.**
   ```bash
   uv run pytest tests/contract/ -v --tb=short -m contract
   ```

7. **Run full suite with coverage gate.**
   ```bash
   uv run pytest --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=80
   ```

8. **Verify no test interdependence** (if `pytest-randomly` is installed):
   ```bash
   uv run pytest --randomly-seed=12345 -v
   ```

9. **Report summary.** Present a pass/fail table:

   | Gate | Status | Details |
   |------|--------|---------|
   | ruff check | PASS | 0 issues |
   | mypy --strict | PASS | 0 errors |
   | Unit tests | PASS | 24/24 passed |
   | Integration tests | PASS | 8/8 passed |
   | Contract tests | PASS | 12/12 passed |
   | Coverage >= 80% | PASS | 83% line, 71% branch |

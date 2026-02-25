---
name: coding-cloud-python-tester:coverage-report
allowed-tools: Read, Glob, Grep, Bash, Task
description: Run pytest with branch coverage reporting, identify uncovered lines and branches prioritized by risk, generate an actionable gap analysis with specific test suggestions per gap, and compare against the 80% line coverage gate.
---

# coverage-report

Deep coverage gap analysis. Runs pytest with branch-level coverage, identifies every uncovered line and branch, prioritizes gaps by risk (async error paths, exception handlers, edge cases), and generates concrete test suggestions for each gap.

## Workflow

### Step 1 — Read project configuration

Read the following to understand the project's coverage setup:
- `pyproject.toml` — `[tool.coverage.run]`, `[tool.coverage.report]`, `[tool.pytest.ini_options]`
- `pytest.ini`
- `.coveragerc` if present

Determine:
- `SRC_DIR`: source directory to measure (from config or user input)
- `TEST_DIR`: test root (default `tests/`)
- `OMIT_PATTERNS`: files to omit (migrations, `__init__.py`, etc.)
- `COVERAGE_THRESHOLD`: gate value (default 80)

If the user specified a target module (e.g., `src/orders/`), store it as `TARGET_MODULE`. Otherwise use `SRC_DIR`.

### Step 2 — Spawn coverage-analyzer agent

Spawn the `coverage-analyzer` agent with full context.

Pass:
- `SRC_DIR`: source root for `--cov`
- `TEST_DIR`: pytest test root
- `TARGET_MODULE`: specific module to analyze (or empty for all)
- `OMIT_PATTERNS`: comma-separated list of file globs to omit
- `COVERAGE_THRESHOLD`: the gate value

The coverage-analyzer will execute:

```bash
pytest {TEST_DIR} \
  --cov={SRC_DIR} \
  --cov-branch \
  --cov-report=term-missing:skip-covered \
  --cov-report=json:coverage.json \
  --cov-report=html:htmlcov \
  --tb=no \
  -q
```

The agent then reads `coverage.json` to extract:
- Per-file coverage percentages
- Missing line numbers per file
- Branch coverage data (executed branches vs. total branches)
- Partially covered branches (one direction taken, other not)

### Step 3 — Risk-prioritized gap analysis

The coverage-analyzer classifies each uncovered region by risk tier:

**Tier 1 — Critical (must test):**
- Exception handlers and error branches (`except`, `raise`, error returns)
- Async code paths in `async def` functions with `await` expressions
- Authentication and authorization branches
- Data validation failure paths
- Any code guarded by `if TYPE_CHECKING:` that still runs at test time

**Tier 2 — High (should test):**
- Retry logic and circuit breaker branches
- Configuration-dependent branches (`if settings.FEATURE_X`)
- Pagination edge cases (empty results, last page)
- Background task callbacks

**Tier 3 — Medium (worth testing):**
- Logging branches (`if logger.isEnabledFor(...)`)
- Fallback/default value paths
- Optional parameter handling

**Tier 4 — Low (skip if coverage already adequate):**
- `__repr__` and `__str__` methods
- Type annotation branches
- Import guard blocks (`if __name__ == "__main__"`)

For each gap, the agent reads the surrounding source code (using Read on the source file with line offset and limit) to generate a specific test suggestion.

### Step 4 — Format the coverage report

Present the report in three sections:

**Section 1: Coverage Gate Status**

```
Coverage Gate: 80%
==================
Overall line coverage:   <N>%  [PASS / FAIL]
Overall branch coverage: <N>%

Files below 80% threshold:
  src/orders/service.py      67%  (missing: 23/34 lines)
  src/payments/processor.py  71%  (missing: 8/11 lines)
  src/auth/middleware.py     54%  (missing: 15/28 lines)
```

**Section 2: Prioritized Gap List**

```
GAP ANALYSIS — 12 gaps found
=============================

[TIER 1 - CRITICAL] src/orders/service.py lines 89-94
  Code: except IntegrityError as e: raise OrderConflictError(...)
  Risk: Database conflict error path never tested
  Suggested test:
    async def test_create_order_duplicate_raises_conflict(db_session, async_client):
        # Insert the order once, then attempt to insert again
        # Assert HTTP 409 or OrderConflictError is raised

[TIER 1 - CRITICAL] src/auth/middleware.py lines 34-38
  Code: if token is None: return JSONResponse(status_code=401, ...)
  Risk: Unauthenticated request path untested
  Suggested test:
    async def test_request_without_token_returns_401(async_client):
        response = await async_client.get("/protected-route")
        assert response.status_code == 401

[TIER 2 - HIGH] src/payments/processor.py lines 112-118
  Code: for attempt in range(self.max_retries): ...
  Risk: Retry logic branch — only first attempt path is tested
  Suggested test:
    async def test_payment_retries_on_transient_error(mock_gateway):
        mock_gateway.charge.side_effect = [TransientError(), TransientError(), success_response]
        result = await processor.charge(amount=100)
        assert mock_gateway.charge.call_count == 3
```

**Section 3: Action Plan**

```
Action Plan
===========
Quick wins (< 30 min each):
  1. Add test for unauthenticated request in test_auth.py
  2. Add test for empty paginated response in test_orders.py
  3. Add test for duplicate order conflict in test_orders.py

Estimated coverage gain if all Tier 1 + Tier 2 gaps are addressed:
  src/orders/service.py:      67% → ~88%
  src/payments/processor.py:  71% → ~85%
  src/auth/middleware.py:     54% → ~91%
  Overall:                    <N>% → ~<N+X>%

Run /scaffold-tests to generate test stubs for the gaps above.
```

### Error handling

- If `coverage.json` is missing after the run: re-run with `--cov-report=json` explicitly and retry once.
- If the coverage-analyzer agent fails: show the raw pytest coverage output from stdout as a fallback.
- If no tests are collected: warn that the test suite may be empty and suggest running `/scaffold-tests` first.
- If `SRC_DIR` does not exist: ask the user for the correct source directory.
- If branch coverage data is unavailable (no `--cov-branch` in config): note this and add `branch = True` under `[tool.coverage.run]` in `pyproject.toml` as a recommendation.

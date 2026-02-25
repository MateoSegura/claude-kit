---
name: cloud-python-tester:run-tests
allowed-tools: Read, Glob, Grep, Bash, Task
description: Execute pytest with coverage reporting, support for targeting specific files or markers, and a pass/fail summary with the 80% line coverage gate and file:line failure references.
---

# run-tests

Execute the test suite using pytest with coverage. Supports targeting a specific file, test marker subset, or the full suite. Reports results with coverage percentage against the 80% gate and precise failure references.

## Workflow

### Step 1 — Resolve run configuration

Read the following files if they exist to understand project configuration:
- `pyproject.toml` — look for `[tool.pytest.ini_options]`, `[tool.coverage.run]`, `[tool.coverage.report]`
- `pytest.ini` — fallback configuration
- `setup.cfg` — legacy fallback

Determine:
- `TEST_DIR`: root directory for tests (default: `tests/`)
- `SRC_DIR`: source directory to measure coverage on (default: `src/` or the top-level package directory)
- `COVERAGE_THRESHOLD`: from config or default `80`

If the user specified a target (file path, module pattern, or marker expression), capture it as `TARGET`.

### Step 2 — Spawn test-runner agent

Spawn the `test-runner` agent with all execution context.

Pass:
- `TEST_DIR`: resolved test root
- `SRC_DIR`: source directory for `--cov` flag
- `TARGET`: specific file, marker expression, or empty for full suite
- `COVERAGE_THRESHOLD`: the pass/fail gate value (default 80)
- `EXTRA_ARGS`: any additional pytest flags the user specified (e.g., `-x`, `-v`, `--tb=short`)

The test-runner will construct and execute one of these commands depending on `TARGET`:

```bash
# Full suite
pytest {TEST_DIR} --cov={SRC_DIR} --cov-report=term-missing --cov-report=json -v

# Specific file
pytest {TARGET} --cov={SRC_DIR} --cov-report=term-missing --cov-report=json -v

# Marker filter
pytest {TEST_DIR} -m "{TARGET}" --cov={SRC_DIR} --cov-report=term-missing --cov-report=json -v
```

The test-runner captures:
- Exit code (0 = all passed, 1 = failures, 2 = interrupted, 3 = internal error, 4 = command-line error, 5 = no tests collected)
- Full stdout/stderr output
- `coverage.json` if generated (typically at `.coverage` or `coverage.json`)

### Step 3 — Parse and format results

After the test-runner completes, parse its output to produce a structured report.

**Test result summary:**

```
Test Results
============
Passed:  <N>
Failed:  <N>
Skipped: <N>
Errors:  <N>
Duration: <Xs>
```

**Failure details** (one block per failure):
```
FAILED tests/test_orders.py::test_create_order_missing_field
  File: tests/test_orders.py, line 47
  AssertionError: Expected 422, got 200

  Relevant code:
    45:  response = await client.post("/orders", json={})
    46:  assert response.status_code == 422
```

For each failure, use Grep to locate the exact source line and include a 3-line context snippet.

**Coverage summary:**

```
Coverage Report
===============
Overall:  <N>%  [PASS | FAIL — below 80% gate]

Module coverage:
  src/orders/router.py     92%
  src/orders/service.py    78%  <-- below threshold
  src/auth/dependencies.py 45%  <-- below threshold

Run /coverage-report for gap analysis and test suggestions.
```

### Step 4 — Determine exit status

- If all tests pass AND coverage >= threshold: report success clearly.
- If tests fail: list every failure with `file:line` reference. Do NOT truncate.
- If coverage < threshold: flag modules below threshold. Suggest running `/coverage-report`.
- If exit code 5 (no tests collected): warn that the target path or marker matched nothing and suggest checking the target expression.

### Error handling

- If pytest is not installed: output `pip install pytest pytest-cov` and stop.
- If the test-runner agent fails (not a test failure, but an agent error): show the error and offer Retry.
- If `coverage.json` is missing after a successful run: fall back to parsing the terminal coverage table from stdout.
- If `SRC_DIR` is not found: ask the user to specify the source directory explicitly.

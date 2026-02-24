---
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
description: Generate a complete test scaffold for a target Python module or service, including conftest.py fixtures and pytest-marked test files with one representative test per behavior category and TODOs for remaining cases.
---

# scaffold-tests

Generate a complete pytest scaffold for a target Python module or cloud service. Produces conftest.py with protocol-appropriate fixtures plus one representative test per behavior category, with `# TODO` markers for remaining cases.

## Workflow

### Step 1 — Locate and read the target

Identify which module or service to scaffold tests for. The user may pass a path, a module name, or describe a service. Use Read, Glob, and Grep to:

1. Find the target source file(s) — look for `*.py` files matching the user's description.
2. Read the main module or entrypoint.
3. Scan for FastAPI `app`, gRPC servicer classes, Celery tasks, aiokafka consumers/producers, and NATS subscriptions.
4. Read any existing `conftest.py` and `pyproject.toml` or `pytest.ini` to understand the current test configuration.

If the user did not specify a target, ask: "Which module, service, or file should I generate tests for?"

### Step 2 — Identify testable behaviors

Analyze the source to produce a behavior inventory. For each public function, route, RPC method, task, or event handler, classify it as one of:

| Category | Pytest Marker | Examples |
|----------|---------------|---------|
| Unit — pure logic | `@pytest.mark.unit` | validators, transformers, business rules |
| Integration — DB/cache | `@pytest.mark.integration` | repo methods, cache reads/writes |
| Integration — HTTP | `@pytest.mark.asyncio, @pytest.mark.integration` | FastAPI route handlers |
| Integration — gRPC | `@pytest.mark.asyncio, @pytest.mark.integration` | gRPC servicer methods |
| Integration — messaging | `@pytest.mark.asyncio, @pytest.mark.integration` | Kafka/NATS/Celery handlers |
| Slow / external | `@pytest.mark.slow` | full end-to-end with real containers |

Output: a numbered behavior list with category and priority (high/medium/low).

### Step 3 — Spawn fixture-composer (first)

Fixtures must exist before test files reference them. Spawn the `fixture-composer` agent synchronously before spawning `test-writer`.

Pass the agent:
- `TARGET_MODULE`: path to the source file being tested
- `BEHAVIOR_INVENTORY`: the categorized behavior list from Step 2
- `EXISTING_CONFTEST`: content of any existing conftest.py (or empty string)
- `OUTPUT_PATH`: path for the conftest.py to write (typically `tests/conftest.py` or alongside the source)

The fixture-composer will produce:
- `conftest.py` with pytest fixtures for all protocols detected (httpx.AsyncClient, Testcontainers for Postgres/Redis/Kafka, in-process gRPC server, NATS test server, Celery eager mode)
- Correct `pytest.ini` or `pyproject.toml` `[tool.pytest.ini_options]` block with `asyncio_mode = "auto"` and marker registrations

Wait for the fixture-composer to complete before proceeding.

### Step 4 — Spawn test-writer (second)

After fixture-composer completes, spawn the `test-writer` agent to generate the actual test files.

Pass the agent:
- `TARGET_MODULE`: path to the source file being tested
- `BEHAVIOR_INVENTORY`: the categorized behavior list
- `CONFTEST_PATH`: path to the conftest.py written in Step 3
- `CONFTEST_CONTENT`: full content of the conftest.py just written
- `OUTPUT_DIR`: directory to write test file(s)

The test-writer must:
- Produce one test file per logical unit (e.g., `test_user_router.py`, `test_order_service.py`)
- Include exactly one concrete test implementation per behavior category
- Add `# TODO: test <behavior description>` stubs for all remaining behaviors in each category
- Apply correct pytest markers on every test function (`@pytest.mark.asyncio`, `@pytest.mark.integration`, etc.)
- Use fixtures from conftest.py by name — no inline setup

### Step 5 — Verify and summarize

After both agents complete:

1. Use Glob to confirm all expected files exist.
2. Read the generated test files and conftest.py.
3. Run a quick syntax check: `python -m py_compile <each test file>` via Bash.
4. Present a summary table:

```
Files generated:
  tests/conftest.py          — <N> fixtures
  tests/test_<module>.py     — <N> tests + <M> TODOs

Markers applied: asyncio, integration, unit
Fixtures defined: async_client, db_session, kafka_container, ...

Next steps:
  Run: pytest tests/ -m unit
  Run: pytest tests/ -m integration
  Run: /run-tests to execute with coverage
```

### Error handling

- If fixture-composer fails: show the error, offer Retry or Skip (skip generates test file without fixture references, marking all fixtures as `# TODO: add fixture`).
- If test-writer fails: show the error, offer Retry or Skip.
- If py_compile fails on any generated file: display the syntax error and offer to re-spawn test-writer with the error as additional context.
- If no testable behaviors are found: report this clearly and ask the user to confirm the target path.

# coding-cloud-python-tester

> **Role:** Tester · **Version:** 0.0.2

Python cloud-backend tester — writes and runs unit, integration (testcontainers), and API contract tests with pytest-asyncio, 80% coverage gating, and scaffold-first generation.

```bash
claude-kit --kit coding-cloud-python-tester
# or load the full team:
claude-kit --kit coding-cloud-python
```

**Companion auto-loaded:** `coding-cloud-python-knowledge` (asyncio, FastAPI, gRPC, Docker, Kubernetes, design patterns)

---

## Agents

| Agent | Description |
|-------|-------------|
| `test-writer` | Writes pytest test files for Python cloud services: unit tests, integration tests, and API contract tests. Use when the user needs new test files created, test coverage for untested modules, or test scaffolding with representative examples and TODOs for expansion. |
| `fixture-composer` | Creates and manages pytest conftest.py files, factory fixtures, testcontainers fixtures, and httpx.AsyncClient fixtures. Use when the user needs shared test infrastructure, fixture scope management, or conftest.py files for a test directory. |
| `contract-validator` | Generates and validates API contract tests for REST, gRPC, and event-driven interfaces. Verifies backward compatibility of schemas, detects breaking changes in API surfaces, and ensures protocol compliance. Use when the user needs contract tests, schema validation, or backward compatibility checks. |
| `coverage-analyzer` | Parses pytest-cov output and identifies untested modules, ranks coverage gaps by impact, and produces actionable recommendations for test prioritization. READ-ONLY agent that analyzes coverage data but does not write test files. Use when the user wants to understand test coverage, find gaps, or prioritize what to test next. |
| `test-runner` | Executes pytest with appropriate markers, flags, and environment setup. Handles Docker prerequisite checks for testcontainers, parallel execution with pytest-xdist, structured failure output, and retry logic. READ-ONLY agent that runs tests but does not modify test files. Use when the user wants to run tests, diagnose test failures, or execute specific test suites. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-cloud-python-tester:scaffold-tests` | Generate a complete pytest scaffold for a target Python module or service, including conftest.py fixtures and pytest-marked test files with one representative test per behavior category and TODOs for remaining cases. |
| `/coding-cloud-python-tester:run-tests` | Execute the test suite using pytest with coverage. Supports targeting a specific file, test marker subset, or the full suite. Reports results with coverage percentage against the 80% gate and precise failure references. |
| `/coding-cloud-python-tester:coverage-report` | Deep coverage gap analysis. Runs pytest with branch-level coverage, identifies every uncovered line and branch, prioritizes gaps by risk, and generates concrete test suggestions for each gap. |

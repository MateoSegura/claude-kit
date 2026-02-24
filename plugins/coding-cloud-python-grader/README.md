# coding-cloud-python-grader

> **Role:** Grader · **Version:** 0.0.3

Blind quantitative code grading for Python cloud-backend services. Scores code across 8 weighted dimensions: async correctness, type safety, security, observability, API contracts, performance risk, test coverage, and K8s hygiene.

```bash
claude-kit --kit coding-cloud-python-grader
# or load the full team:
claude-kit --kit coding-cloud-python
```

**Companion auto-loaded:** `coding-cloud-python-knowledge` (Python cloud-backend domain reference for review context)

---

## Agents

| Agent | Description |
|-------|-------------|
| `review-orchestrator` | Orchestrates parallel code grading across 8 review dimensions for cloud Python projects. Use when the user invokes the grading command or requests a code review. Identifies target files, determines applicable dimensions, fans out to dimension-specific reviewers, collects results, and spawns the score-synthesizer to produce a unified report. |
| `async-correctness-reviewer` | Evaluates async/await correctness in cloud Python code. Checks TaskGroup usage, detects bare create_task() calls, sync-in-async anti-patterns, missing timeouts, cancellation handling, asyncio.gather error propagation, and async context manager correctness. Use for the async-correctness grading dimension. |
| `type-safety-reviewer` | Evaluates type safety and static analysis compliance in cloud Python code. Checks mypy strict-mode readiness, Pydantic v2 model correctness, generic type usage, Protocol/ABC conformance, and unjustified type: ignore comments. Use for the type-safety grading dimension. |
| `security-reviewer` | Evaluates security posture of cloud Python applications. Checks input validation, SQL injection resistance, hardcoded secrets, CORS/CSP configuration, authentication patterns, rate limiting, dependency vulnerabilities, and Dockerfile security. Use for the security grading dimension. |
| `observability-reviewer` | Evaluates observability instrumentation in cloud Python services. Checks OpenTelemetry (OTel) tracing, structlog structured logging, Prometheus metrics exposition, health check endpoints, error reporting integration, and trace context propagation across service boundaries. Use for the observability grading dimension. |
| `api-contracts-reviewer` | Evaluates API design quality for cloud Python services. Reviews REST endpoints against Google API Design Guide, gRPC service hygiene, Pydantic request/response model completeness, error response standardization (RFC 7807), pagination patterns, and API versioning strategy. Use for the api-contracts grading dimension. |
| `performance-risk-reviewer` | Evaluates performance risks in cloud Python services. Detects N+1 query patterns, missing database indexes, unbounded result sets, absent connection pooling, synchronous blocking in async paths, missing caching layers, and pagination gaps. Use for the performance-risk grading dimension. |
| `test-coverage-reviewer` | Evaluates test quality and coverage in cloud Python projects. Reviews test existence for critical paths, fixture design, async test patterns (pytest-asyncio), mock isolation, edge case coverage, factory patterns (factory_boy), and test organization. Use for the test-coverage grading dimension. |
| `k8s-hygiene-reviewer` | Evaluates Kubernetes deployment hygiene and container best practices for cloud Python services. Reviews Dockerfile multi-stage builds, non-root execution, resource limits, liveness/readiness probes, ConfigMap and Secret usage, PodDisruptionBudgets, and NetworkPolicy definitions. Use for the k8s-hygiene grading dimension. |
| `score-synthesizer` | Synthesizes findings from all dimension reviewers into a unified grading report. Applies severity weighting, calculates per-dimension and overall weighted scores, generates structured findings JSON, formats inline code annotations, and produces an executive summary. Use after all dimension reviewers have completed their analysis. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-cloud-python-grader:grade` | Full-service on-demand code review. Accepts a service path or file glob, grades all 8 dimensions via parallel subagents, and produces a unified report with weighted final score, per-dimension scores, findings list, and inline annotations. |
| `/coding-cloud-python-grader:grade-diff` | Fast diff-scoped pre-commit review. Accepts a git diff range (default: staged changes), scopes grading to changed files and their direct dependents, and produces a focused report suitable for pre-commit or PR review gates. |

---

## Grading Dimensions

8 weighted dimensions: async correctness (20%), type safety (15%), security (20%), observability (10%), API contracts (15%), performance risk (10%), test coverage (5%), K8s hygiene (5%).

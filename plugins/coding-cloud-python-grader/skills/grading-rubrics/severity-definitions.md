# Severity Definitions — Grading Framework

Severity criteria, examples, scoring weight rationale, and escalation rules for the coding-cloud-python-grader framework.

---

## Severity Levels

### Critical

**Definition**: A finding that, if unaddressed, will cause data loss, a security breach, a hard crash in production, or service-wide unavailability. Critical findings are blockers — no code with a Critical finding should be merged.

**Characteristics:**
- Exploitable or directly causes outage without any additional conditions
- Affects data integrity, confidentiality, or service availability
- Cannot be mitigated at runtime by configuration alone
- Independently reproducible given normal production inputs

**Scoring impact**: -25 points from the affected dimension score per finding.

**Examples:**

| Finding | Dimension | Why Critical |
|---------|-----------|--------------|
| Hardcoded AWS secret key in source file | security | Immediate credential exposure if repo is leaked or read |
| `SELECT * FROM users WHERE name = '{user_input}'` (SQL injection) | security | Arbitrary data read/write/deletion |
| `time.sleep(30)` inside `async def handle_request()` | async-correctness | Blocks event loop, stalls all concurrent requests for 30s |
| `asyncio.run(do_work())` called from within a running loop | async-correctness | Raises RuntimeError; crash under load |
| Breaking removal of field from response model used by downstream | api-contracts | Silently breaks consuming services; data loss |
| `open(request.json()["path"])` without path sanitization | security | Path traversal / arbitrary file read |
| `pickle.loads(user_data)` | security | Remote code execution via deserialization |
| PII (email, SSN) emitted to log | observability | Regulatory violation; data leak |
| `privileged: true` in Pod securityContext | k8s-hygiene | Container escape; full node compromise |

---

### High

**Definition**: A finding that causes incorrect behavior, resource leaks, degraded reliability, or a significant maintenance burden. High findings must be fixed before the branch is merged to the primary release track but are not deployment-day stoppers if tracked in an issue.

**Characteristics:**
- Causes measurable harm under production conditions
- May not manifest in unit tests but will appear under load or edge cases
- Requires code change to fix — cannot be mitigated purely by config
- Affects a non-trivial fraction of requests or data

**Scoring impact**: -15 points from the affected dimension score per finding.

**Examples:**

| Finding | Dimension | Why High |
|---------|-----------|----------|
| `requests.get(url)` (sync) inside `async def` handler | async-correctness | Blocks event loop on every call; throughput degrades linearly |
| `asyncio.create_task(work())` with no reference held | async-correctness | Task silently dropped if event loop exits; work lost |
| Public function `def process(data)` with no type hints | type-safety | mypy cannot verify callers; runtime type errors |
| `os.environ.get("SECRET", "dev-secret")` | security | Plaintext fallback used when env var is unset |
| `ssl=False` on outbound HTTPS client | security | TLS verification disabled; MITM vulnerability |
| No `livenessProbe` on Deployment | k8s-hygiene | Kubernetes cannot detect hung pods; no automatic recovery |
| List endpoint returning all rows without pagination | performance-risk | Full table scan; OOM under data growth |
| N+1 query in loop | performance-risk | Latency grows linearly with result set |
| No correlation ID in log records | observability | Cannot trace request path across services |
| External HTTP calls not mocked in unit tests | test-coverage | Tests make real network calls; flaky in CI |
| FastAPI route missing `response_model` | api-contracts | Schema not enforced; undocumented response shape |
| 200 returned for partial failure | api-contracts | Consumers cannot distinguish success from failure |
| `runAsUser: 0` in securityContext | k8s-hygiene | Container runs as root; privilege escalation risk |

---

### Medium

**Definition**: A finding that introduces technical debt, creates a non-obvious maintenance trap, poses a latent risk under specific conditions, or deviates from established team patterns in a way that will confuse future authors.

**Characteristics:**
- Does not directly cause harm today but creates conditions for future failures
- Requires fixing within 1–2 sprints per standard team SLO
- May affect a minority of code paths or edge cases
- Identifiable through code review but unlikely to surface in standard test suites

**Scoring impact**: -8 points from the affected dimension score per finding.

**Examples:**

| Finding | Dimension | Why Medium |
|---------|-----------|------------|
| Sequential `await` on two independent service calls | async-correctness | Suboptimal latency; no correctness issue |
| `# type: ignore` without explanation comment | type-safety | Silent suppression of type errors; confuses future authors |
| Missing return type annotation on `async def` | type-safety | mypy weakened; no immediate runtime impact |
| `print()` used instead of logger | observability | Log not captured by log aggregator; lost in production |
| Error responses inconsistent between endpoints | api-contracts | Consumers must handle two error shapes; SDK breakage |
| `SELECT *` on moderate-sized table | performance-risk | Wasteful network/memory for unneeded columns |
| Unbounded `asyncio.gather()` without semaphore | performance-risk | Spikes under burst; may exhaust DB connections |
| `asyncio.run()` in test body | test-coverage | Works but bypasses pytest-asyncio event loop; may break under fixtures |
| No `securityContext` in Pod spec | k8s-hygiene | Missing defense-in-depth; not exploitable alone |
| `image: latest` tag in Deployment | k8s-hygiene | Non-reproducible; unknown image version deployed |
| Exception swallowed silently in middleware | observability | Error invisible in production logs |
| Nullable Pydantic field not typed `Optional` | api-contracts | Runtime validation error for legitimate `null` values |

---

### Low

**Definition**: A stylistic, convention, or minor quality issue that does not affect correctness, security, or reliability. Low findings are informational — they are reported in the review output but do not reduce dimension scores below 70.

**Characteristics:**
- No runtime impact under normal conditions
- Deviates from style guide or team convention
- Easily fixed in a follow-up PR or automated formatter pass
- Does not create risk of misuse by future authors

**Scoring impact**: -3 points from the affected dimension score per finding. **Floor rule: Low findings cannot push any dimension score below 70.**

**Examples:**

| Finding | Dimension | Note |
|---------|-----------|------|
| `Optional[str]` used instead of `str \| None` (Python 3.10+) | type-safety | Convention preference; both are valid |
| `openapi_extra` used to annotate an endpoint | api-contracts | Minor schema tool bypass; not harmful |
| ERROR log level on a 4xx client error | observability | Should be WARNING; no production impact |
| Cache with no explicit TTL | performance-risk | Latent memory growth; not immediate |
| `preStop` hook absent but pod has low request volume | k8s-hygiene | Best practice; not a reliability gap at this scale |
| Docstring missing on public async function | type-safety | Documentation gap; no runtime impact |
| Thread pool used for an already-async-native operation | async-correctness | Unnecessary overhead; no correctness issue |
| Test only covers the happy path | test-coverage | Informational; not a blocking gap at low risk areas |

---

## Escalation Rules

### When to Escalate Severity

A finding's severity may be escalated one level when any of the following apply:

1. **Blast radius**: The finding affects a shared library, middleware, or base class used by many services — not just one endpoint.
2. **Regulatory context**: The service processes PII, PHI, PCI data, or operates under SOC 2 / HIPAA compliance — security findings escalate one level.
3. **Known production path**: The finding is on a code path exercised by > 10% of production traffic (hot path).
4. **Cumulative pattern**: The same pattern appears in 5+ places — treat the pattern as one level higher than any single instance.

### When to Downgrade Severity

A finding's severity may be downgraded one level when:

1. **Mitigation exists in infrastructure**: The finding is mitigated by a WAF rule, API gateway policy, or infrastructure control that is documented and enforced.
2. **Test-only code**: The finding is in a test helper or fixture file with no production path.
3. **Explicitly acknowledged tech debt**: The finding is documented in a tracked issue linked in a code comment with a resolution timeline.

---

## Scoring Weight Rationale

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| async-correctness | 20% | Async bugs can stall the entire service — a single blocking call under load degrades all concurrent requests simultaneously |
| security | 20% | Security failures have irreversible consequences (data breach, credential theft); regulatory and reputational impact disproportionate to code volume |
| type-safety | 15% | Types are the first line of defense against cross-service contract mismatches; foundational for reliable refactoring |
| api-contracts | 15% | In microservice architectures, a broken contract cascades to all consumers; breakages are hard to rollback |
| observability | 10% | Poor observability multiplies the cost of every incident; MTTR correlates directly with log/trace quality |
| performance-risk | 10% | Performance bugs are often invisible in tests but manifest catastrophically under production load |
| test-coverage | 5% | Weighted lower because coverage quantity is a poor proxy for quality; checks focus on test pattern correctness |
| k8s-hygiene | 5% | Weighted lower because many issues are mitigated by platform-level policies; still required for self-healing behavior |

---

## Reporting Format

Each finding in the grading report must include:

```
[SEVERITY] DIMENSION — Short title
Location: file_path:line_number (or "not found" if absence-based finding)
Finding: Specific description of what was observed
Impact: Why this matters in production
Recommendation: Concrete fix with example code if applicable
Score Impact: -N pts from <dimension> dimension
```

### Example Finding

```
[CRITICAL] security — Hardcoded database password
Location: app/config.py:14
Finding: DB_PASSWORD assigned to string literal "prod-secret-2024"
Impact: Credential exposed in version control history; anyone with repo
        read access can connect to the production database.
Recommendation: Remove the literal. Load from environment:
        db_password = os.environ["DATABASE_PASSWORD"]
        Use SecretStr type in Pydantic settings to prevent logging.
Score Impact: -25 pts from security dimension
```

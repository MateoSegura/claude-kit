# Phase 06: Dashboard, Infrastructure & Production

## Objective

Build the SvelteKit web dashboard (auth, sessions, analytics, live monitoring), deploy the full stack to Kubernetes via Helm charts, establish the production CI/CD pipeline, harden security, and build the testing/benchmarking infrastructure.

## Satisfies

- R15: Web dashboard — signup/login, session history, usage analytics, plugin config, API key management
- R16: Live session monitoring — WebSocket streaming of autonomous sessions
- R17: Kubernetes deployment — Helm charts, health checks, HPA, ingress
- R18: Infrastructure as code — all deploy configs in `deploy/`
- R19: Testing infrastructure — unit, integration, E2E, benchmarks
- R20: Security — garble, encryption, auth hardening, crash report sanitization

## Steps

### Dashboard (R15, R16)

1. [ ] Scaffold SvelteKit project — `apps/web/` with TypeScript, Tailwind CSS, adapter-node for SSR deployment
2. [ ] Implement auth pages — `(auth)/login`, `(auth)/signup`, `(auth)/forgot-password` with form validation, error handling, JWT storage in httpOnly cookies
3. [ ] Implement dashboard layout — sidebar navigation (Dashboard, Sessions, Analytics, Settings), responsive design, dark/light mode
4. [ ] Build dashboard home — summary cards (total sessions, active plugins, error rate, usage trend), recent sessions list, quick actions
5. [ ] Build session history page — paginated table with filters (date range, kit, mode), click-through to session detail showing conversation log viewer
6. [ ] Build live session monitor — WebSocket connection to `/sessions/{id}/stream`, real-time terminal output rendering (using xterm.js or custom ANSI renderer), status overlay showing spec compliance
7. [ ] Build analytics page — usage charts (sessions per day, model usage distribution, plugin popularity, compact frequency), date range picker, exportable data
8. [ ] Build settings page — profile management, API key CRUD (create, view masked, revoke), telemetry preferences, notification settings
9. [ ] Build plugin config page — list loaded plugins per kit, view plugin metadata, toggle auto-loading preferences
10. [ ] Implement API client layer — `apps/web/src/lib/api/` with typed fetch functions, automatic token refresh, error handling

### Infrastructure (R17, R18)

11. [ ] Create API server Dockerfile — `deploy/backend/Dockerfile` multi-stage build (Go compile → distroless runtime image ~15MB)
12. [ ] Create dashboard Dockerfile — `deploy/web/Dockerfile` multi-stage build (Node build → nginx runtime for static assets + SSR)
13. [ ] Create API Helm chart — `deploy/backend/helm/` with Deployment, Service, Ingress, HPA, ConfigMap, Secret, migration Job templates
14. [ ] Create dashboard Helm chart — `deploy/web/helm/` with Deployment, Service, Ingress templates
15. [ ] Create shared infra manifests — `deploy/infra/` with namespace, cert-manager ClusterIssuer, monitoring stack (Prometheus ServiceMonitor, Grafana dashboards)
16. [ ] Create PostgreSQL Helm values — use Bitnami PostgreSQL chart as dependency with persistence, backup CronJob
17. [ ] Create MinIO/S3 configuration — Helm values for MinIO in dev, environment variables for production S3
18. [ ] Create CI workflow for backend deploys — `.github/workflows/release-backend.yml` builds Docker image, pushes to GHCR, updates Helm values
19. [ ] Create CI workflow for dashboard deploys — `.github/workflows/release-web.yml` builds Docker image, pushes to GHCR, updates Helm values
20. [ ] Create unified deploy workflow — `.github/workflows/deploy.yml` triggered manually or by release, runs `helm upgrade` against the cluster

### Testing (R19)

21. [ ] Write Go unit tests — target >80% coverage on `internal/` packages with table-driven tests
22. [ ] Write API integration tests — `testcontainers-go` for Postgres + MinIO, test all endpoint flows
23. [ ] Write E2E CLI tests — binary black-box tests: build binary, run commands, assert output (`tools/test-cli.sh` rewritten)
24. [ ] Write SvelteKit component tests — Vitest + Testing Library for dashboard components
25. [ ] Write E2E dashboard tests — Playwright for critical flows (signup → login → view sessions → create API key)
26. [ ] Create performance benchmarks — `go test -bench` for plugin loading, crypto, PTY throughput; store results for regression tracking
27. [ ] Create load tests — k6 or vegeta scripts for API endpoints under load (1000 concurrent users)

### Security (R20)

28. [ ] Integrate garble into release builds — GoReleaser uses `garble -literals -tiny build` for all release (not snapshot) builds
29. [ ] Implement crash report sanitizer — strip API keys (`ck_*`), home directory paths (`/Users/`, `/home/`), environment variables from stack traces before upload
30. [ ] Implement CSRF protection — SameSite cookies + CSRF token for dashboard form submissions
31. [ ] Implement content security policy — strict CSP headers for dashboard (no inline scripts)
32. [ ] Create security checklist — documented pre-release security review checklist covering OWASP Top 10

## Files to Create/Modify

### Create — Dashboard
- `apps/web/package.json` — SvelteKit project dependencies
- `apps/web/svelte.config.js` — SvelteKit configuration (adapter-node)
- `apps/web/vite.config.ts` — Vite configuration
- `apps/web/tailwind.config.js` — Tailwind CSS configuration
- `apps/web/src/app.html` — HTML shell
- `apps/web/src/routes/(auth)/login/+page.svelte` — login page
- `apps/web/src/routes/(auth)/signup/+page.svelte` — signup page
- `apps/web/src/routes/dashboard/+page.svelte` — dashboard home
- `apps/web/src/routes/sessions/+page.svelte` — session history
- `apps/web/src/routes/sessions/[id]/+page.svelte` — session detail + live view
- `apps/web/src/routes/analytics/+page.svelte` — usage analytics
- `apps/web/src/routes/settings/+page.svelte` — settings + API keys
- `apps/web/src/lib/components/` — reusable components (TerminalViewer, StatCard, Chart, DataTable)
- `apps/web/src/lib/stores/auth.ts` — auth state store
- `apps/web/src/lib/stores/sessions.ts` — session data store
- `apps/web/src/lib/api/client.ts` — typed API client with token refresh
- `apps/web/src/lib/api/auth.ts` — auth API functions
- `apps/web/src/lib/api/sessions.ts` — session API functions
- `apps/web/src/lib/api/telemetry.ts` — telemetry API functions

### Create — Infrastructure
- `deploy/backend/Dockerfile` — API server container
- `deploy/web/Dockerfile` — dashboard container
- `deploy/backend/helm/Chart.yaml` — API Helm chart definition
- `deploy/backend/helm/values.yaml` — default values
- `deploy/backend/helm/values.production.yaml` — production overrides
- `deploy/backend/helm/templates/deployment.yaml`
- `deploy/backend/helm/templates/service.yaml`
- `deploy/backend/helm/templates/ingress.yaml`
- `deploy/backend/helm/templates/hpa.yaml`
- `deploy/backend/helm/templates/configmap.yaml`
- `deploy/backend/helm/templates/secret.yaml`
- `deploy/backend/helm/templates/migration-job.yaml`
- `deploy/web/helm/Chart.yaml`
- `deploy/web/helm/values.yaml`
- `deploy/web/helm/templates/deployment.yaml`
- `deploy/web/helm/templates/service.yaml`
- `deploy/web/helm/templates/ingress.yaml`
- `deploy/infra/namespace.yaml`
- `deploy/infra/cert-manager/clusterissuer.yaml`
- `deploy/infra/monitoring/servicemonitor.yaml`
- `deploy/infra/monitoring/grafana-dashboard.json`

### Create — CI/CD
- `.github/workflows/release-backend.yml` — build + push API container on tag
- `.github/workflows/release-web.yml` — build + push dashboard container on tag
- `.github/workflows/deploy.yml` — Helm upgrade to cluster

### Create — Testing
- `tools/benchmark/bench_plugin_load_test.go` — plugin loading benchmark
- `tools/benchmark/bench_crypto_test.go` — encryption/decryption benchmark
- `tools/benchmark/bench_pty_test.go` — PTY throughput benchmark
- `apps/web/tests/auth.spec.ts` — Playwright E2E: auth flows
- `apps/web/tests/sessions.spec.ts` — Playwright E2E: session browsing
- `apps/web/vitest.config.ts` — Vitest configuration
- `tools/loadtest/api.js` — k6 load test script for API

### Modify
- `.github/workflows/push.yml` — add `go build`, `go test`, `go vet` steps; add SvelteKit build step
- `.github/workflows/pr.yml` — add Go test results to PR comment

## Dashboard Pages

### Login / Signup
- Email + password form with validation
- "Sign up" link from login, "Log in" link from signup
- "Forgot password" link → email reset flow
- JWT stored in httpOnly secure cookie, not localStorage

### Dashboard Home
```
┌────────────────────────────────────────────────────┐
│  claude-kit Dashboard                    [user@] │
├────────────┬───────────────────────────────────────┤
│            │                                       │
│  Dashboard │  ┌─────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  Sessions  │  │ 142 │ │  12  │ │ 0.3% │ │ +24% │ │
│  Analytics │  │ ses │ │ kits │ │ err  │ │ use  │ │
│  Settings  │  └─────┘ └──────┘ └──────┘ └──────┘ │
│            │                                       │
│            │  Recent Sessions                      │
│            │  ┌────────────────────────────────┐   │
│            │  │ 10:30 │ zephyr-eng │ auto │ ✓  │   │
│            │  │ 09:15 │ svelte-eng │ int  │ ✓  │   │
│            │  │ 08:00 │ python-eng │ auto │ ✗  │   │
│            │  └────────────────────────────────┘   │
└────────────┴───────────────────────────────────────┘
```

### Live Session Monitor
```
┌────────────────────────────────────────────────────┐
│  Live Session: embedded-zephyr-engineer             │
│  Mode: AUTONOMOUS │ Phase 2/4 │ Duration: 00:12:34 │
├────────────────────────────────────────────────────┤
│                                                     │
│  [Real-time Claude terminal output via xterm.js]    │
│  │                                                  │
│  │  > Implement GPIO driver for STM32F4             │
│  │                                                  │
│  │  I'll start by reading the HAL configuration...  │
│  │  [Read] src/drivers/gpio.h                       │
│  │  [Write] src/drivers/gpio.c                      │
│  │                                                  │
├────────────────────────────────────────────────────┤
│  Spec Compliance: ✓ R1 ✓ R2 ○ R3 ○ R4              │
│  Files Modified: 3 │ Compacts: 1 │ Steps: 4/8       │
└────────────────────────────────────────────────────┘
```

## Kubernetes Architecture

```
┌─ Namespace: claude-kit ──────────────────────────────┐
│                                                       │
│  ┌── Ingress (nginx) ──────────────────────────────┐ │
│  │  api.claude-kit.dev → API Service               │ │
│  │  app.claude-kit.dev → Web Service               │ │
│  │  (TLS via cert-manager + Let's Encrypt)         │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ┌── API Deployment ──┐  ┌── Web Deployment ──────┐ │
│  │  2-10 replicas     │  │  2-5 replicas          │ │
│  │  HPA: CPU 70%      │  │  HPA: CPU 70%         │ │
│  │  Port: 8080         │  │  Port: 3000           │ │
│  │  Liveness: /health  │  │  Liveness: /          │ │
│  │  Readiness: /ready  │  │  Readiness: /         │ │
│  └─────────┬──────────┘  └────────────────────────┘ │
│            │                                          │
│  ┌─────────▼──────────┐  ┌── MinIO/S3 ───────────┐ │
│  │  PostgreSQL (HA)    │  │  Conversation logs    │ │
│  │  Bitnami chart      │  │  Crash reports        │ │
│  │  PVC: 50Gi          │  │  PVC: 100Gi          │ │
│  └────────────────────┘  └────────────────────────┘ │
│                                                       │
│  ┌── Monitoring ──────────────────────────────────┐  │
│  │  Prometheus (ServiceMonitor scrape)            │  │
│  │  Grafana (pre-built dashboards)                │  │
│  │  AlertManager (error rate, latency SLOs)       │  │
│  └────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

## Acceptance Criteria

### Dashboard
- [ ] User can sign up, log in, and see the dashboard home with usage summary cards
- [ ] Session history page shows paginated list with filters; clicking a session shows the conversation log
- [ ] Live session page streams real-time output from an active autonomous session via WebSocket
- [ ] Analytics page shows usage charts (sessions/day, model distribution, plugin popularity) for configurable date ranges
- [ ] Settings page allows creating, viewing (masked), and revoking API keys
- [ ] Dashboard works on mobile viewports (responsive design)
- [ ] Dark mode toggle persists across sessions

### Infrastructure
- [ ] `helm install claude-kit-api deploy/backend/helm/` deploys a working API server to Kubernetes
- [ ] `helm install claude-kit-web deploy/web/helm/` deploys a working dashboard to Kubernetes
- [ ] Database migrations run automatically on deploy via Kubernetes Job
- [ ] HPA scales API pods from 2 to 10 based on CPU utilization
- [ ] TLS certificates are provisioned automatically via cert-manager
- [ ] Prometheus scrapes API metrics; Grafana dashboard shows request rate, latency, error rate

### Testing
- [ ] `go test ./...` passes with >80% coverage on `internal/` packages
- [ ] `go test -bench ./...` produces reproducible benchmarks for plugin loading (<10ms), crypto (<50ms), PTY throughput (>10MB/s)
- [ ] Playwright E2E tests pass for: signup → login → view sessions → create API key → logout
- [ ] k6 load test shows API handles 1000 concurrent users with <200ms p95 latency

### Security
- [ ] Release binaries are obfuscated with `garble -literals -tiny`
- [ ] API keys are hashed with argon2id before storage — no plaintext keys in the database
- [ ] JWTs are signed with RS256 (asymmetric) — public key distributed to services, private key in Secret
- [ ] Dashboard sets strict CSP headers, SameSite cookies, CSRF tokens
- [ ] Crash reports uploaded to the API contain no API keys, credentials, or home directory paths
- [ ] `go vet ./...` and `golangci-lint run` pass with zero findings on security linters

## Dependencies

- Requires: Phase 03 (API server + auth), Phase 04 (telemetry data to display), Phase 05 (autonomous WebSocket stream)
- Blocks: None (final phase)

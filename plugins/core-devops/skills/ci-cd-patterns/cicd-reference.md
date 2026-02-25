# CI/CD Reference -- Full Pipeline Patterns

Comprehensive reference for CI/CD pipeline design, artifact management, and environment promotion.

---

## GitHub Actions Pipeline Template

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true    # cancel stale runs on same branch

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup toolchain
        # Language-specific setup step
        run: echo "Install linter"
      - name: Lint
        run: echo "Run linter"

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]    # parallel test shards
    steps:
      - uses: actions/checkout@v4
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache
          key: deps-${{ hashFiles('**/lockfile') }}
          restore-keys: deps-
      - name: Install
        run: echo "Install dependencies"
      - name: Test
        run: echo "Run test shard ${{ matrix.shard }}"

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Dependency audit
        run: echo "Audit dependencies for vulnerabilities"
      - name: SAST scan
        run: echo "Run static analysis security testing"

  build:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: echo "Build the deployable artifact"
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-${{ github.sha }}
          path: dist/

  deploy-staging:
    needs: [build]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: app-${{ github.sha }}
      - name: Deploy to staging
        run: echo "Deploy to staging environment"
      - name: Smoke tests
        run: echo "Run smoke tests against staging"

  deploy-production:
    needs: [deploy-staging]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production    # requires manual approval
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: app-${{ github.sha }}
      - name: Deploy to production
        run: echo "Deploy to production environment"
      - name: Health check
        run: echo "Verify production health"
```

---

## GitLab CI Pipeline Template

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - build
  - deploy

variables:
  ARTIFACT_NAME: "app-${CI_COMMIT_SHORT_SHA}"

# --- Validate ---
lint:
  stage: validate
  script:
    - echo "Run linter"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# --- Test ---
unit-test:
  stage: test
  parallel: 4
  script:
    - echo "Run test shard"
  cache:
    key:
      files: [lockfile]
    paths: [.cache/]
  artifacts:
    reports:
      junit: test-results.xml

security-scan:
  stage: test
  script:
    - echo "SAST and dependency scan"
  allow_failure: false

# --- Build ---
build:
  stage: build
  script:
    - echo "Build deployable artifact"
  artifacts:
    paths: [dist/]
    expire_in: 7 days
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# --- Deploy ---
deploy-staging:
  stage: deploy
  script:
    - echo "Deploy to staging"
    - echo "Run smoke tests"
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-production:
  stage: deploy
  script:
    - echo "Deploy to production"
  environment:
    name: production
    url: https://app.example.com
  when: manual    # requires manual trigger
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## Artifact Management

### Container Image Tagging Strategy

| Tag format | When to use | Example |
|-----------|-------------|---------|
| Git SHA (short) | Every build | `api:a1b2c3d` |
| Semantic version | Releases | `api:1.2.3` |
| `latest` | Most recent main build | `api:latest` |
| Branch name | Feature previews | `api:feat-auth` |
| `staging` / `production` | Environment tracking | `api:staging` |

**Rules:**
- Always tag with the git SHA for traceability
- Add semantic version tags for releases
- Never use `latest` in production manifests -- always pin to a specific version
- Clean up old images with a retention policy (keep last N per tag pattern)

### Artifact Registry Patterns

```
registry.example.com/
  project/
    api:a1b2c3d          # git SHA
    api:1.2.3            # semantic version
    api:staging           # environment marker
    worker:a1b2c3d
    worker:1.2.3
```

**Promotion flow:**
1. CI builds and pushes `api:a1b2c3d`
2. Staging deploy uses `api:a1b2c3d`
3. After verification, re-tag as `api:1.2.3`
4. Production deploy uses `api:1.2.3`

---

## Environment Promotion Patterns

### Pattern 1: Image Promotion (Recommended)

```
Build -> Push api:SHA -> Deploy staging (api:SHA) -> Verify -> Deploy prod (api:SHA)
```

Same image, different config. Configuration injected via environment variables, ConfigMaps, or secrets manager.

### Pattern 2: GitOps Promotion

```
Build -> Push api:SHA -> Update staging manifest -> ArgoCD syncs staging
                       -> Update prod manifest    -> ArgoCD syncs production
```

Infrastructure state tracked in a Git repository. Changes to manifests trigger deployments.

### Pattern 3: Helm-Based Promotion

```bash
# Staging
helm upgrade api ./charts/api \
  --set image.tag=${SHA} \
  -f values.staging.yaml \
  -n staging

# Production (after staging verification)
helm upgrade api ./charts/api \
  --set image.tag=${SHA} \
  -f values.production.yaml \
  -n production
```

---

## Caching Deep Dive

### Dependency Cache Patterns

```yaml
# GitHub Actions -- cache by lockfile hash
- uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      ~/.cache/pip
      ~/.m2/repository
      ~/.gradle/caches
    key: deps-${{ runner.os }}-${{ hashFiles('**/lockfile') }}
    restore-keys: |
      deps-${{ runner.os }}-
```

### Docker Layer Caching in CI

```yaml
# GitHub Actions with Docker Buildx
- uses: docker/setup-buildx-action@v3
- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: registry.example.com/api:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Build Cache Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Cache everything | Stale deps mask issues | Cache only lockfile-keyed deps |
| No cache versioning | OS/arch mismatches | Include runner OS in cache key |
| Infinite cache TTL | Never invalidated | Set max-age or periodic purge |
| Cache build outputs across branches | Wrong artifacts | Scope cache to branch or main |

---

## Pipeline Security

### Secret Management in CI

| Secret type | Storage | Access |
|------------|---------|--------|
| API keys, tokens | CI platform secrets | Injected as env vars at runtime |
| Signing keys | Hardware security module or vault | Accessed via API during build |
| Cloud credentials | OIDC federation (preferred) | Short-lived tokens, no stored secrets |
| Registry credentials | CI platform or workload identity | Push/pull during build stage |

**Rules:**
- Never echo secrets in logs -- mask them in CI config
- Use OIDC workload identity over long-lived credentials when available
- Rotate secrets on a schedule (90 days max)
- Audit secret access in CI logs

### Supply Chain Security

```yaml
# Pin actions to SHA, not tags (prevents tag hijacking)
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1

# Sign container images
- name: Sign image
  run: cosign sign --yes registry.example.com/api:${SHA}

# Generate SBOM
- name: Generate SBOM
  run: syft registry.example.com/api:${SHA} -o spdx-json > sbom.json
```

---

## Monorepo CI Patterns

### Affected-Only Builds

Only build and test what changed:

```yaml
# Detect changed paths
changes:
  - name: Detect changes
    run: |
      # Compare against base branch
      CHANGED=$(git diff --name-only origin/main...HEAD)
      echo "changed=$CHANGED" >> $GITHUB_OUTPUT

# Run jobs conditionally
build-api:
  if: contains(needs.changes.outputs.changed, 'packages/api/')
  # ...

build-web:
  if: contains(needs.changes.outputs.changed, 'packages/web/')
  # ...
```

### Nx/Turborepo Integration

```yaml
# Build only affected projects
- run: npx nx affected -t build --base=origin/main
- run: npx nx affected -t test --base=origin/main

# Or with Turborepo
- run: npx turbo run build test --filter='...[origin/main]'
```

---

## Pipeline Metrics

Track these metrics to measure CI/CD health:

| Metric | Target | Why |
|--------|--------|-----|
| Build duration | < 10 min | Developer productivity |
| Deploy frequency | Multiple per day | Delivery velocity |
| Lead time (commit to production) | < 1 hour | Flow efficiency |
| Change failure rate | < 5% | Quality |
| MTTR (mean time to recovery) | < 1 hour | Resilience |
| Pipeline success rate | > 95% | Reliability |
| Flaky test rate | < 1% | Trust in pipeline |

These align with the DORA metrics framework for measuring software delivery performance.

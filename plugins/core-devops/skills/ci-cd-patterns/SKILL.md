---
name: core-devops:ci-cd-patterns
description: "CI/CD pipeline design patterns: build-test-deploy stages, environment promotion, artifact management, caching strategies, parallelization, status checks as gates, trunk-based vs feature-branch CI. Load when designing or reviewing CI/CD pipelines."
user-invocable: false
---

# CI/CD Patterns -- Quick Reference

## Additional resources

- [cicd-reference.md](cicd-reference.md) -- Full pipeline patterns, caching strategies, artifact management, and environment promotion

---

## Pipeline Design Principles

### The Build-Test-Deploy Pipeline

Every CI/CD pipeline follows the same core flow regardless of tooling:

```
Source -> Build -> Test -> Package -> Deploy(staging) -> Verify -> Deploy(production)
```

**Stage responsibilities:**

| Stage | Purpose | Failure action |
|-------|---------|----------------|
| Build | Compile, resolve dependencies, generate artifacts | Fail fast, notify developer |
| Test | Unit tests, integration tests, linting, security scans | Block merge/deploy |
| Package | Create deployable artifact (container image, binary, archive) | Fail the pipeline |
| Deploy (staging) | Deploy to pre-production environment | Roll back automatically |
| Verify | Smoke tests, integration tests against staging | Block production deploy |
| Deploy (production) | Release to users | Roll back or roll forward |

### Key Rules

1. **Builds must be reproducible** -- same commit produces identical artifacts
2. **Build once, deploy many** -- produce one artifact, promote through environments
3. **Fail fast** -- run cheapest checks first (lint, compile, unit tests)
4. **Immutable artifacts** -- never modify a built artifact; rebuild instead
5. **Every merge to main is deployable** -- keep main branch always releasable

---

## Branching Strategies for CI

### Trunk-Based Development (Recommended)

- Developers commit to `main` (or short-lived feature branches merged within hours)
- Feature flags gate incomplete work
- CI runs on every push to main
- Releases cut from main via tags or release branches

**Best for:** teams with strong test coverage, frequent deploys, and feature flag infrastructure.

### Feature-Branch CI

- Long-lived branches per feature (days to weeks)
- CI runs on every push to the feature branch + on merge to main
- PRs gate merges via required status checks

**Best for:** teams with less mature testing, regulated environments, or open-source projects.

### Environment Promotion

```
feature-branch -> main -> staging -> production
                   |
                   v
              artifact registry
```

- Tag artifacts with the git SHA or semantic version
- Promote the same image/binary through environments -- never rebuild
- Use environment-specific configuration (ConfigMaps, env vars, secrets) -- not different builds

---

## Caching Strategies

| What to cache | Key pattern | Invalidation |
|--------------|-------------|--------------|
| Dependencies (npm, pip, Maven) | Hash of lockfile | Lockfile changes |
| Build outputs (compiled code) | Hash of source + deps | Source or deps change |
| Docker layers | Layer hash (automatic) | Dockerfile or context changes |
| Test results | Hash of source + test files | Source or tests change |

**Rules:**
- Always use lockfile hashes for dependency caches -- not timestamps
- Separate caches for different OS/architecture combinations
- Set max cache TTL to prevent stale caches from masking issues

---

## Parallelization

Run independent steps concurrently to minimize pipeline duration:

```
          +-> lint --------+
          |                |
source -> +-> unit-test ---+-> package -> deploy
          |                |
          +-> sec-scan ----+
```

**What can run in parallel:**
- Linting and unit tests
- Different test suites (unit, integration, e2e)
- Security scans and dependency audits
- Multi-platform builds

**What must be sequential:**
- Build before test (tests need the artifact)
- Test before deploy (deploy needs passing tests)
- Deploy staging before deploy production

---

## Status Checks as Gates

Every PR should require passing status checks before merge:

| Check | Blocks merge? | Purpose |
|-------|--------------|---------|
| Build | Yes | Code compiles/bundles |
| Unit tests | Yes | Logic correctness |
| Lint / format | Yes | Code standards |
| Security scan | Yes (critical/high) | Vulnerability detection |
| Integration tests | Recommended | Cross-component correctness |
| Coverage threshold | Optional | Prevent coverage regression |

**Implementation pattern:**
- Required checks block the merge button
- Optional checks post results as PR comments
- Flaky tests get quarantined, not disabled

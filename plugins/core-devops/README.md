# core-devops

> **Role:** Knowledge companion · **Version:** 0.0.1

General-purpose DevOps patterns -- CI/CD pipelines, containerization, observability, and deployment strategies for any software project.

This plugin is a **universal knowledge companion** designed to be auto-loaded alongside role plugins for any technology stack. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `ci-cd-patterns` | Pipeline design (build-test-deploy), environment promotion, artifact management, caching strategies, parallelization, status checks as gates, trunk-based vs feature-branch CI |
| `containerization` | Docker fundamentals (multi-stage builds, layer caching, minimal images, .dockerignore), Docker Compose for local dev, K8s basics (Deployments, Services, ConfigMaps, Secrets, Ingress), health probes, resource limits, HPA |
| `observability` | Three pillars (logs, metrics, traces), structured logging patterns, OpenTelemetry concepts, alerting strategies, SLIs/SLOs/SLAs, dashboard design principles |
| `deployment-strategies` | Blue-green, canary, rolling update, feature flags, database migrations in deployments, rollback strategies, zero-downtime deployment patterns |

---

## Auto-Loading

This plugin uses `domain: "universal"` in its `ctl.json`, making it available as a companion for any team's role plugins that declare it as a dependency.

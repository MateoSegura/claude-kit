---
name: core-devops:identity
description: "Domain overview for DevOps and infrastructure knowledge. Auto-loaded for all domain tasks."
user-invocable: false
---

# DevOps & Infrastructure -- Domain Knowledge

This plugin provides language-agnostic reference material for DevOps practices, infrastructure patterns, and operational excellence. It covers the full delivery lifecycle from CI/CD pipelines through containerization, orchestration, observability, and deployment strategies.

## What this plugin contains

- **CI/CD patterns**: Pipeline design, build-test-deploy stages, environment promotion, artifact management, caching, parallelization, trunk-based vs feature-branch workflows
- **Containerization**: Docker fundamentals (multi-stage builds, layer caching, minimal images, .dockerignore), Docker Compose for local development, Kubernetes core objects (Deployments, Services, ConfigMaps, Secrets, Ingress), health probes, resource limits
- **Observability**: The three pillars (logs, metrics, traces), structured logging, OpenTelemetry concepts, alerting strategies, SLIs/SLOs/SLAs, dashboard design
- **Deployment strategies**: Blue-green, canary, rolling updates, feature flags, database migrations during deployments, rollback strategies, zero-downtime patterns

## What this plugin does NOT contain

- No agent definitions -- agents belong in role plugins (engineer, grader, tester)
- No slash commands -- workflow orchestration belongs in role plugins
- No persona or communication style -- role plugins define their own identity
- No hooks or enforcement rules -- role plugins own those
- No language-specific tooling -- language plugins cover that

## Usage

This is a universal companion plugin loaded alongside role plugins for any technology stack. It centralizes DevOps domain knowledge so that all role variants share a single, consistent infrastructure reference base.

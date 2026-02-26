---
name: cloud-python-engineer:plan
description: "Architecture planning for Python cloud services — service decomposition, API boundary design, database schema planning, inter-service communication strategy, and infrastructure topology"
allowed-tools: Task, Read, Glob, Grep, Bash, AskUserQuestion, WebSearch
user-invocable: true
---

# Plan — Cloud Architecture Orchestrator

You orchestrate architecture planning for Python cloud-backend projects by analyzing the user's design challenge and dispatching the `architect` agent to produce a detailed architecture plan. This is a read-only workflow — no code is written or modified.

## Step 1: Classify the Design Challenge

Read the user's request and classify it:

| Category | Signals | Architect Focus |
|----------|---------|----------------|
| New system architecture | "design system", "plan services", "architect the backend" | Full decomposition: services, APIs, data, infrastructure |
| Service architecture | "plan this service", "design the service", "how to structure" | Single-service internals: layers, modules, endpoints, workers |
| API design | "plan API", "design endpoints", "API boundaries" | REST/gRPC contract design, versioning, auth |
| Data architecture | "database design", "schema planning", "data model" | Schema design, relationships, indexing, migration strategy |
| Infrastructure planning | "deployment plan", "K8s architecture", "scaling strategy" | K8s topology, networking, HPA, observability pipeline |
| Migration/refactoring | "break up monolith", "refactor service", "migrate to" | Current state analysis, target state, phased migration |

## Step 2: Gather Context

Before dispatching, collect relevant project information:

```
Glob: **/pyproject.toml — project metadata and dependencies
Glob: src/**/*.py — module layout
Glob: **/*.proto — gRPC service definitions
Glob: alembic/versions/*.py — migration history
Glob: **/Dockerfile — container setup
Glob: **/k8s/** or **/helm/** — Kubernetes resources
Read: pyproject.toml — dependencies, Python version, tools
```

If reviewing an existing system, also check:

```
Grep: "app = FastAPI" — entry points
Grep: "class.*Base.*Model" — SQLAlchemy models
Grep: "router = APIRouter" — existing route modules
Bash: find . -name "docker-compose*.yml" -type f — service composition
```

## Step 3: Clarify Requirements

If the request is ambiguous, use `AskUserQuestion` to clarify:

- **Scale**: "Expected request volume? (requests/sec, concurrent users)"
- **Communication**: "How do services communicate? (REST, gRPC, events, or mixed)"
- **Data**: "What database? (PostgreSQL assumed. Redis caching needed?)"
- **Infrastructure**: "Target platform? (Kubernetes, Docker Compose, cloud-managed, or serverless)"
- **Consistency**: "Strong consistency or eventual? Any cross-service transactions?"

Do NOT ask if the request already has enough information to dispatch.

## Step 4: Dispatch Architect

Spawn a SINGLE `architect` subagent:

```
Task(architect):
  Input: <full design challenge description>
  Context:
    - User request: [verbatim]
    - Existing services: [service inventory from codebase]
    - Current models: [SQLAlchemy model list]
    - Existing APIs: [router/endpoint summary]
    - Proto definitions: [gRPC service list]
    - Infrastructure: [K8s/Docker resources found]
    - Constraints: [latency, throughput, consistency, team size]
```

The `architect` agent has these skills preloaded:
- `python-backend` — FastAPI, async patterns, Pydantic, SQLAlchemy
- `design-patterns` — cloud-native Python design patterns
- `distributed-systems` — messaging, caching, consistency
- `containers-orchestration` — Docker, Kubernetes, Helm

## Step 5: Present the Architecture Plan

After the architect completes:

1. Present the full architecture plan organized by section
2. Highlight cross-service communication decisions (sync vs async)
3. Flag any assumptions about infrastructure or scale
4. Call out consistency trade-offs and failure mode implications

Offer follow-up actions:

- "Ready to implement? Run `/cloud-python-engineer:engineer` to start building."
- "Need to scaffold a service from this plan? I'll route to `service-scaffolder`."
- "Want to adjust the plan? Tell me which aspect to refine."

## Common Patterns

### New System Architecture

```
1. Gather: Business capabilities, scale expectations, team structure
2. Clarify: Consistency requirements, infrastructure platform, external integrations
3. Architect: Service decomposition, API boundaries, data ownership, infrastructure
```

### Service Internal Design

```
1. Read: Existing service code, models, endpoints
2. Architect: Layer organization, module boundaries, dependency injection
3. Present: Directory structure, interface definitions, testing strategy
```

### Microservice Migration

```
1. Analyze: Current monolith structure, module coupling, shared state
2. Architect: Bounded contexts, extraction order, strangler fig approach
3. Present: Phased migration plan, data migration strategy, parallel running
```

## Error Handling

- **Ambiguous scope** → Use `AskUserQuestion` to narrow the design challenge
- **No existing codebase** → Architecture plan assumes greenfield Python service
- **Conflicting requirements** → Present trade-offs (e.g., consistency vs latency)
- **Architect returns incomplete** → Report gaps, offer to re-run with more context

## Important Constraints

- This command produces READ-ONLY architecture plans — no files are modified
- Always pass sufficient context to the architect (services, models, config)
- Use absolute file paths in context and results
- Do NOT execute git commands unless explicitly requested
- The architect CANNOT spawn other agents — keep hierarchy flat

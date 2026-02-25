---
name: core-devops:deployment-strategies
description: "Deployment strategy patterns: blue-green, canary, rolling updates, feature flags, database migrations in deployments, rollback strategies, and zero-downtime deployment techniques. Load when planning releases or designing deployment workflows."
user-invocable: false
---

# Deployment Strategies -- Quick Reference

## Additional resources

- [deployment-reference.md](deployment-reference.md) -- Detailed patterns for each strategy, database migration handling, rollback procedures, and zero-downtime checklists

---

## Strategy Comparison

| Strategy | Risk | Complexity | Rollback speed | Resource cost |
|----------|------|-----------|----------------|---------------|
| Rolling update | Low-medium | Low | Medium (rollback) | 1x + surge |
| Blue-green | Low | Medium | Instant (switch) | 2x |
| Canary | Lowest | High | Instant (route change) | 1x + small % |
| Feature flags | Lowest | Medium | Instant (flag toggle) | 1x |
| Recreate | High | Low | Slow (redeploy) | 1x |

---

## Rolling Update

Replace instances gradually, one (or a few) at a time:

```
v1 v1 v1 v1    ->    v2 v1 v1 v1    ->    v2 v2 v1 v1    ->    v2 v2 v2 v2
```

**When to use:** Default strategy for most services. Good when old and new versions can coexist briefly.

**K8s configuration:**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # 1 extra pod during rollout
    maxUnavailable: 0  # zero-downtime: never reduce below desired count
```

**Rules:**
- Set `maxUnavailable: 0` for zero-downtime
- Ensure readiness probes pass before routing traffic
- Both versions serve traffic simultaneously during rollout
- API changes must be backward-compatible

---

## Blue-Green Deployment

Run two identical environments; switch traffic atomically:

```
[Blue: v1] <-- traffic    [Green: v2] (idle, verified)
[Blue: v1] (idle)         [Green: v2] <-- traffic (switched)
```

**When to use:** When you need instant rollback capability or cannot tolerate mixed versions serving traffic.

**Implementation:**
1. Deploy v2 to the idle environment (green)
2. Run smoke tests against green
3. Switch the load balancer/service to point to green
4. Keep blue running for quick rollback
5. After confidence period, decommission blue or repurpose it

**Trade-off:** Requires 2x infrastructure during deployment.

---

## Canary Deployment

Route a small percentage of traffic to the new version; increase gradually:

```
v1 (95%) ──┐                v1 (75%) ──┐               v2 (100%)
            ├── users          ├── users
v2 (5%)  ──┘                v2 (25%) ──┘
```

**When to use:** High-risk changes where you want to validate with real traffic before full rollout.

**Progression example:**
1. Deploy canary: 5% traffic to v2
2. Monitor error rate, latency, business metrics for 15 min
3. If healthy: increase to 25%, then 50%, then 100%
4. If unhealthy: route 100% back to v1

**Requirements:**
- Traffic splitting capability (service mesh, ingress controller, or load balancer)
- Automated metric comparison between canary and baseline
- Clear rollback criteria defined before deployment

---

## Feature Flags

Deploy code changes but control activation at runtime:

```
Code deployed: v2 (with feature behind flag)
Flag OFF: all users see v1 behavior
Flag ON for 5%: 5% see v2 behavior
Flag ON for 100%: full rollout
```

**When to use:** Decouple deployment from release. Deploy anytime, activate when ready.

**Benefits:**
- Zero-risk deployments (code is inactive until flag is enabled)
- Gradual rollouts by user segment, geography, or percentage
- Instant rollback (toggle the flag off)
- A/B testing capability

**Rules:**
- Clean up flags after full rollout (flag debt accumulates fast)
- Set expiration dates on flags
- Audit which flags are active in production
- Never use flags for permanent configuration -- use config management instead

---

## Database Migrations in Deployments

Database schema changes are the hardest part of zero-downtime deployment:

### Expand-Contract Pattern

1. **Expand:** Add new columns/tables (backward compatible)
2. **Deploy:** Roll out new code that writes to both old and new schema
3. **Migrate:** Backfill old data into new schema
4. **Contract:** Remove old columns/tables after all code uses the new schema

### Rules

- Never rename or drop a column in the same release that changes the code
- Always make migrations backward-compatible with the previous code version
- Use advisory locks or migration tools to prevent concurrent migrations
- Test migrations against a copy of production data for timing and correctness
- Have a rollback migration ready for every forward migration

---

## Rollback Strategies

| Scenario | Rollback method | Time to recover |
|----------|----------------|-----------------|
| Bad deploy (rolling) | `kubectl rollout undo` | 1-5 minutes |
| Bad deploy (blue-green) | Switch traffic back to blue | Seconds |
| Bad deploy (canary) | Route 100% to stable | Seconds |
| Bad feature | Toggle feature flag off | Seconds |
| Bad migration | Run reverse migration + redeploy | 5-30 minutes |
| Data corruption | Restore from backup | Minutes to hours |

**Rules:**
- Every deployment must have a documented rollback plan
- Test rollback procedures regularly (not just during incidents)
- Keep previous version available for at least 1 hour after deployment
- Automate rollback triggers based on error rate or SLO burn rate

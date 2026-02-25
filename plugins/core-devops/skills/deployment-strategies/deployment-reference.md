# Deployment Strategies Reference -- Full Patterns

Comprehensive reference for deployment strategies, migration handling, and zero-downtime techniques.

---

## Rolling Update -- Detailed Configuration

### Kubernetes Rolling Update

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # at most 5 pods during rollout (4 + 1)
      maxUnavailable: 0  # always maintain 4 ready pods
  template:
    spec:
      containers:
        - name: app
          image: registry.example.com/app:2.0.0
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 3
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
      terminationGracePeriodSeconds: 30
```

### Rollout Commands

```bash
# Watch rollout progress
kubectl rollout status deployment/app -n production

# View revision history
kubectl rollout history deployment/app -n production

# Rollback to previous version
kubectl rollout undo deployment/app -n production

# Rollback to specific revision
kubectl rollout undo deployment/app --to-revision=3 -n production

# Pause and resume rollout
kubectl rollout pause deployment/app -n production
kubectl rollout resume deployment/app -n production
```

### Tuning Parameters

| Parameter | Conservative | Balanced | Aggressive |
|-----------|-------------|----------|------------|
| maxSurge | 1 | 25% | 50% |
| maxUnavailable | 0 | 1 | 25% |
| Rollout time (10 pods) | ~10 min | ~4 min | ~2 min |
| Risk during rollout | Lowest | Low | Medium |

---

## Blue-Green Deployment -- Implementation

### Using Kubernetes Services

```yaml
# Blue deployment (current production)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels: { app: app, slot: blue }
spec:
  replicas: 3
  selector:
    matchLabels: { app: app, slot: blue }
  template:
    metadata:
      labels: { app: app, slot: blue }
    spec:
      containers:
        - name: app
          image: registry.example.com/app:1.0.0

---
# Green deployment (new version)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels: { app: app, slot: green }
spec:
  replicas: 3
  selector:
    matchLabels: { app: app, slot: green }
  template:
    metadata:
      labels: { app: app, slot: green }
    spec:
      containers:
        - name: app
          image: registry.example.com/app:2.0.0

---
# Service points to active slot
apiVersion: v1
kind: Service
metadata:
  name: app-svc
spec:
  selector:
    app: app
    slot: blue    # Change to "green" to switch traffic
  ports:
    - port: 80
      targetPort: 8080
```

### Switch Traffic

```bash
# Verify green is healthy
kubectl rollout status deployment/app-green -n production

# Switch traffic to green
kubectl patch service app-svc -n production \
  -p '{"spec":{"selector":{"slot":"green"}}}'

# Verify traffic is flowing to green
kubectl get endpoints app-svc -n production

# Rollback: switch back to blue
kubectl patch service app-svc -n production \
  -p '{"spec":{"selector":{"slot":"blue"}}}'
```

### Blue-Green Checklist

1. Deploy green with identical replica count as blue
2. Wait for all green pods to pass readiness probes
3. Run smoke tests against green (via a separate test service or port-forward)
4. Switch the service selector to green
5. Monitor error rates for 5-15 minutes
6. If healthy: scale down blue (but keep the deployment for quick rollback)
7. If unhealthy: switch selector back to blue immediately

---

## Canary Deployment -- Implementation

### Using Istio Virtual Service

```yaml
# Traffic split: 95% stable, 5% canary
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: app
spec:
  hosts: [app-svc]
  http:
    - route:
        - destination:
            host: app-svc
            subset: stable
          weight: 95
        - destination:
            host: app-svc
            subset: canary
          weight: 5

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: app
spec:
  host: app-svc
  subsets:
    - name: stable
      labels: { version: "1.0.0" }
    - name: canary
      labels: { version: "2.0.0" }
```

### Using Nginx Ingress Canary

```yaml
# Stable ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-stable
spec:
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-stable
                port: { number: 80 }

---
# Canary ingress (5% of traffic)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "5"
spec:
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-canary
                port: { number: 80 }
```

### Canary Promotion Procedure

```bash
# Phase 1: Deploy canary (5%)
kubectl apply -f canary-deployment.yaml
# Update canary weight to 5%

# Phase 2: Observe (15 min)
# Compare metrics: canary vs stable
#   - Error rate: canary <= stable + 0.1%
#   - p99 latency: canary <= stable * 1.1
#   - Business metrics: conversion rate, etc.

# Phase 3: Increase (25%)
# Update canary weight to 25%

# Phase 4: Observe (15 min)
# Same metric comparison

# Phase 5: Full rollout (100%)
# Update stable deployment to v2
# Remove canary deployment

# Abort at any phase:
# Set canary weight to 0%
# Delete canary deployment
```

---

## Feature Flag Patterns

### Flag Types

| Type | Description | Lifetime | Example |
|------|------------|----------|---------|
| Release flag | Gate incomplete features | Days to weeks | `new_checkout_flow` |
| Experiment flag | A/B test variations | Weeks to months | `pricing_page_variant_b` |
| Ops flag | Runtime kill switch | Permanent | `enable_cache_layer` |
| Permission flag | User entitlement | Permanent | `premium_feature_access` |

### Flag Evaluation Flow

```
Request comes in
  -> Evaluate flag rules:
       1. User is in allow-list? -> ON
       2. User in percentage rollout? -> ON/OFF based on hash
       3. User in target segment? -> ON/OFF per segment rules
       4. Default: OFF
  -> Return flag value
  -> Application branches on value
```

### Flag Hygiene

| Practice | Why |
|----------|-----|
| Set expiration date on every release flag | Prevent flag debt |
| Review active flags monthly | Remove fully-rolled-out flags |
| Limit total active flags per service (< 20) | Reduce combinatorial complexity |
| Test both flag states in CI | Ensure both paths work |
| Log flag evaluation decisions | Debug unexpected behavior |

---

## Database Migration Patterns

### Expand-Contract (Zero-Downtime Schema Change)

**Example: Rename a column from `user_name` to `username`**

```
Phase 1 (Expand):
  - Add new column: ALTER TABLE users ADD COLUMN username VARCHAR(255);
  - Deploy v2: write to BOTH user_name AND username
  - Backfill: UPDATE users SET username = user_name WHERE username IS NULL;

Phase 2 (Transition):
  - Deploy v3: read from username, still write to both
  - Verify all reads use new column

Phase 3 (Contract):
  - Deploy v4: stop writing to user_name
  - Drop old column: ALTER TABLE users DROP COLUMN user_name;
```

### Migration Safety Rules

| Rule | Reason |
|------|--------|
| Never drop a column in the same release that stops using it | Previous version may still be running |
| Add columns as NULLABLE or with defaults | Avoids table lock on large tables |
| Use online DDL tools for large tables | `pt-online-schema-change`, `gh-ost`, or native online DDL |
| Run migrations in a separate step, not during pod startup | Prevents race conditions with multiple pods |
| Test migration timing on production-sized data | A 5-second dev migration may take 30 minutes on production |
| Always write a reverse migration | You will need it during an incident |

### Migration Execution Order

```
1. Run forward migration          (schema is expanded)
2. Deploy new application version (code uses new schema)
3. Verify for 24-48 hours         (confirm stability)
4. Run cleanup migration          (remove old columns/tables)
```

Never combine steps 1 and 4 in the same release.

---

## Zero-Downtime Deployment Checklist

### Before Deployment

- [ ] New version is backward-compatible with current schema
- [ ] Database migrations are expand-only (no drops/renames)
- [ ] API changes are additive (no removed or renamed fields)
- [ ] Health check endpoints return correct status
- [ ] Readiness probe distinguishes "starting" from "ready"
- [ ] Graceful shutdown handles in-flight requests

### During Deployment

- [ ] Monitor error rate, latency, and throughput in real time
- [ ] Verify new pods pass readiness probes before receiving traffic
- [ ] Check that old pods drain connections during termination
- [ ] Confirm no increase in 5xx errors or timeout rates

### After Deployment

- [ ] Verify all pods running the new version
- [ ] Check SLO dashboard for any degradation
- [ ] Run smoke tests against production
- [ ] Confirm logs show expected behavior
- [ ] Keep previous version available for rollback (1 hour minimum)

---

## Rollback Procedures

### Automated Rollback Triggers

Set up automated rollback when:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Error rate spike | > 5% for 2 minutes | Halt rollout |
| Latency degradation | p99 > 2x baseline for 5 min | Halt rollout |
| Pod crash loop | > 3 restarts in 5 min | Rollback |
| Health check failures | > 50% failing for 1 min | Rollback |

### Manual Rollback Commands

```bash
# Kubernetes rolling update rollback
kubectl rollout undo deployment/app -n production

# Helm rollback
helm rollback app 1 -n production

# Blue-green rollback (switch service selector)
kubectl patch service app-svc -n production \
  -p '{"spec":{"selector":{"slot":"blue"}}}'

# Canary rollback (remove canary traffic)
kubectl patch ingress app-canary -n production \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"0"}}}'

# Feature flag rollback
# Toggle flag OFF in feature flag service (instant, no deployment needed)
```

### Post-Rollback Actions

1. Confirm traffic is stable on the previous version
2. Collect logs and metrics from the failed deployment
3. Create an incident report if SLO was impacted
4. Fix the root cause on a branch (do not push to main until fixed)
5. Test the fix thoroughly before re-attempting deployment

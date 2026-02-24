# Kubernetes Reference — Python Service Manifests

Full manifest patterns, deployment strategies, and Helm chart structure.

---

## Complete Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
  labels:
    app: api
    version: "1.2.3"
    component: backend
  annotations:
    deployment.kubernetes.io/revision: "1"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # allow 1 extra pod during rollout
      maxUnavailable: 0  # never reduce below desired count (zero-downtime)
  template:
    metadata:
      labels:
        app: api
        version: "1.2.3"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: api-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
        - name: api
          image: my-registry.io/api:1.2.3
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
              name: http
              protocol: TCP
          envFrom:
            - configMapRef:
                name: api-config
            - secretRef:
                name: api-secrets
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
          resources:
            requests:
              cpu: "100m"       # guaranteed allocation; used by HPA
              memory: "128Mi"
            limits:
              cpu: "1000m"      # 1 full CPU max
              memory: "512Mi"   # OOMKilled if exceeded
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
            successThreshold: 1
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 5
            failureThreshold: 3
            successThreshold: 1
          startupProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 12  # allow 60s for startup (5s * 12)
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]  # drain in-flight requests
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
      terminationGracePeriodSeconds: 30
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: api
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: api
                topologyKey: kubernetes.io/hostname
```

---

## Service Manifest

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-svc
  namespace: production
  labels: { app: api }
spec:
  selector: { app: api }
  ports:
    - name: http
      port: 80
      targetPort: 8000
      protocol: TCP
  type: ClusterIP   # internal only; expose via Ingress
```

---

## Ingress Manifest

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts: [api.example.com]
      secretName: api-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-svc
                port: { name: http }
```

---

## ConfigMap and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: production
data:
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  MAX_CONNECTIONS: "20"
  REDIS_URL: "redis://redis-svc.production.svc.cluster.local:6379"
  ALLOWED_ORIGINS: "https://app.example.com"

---
# k8s/secret.yaml — Use External Secrets Operator in production
# This example shows the structure; real values should come from a secrets manager
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: production
type: Opaque
stringData:  # stringData auto-encodes to base64
  DATABASE_URL: "postgresql+asyncpg://user:pass@postgres-svc:5432/appdb"
  SECRET_KEY: "change-me-in-production"
  SENTRY_DSN: "https://xxx@sentry.io/yyy"
```

### External Secrets Operator (Production Pattern)

```yaml
# k8s/external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: api-secrets
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: api-secrets
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: production/api/database
        property: url
    - secretKey: SECRET_KEY
      remoteRef:
        key: production/api/app
        property: secret_key
```

---

## HPA — Full Configuration

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60      # target 60% CPU utilization
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    # Custom metric from Prometheus (requires kube-adapter)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0   # react immediately to spikes
      policies:
        - type: Pods
          value: 4
          periodSeconds: 15
        - type: Percent
          value: 100
          periodSeconds: 15
      selectPolicy: Max               # choose the policy that allows most scale-up
    scaleDown:
      stabilizationWindowSeconds: 300  # wait 5 minutes before scaling down
      policies:
        - type: Pods
          value: 1
          periodSeconds: 60           # remove at most 1 pod per minute
```

---

## PodDisruptionBudget

```yaml
# k8s/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
  namespace: production
spec:
  selector:
    matchLabels: { app: api }
  minAvailable: 2    # always keep at least 2 pods during node drains
  # OR: maxUnavailable: 1
```

---

## ServiceAccount with IRSA (AWS)

```yaml
# k8s/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-sa
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/api-role
```

---

## Helm Chart Structure

```
charts/api/
├── Chart.yaml
├── values.yaml
├── values.production.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    ├── hpa.yaml
    ├── pdb.yaml
    └── _helpers.tpl
```

### Chart.yaml

```yaml
apiVersion: v2
name: api
description: Python FastAPI backend service
type: application
version: 0.1.0          # chart version
appVersion: "1.2.3"     # app version (from git tag)
```

### values.yaml

```yaml
image:
  repository: my-registry.io/api
  tag: latest
  pullPolicy: IfNotPresent

replicaCount: 3

resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "1000m"
    memory: "512Mi"

hpa:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  cpuTargetUtilization: 60

ingress:
  enabled: true
  host: api.example.com
  tls: true

env:
  LOG_LEVEL: INFO
  MAX_CONNECTIONS: "20"
```

### Helm Commands

```bash
# Install
helm install api ./charts/api -f charts/api/values.production.yaml -n production

# Upgrade
helm upgrade api ./charts/api -f charts/api/values.production.yaml -n production

# Rollback
helm rollback api 1 -n production

# Dry-run
helm upgrade api ./charts/api --dry-run --debug -n production

# Template render (without installing)
helm template api ./charts/api -f values.production.yaml
```

---

## kubectl Quick Reference

```bash
# Deployment management
kubectl apply -f k8s/                                 # apply all manifests
kubectl rollout status deployment/api -n production   # watch rollout
kubectl rollout history deployment/api -n production  # show revisions
kubectl rollout undo deployment/api -n production     # rollback

# Pod debugging
kubectl logs -f deployment/api -n production --tail=100
kubectl exec -it deployment/api -n production -- /bin/sh
kubectl describe pod <pod-name> -n production
kubectl top pods -n production

# Port forwarding for local debugging
kubectl port-forward svc/api-svc 8000:80 -n production

# Resource usage
kubectl top nodes
kubectl top pods -n production --sort-by=memory

# Events (useful for debugging)
kubectl get events -n production --sort-by='.lastTimestamp'
```

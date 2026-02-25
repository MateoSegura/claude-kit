# Kubernetes Reference -- Language-Agnostic Manifests

Full manifest patterns, deployment strategies, and Helm chart structure for any application.

---

## Complete Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  namespace: production
  labels:
    app: app
    version: "1.0.0"
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels: { app: app }
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # allow 1 extra pod during rollout
      maxUnavailable: 0  # never reduce below desired count (zero-downtime)
  template:
    metadata:
      labels:
        app: app
        version: "1.0.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: app-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
        - name: app
          image: registry.example.com/app:1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
              name: http
              protocol: TCP
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secrets
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
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 12    # allow 60s for startup
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
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
            matchLabels: { app: app }
```

---

## Service Manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-svc
  namespace: production
  labels: { app: app }
spec:
  selector: { app: app }
  ports:
    - name: http
      port: 80
      targetPort: 8080
      protocol: TCP
  type: ClusterIP
```

---

## Ingress Manifest

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts: [app.example.com]
      secretName: app-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-svc
                port: { name: http }
```

---

## ConfigMap and Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  MAX_CONNECTIONS: "20"

---
# Use External Secrets Operator or Vault in production
# This shows structure only; never commit real secrets
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@postgres-svc:5432/appdb"
  SECRET_KEY: "change-me-in-production"
```

### External Secrets Operator (Production Pattern)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: production/app/database
        property: url
    - secretKey: SECRET_KEY
      remoteRef:
        key: production/app/config
        property: secret_key
```

---

## HPA -- Full Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    # Custom metric (requires prometheus-adapter)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Pods
          value: 4
          periodSeconds: 15
        - type: Percent
          value: 100
          periodSeconds: 15
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 60
```

**HPA rules:**
- Always set `resources.requests.cpu` in the Deployment -- HPA requires it
- Set `minReplicas: 2` for high availability
- `stabilizationWindowSeconds: 300` on scale-down prevents flapping
- Custom metrics require prometheus-adapter or kube-metrics-adapter

---

## PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
  namespace: production
spec:
  selector:
    matchLabels: { app: app }
  minAvailable: 2
```

---

## Helm Chart Structure

```
charts/app/
├── Chart.yaml
├── values.yaml
├── values.staging.yaml
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

### values.yaml

```yaml
image:
  repository: registry.example.com/app
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
  host: app.example.com
  tls: true

env:
  LOG_LEVEL: INFO
```

### Helm Commands

```bash
# Install
helm install app ./charts/app -f values.production.yaml -n production

# Upgrade
helm upgrade app ./charts/app -f values.production.yaml -n production

# Rollback
helm rollback app 1 -n production

# Dry-run
helm upgrade app ./charts/app --dry-run --debug -n production

# Template render
helm template app ./charts/app -f values.production.yaml
```

---

## kubectl Quick Reference

```bash
# Deployment management
kubectl apply -f k8s/
kubectl rollout status deployment/app -n production
kubectl rollout history deployment/app -n production
kubectl rollout undo deployment/app -n production

# Pod debugging
kubectl logs -f deployment/app -n production --tail=100
kubectl exec -it deployment/app -n production -- /bin/sh
kubectl describe pod <pod-name> -n production
kubectl top pods -n production

# Port forwarding
kubectl port-forward svc/app-svc 8080:80 -n production

# Resource usage
kubectl top nodes
kubectl top pods -n production --sort-by=memory

# Events
kubectl get events -n production --sort-by='.lastTimestamp'
```

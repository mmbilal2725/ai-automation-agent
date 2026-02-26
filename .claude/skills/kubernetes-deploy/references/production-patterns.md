# Production Best Practices

Production-grade Kubernetes deployment patterns based on official Kubernetes documentation and 2026 industry standards.

---

## Security Best Practices

### 1. Run as Non-Root User

**Why**: Mitigate container escape attacks, comply with pod security standards

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    fsGroup: 10001
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

**Dockerfile requirement**:
```dockerfile
# Create non-root user
RUN adduser -D -u 10001 appuser
USER 10001
```

### 2. Read-Only Root Filesystem

**Why**: Prevent runtime file modifications, reduce attack surface

```yaml
securityContext:
  readOnlyRootFilesystem: true
```

**Provide writable volumes**:
```yaml
volumeMounts:
- name: tmp
  mountPath: /tmp
- name: cache
  mountPath: /app/.cache
volumes:
- name: tmp
  emptyDir: {}
- name: cache
  emptyDir: {}
```

### 3. Drop All Capabilities

**Why**: Minimize privileges granted to containers

```yaml
securityContext:
  capabilities:
    drop:
    - ALL
```

### 4. External Secrets Management

**Never commit secrets to version control**. Use external secrets management:

**Option 1: Kubernetes Secrets (basic)**
```bash
kubectl create secret generic app-secrets \
  --from-literal=db-url='postgresql://...' \
  --from-literal=api-key='...'
```

**Option 2: HashiCorp Vault (recommended)**
```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "myapp"
  vault.hashicorp.com/agent-inject-secret-db: "secret/data/myapp/db"
```

**Option 3: AWS Secrets Manager, GCP Secret Manager, Azure Key Vault**
- Use ExternalSecrets Operator
- Sync cloud secrets to Kubernetes

### 5. Image Security

**Scan images for vulnerabilities**:
```bash
# Trivy scanning
trivy image myapp:1.0.0

# In CI/CD pipeline
docker build -t myapp:1.0.0 .
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:1.0.0
docker push myapp:1.0.0
```

**Use signed images (Cosign)**:
```bash
# Sign image
cosign sign myapp:1.0.0

# Verify signature
cosign verify myapp:1.0.0
```

**Enforce image pull policy**:
```yaml
containers:
- name: app
  image: myapp:1.0.0
  imagePullPolicy: Always  # Always pull latest, verify signatures
```

### 6. Network Policies

**Limit pod-to-pod communication**:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-network-policy
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          role: database
    ports:
    - protocol: TCP
      port: 5432
  - to:  # DNS
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

### 7. RBAC Policies

**Principle of least privilege**:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: myapp-role
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: myapp-rolebinding
subjects:
- kind: ServiceAccount
  name: myapp-sa
roleRef:
  kind: Role
  name: myapp-role
  apiGroup: rbac.authorization.k8s.io
---
# Use in deployment
spec:
  template:
    spec:
      serviceAccountName: myapp-sa
```

---

## High Availability Patterns

### 1. Multiple Replicas

**Minimum 3 replicas for production**:
```yaml
spec:
  replicas: 3
```

**Why**: Survive node failures, distribute load, enable zero-downtime updates

### 2. Pod Disruption Budgets (PDB)

**Prevent too many pods from being down simultaneously**:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
spec:
  minAvailable: 2  # At least 2 pods must remain available
  selector:
    matchLabels:
      app: myapp
---
# Alternative: maxUnavailable
spec:
  maxUnavailable: 1  # At most 1 pod can be unavailable
  selector:
    matchLabels:
      app: myapp
```

**Use cases**:
- Cluster upgrades
- Node maintenance
- Autoscaling down
- Voluntary disruptions

### 3. Pod Anti-Affinity

**Spread pods across nodes/zones**:

```yaml
spec:
  affinity:
    podAntiAffinity:
      # Hard requirement: MUST be on different nodes
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - myapp
        topologyKey: kubernetes.io/hostname
      # Soft preference: PREFER different zones
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - myapp
          topologyKey: topology.kubernetes.io/zone
```

### 4. Readiness Gates

**Coordinate with external systems before accepting traffic**:

```yaml
spec:
  template:
    spec:
      readinessGates:
      - conditionType: "example.com/load-balancer-ready"
```

---

## Resource Management

### 1. Define Requests and Limits

**Always specify resource requirements**:

```yaml
resources:
  requests:
    cpu: 250m      # 0.25 CPU cores
    memory: 512Mi  # 512 MiB RAM
  limits:
    cpu: 1000m     # 1 CPU core
    memory: 1Gi    # 1 GiB RAM
```

**Guidelines**:
- **Requests**: Minimum guaranteed resources (used for scheduling)
- **Limits**: Maximum allowed resources (enforced by kubelet)
- **CPU**: 1 CPU = 1000m (millicores)
- **Memory**: Use Mi (mebibytes) or Gi (gibibytes)

**Quality of Service (QoS) Classes**:
- **Guaranteed**: requests = limits for all resources
- **Burstable**: requests < limits
- **BestEffort**: no requests or limits (avoid in production)

### 2. Resource Quotas (Namespace-Level)

**Limit total resource consumption per namespace**:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    limits.cpu: "200"
    limits.memory: "400Gi"
    pods: "100"
    services: "50"
    persistentvolumeclaims: "50"
```

### 3. Limit Ranges (Pod-Level)

**Set default and maximum resources for pods**:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
spec:
  limits:
  - max:
      cpu: "2"
      memory: "4Gi"
    min:
      cpu: "100m"
      memory: "128Mi"
    default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "250m"
      memory: "256Mi"
    type: Container
```

---

## Rolling Updates and Rollbacks

### 1. Rolling Update Strategy

**Zero-downtime deployments**:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1         # 1 extra pod during update
      maxUnavailable: 0   # No pods can be unavailable
```

**Settings**:
- **maxSurge**: Extra pods allowed during update (can be number or percentage)
- **maxUnavailable**: Pods that can be unavailable during update

**Conservative (slower, safer)**:
```yaml
rollingUpdate:
  maxSurge: 1
  maxUnavailable: 0
```

**Aggressive (faster, riskier)**:
```yaml
rollingUpdate:
  maxSurge: 50%
  maxUnavailable: 50%
```

### 2. Deployment Annotations

**Record change cause**:
```yaml
metadata:
  annotations:
    kubernetes.io/change-cause: "Update to v2.0.0 with new features"
```

### 3. Rollout Commands

```bash
# Update image
kubectl set image deployment/myapp myapp=myapp:v2 --record

# Check rollout status
kubectl rollout status deployment/myapp

# View rollout history
kubectl rollout history deployment/myapp

# Rollback to previous version
kubectl rollout undo deployment/myapp

# Rollback to specific revision
kubectl rollout undo deployment/myapp --to-revision=3

# Pause rollout (apply multiple fixes)
kubectl rollout pause deployment/myapp
kubectl set image deployment/myapp myapp=myapp:v2
kubectl set resources deployment/myapp -c=myapp --limits=cpu=1,memory=1Gi
kubectl rollout resume deployment/myapp
```

---

## Health Checks and Monitoring

### 1. Comprehensive Probe Configuration

```yaml
containers:
- name: myapp
  # Startup probe: For slow-starting applications
  startupProbe:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 0
    periodSeconds: 10
    failureThreshold: 30  # 300 seconds max startup time

  # Liveness probe: Detect deadlocks, restart container
  livenessProbe:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3

  # Readiness probe: Detect when ready for traffic
  readinessProbe:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 5
    periodSeconds: 5
    timeoutSeconds: 3
    failureThreshold: 2
    successThreshold: 1
```

**Probe best practices**:
- Use same endpoint for all probes (simple, fast)
- Ensure endpoint responds quickly (<1s)
- Set higher failureThreshold for liveness (3-5)
- Set lower failureThreshold for readiness (1-2)
- Include startup probe for apps taking >30s to start

### 2. Metrics and Monitoring

**Expose Prometheus metrics**:
```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"
```

**Recommended metrics**:
- Request rate
- Error rate
- Response time (latency)
- Resource utilization (CPU, memory)
- Custom business metrics

---

## Scaling Patterns

### 1. Horizontal Pod Autoscaler (HPA)

**Multi-metric HPA with scaling behavior**:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max  # Most aggressive
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min  # Most conservative
```

**Key settings**:
- **minReplicas**: Minimum pods (never go below)
- **maxReplicas**: Maximum pods (cost control)
- **stabilizationWindowSeconds**: Prevent flapping
- **scaleUp policy**: Aggressive (respond quickly to load)
- **scaleDown policy**: Conservative (avoid premature scale-down)

### 2. Vertical Pod Autoscaler (VPA)

**Automatically adjust resource requests/limits**:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: myapp-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  updatePolicy:
    updateMode: "Auto"  # Auto, Recreate, Initial, Off
  resourcePolicy:
    containerPolicies:
    - containerName: myapp
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
```

**Note**: Don't use VPA with HPA on CPU/memory metrics simultaneously

### 3. Cluster Autoscaler

**Automatically add/remove nodes based on pod resource requests**:

- Adds nodes when pods can't be scheduled due to insufficient resources
- Removes nodes when utilization is low
- Cloud-provider specific (EKS, GKE, AKS)

---

## Namespace Organization

### Multi-Environment Strategy

```yaml
# development.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development
  labels:
    environment: development
---
# staging.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    environment: staging
---
# production.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    environment: production
```

**Apply resource quotas per environment**:
```yaml
# production-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
```

---

## Configuration Management

### 1. ConfigMaps for Non-Sensitive Data

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
  namespace: production
data:
  LOG_LEVEL: "info"
  ENVIRONMENT: "production"
  MAX_WORKERS: "4"
```

### 2. Secrets for Sensitive Data

```bash
kubectl create secret generic myapp-secrets \
  --namespace=production \
  --from-literal=db-url='postgresql://...' \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Immutable ConfigMaps/Secrets

**Prevent accidental modifications**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config-v1
immutable: true
data:
  config: "..."
```

**Benefits**:
- Protects from accidental updates
- Improves performance (kubelet doesn't watch)
- Forces versioning (create new ConfigMap for changes)

---

## Labels and Annotations

### Recommended Labels

```yaml
metadata:
  labels:
    app: myapp                          # Application name
    version: v1.0.0                     # Application version
    component: backend                  # Component type
    environment: production             # Environment
    tier: api                           # Architecture tier
    managed-by: kubernetes              # Management tool
    part-of: microservices-platform     # Larger application
```

### Useful Annotations

```yaml
metadata:
  annotations:
    # Deployment info
    kubernetes.io/change-cause: "Update to v2.0.0"
    deployment.kubernetes.io/revision: "3"

    # Monitoring
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"

    # Networking
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"

    # Documentation
    description: "FastAPI REST API for task management"
    owner: "platform-team"
    contact: "platform@example.com"
```

---

## Production Checklist

Before deploying to production, verify:

**Security**:
- [ ] Running as non-root user
- [ ] Read-only root filesystem
- [ ] All capabilities dropped
- [ ] Secrets stored externally (not in code)
- [ ] Container images scanned for vulnerabilities
- [ ] Network policies configured
- [ ] RBAC policies implemented

**High Availability**:
- [ ] Minimum 3 replicas
- [ ] Pod Disruption Budget configured
- [ ] Pod anti-affinity rules set
- [ ] Health checks configured (startup, liveness, readiness)
- [ ] Rolling update strategy defined

**Resource Management**:
- [ ] Resource requests and limits set
- [ ] Resource quotas configured (namespace)
- [ ] Limit ranges configured
- [ ] QoS class is Guaranteed or Burstable

**Scaling**:
- [ ] HPA configured with appropriate min/max
- [ ] Metrics Server installed
- [ ] Scaling policies tuned (stabilization windows)

**Monitoring**:
- [ ] Prometheus metrics exposed
- [ ] Logging configured
- [ ] Alerting rules defined
- [ ] Dashboards created

**Configuration**:
- [ ] ConfigMaps used for non-sensitive config
- [ ] Secrets used for sensitive data
- [ ] Environment-specific values separated
- [ ] Immutable ConfigMaps for stable configs

**Deployment**:
- [ ] Deployment annotations added
- [ ] Labels consistent across resources
- [ ] Namespace isolation implemented
- [ ] Rollback strategy documented

**Testing**:
- [ ] Load testing performed
- [ ] Failure scenarios tested
- [ ] Rollback tested
- [ ] Recovery procedures documented

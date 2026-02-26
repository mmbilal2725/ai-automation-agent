# Kubernetes Integration for Docker Python/FastAPI

Complete guide to preparing Docker images for Kubernetes deployment with health checks, probes, security contexts, and production patterns.

## Kubernetes Readiness Requirements

### 1. Health Checks

Kubernetes needs to know if your container is alive and ready to serve traffic.

**Add health endpoint to FastAPI:**

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Kubernetes probes.
    Returns 200 OK if application is healthy.
    """
    # Add checks: database connection, dependencies, etc.
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

**Add HEALTHCHECK to Dockerfile:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

### 2. Non-Root User

Kubernetes Pod Security Standards require non-root users.

```dockerfile
# Create user with specific UID
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

USER appuser
```

### 3. Graceful Shutdown

Handle SIGTERM signal for graceful shutdown.

```python
# main.py
import signal
import sys

def signal_handler(sig, frame):
    print('Gracefully shutting down...')
    # Close database connections, finish requests, etc.
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
```

### 4. Environment-Based Configuration

Use environment variables for configuration (12-factor app).

```python
# config.py
import os

DATABASE_URL = os.getenv("DB_URL", "postgresql://localhost/db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
```

## Kubernetes Deployment Manifest

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: app
        image: your-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Service (Load Balancer)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app
spec:
  type: LoadBalancer
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
```

### Secret for Database URL

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  url: "postgresql://user:password@postgres-host:5432/dbname?sslmode=require"
```

## Production-Ready Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  namespace: production
  labels:
    app: fastapi-app
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      # Security context (Pod level)
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault

      # Service account
      serviceAccountName: fastapi-app-sa

      containers:
      - name: app
        image: your-registry/fastapi-app:v1.2.3  # Specific version
        imagePullPolicy: IfNotPresent

        ports:
        - containerPort: 8000
          name: http
          protocol: TCP

        # Environment variables
        env:
        - name: ENV
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: DB_POOL_SIZE
          value: "5"
        - name: DB_MAX_OVERFLOW
          value: "10"

        # Security context (Container level)
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: true

        # Health probes
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3

        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 30

        # Resource management
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

        # Volume mounts (for read-only root filesystem)
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: app-tmp
          mountPath: /app/tmp

      # Volumes
      volumes:
      - name: tmp
        emptyDir: {}
      - name: app-tmp
        emptyDir: {}

      # Node selection
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: fastapi-app
              topologyKey: kubernetes.io/hostname
```

## Probe Types Explained

### Liveness Probe

Determines if container needs to be restarted.

**When to fail:**
- Application deadlock
- Unrecoverable error
- Process hung

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30  # Wait 30s after start
  periodSeconds: 30         # Check every 30s
  timeoutSeconds: 5         # 5s timeout
  failureThreshold: 3       # Restart after 3 failures
```

### Readiness Probe

Determines if container should receive traffic.

**When to fail:**
- Database not connected
- Dependency not available
- Warming up cache

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10  # Wait 10s after start
  periodSeconds: 10         # Check every 10s
  timeoutSeconds: 3         # 3s timeout
  failureThreshold: 3       # Remove from service after 3 failures
```

### Startup Probe

Determines if application has started (for slow-starting apps).

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  periodSeconds: 10
  failureThreshold: 30  # 30 * 10 = 300s (5min) max startup time
```

**Usage:** Disables liveness/readiness until startup succeeds.

## Advanced Health Checks

### Comprehensive Health Endpoint

```python
# health.py
from fastapi import FastAPI, status, Response
from sqlalchemy import text
from redis import Redis
import httpx

app = FastAPI()

async def check_database():
    """Check database connection."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database check failed: {e}")
        return False

async def check_redis():
    """Check Redis connection."""
    try:
        redis = Redis(host='redis', port=6379)
        redis.ping()
        return True
    except Exception as e:
        print(f"Redis check failed: {e}")
        return False

@app.get("/health")
async def health_check(response: Response):
    """
    Kubernetes health check with dependency checks.
    Returns 200 if healthy, 503 if unhealthy.
    """
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
    }

    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "checks": checks}

@app.get("/liveness")
async def liveness():
    """Simple liveness check - just return 200."""
    return {"status": "alive"}

@app.get("/readiness")
async def readiness(response: Response):
    """Readiness check - verify dependencies."""
    if await check_database():
        return {"status": "ready"}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}
```

**Use separate endpoints:**

```yaml
livenessProbe:
  httpGet:
    path: /liveness  # Simple check
    port: 8000

readinessProbe:
  httpGet:
    path: /readiness  # Dependency checks
    port: 8000
```

## Security Context Best Practices

### Pod Security Standards (PSS)

Kubernetes has three security levels:
1. **Privileged** - Unrestricted
2. **Baseline** - Minimal restrictions
3. **Restricted** - Heavily restricted (recommended)

**Restricted PSS requires:**

```yaml
securityContext:
  # Pod level
  runAsNonRoot: true
  runAsUser: 10001
  fsGroup: 10001
  seccompProfile:
    type: RuntimeDefault

  # Container level
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
```

### Read-Only Root Filesystem

Improves security by preventing writes to container filesystem.

**Dockerfile changes:**

```dockerfile
# Ensure app doesn't write to root filesystem
# Use /tmp for temporary files
ENV TMPDIR=/tmp

# Or create writable directory
RUN mkdir -p /app/tmp && chown appuser:appuser /app/tmp
```

**Kubernetes volumes:**

```yaml
volumeMounts:
- name: tmp
  mountPath: /tmp
- name: app-tmp
  mountPath: /app/tmp

volumes:
- name: tmp
  emptyDir: {}
- name: app-tmp
  emptyDir: {}
```

## Resource Management

### Setting Requests and Limits

```yaml
resources:
  requests:
    memory: "128Mi"  # Guaranteed minimum
    cpu: "100m"      # 0.1 CPU
  limits:
    memory: "512Mi"  # Maximum allowed
    cpu: "500m"      # 0.5 CPU
```

**Guidelines:**
- **requests**: What app needs to run
- **limits**: Maximum app can use
- Set limits 2-4x higher than requests
- Monitor actual usage and adjust

### Quality of Service (QoS)

| QoS Class | Condition | Priority |
|-----------|-----------|----------|
| **Guaranteed** | requests == limits | Highest (last to evict) |
| **Burstable** | requests < limits | Medium |
| **BestEffort** | No requests/limits | Lowest (first to evict) |

**Production recommendation:** Guaranteed or Burstable.

## ConfigMap for Application Config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastapi-config
data:
  LOG_LEVEL: "info"
  WORKERS: "4"
  TIMEOUT: "30"
  app.conf: |
    # Application configuration file
    timeout: 30
    max_connections: 100
```

**Use in Deployment:**

```yaml
env:
- name: LOG_LEVEL
  valueFrom:
    configMapKeyRef:
      name: fastapi-config
      key: LOG_LEVEL

volumeMounts:
- name: config
  mountPath: /app/config

volumes:
- name: config
  configMap:
    name: fastapi-config
    items:
    - key: app.conf
      path: app.conf
```

## Horizontal Pod Autoscaling (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 3
  maxReplicas: 10
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
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5min before scaling down
    scaleUp:
      stabilizationWindowSeconds: 60   # Wait 1min before scaling up
```

## Complete Kubernetes Deployment Example

```bash
# Directory structure
k8s/
├── namespace.yaml
├── secret.yaml
├── configmap.yaml
├── deployment.yaml
├── service.yaml
└── hpa.yaml
```

**Deploy:**

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment
kubectl get deployments -n production

# Check pods
kubectl get pods -n production

# Check service
kubectl get svc -n production

# View logs
kubectl logs -f deployment/fastapi-app -n production

# Describe pod (troubleshooting)
kubectl describe pod <pod-name> -n production

# Execute command in pod
kubectl exec -it <pod-name> -n production -- /bin/bash
```

## Debugging Kubernetes Deployments

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n production

# Describe pod for events
kubectl describe pod <pod-name> -n production

# Common issues:
# - ImagePullBackOff: Wrong image name or registry auth
# - CrashLoopBackOff: App crashes on startup
# - Pending: Resource constraints
```

### Probe Failures

```bash
# Check logs
kubectl logs <pod-name> -n production

# Common issues:
# - initialDelaySeconds too short
# - App not listening on 0.0.0.0
# - /health endpoint not implemented
# - Database not accessible
```

### Resource Issues

```bash
# Check resource usage
kubectl top pods -n production

# Check limits
kubectl describe pod <pod-name> -n production | grep -A 5 Limits

# Common issues:
# - Memory limit too low (OOMKilled)
# - CPU throttling
# - No resources available in cluster
```

## Best Practices Checklist

```markdown
### Docker Image
- [ ] Multi-stage build implemented
- [ ] Non-root user (UID 10001)
- [ ] Health check in Dockerfile
- [ ] Image size <200MB
- [ ] Specific version tag (not :latest)

### Application
- [ ] /health endpoint implemented
- [ ] Graceful shutdown (SIGTERM handling)
- [ ] Environment-based configuration
- [ ] Logging to stdout/stderr
- [ ] Connection pooling configured

### Kubernetes Manifest
- [ ] Liveness probe configured
- [ ] Readiness probe configured
- [ ] Resource requests and limits set
- [ ] Security context configured
- [ ] Secrets for sensitive data
- [ ] ConfigMaps for configuration
- [ ] Multiple replicas (HA)
- [ ] Pod anti-affinity rules

### Security
- [ ] runAsNonRoot: true
- [ ] allowPrivilegeEscalation: false
- [ ] readOnlyRootFilesystem: true
- [ ] Capabilities dropped
- [ ] Network policies defined
- [ ] RBAC configured
```

## References

- [Kubernetes Official Docs - Configure Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [12-Factor App](https://12factor.net/)

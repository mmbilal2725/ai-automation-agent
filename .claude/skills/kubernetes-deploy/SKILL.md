---
name: kubernetes-deploy
description: |
  Deploy and scale containerized applications using Kubernetes from hello world to production-grade systems.
  This skill should be used when users want to: (1) Deploy applications to Kubernetes clusters (local or cloud), (2) Create and manage Kubernetes resources (Deployments, Services, ConfigMaps, Secrets, Ingress), (3) Scale applications horizontally with autoscaling, (4) Configure health checks, readiness probes, and liveness probes, (5) Set up production-ready deployments with best practices, (6) Troubleshoot Kubernetes deployments, (7) Implement rolling updates and rollbacks, (8) Manage multi-environment deployments (dev, staging, production).
  Triggers include: "deploy to Kubernetes", "create k8s deployment", "scale pods", "set up ingress", "configure health checks", "production Kubernetes", "k8s best practices", "kubectl commands".
  Supports all containerized applications (Python, Node.js, Go, Java, etc.) across local and cloud environments.
---

# Kubernetes Deployment Skill

Deploy and scale containerized applications from hello world to production-grade systems.

## Requirements

- Kubernetes 1.25+ (for autoscaling/v2, ingress networking.k8s.io/v1)
- kubectl 1.25+
- Existing container image (any language: Python, Node.js, Go, Java, etc.)
- Kubernetes cluster access (local: minikube/kind, cloud: EKS/GKE/AKS)

## Before Implementation

Gather context to ensure successful deployment:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing Dockerfiles, container images, application structure, ports, environment variables |
| **Conversation** | User's deployment target (local/cloud), environment (dev/prod), scaling requirements, constraints |
| **Skill References** | Kubernetes patterns from `references/` (deployment strategies, service types, scaling configs) |
| **User Guidelines** | Project-specific naming conventions, namespace organization, resource limits |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (Kubernetes expertise is in this skill).

---

## Required Clarifications

Ask these questions if not inferrable from codebase/conversation:

1. **Container image**: Name and tag (e.g., `myapp:1.0.0`)
2. **Application port**: Container listening port (e.g., `8000`)
3. **Deployment target**: Local (minikube/kind) or cloud (EKS/GKE/AKS)
4. **Maturity level**: Hello world, development, or production

## Optional Clarifications

Ask only if relevant or user-specific:

5. **Environment variables**: Required config (DB_URL, API_KEY, etc.) - check .env files first
6. **Resource requirements**: CPU/memory if non-standard - use defaults otherwise
7. **Health endpoint**: If not `/health` - check codebase first
8. **Domain name**: For production Ingress - only if setting up TLS

**Note**: Avoid asking too many questions in a single message. Start with questions 1-4, then follow up if needed.

---

## How This Skill Works

```
User: "Deploy my app to Kubernetes"
       ↓
Gather context (image, ports, environment)
       ↓
Determine deployment level (hello world, dev, or production)
       ↓
Generate appropriate manifests with best practices
       ↓
Deploy and verify
```

## What This Skill Does

- **Creates Kubernetes manifests** (Deployments, Services, ConfigMaps, Secrets, Ingress, HPA)
- **Deploys applications** to local (minikube, kind) or cloud (EKS, GKE, AKS) clusters
- **Configures scaling** with Horizontal Pod Autoscaler
- **Sets up health checks** (liveness, readiness, startup probes)
- **Implements production patterns** (rolling updates, resource limits, security)
- **Provides kubectl commands** for deployment and troubleshooting
- **Adapts complexity** based on maturity (hello world → development → production)
- **Supports all languages**: Python, Node.js, Go, Java, etc. (language-agnostic)

## What This Skill Does NOT Do

- Create Docker images (use existing images or docker-python-fastapi-pro skill)
- Provision Kubernetes clusters (assumes cluster exists)
- Set up CI/CD pipelines (focuses on manifests and deployment)
- Configure cluster-level resources (ingress controllers, CSI drivers, Metrics Server)

---

## Deployment Levels

### Level 1: Hello World
**Purpose**: Learn Kubernetes basics, validate cluster connectivity

**Includes**: Simple Deployment (1 replica), ClusterIP Service, basic resource requests

**Use when**: Learning, testing cluster access, proof of concept

### Level 2: Development
**Purpose**: Development environment with essential features

**Includes**: Multi-replica Deployment, NodePort/LoadBalancer Service, ConfigMaps, health checks, resource limits, rolling update strategy

**Use when**: Development, staging, internal testing

### Level 3: Production
**Purpose**: Production-ready with security, scaling, monitoring

**Includes**: All Level 2 features, plus: HPA, Ingress with TLS, Secrets management, Pod Disruption Budgets, security contexts (non-root), comprehensive resource limits, anti-affinity rules

**Use when**: Production deployments, high availability requirements

---

## Implementation Workflow

### Step 1: Gather Application Context

Ask required clarifications (see above). Check codebase for:
- Dockerfile → ports, environment variables, health endpoints
- README/docs → deployment instructions
- .env files → configuration needs

### Step 2: Generate Manifests

Create manifests based on deployment level. See `references/manifest-patterns.md` for complete examples.

**File structure**:
```
k8s/
├── namespace.yaml (optional)
├── configmap.yaml
├── secret.yaml (if needed)
├── deployment.yaml
├── service.yaml
├── ingress.yaml (production)
└── hpa.yaml (production)
```

**Service type selection**:

| Target | Service Type | Reason |
|--------|--------------|--------|
| Local (minikube/kind) | NodePort | Easy access via node IP |
| Cloud (dev) | LoadBalancer | Automatic external IP |
| Cloud (prod) | ClusterIP + Ingress | Cost-effective, TLS termination |

### Step 3: Apply and Verify

```bash
# Create namespace (if used)
kubectl apply -f k8s/namespace.yaml

# Apply configs first
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Production: Ingress and HPA
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# ✅ Verify deployment
kubectl get pods                    # Check pod status (should be Running)
kubectl get deployments             # Check deployment ready (e.g., 3/3)
kubectl get services                # Check service endpoints
kubectl describe deployment <name>  # Verify configuration

# ✅ Verify health
kubectl logs -f deployment/<name>   # Check application logs
kubectl get events --sort-by='.lastTimestamp'  # Check for errors

# ✅ Test connectivity
kubectl get service <name>          # Note LoadBalancer IP or NodePort
curl http://<service-ip>/health     # Test health endpoint
```

See `references/kubectl-commands.md` for comprehensive command reference.

---

## Health Checks Configuration

**CRITICAL for production**. Configure all three probe types:

### Liveness Probe
Detect deadlocks/unrecoverable errors → Restart container

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

### Readiness Probe
Detect when container is ready to serve traffic

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 2
```

### Startup Probe
Allow slow-starting apps (>30s) to initialize

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  periodSeconds: 10
  failureThreshold: 30  # 300s max startup
```

**Best Practices**:
- Use same endpoint for all probes
- Higher `failureThreshold` for liveness (3-5) than readiness (1-2)
- Include startup probe for slow-starting apps
- Ensure health endpoint responds quickly (<1s)

See `references/health-checks.md` for detailed patterns.

---

## Scaling Configuration

### Manual Scaling
```bash
kubectl scale deployment <name> --replicas=5
kubectl get deployment <name>  # ✅ Verify
```

### Horizontal Pod Autoscaler (HPA)

**CPU-based scaling**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Requirements**:
- Deployment must have resource requests defined
- Metrics Server installed: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`

**Verify HPA**:
```bash
kubectl get hpa              # ✅ Check status
kubectl describe hpa <name>  # ✅ View metrics
kubectl top pods             # ✅ Verify metrics collection
```

See `references/scaling-patterns.md` for multi-metric configurations.

---

## Production Best Practices

### 1. Resource Management
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 2. Security
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

### 3. High Availability
```yaml
replicas: 3  # Minimum for HA
```

**Pod Disruption Budget**:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: myapp
```

### 4. Rolling Updates
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### 5. Secrets Management
```yaml
env:
- name: DB_URL
  valueFrom:
    secretKeyRef:
      name: app-secrets
      key: db-url
```

See `references/production-patterns.md` for comprehensive best practices.

---

## Common Anti-Patterns to Avoid

| ❌ Anti-Pattern | ✅ Best Practice |
|----------------|------------------|
| No resource limits | Always define requests and limits |
| Running as root user | Use non-root user (runAsUser: 10001) |
| No health checks | Configure liveness, readiness, startup probes |
| Hardcoded secrets in manifests | Use Kubernetes Secrets or external secret management |
| Single replica in production | Use minimum 3 replicas for HA |
| No Pod Disruption Budget | Configure PDB to prevent all pods going down |
| Writable root filesystem | Use readOnlyRootFilesystem: true |
| Using :latest tag | Use specific version tags (e.g., myapp:1.0.0) |
| No rolling update strategy | Configure maxSurge/maxUnavailable |
| Missing labels | Use consistent labels for all resources |

See `references/troubleshooting.md` for debugging these issues.

---

## Good vs Bad Examples

### Deployment: Resource Limits

**❌ Bad** (no limits):
```yaml
containers:
- name: app
  image: myapp:latest
  # No resource limits = unbounded resource usage
```

**✅ Good** (with limits):
```yaml
containers:
- name: app
  image: myapp:1.0.0  # Specific version
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
```

### Security Context

**❌ Bad** (default/root):
```yaml
containers:
- name: app
  image: myapp:latest
  # Runs as root by default
```

**✅ Good** (non-root):
```yaml
containers:
- name: app
  image: myapp:1.0.0
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    readOnlyRootFilesystem: true
```

---

## Troubleshooting Quick Reference

**Pods not starting**:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl get events --sort-by='.lastTimestamp'
```

**Service not accessible**:
```bash
kubectl get endpoints <service-name>
kubectl get pods --show-labels
kubectl describe service <service-name>
```

**HPA not scaling**:
```bash
kubectl top nodes
kubectl top pods
kubectl describe hpa <hpa-name>
```

See `references/troubleshooting.md` for comprehensive debugging guide (663 lines covering all common issues).

---

## Environment-Specific Configurations

### Local (minikube)
```bash
minikube start
eval $(minikube docker-env)
docker build -t myapp:latest .
kubectl apply -f k8s/
minikube service <service-name>
```

### Cloud (EKS/GKE/AKS)
```bash
# EKS
aws eks update-kubeconfig --name <cluster> --region <region>

# GKE
gcloud container clusters get-credentials <cluster> --region <region>

# AKS
az aks get-credentials --resource-group <rg> --name <cluster>

# Deploy
kubectl apply -f k8s/
```

---

## Reference Files

| File | Purpose |
|------|---------|
| `references/manifest-patterns.md` | Complete manifest templates (846 lines) |
| `references/kubectl-commands.md` | Comprehensive kubectl reference (658 lines) |
| `references/production-patterns.md` | Production best practices (785 lines) |
| `references/troubleshooting.md` | Debugging guide (663 lines) |
| `references/sources.md` | Official Kubernetes documentation sources |
| `examples/fastapi-prod/` | Production-ready FastAPI deployment example |

**Progressive learning path**: See `examples/README.md` for step-by-step guide from hello world to production.

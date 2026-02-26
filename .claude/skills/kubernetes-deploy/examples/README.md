# Kubernetes Deployment Examples

Progressive learning path from hello world to production-grade deployments.

---

## Progressive Learning Path

### Step 1: Hello World (5 minutes)
**Goal**: Understand basic Kubernetes concepts

Deploy a simple nginx container:
```bash
# Create deployment
kubectl create deployment nginx --image=nginx:alpine

# Expose as service
kubectl expose deployment nginx --port=80 --type=NodePort

# Check status
kubectl get pods
kubectl get services

# Access (minikube)
minikube service nginx
```

**Learn**: Pods, Deployments, Services, basic kubectl commands

---

### Step 2: Your First App (15 minutes)
**Goal**: Deploy your application with basic health checks

**Prerequisites**: Your app Docker image pushed to registry

```bash
# Create directory
mkdir -p k8s

# Create deployment.yaml
cat > k8s/deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: your-image:1.0.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

# Create service.yaml
cat > k8s/service.yaml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8000
EOF

# Deploy
kubectl apply -f k8s/

# Verify
kubectl get pods
kubectl describe deployment myapp
kubectl logs -f deployment/myapp

# Access
minikube service myapp
```

**Learn**: Health checks (liveness/readiness probes), resource limits, labels/selectors

---

### Step 3: Development Setup (30 minutes)
**Goal**: Add configuration management and scaling

**Add to your k8s/ directory**:

```bash
# Create configmap.yaml
cat > k8s/configmap.yaml <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  LOG_LEVEL: "debug"
  ENVIRONMENT: "development"
  MAX_WORKERS: "2"
EOF

# Create secret (don't commit this!)
kubectl create secret generic myapp-secrets \
  --from-literal=db-url='postgresql://localhost/dev' \
  --dry-run=client -o yaml > k8s/secret.yaml

# Update deployment to use ConfigMap and Secret
# Add to deployment.yaml containers section:
#   envFrom:
#   - configMapRef:
#       name: myapp-config
#   env:
#   - name: DB_URL
#     valueFrom:
#       secretKeyRef:
#         name: myapp-secrets
#         key: db-url

# Apply all
kubectl apply -f k8s/

# Test scaling
kubectl scale deployment myapp --replicas=3
kubectl get pods -w
```

**Learn**: ConfigMaps, Secrets, environment variables, manual scaling

---

### Step 4: Production Ready (1-2 hours)
**Goal**: Production-grade deployment with all best practices

**See complete example**: `examples/fastapi-prod/`

**Adds**:
- ✅ Namespace isolation
- ✅ Horizontal Pod Autoscaler (HPA)
- ✅ Ingress with TLS
- ✅ Pod Disruption Budget (PDB)
- ✅ Security contexts (non-root user, read-only filesystem)
- ✅ Pod anti-affinity rules
- ✅ Startup probes for slow-starting apps
- ✅ Proper resource requests and limits
- ✅ Rolling update strategy
- ✅ Production-grade labels and annotations

**Deploy production example**:
```bash
cd examples/fastapi-prod

# Create secrets (update with your values)
kubectl create secret generic fastapi-secrets \
  --namespace=production \
  --from-literal=db-url='your-production-db-url'

# Deploy
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml
kubectl apply -f pdb.yaml
kubectl apply -f ingress.yaml

# Verify
kubectl get all -n production
kubectl describe deployment fastapi -n production
kubectl get hpa -n production
```

**Learn**: Production best practices, security, high availability, autoscaling, ingress

---

## Example Structure

```
examples/
├── README.md              # This file (learning path)
└── fastapi-prod/          # Complete production example
    ├── README.md          # Detailed deployment guide
    ├── namespace.yaml     # Production namespace
    ├── configmap.yaml     # Non-sensitive configuration
    ├── deployment.yaml    # Production deployment (3 replicas)
    ├── service.yaml       # ClusterIP service
    ├── ingress.yaml       # HTTPS ingress with TLS
    ├── hpa.yaml           # Horizontal Pod Autoscaler
    └── pdb.yaml           # Pod Disruption Budget
```

---

## Key Concepts by Level

### Level 1 (Hello World)
- Pods
- Deployments
- Services (NodePort)
- Basic kubectl commands

### Level 2 (Development)
- ConfigMaps
- Secrets
- Health checks (liveness, readiness)
- Resource limits
- Labels and selectors
- Manual scaling

### Level 3 (Production)
- Namespaces
- Horizontal Pod Autoscaler (HPA)
- Ingress with TLS
- Pod Disruption Budgets (PDB)
- Security contexts
- Anti-affinity rules
- Startup probes
- Production-grade configurations

---

## Common Commands by Level

### Level 1
```bash
kubectl create deployment <name> --image=<image>
kubectl expose deployment <name> --port=<port>
kubectl get pods
kubectl get services
kubectl logs <pod-name>
```

### Level 2
```bash
kubectl apply -f k8s/
kubectl scale deployment <name> --replicas=<count>
kubectl rollout status deployment/<name>
kubectl describe deployment <name>
kubectl get events
```

### Level 3
```bash
kubectl apply -f k8s/ -n production
kubectl get all -n production
kubectl get hpa -n production
kubectl describe hpa <name> -n production
kubectl top pods -n production
kubectl rollout restart deployment/<name> -n production
kubectl rollout undo deployment/<name> -n production
```

---

## Troubleshooting by Level

### Level 1
**Pod not running**:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Level 2
**Service not accessible**:
```bash
kubectl get endpoints <service-name>
kubectl describe service <service-name>
kubectl port-forward deployment/<name> 8080:8000
```

### Level 3
**HPA not scaling**:
```bash
kubectl top nodes
kubectl top pods -n production
kubectl describe hpa <name> -n production
```

**Ingress not working**:
```bash
kubectl get ingress -n production
kubectl describe ingress <name> -n production
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

---

## Next Steps

1. **Start with Level 1**: Deploy nginx to understand basics
2. **Move to Level 2**: Deploy your app with health checks and ConfigMaps
3. **Advance to Level 3**: Review `examples/fastapi-prod/` for production patterns
4. **Read references**: Deep dive into `references/` for comprehensive patterns

**Reference documentation**:
- `references/manifest-patterns.md` - Complete manifest templates
- `references/kubectl-commands.md` - Comprehensive kubectl reference
- `references/production-patterns.md` - Production best practices
- `references/troubleshooting.md` - Debugging guide
- `references/sources.md` - Official Kubernetes documentation

---

## Tips for Success

1. **Always check codebase first** - Look for existing Dockerfiles, ports, env vars
2. **Start simple** - Begin with Level 1, add complexity as needed
3. **Verify each step** - Use `kubectl get`, `describe`, and `logs` commands
4. **Read error messages** - Kubernetes error messages are informative
5. **Use official docs** - When in doubt, check kubernetes.io
6. **Test locally first** - Use minikube or kind before deploying to cloud
7. **Version your images** - Never use `:latest` in production

---

## Quick Reference

| Need | Command |
|------|---------|
| Deploy app | `kubectl apply -f k8s/` |
| Check status | `kubectl get pods` |
| View logs | `kubectl logs -f deployment/<name>` |
| Scale manually | `kubectl scale deployment <name> --replicas=<count>` |
| Update image | `kubectl set image deployment/<name> <container>=<image>:<tag>` |
| Rollback | `kubectl rollout undo deployment/<name>` |
| Debug pod | `kubectl describe pod <pod-name>` |
| Access service | `kubectl port-forward service/<name> 8080:80` |
| Delete resources | `kubectl delete -f k8s/` |

**Happy deploying!**

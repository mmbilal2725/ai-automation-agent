# Production FastAPI Deployment Example

Complete production-grade Kubernetes deployment for the FastAPI Task Management application.

## Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or local)
- kubectl configured
- Docker image pushed to registry: `cloud-native-fastapi:latest`
- Neon PostgreSQL database URL
- Metrics Server installed (for HPA)
- Ingress controller installed (nginx-ingress)

## Features

- **Security**: Non-root user, read-only filesystem, dropped capabilities
- **High Availability**: 3 replicas, pod disruption budget, anti-affinity
- **Scaling**: Horizontal Pod Autoscaler (2-10 replicas)
- **Health Checks**: Startup, liveness, and readiness probes
- **Configuration**: ConfigMaps for non-sensitive data, Secrets for credentials
- **Networking**: ClusterIP service + Ingress with TLS
- **Resource Management**: Defined requests and limits
- **Rolling Updates**: Zero-downtime deployments

## Quick Start

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Create secrets (replace with your values)
kubectl create secret generic fastapi-secrets \
  --namespace=production \
  --from-literal=db-url='postgresql://user:pass@host.neon.tech/db?sslmode=require'

# 3. Apply configurations
kubectl apply -f configmap.yaml

# 4. Deploy application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 5. Set up autoscaling
kubectl apply -f hpa.yaml
kubectl apply -f pdb.yaml

# 6. Configure ingress (update host in ingress.yaml first)
kubectl apply -f ingress.yaml

# 7. Verify deployment
kubectl get all -n production
kubectl get ingress -n production
```

## File Structure

```
fastapi-prod/
├── README.md               # This file
├── namespace.yaml          # Production namespace
├── configmap.yaml          # Non-sensitive configuration
├── deployment.yaml         # Main application deployment
├── service.yaml            # ClusterIP service
├── ingress.yaml            # HTTPS ingress with TLS
├── hpa.yaml                # Horizontal Pod Autoscaler
└── pdb.yaml                # Pod Disruption Budget
```

## Configuration

### Update Before Deploying

1. **ingress.yaml**: Replace `api.example.com` with your domain
2. **Secret**: Create with your actual database URL
3. **Image**: Update image name/tag if different

### Environment Variables

**ConfigMap** (configmap.yaml):
- `LOG_LEVEL`: Logging verbosity
- `ENVIRONMENT`: Environment name
- `MAX_WORKERS`: Uvicorn workers

**Secret** (created via kubectl):
- `DB_URL`: PostgreSQL connection string

## Deployment Commands

### Initial Deployment

```bash
# Deploy all resources
kubectl apply -f .

# Watch rollout
kubectl rollout status deployment/fastapi -n production

# Check pods
kubectl get pods -n production

# View logs
kubectl logs -f deployment/fastapi -n production
```

### Update Application

```bash
# Update image
kubectl set image deployment/fastapi \
  fastapi=cloud-native-fastapi:v2 \
  -n production

# Monitor rollout
kubectl rollout status deployment/fastapi -n production

# Rollback if needed
kubectl rollout undo deployment/fastapi -n production
```

### Scale Manually

```bash
# Scale to 5 replicas
kubectl scale deployment fastapi --replicas=5 -n production

# Verify
kubectl get pods -n production
```

## Monitoring

### Check Status

```bash
# Get all resources
kubectl get all -n production

# Describe deployment
kubectl describe deployment fastapi -n production

# View events
kubectl get events -n production --sort-by='.lastTimestamp'

# Check HPA status
kubectl get hpa -n production
kubectl describe hpa fastapi-hpa -n production

# Resource usage
kubectl top pods -n production
kubectl top nodes
```

### View Logs

```bash
# Stream logs
kubectl logs -f deployment/fastapi -n production

# Logs from specific pod
kubectl logs <pod-name> -n production

# Previous logs (after crash)
kubectl logs <pod-name> -n production --previous
```

### Access Application

```bash
# Via ingress (if DNS configured)
curl https://api.example.com/health

# Via port forward (for testing)
kubectl port-forward -n production service/fastapi 8080:80
curl http://localhost:8080/health
```

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n production
kubectl logs <pod-name> -n production
```

### Service Not Accessible

```bash
kubectl get endpoints fastapi -n production
kubectl describe service fastapi -n production
```

### HPA Not Scaling

```bash
kubectl describe hpa fastapi-hpa -n production
kubectl top pods -n production
```

### Ingress Issues

```bash
kubectl describe ingress fastapi-ingress -n production
kubectl get ingress -n production
```

## Clean Up

```bash
# Delete all resources
kubectl delete -f .

# Or delete namespace (deletes everything)
kubectl delete namespace production
```

## Production Checklist

- [x] Running as non-root user (UID 10001)
- [x] Read-only root filesystem with writable volumes
- [x] All capabilities dropped
- [x] Resource requests and limits defined
- [x] Multiple replicas (3) for high availability
- [x] Pod Disruption Budget configured
- [x] Pod anti-affinity rules set
- [x] Health checks configured (startup, liveness, readiness)
- [x] Horizontal Pod Autoscaler configured
- [x] Secrets management implemented
- [x] Rolling update strategy defined
- [x] Ingress with TLS configured

## Security Notes

- Secrets are stored in Kubernetes Secrets (base64 encoded, not encrypted by default)
- For production, enable encryption at rest in etcd
- Consider using external secrets management (Vault, AWS Secrets Manager)
- Image pull policy set to Always to ensure latest security patches
- Container security context enforces non-root user and read-only filesystem

## Performance Notes

- HPA targets 70% CPU utilization
- Scales between 2-10 replicas
- Resource requests: 250m CPU, 512Mi memory
- Resource limits: 1 CPU, 1Gi memory
- Connection pooling configured in application

## High Availability

- Minimum 3 replicas running
- Pod Disruption Budget ensures at least 2 pods available during disruptions
- Anti-affinity rules spread pods across nodes
- Rolling update with maxUnavailable=0 ensures zero downtime

# kubectl Command Reference

Comprehensive kubectl command guide for Kubernetes deployment and management.

---

## Basic Syntax

```bash
kubectl [command] [TYPE] [NAME] [flags]
```

**Resource types** (case-insensitive):
- Singular: `kubectl get pod my-pod`
- Plural: `kubectl get pods my-pod`
- Abbreviated: `kubectl get po my-pod`

---

## Essential Commands

### Apply and Create

```bash
# Apply configuration from file
kubectl apply -f deployment.yaml

# Apply all files in directory
kubectl apply -f k8s/
kubectl apply -f k8s/ --recursive

# Create resource (imperative)
kubectl create deployment myapp --image=myapp:latest
kubectl create service clusterip myapp --tcp=80:8000

# Dry run (preview changes)
kubectl apply -f deployment.yaml --dry-run=client -o yaml
kubectl apply -f deployment.yaml --dry-run=server -o yaml
```

### Get Resources

```bash
# List resources
kubectl get pods
kubectl get deployments
kubectl get services
kubectl get all

# List across all namespaces
kubectl get pods --all-namespaces
kubectl get pods -A

# List in specific namespace
kubectl get pods -n production

# Watch for changes
kubectl get pods --watch
kubectl get pods -w

# Output formats
kubectl get pods -o wide
kubectl get pods -o yaml
kubectl get pods -o json
kubectl get pods -o jsonpath='{.items[*].metadata.name}'

# Show labels
kubectl get pods --show-labels
kubectl get pods -L app,version

# Filter by labels
kubectl get pods -l app=myapp
kubectl get pods -l app=myapp,environment=production
kubectl get pods -l 'environment in (production,staging)'
```

### Describe Resources

```bash
# Detailed resource information
kubectl describe pod my-pod
kubectl describe deployment myapp
kubectl describe service myapp
kubectl describe node node-1

# Describe all pods
kubectl describe pods

# Describe in namespace
kubectl describe pod my-pod -n production
```

### Logs

```bash
# View logs
kubectl logs my-pod

# Follow logs (stream)
kubectl logs -f my-pod

# Logs from specific container
kubectl logs my-pod -c container-name

# Previous container logs (after crash)
kubectl logs my-pod --previous

# Logs from all containers in pod
kubectl logs my-pod --all-containers

# Logs from deployment
kubectl logs deployment/myapp

# Tail last N lines
kubectl logs my-pod --tail=100

# Since timestamp
kubectl logs my-pod --since=1h
kubectl logs my-pod --since-time=2026-02-03T10:00:00Z
```

### Execute Commands in Containers

```bash
# Run command
kubectl exec my-pod -- ls /app

# Interactive shell
kubectl exec -it my-pod -- /bin/sh
kubectl exec -it my-pod -- /bin/bash

# Execute in specific container
kubectl exec my-pod -c container-name -- ls /

# Run command in deployment pod
kubectl exec deployment/myapp -- env
```

### Delete Resources

```bash
# Delete by name
kubectl delete pod my-pod
kubectl delete deployment myapp
kubectl delete service myapp

# Delete from file
kubectl delete -f deployment.yaml

# Delete all in directory
kubectl delete -f k8s/

# Delete by label
kubectl delete pods -l app=myapp

# Delete all pods in namespace
kubectl delete pods --all -n development

# Force delete (immediately)
kubectl delete pod my-pod --force --grace-period=0

# Delete namespace (deletes all resources in it)
kubectl delete namespace development
```

---

## Deployment Management

### Scaling

```bash
# Scale deployment
kubectl scale deployment myapp --replicas=5

# Scale multiple deployments
kubectl scale deployment myapp myapp2 --replicas=3

# Autoscale (create HPA)
kubectl autoscale deployment myapp --min=2 --max=10 --cpu-percent=70
```

### Rollout Management

```bash
# Check rollout status
kubectl rollout status deployment/myapp

# View rollout history
kubectl rollout history deployment/myapp

# View specific revision
kubectl rollout history deployment/myapp --revision=2

# Rollback to previous version
kubectl rollout undo deployment/myapp

# Rollback to specific revision
kubectl rollout undo deployment/myapp --to-revision=2

# Pause rollout
kubectl rollout pause deployment/myapp

# Resume rollout
kubectl rollout resume deployment/myapp

# Restart deployment (recreate pods)
kubectl rollout restart deployment/myapp
```

### Update Image

```bash
# Update container image
kubectl set image deployment/myapp myapp=myapp:v2

# Update multiple containers
kubectl set image deployment/myapp container1=image1:v2 container2=image2:v2

# Update image and record in rollout history
kubectl set image deployment/myapp myapp=myapp:v2 --record
```

### Edit Resources

```bash
# Edit deployment (opens in editor)
kubectl edit deployment myapp

# Edit with specific editor
KUBE_EDITOR="nano" kubectl edit deployment myapp

# Patch resource
kubectl patch deployment myapp -p '{"spec":{"replicas":3}}'

# Patch with file
kubectl patch deployment myapp --patch-file patch.yaml
```

---

## Namespace Management

```bash
# List namespaces
kubectl get namespaces
kubectl get ns

# Create namespace
kubectl create namespace production

# Delete namespace
kubectl delete namespace development

# Set default namespace for context
kubectl config set-context --current --namespace=production

# View current namespace
kubectl config view --minify --output 'jsonpath={..namespace}'
```

---

## ConfigMap and Secret Management

### ConfigMaps

```bash
# Create from literal values
kubectl create configmap myapp-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=ENVIRONMENT=production

# Create from file
kubectl create configmap myapp-config --from-file=config.yaml

# Create from directory
kubectl create configmap myapp-config --from-file=config/

# View configmap
kubectl get configmap myapp-config
kubectl get configmap myapp-config -o yaml

# Describe configmap
kubectl describe configmap myapp-config

# Edit configmap
kubectl edit configmap myapp-config

# Delete configmap
kubectl delete configmap myapp-config
```

### Secrets

```bash
# Create from literal values
kubectl create secret generic myapp-secrets \
  --from-literal=db-url='postgresql://user:pass@host/db' \
  --from-literal=api-key='secret-key'

# Create from file
kubectl create secret generic myapp-secrets --from-file=db-url=./db-url.txt

# Create TLS secret
kubectl create secret tls tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key

# Create Docker registry secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=email@example.com

# View secrets (values are hidden)
kubectl get secrets
kubectl get secret myapp-secrets

# View secret values (base64 decoded)
kubectl get secret myapp-secrets -o jsonpath='{.data.db-url}' | base64 -d

# Describe secret
kubectl describe secret myapp-secrets

# Delete secret
kubectl delete secret myapp-secrets
```

---

## Service and Networking

### Services

```bash
# Create service
kubectl create service clusterip myapp --tcp=80:8000
kubectl create service nodeport myapp --tcp=80:8000 --node-port=30080
kubectl create service loadbalancer myapp --tcp=80:8000

# Expose deployment as service
kubectl expose deployment myapp --port=80 --target-port=8000 --type=LoadBalancer

# Get services
kubectl get services
kubectl get svc

# Get service endpoints
kubectl get endpoints myapp

# Describe service
kubectl describe service myapp

# Delete service
kubectl delete service myapp
```

### Port Forwarding

```bash
# Forward local port to pod
kubectl port-forward pod/my-pod 8080:8000

# Forward to deployment
kubectl port-forward deployment/myapp 8080:8000

# Forward to service
kubectl port-forward service/myapp 8080:80

# Listen on all addresses
kubectl port-forward --address 0.0.0.0 pod/my-pod 8080:8000
```

### Ingress

```bash
# Get ingresses
kubectl get ingress
kubectl get ing

# Describe ingress
kubectl describe ingress myapp-ingress

# Delete ingress
kubectl delete ingress myapp-ingress
```

---

## Monitoring and Debugging

### Resource Usage

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods

# Pod resource usage in namespace
kubectl top pods -n production

# Pod resource usage with containers
kubectl top pods --containers

# Sort by CPU or memory
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory
```

### Events

```bash
# Get events
kubectl get events

# Get events sorted by timestamp
kubectl get events --sort-by='.lastTimestamp'

# Watch events
kubectl get events --watch

# Events for specific resource
kubectl get events --field-selector involvedObject.name=my-pod
```

### Debugging

```bash
# Check pod status
kubectl get pod my-pod
kubectl describe pod my-pod

# Check logs
kubectl logs my-pod
kubectl logs my-pod --previous

# Interactive debugging
kubectl exec -it my-pod -- /bin/sh

# Run temporary debug pod
kubectl run debug --rm -it --image=alpine -- sh

# Debug node
kubectl debug node/node-1 -it --image=ubuntu

# Copy files from pod
kubectl cp my-pod:/path/to/file ./local-file
kubectl cp ./local-file my-pod:/path/to/file
```

---

## Context and Configuration

### Contexts

```bash
# View current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context my-context

# Set namespace for context
kubectl config set-context --current --namespace=production

# Rename context
kubectl config rename-context old-name new-name

# Delete context
kubectl config delete-context my-context
```

### Cluster Info

```bash
# View cluster info
kubectl cluster-info

# View cluster info dump
kubectl cluster-info dump

# View API resources
kubectl api-resources

# View API versions
kubectl api-versions

# Explain resource fields
kubectl explain pod
kubectl explain deployment.spec
kubectl explain pod.spec.containers
```

---

## Advanced Commands

### Labels and Annotations

```bash
# Add label
kubectl label pods my-pod environment=production

# Update label
kubectl label pods my-pod environment=staging --overwrite

# Remove label
kubectl label pods my-pod environment-

# Add annotation
kubectl annotate pods my-pod description="My application pod"

# Remove annotation
kubectl annotate pods my-pod description-
```

### Taints and Tolerations

```bash
# Add taint to node
kubectl taint nodes node-1 key=value:NoSchedule

# Remove taint
kubectl taint nodes node-1 key=value:NoSchedule-

# View node taints
kubectl describe node node-1 | grep Taints
```

### Drain and Cordon

```bash
# Cordon node (mark unschedulable)
kubectl cordon node-1

# Uncordon node
kubectl uncordon node-1

# Drain node (evict pods)
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data

# Drain with grace period
kubectl drain node-1 --grace-period=300 --ignore-daemonsets
```

---

## Troubleshooting Commands

### Pod Issues

```bash
# Why is my pod not running?
kubectl get pod my-pod
kubectl describe pod my-pod
kubectl logs my-pod
kubectl get events --field-selector involvedObject.name=my-pod

# ImagePullBackOff
kubectl describe pod my-pod | grep -A 10 "Events"

# CrashLoopBackOff
kubectl logs my-pod --previous
kubectl describe pod my-pod
```

### Service Issues

```bash
# Service not accessible
kubectl get endpoints my-service
kubectl describe service my-service
kubectl get pods --show-labels
```

### Deployment Issues

```bash
# Deployment stuck
kubectl get deployment myapp
kubectl describe deployment myapp
kubectl get rs
kubectl describe rs <replicaset-name>
```

### HPA Issues

```bash
# HPA not scaling
kubectl get hpa
kubectl describe hpa myapp-hpa
kubectl top pods
kubectl top nodes
```

---

## Useful Flags

| Flag | Description |
|------|-------------|
| `-n, --namespace` | Specify namespace |
| `--all-namespaces, -A` | All namespaces |
| `-o, --output` | Output format (yaml, json, wide, etc.) |
| `-l, --selector` | Label selector |
| `--show-labels` | Show labels |
| `-w, --watch` | Watch for changes |
| `--dry-run=client` | Preview without applying |
| `--force` | Force operation |
| `--grace-period` | Seconds before force delete |
| `-f, --filename` | File or directory |
| `--recursive` | Process directory recursively |
| `--record` | Record command in rollout history |

---

## Quick Reference

```bash
# Get cluster info
kubectl cluster-info
kubectl get nodes

# Deploy application
kubectl apply -f k8s/
kubectl get all

# Check deployment
kubectl get pods
kubectl describe deployment myapp
kubectl logs -f deployment/myapp

# Scale
kubectl scale deployment myapp --replicas=3

# Update image
kubectl set image deployment/myapp myapp=myapp:v2
kubectl rollout status deployment/myapp

# Rollback
kubectl rollout undo deployment/myapp

# Debug
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl exec -it <pod-name> -- /bin/sh

# Clean up
kubectl delete -f k8s/
```

# Kubernetes Troubleshooting Guide

Comprehensive debugging guide for common Kubernetes issues based on official documentation and production experience.

---

## General Debugging Workflow

```
1. Check pod status          → kubectl get pods
2. Describe pod              → kubectl describe pod <name>
3. View logs                 → kubectl logs <name>
4. Check events              → kubectl get events --sort-by='.lastTimestamp'
5. Verify service/endpoints  → kubectl get endpoints <service>
6. Exec into container       → kubectl exec -it <pod> -- /bin/sh
```

---

## Pod Issues

### Pod Status: Pending

**Symptoms**: Pod stuck in `Pending` state

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Insufficient resources** | `kubectl describe pod <name>` shows "Insufficient cpu" or "Insufficient memory" | Reduce resource requests or add more nodes |
| **Node selector mismatch** | No nodes match pod's nodeSelector | Fix nodeSelector or add matching labels to nodes |
| **PersistentVolumeClaim not bound** | PVC status is `Pending` | Create PersistentVolume or fix storage class |
| **Image pull secrets missing** | Private registry auth failed | Create docker-registry secret |

**Debug commands**:
```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl get nodes
kubectl describe node <node-name>
kubectl top nodes
```

### Pod Status: ImagePullBackOff / ErrImagePull

**Symptoms**: Pod cannot pull container image

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Image doesn't exist** | `kubectl describe pod` shows 404 error | Fix image name/tag in deployment |
| **Private registry auth** | `kubectl describe pod` shows auth error | Create image pull secret |
| **Network issues** | Can't reach registry | Check network policies, firewall |
| **Rate limiting** | Docker Hub rate limit exceeded | Use authenticated pulls or mirror |

**Debug commands**:
```bash
kubectl describe pod <pod-name>
kubectl get events --field-selector involvedObject.name=<pod-name>

# Check image pull secret
kubectl get secret <secret-name> -o yaml
kubectl describe secret <secret-name>
```

**Create image pull secret**:
```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=<user> \
  --docker-password=<pass> \
  --docker-email=<email>

# Add to deployment
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
```

### Pod Status: CrashLoopBackOff

**Symptoms**: Container starts, then crashes repeatedly

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Application error** | `kubectl logs <pod>` shows error | Fix application code |
| **Missing environment variables** | App fails due to missing config | Add required env vars |
| **Failed health checks** | Liveness probe kills container | Fix probe config or app health endpoint |
| **Permission issues** | Read-only filesystem, wrong user | Fix security context or volume mounts |

**Debug commands**:
```bash
# View current logs
kubectl logs <pod-name>

# View previous container logs (after crash)
kubectl logs <pod-name> --previous

# Check all containers in pod
kubectl logs <pod-name> --all-containers

# Stream logs
kubectl logs -f <pod-name>

# Describe pod for events
kubectl describe pod <pod-name>
```

**Common fixes**:

**1. Missing writable directories (read-only filesystem)**:
```yaml
spec:
  containers:
  - name: app
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

**2. Wrong user permissions**:
```yaml
securityContext:
  runAsUser: 10001
  fsGroup: 10001
```

**3. Failed liveness probe**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30  # Give app time to start
  failureThreshold: 5      # Allow more failures before restart
```

### Pod Status: CreateContainerConfigError

**Symptoms**: Cannot create container configuration

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Missing ConfigMap** | `kubectl describe pod` shows ConfigMap not found | Create ConfigMap or fix name |
| **Missing Secret** | `kubectl describe pod` shows Secret not found | Create Secret or fix name |
| **Invalid ConfigMap key** | Key doesn't exist in ConfigMap | Fix key name or add to ConfigMap |

**Debug commands**:
```bash
kubectl describe pod <pod-name>
kubectl get configmap <name> -o yaml
kubectl get secret <name> -o yaml
```

### Pod Status: OOMKilled (Out of Memory)

**Symptoms**: Container killed due to out-of-memory

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Memory limit too low** | `kubectl describe pod` shows OOMKilled | Increase memory limit |
| **Memory leak** | Memory usage grows over time | Fix application memory leak |
| **No limit set** | Pod uses all node memory | Set appropriate memory limits |

**Debug commands**:
```bash
kubectl describe pod <pod-name>
kubectl top pod <pod-name>
kubectl logs <pod-name> --previous

# Check resource usage
kubectl top pods --containers
kubectl top nodes
```

**Fix**:
```yaml
resources:
  requests:
    memory: 512Mi
  limits:
    memory: 1Gi  # Increase as needed
```

---

## Service and Networking Issues

### Service Not Accessible

**Symptoms**: Cannot reach service from inside or outside cluster

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **No endpoints** | `kubectl get endpoints <service>` is empty | Fix pod labels to match service selector |
| **Wrong port** | Service port doesn't match container port | Fix targetPort in service |
| **Pods not ready** | Pods failing readiness probe | Fix readiness probe or app |
| **Network policy blocking** | Network policy denies traffic | Update network policy |

**Debug commands**:
```bash
# Check service
kubectl get service <service-name>
kubectl describe service <service-name>

# Check endpoints
kubectl get endpoints <service-name>

# Check pod labels
kubectl get pods --show-labels
kubectl get pods -l app=myapp

# Verify service selector
kubectl describe service <service-name> | grep Selector

# Test from another pod
kubectl run curl --image=curlimages/curl -it --rm -- sh
curl http://<service-name>.<namespace>.svc.cluster.local
```

**Common fixes**:

**1. Labels don't match**:
```yaml
# Service selector
spec:
  selector:
    app: myapp  # Must match pod labels

# Pod labels
metadata:
  labels:
    app: myapp  # Must match service selector
```

**2. Wrong target port**:
```yaml
# Service
spec:
  ports:
  - port: 80
    targetPort: 8000  # Must match container port

# Container
spec:
  containers:
  - name: app
    ports:
    - containerPort: 8000  # Must match targetPort
```

### LoadBalancer External IP Pending

**Symptoms**: LoadBalancer service stuck with `<pending>` external IP

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Cloud provider not configured** | No load balancer controller | Install cloud provider integration |
| **Local cluster (minikube/kind)** | No external load balancer support | Use NodePort or `minikube tunnel` |
| **Quota exceeded** | Cloud provider quota limit reached | Request quota increase |

**Debug commands**:
```bash
kubectl get service <service-name>
kubectl describe service <service-name>

# minikube
minikube tunnel

# kind (use NodePort instead)
kubectl patch svc <service-name> -p '{"spec":{"type":"NodePort"}}'
```

### Ingress Not Working

**Symptoms**: Cannot access application via Ingress

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Ingress controller not installed** | No ingress controller pods | Install ingress controller (nginx, traefik) |
| **Wrong ingress class** | IngressClass doesn't match controller | Fix ingressClassName |
| **DNS not configured** | Host doesn't resolve | Configure DNS or use `/etc/hosts` |
| **TLS secret missing** | Certificate secret not found | Create TLS secret |

**Debug commands**:
```bash
# Check ingress
kubectl get ingress
kubectl describe ingress <ingress-name>

# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Test backend service directly
kubectl port-forward service/<service-name> 8080:80
```

**Install nginx ingress controller**:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

---

## Deployment Issues

### Deployment Stuck (Rollout Not Progressing)

**Symptoms**: Deployment doesn't reach desired state

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Image pull issues** | Pods stuck in ImagePullBackOff | Fix image or add pull secret |
| **Insufficient resources** | Pods stuck in Pending | Add nodes or reduce requests |
| **Failed health checks** | Pods CrashLoopBackOff | Fix health checks or app |
| **Deployment paused** | Rollout manually paused | Resume rollout |

**Debug commands**:
```bash
kubectl get deployments
kubectl describe deployment <deployment-name>
kubectl rollout status deployment/<deployment-name>
kubectl rollout history deployment/<deployment-name>

# Check ReplicaSets
kubectl get rs
kubectl describe rs <replicaset-name>
```

**Resume paused deployment**:
```bash
kubectl rollout resume deployment/<deployment-name>
```

---

## Autoscaling Issues

### HPA Not Scaling

**Symptoms**: HorizontalPodAutoscaler not creating/deleting pods

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Metrics Server not installed** | `kubectl top pods` fails | Install Metrics Server |
| **No resource requests** | Deployment missing resource requests | Add resource requests |
| **Metrics not available** | HPA shows `<unknown>` | Wait for metrics collection or check Metrics Server |
| **Target already met** | Current utilization within target | Adjust target or wait for load |

**Debug commands**:
```bash
# Check HPA status
kubectl get hpa
kubectl describe hpa <hpa-name>

# Check metrics
kubectl top pods
kubectl top nodes

# Check Metrics Server
kubectl get deployment metrics-server -n kube-system
kubectl logs -n kube-system -l k8s-app=metrics-server
```

**Install Metrics Server**:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**Fix missing resource requests**:
```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
```

---

## ConfigMap and Secret Issues

### ConfigMap/Secret Not Updating in Pods

**Symptoms**: Pod still using old ConfigMap/Secret values

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **Environment variables** | Env vars don't auto-update | Restart pods or use volume mounts |
| **Volume mount cache** | Volume takes time to update | Wait (up to kubelet sync period) or force restart |
| **Immutable ConfigMap** | ConfigMap marked immutable | Create new ConfigMap with new name |

**Solutions**:

**1. Restart deployment to pick up changes**:
```bash
kubectl rollout restart deployment/<deployment-name>
```

**2. Use volume mounts (auto-update)**:
```yaml
containers:
- name: app
  volumeMounts:
  - name: config
    mountPath: /etc/config
volumes:
- name: config
  configMap:
    name: app-config
```

**3. Version ConfigMaps** (recommended for production):
```yaml
# Create new ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-v2  # New name
data:
  config: "new value"
---
# Update deployment
spec:
  template:
    spec:
      volumes:
      - name: config
        configMap:
          name: app-config-v2  # Reference new ConfigMap
```

---

## Node Issues

### Node NotReady

**Symptoms**: Node in `NotReady` state

**Debug commands**:
```bash
kubectl get nodes
kubectl describe node <node-name>
kubectl get pods -o wide  # See which pods are on node

# SSH to node and check
systemctl status kubelet
journalctl -u kubelet -f
```

### Node Running Out of Resources

**Symptoms**: Pods evicted, node pressure

**Debug commands**:
```bash
kubectl top nodes
kubectl describe node <node-name>
kubectl get pods --all-namespaces -o wide --field-selector spec.nodeName=<node-name>

# Check for evicted pods
kubectl get pods --all-namespaces --field-selector status.phase=Failed
```

---

## Persistent Volume Issues

### PersistentVolumeClaim Pending

**Symptoms**: PVC stuck in `Pending` state

**Causes and Solutions**:

| Cause | Check | Solution |
|-------|-------|----------|
| **No PV available** | No matching PV | Create PV or use dynamic provisioning |
| **Storage class missing** | StorageClass not found | Create StorageClass or fix name |
| **Access mode mismatch** | PV and PVC access modes don't match | Fix access modes |

**Debug commands**:
```bash
kubectl get pvc
kubectl describe pvc <pvc-name>
kubectl get pv
kubectl get storageclass
```

---

## General Debugging Tips

### View All Resources

```bash
# All resources in current namespace
kubectl get all

# All resources in all namespaces
kubectl get all -A

# Specific resource types
kubectl get pods,services,deployments,ingress
```

### Check Events

```bash
# Recent events
kubectl get events --sort-by='.lastTimestamp'

# Watch events
kubectl get events --watch

# Events for specific resource
kubectl get events --field-selector involvedObject.name=<pod-name>
```

### Debug with Temporary Pod

```bash
# Run debug pod
kubectl run debug --rm -it --image=alpine -- sh

# Run debug pod with network tools
kubectl run debug --rm -it --image=nicolaka/netshoot -- sh

# Debug specific node
kubectl debug node/<node-name> -it --image=ubuntu
```

### Copy Files from Pod

```bash
# Copy file from pod
kubectl cp <pod-name>:/path/to/file ./local-file

# Copy file to pod
kubectl cp ./local-file <pod-name>:/path/to/file
```

### Port Forward for Local Testing

```bash
# Forward to pod
kubectl port-forward pod/<pod-name> 8080:8000

# Forward to service
kubectl port-forward service/<service-name> 8080:80

# Forward to deployment
kubectl port-forward deployment/<deployment-name> 8080:8000
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ImagePullBackOff` | Cannot pull image | Fix image name or add pull secret |
| `CrashLoopBackOff` | Container keeps crashing | Check logs, fix app or health checks |
| `Pending` | Cannot schedule pod | Check resources, node selector, PVC |
| `OOMKilled` | Out of memory | Increase memory limit |
| `CreateContainerConfigError` | Missing ConfigMap/Secret | Create ConfigMap/Secret or fix reference |
| `ErrImagePull` | Image pull failed | Check image name, registry access |
| `InvalidImageName` | Invalid image name | Fix image name format |
| `RunContainerError` | Cannot start container | Check container command, volumes |

---

## Debug Checklist

When troubleshooting Kubernetes issues:

1. **Check pod status**
   ```bash
   kubectl get pods
   ```

2. **Describe pod for detailed info**
   ```bash
   kubectl describe pod <pod-name>
   ```

3. **View pod logs**
   ```bash
   kubectl logs <pod-name>
   kubectl logs <pod-name> --previous
   ```

4. **Check events**
   ```bash
   kubectl get events --sort-by='.lastTimestamp'
   ```

5. **Verify service endpoints**
   ```bash
   kubectl get endpoints <service-name>
   ```

6. **Check resource usage**
   ```bash
   kubectl top pods
   kubectl top nodes
   ```

7. **Test connectivity**
   ```bash
   kubectl port-forward <pod-name> 8080:8000
   ```

8. **Exec into container**
   ```bash
   kubectl exec -it <pod-name> -- /bin/sh
   ```

9. **Check deployment/replicaset**
   ```bash
   kubectl get deployments
   kubectl get rs
   ```

10. **Review configuration**
    ```bash
    kubectl get <resource> <name> -o yaml
    ```

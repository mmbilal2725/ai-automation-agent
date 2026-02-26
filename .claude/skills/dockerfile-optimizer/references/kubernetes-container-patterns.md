# Kubernetes Container Optimization Patterns

K8s-specific optimization strategies for faster deployments and efficient resource usage.

---

## Why Image Size Matters in Kubernetes

### Pull Time Impact

Research shows that **image download accounts for 76% of container startup time**, but only 6.4% of fetched data is actually needed for startup.

### Scaling Implications

| Image Size | Pull Time (100Mbps) | Scaling Impact |
|------------|---------------------|----------------|
| 50 MB | ~4 seconds | Fast horizontal scaling |
| 200 MB | ~16 seconds | Moderate delay |
| 500 MB | ~40 seconds | Slow scaling response |
| 1 GB | ~80 seconds | Very slow, impacts availability |
| 5+ GB (AI/ML) | 5+ minutes | Critical bottleneck |

**In production**: Faster pulls = faster scaling = better availability during traffic spikes.

---

## Image Pull Policies

Configure pull behavior based on deployment patterns.

### Policy Options

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1.2.3
        imagePullPolicy: IfNotPresent  # or Always, Never
```

### Policy Strategies

| Policy | When to Use | Caching Behavior |
|--------|-------------|------------------|
| `IfNotPresent` | **Recommended** - Pinned tags (v1.2.3) | Pull only if not cached on node |
| `Always` | Development, `:latest` tags | Pull every time, verify digest |
| `Never` | Pre-populated node caches | Never pull, fail if not present |

**Best Practice**: Use semantic versioning tags (v1.2.3) with `IfNotPresent` for production.

### Default Behavior

- If tag is `:latest` → `imagePullPolicy: Always`
- If specific tag → `imagePullPolicy: IfNotPresent`
- Can override with explicit policy

---

## Node-Level Image Caching

Kubernetes caches images locally on nodes after first pull.

### How It Works

1. First pod deployment: Pull image from registry
2. Subsequent deployments: Reuse cached image
3. Cache persists across pod restarts and updates
4. Different nodes maintain independent caches

### Optimization Strategy

**Pre-warm critical nodes**:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: image-preloader
spec:
  template:
    spec:
      initContainers:
      - name: preload
        image: myapp:v1.2.3
        command: ['sh', '-c', 'echo "Image cached"']
      containers:
      - name: pause
        image: gcr.io/google-containers/pause:3.1
```

**Benefit**: Pre-pulls images to all nodes, eliminating pull time for actual workloads.

---

## Pull-Through Proxy Caches

Act as intermediary between cluster and upstream registries.

### How They Work

```
Kubernetes Node → Pull-Through Cache → Upstream Registry
                  ↓
                Cache Hit: Serve from cache
                Cache Miss: Pull from upstream, cache, serve
```

### Popular Solutions

| Solution | Type | Features |
|----------|------|----------|
| **Harbor** | CNCF Graduated | Enterprise-grade, replication, scanning |
| **Sonatype Nexus** | Commercial | Multi-format registry, access control |
| **JFrog Artifactory** | Commercial | Universal artifact management |
| **Registry Mirror** | Docker | Simple HTTP registry cache |

### Benefits
- **Faster pulls**: Local network speeds vs internet
- **Reduced bandwidth**: Pull from upstream once, serve many times
- **Resilience**: Continue operating if upstream is down
- **Rate limit avoidance**: Single upstream pull for multiple nodes

### Configuration Example (Docker Hub Mirror)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: docker-config
data:
  daemon.json: |
    {
      "registry-mirrors": ["https://mirror.company.local"]
    }
```

---

## Lazy Loading / Image Streaming

Download data in parallel with application startup.

### The Problem

Traditional pull: Download entire image → Extract → Start container

**Issue**: Applications often need <10% of image data to start.

### Solutions

#### 1. SOCI (Seekable OCI)

AWS technology for lazy loading container images:
- Allows containers to start before entire image is pulled
- Pulls data on-demand as application accesses it
- Reduces startup time by 50-80% for large images

#### 2. eStargz

Seekable tar.gz format enabling lazy pulling:
- Application starts almost instantly
- Rest of image pulls in background
- Compatible with standard OCI registries

### When to Use

- **Large images** (>500 MB): Significant startup improvement
- **AI/ML workloads**: Multi-GB models can start before full download
- **Frequent scaling**: Faster response to load spikes

### Trade-offs

- Initial runtime may be slower (fetching on access)
- Requires registry support
- More complex infrastructure

---

## Layer Sharing and OverlayFS

Kubernetes uses OverlayFS to share layers between images.

### How It Works

```
Image A: [base layer] [app layer 1] [app layer 2]
Image B: [base layer] [app layer 3]

Disk Usage: base layer (once) + app layer 1 + app layer 2 + app layer 3
```

**Benefit**: Multiple images sharing base layers only store differences.

### Optimization Strategy

**Standardize base images** across organization:
- All Python apps use `python:3.11-slim`
- All Node apps use `node:20-alpine`
- All Go apps use `distroless/static`

**Result**: First image pulls base, subsequent images only pull app layers.

### Example Savings

```
Without sharing:
  App1 (500 MB) + App2 (500 MB) + App3 (500 MB) = 1.5 GB

With shared base (400 MB common):
  Base (400 MB) + App1 (100 MB) + App2 (100 MB) + App3 (100 MB) = 700 MB
```

**53% disk savings** from layer sharing.

---

## Image Pre-pulling Strategies

Reduce deployment latency by pre-populating caches.

### 1. DaemonSet Pre-warming

Deploy DaemonSet to pull images to all nodes:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: image-preloader
spec:
  selector:
    matchLabels:
      name: image-preloader
  template:
    metadata:
      labels:
        name: image-preloader
    spec:
      initContainers:
      - name: pull-app-v1
        image: myapp:v1.2.3
        command: ['sh', '-c', 'exit 0']
      - name: pull-app-v2
        image: myapp:v1.2.4
        command: ['sh', '-c', 'exit 0']
      containers:
      - name: pause
        image: gcr.io/google-containers/pause:3.1
```

### 2. Kube-fledged

Kubernetes add-on for managed image caching:

```yaml
apiVersion: kubefledged.io/v1alpha2
kind: ImageCache
metadata:
  name: imagecache
spec:
  cacheSpec:
  - images:
    - myapp:v1.2.3
    - myapp:v1.2.4
```

**Features**:
- Declarative image cache management
- Automatic refresh on image updates
- Node selector support

### 3. Spegel (K3s Embedded)

K3s includes Spegel as in-cluster registry mirror:
- P2P image distribution between nodes
- Reduces registry load
- Faster pulls within cluster

---

## Registry Optimization

### Use Geographically Close Registries

| Registry Location | Pull Time Impact |
|-------------------|------------------|
| Same region | Baseline |
| Cross-region (same cloud) | 2-3x slower |
| Different cloud provider | 3-5x slower |
| On-premise to cloud | 5-10x slower |

**Strategy**: Use cloud provider's container registry in same region as cluster.

### Registry Options by Cloud

| Provider | Registry | Benefits |
|----------|----------|----------|
| AWS | Amazon ECR | VPC endpoints, IAM integration |
| Google Cloud | Artifact Registry | GKE integration, vulnerability scanning |
| Azure | Azure ACR | AKS integration, geo-replication |
| Self-hosted | Harbor | Multi-cloud, on-premise support |

### Avoid Docker Hub Rate Limits

Docker Hub imposes pull rate limits:
- **Anonymous**: 100 pulls per 6 hours per IP
- **Free account**: 200 pulls per 6 hours
- **Pro account**: Unlimited

**Solutions**:
1. Use Docker Hub credentials (increase limit)
2. Mirror frequently used images to private registry
3. Use alternative registries (GitHub Container Registry, Quay.io)

---

## Parallel Image Pulls

Control concurrent image pulls per node.

### Configuration

Kubelet flags:
```yaml
# kubelet config
serializeImagePulls: false  # Enable parallel pulls
maxParallelImagePulls: 5    # Limit concurrent pulls (optional)
```

### Trade-offs

| Setting | Benefit | Cost |
|---------|---------|------|
| Serial (default) | Predictable, lower network usage | Slower multi-image deployment |
| Parallel (limited) | Faster multi-image deployment | Higher network usage |
| Parallel (unlimited) | Fastest deployment | Can overwhelm network/registry |

**Recommendation**: Enable parallel with limit (5-10) for balanced performance.

---

## Resource Management

### Configure Resource Limits

Prevent image pulls from saturating node resources:

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: myapp:v1.2.3
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

### Ephemeral Storage

Image pulls consume ephemeral storage:

```yaml
resources:
  limits:
    ephemeral-storage: "4Gi"
```

**Why**: Prevents image pulls from filling node disk.

---

## Deployment Strategies for Image Updates

### Rolling Update (Default)

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

**Impact**: Pulls new image to nodes incrementally during rollout.

### Blue-Green Deployment

1. Deploy new version (green) alongside old (blue)
2. Pre-pull images to all green pods
3. Switch traffic to green
4. Terminate blue

**Benefit**: All image pulls complete before traffic switch.

### Canary Deployment

1. Deploy small percentage of new version
2. Monitor metrics
3. Gradually increase percentage

**Benefit**: Limits impact of pull failures or bad images.

---

## Optimization Checklist for Kubernetes

### Image Design
- [ ] Multi-stage builds for minimal size
- [ ] Base image <100 MB if possible
- [ ] Standardized base images across organization
- [ ] Semantic versioning tags (no `:latest`)

### Pull Configuration
- [ ] `imagePullPolicy: IfNotPresent` for tagged images
- [ ] Use registry in same region as cluster
- [ ] Configure Docker Hub authentication (avoid rate limits)
- [ ] Enable parallel image pulls with reasonable limit

### Caching Strategy
- [ ] Pre-warm nodes with DaemonSet or kube-fledged
- [ ] Consider pull-through cache (Harbor) for large clusters
- [ ] Leverage layer sharing with common base images

### Registry
- [ ] Use cloud provider registry in same region
- [ ] Enable vulnerability scanning
- [ ] Implement image retention policies (clean old images)

### Monitoring
- [ ] Track image pull duration metrics
- [ ] Alert on pull failures
- [ ] Monitor node disk usage (ephemeral storage)
- [ ] Track registry bandwidth costs

---

## Performance Impact Summary

| Optimization | Effort | Impact |
|--------------|--------|--------|
| Reduce image size by 75% | Medium | 75% faster pulls |
| Use regional registry | Low | 50-70% faster pulls |
| Pre-warm critical nodes | Medium | 100% faster first-pod startup |
| Pull-through cache | High | 50-80% faster pulls cluster-wide |
| Layer sharing | Low | 30-50% less disk usage |
| Lazy loading (SOCI) | High | 50-80% faster startup for large images |

**Combined effect**: Optimized setup can achieve 10x faster deployments vs default configuration.

---

## References

- [Kubernetes Image Pull Policy](https://kubernetes.io/docs/concepts/containers/images/#image-pull-policy)
- [Improving Image Pull Performance](https://kubernetes.io/blog/2023/05/15/speed-up-pod-startup/)
- [Harbor Documentation](https://goharbor.io/docs/)
- [AWS SOCI Lazy Loading](https://aws.amazon.com/blogs/containers/start-pods-faster-by-prefetching-images/)
- [Kube-fledged Project](https://github.com/senthilrch/kube-fledged)

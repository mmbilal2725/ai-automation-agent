# Kubernetes Manifest Patterns

Complete manifest templates for all deployment levels with official Kubernetes specifications.

---

## Table of Contents

1. [Deployment Patterns](#deployment-patterns)
2. [Service Patterns](#service-patterns)
3. [ConfigMap Patterns](#configmap-patterns)
4. [Secret Patterns](#secret-patterns)
5. [Ingress Patterns](#ingress-patterns)
6. [HPA Patterns](#hpa-patterns)
7. [Complete Examples](#complete-examples)

---

## Deployment Patterns

### Level 1: Hello World Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 1
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
        image: myapp:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
```

### Level 2: Development Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
    environment: development
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: myapp
        environment: development
    spec:
      containers:
      - name: myapp
        image: myapp:1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: "development"
        envFrom:
        - configMapRef:
            name: myapp-config
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
```

### Level 3: Production Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
  labels:
    app: myapp
    version: v1.0.0
    environment: production
    tier: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: myapp
        version: v1.0.0
        environment: production
        tier: backend
    spec:
      # Security: Run as non-root user
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001

      # High availability: Spread pods across nodes
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - myapp
              topologyKey: kubernetes.io/hostname

      containers:
      - name: myapp
        image: myapp:1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP

        # Environment from ConfigMap and Secrets
        envFrom:
        - configMapRef:
            name: myapp-config
        env:
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: db-url

        # Resource limits for QoS
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi

        # Health checks
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 30

        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL

        # Volume mounts for writable directories
        volumeMounts:
        - name: tmp
          mountPath: /tmp

      volumes:
      - name: tmp
        emptyDir: {}
```

---

## Service Patterns

### ClusterIP (Internal Only)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
```

### NodePort (Local Development)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
    nodePort: 30080  # Optional: 30000-32767 range
```

### LoadBalancer (Cloud)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  labels:
    app: myapp
  annotations:
    # AWS specific
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    # GCP specific
    cloud.google.com/load-balancer-type: "Internal"
spec:
  type: LoadBalancer
  selector:
    app: myapp
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

### Multi-Port Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
  - name: https
    protocol: TCP
    port: 443
    targetPort: 8443
  - name: metrics
    protocol: TCP
    port: 9090
    targetPort: 9090
```

---

## ConfigMap Patterns

### Simple Key-Value ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
  labels:
    app: myapp
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  MAX_WORKERS: "4"
  TIMEOUT: "30"
```

### File-Based ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  # Simple key-value
  database_host: "postgres.default.svc.cluster.local"
  database_port: "5432"

  # File-like keys
  app.conf: |
    server {
      listen 80;
      server_name example.com;
      location / {
        proxy_pass http://backend:8000;
      }
    }

  config.json: |
    {
      "api_version": "v1",
      "features": {
        "caching": true,
        "logging": "verbose"
      }
    }
```

### Using ConfigMap in Deployment

**As environment variables**:
```yaml
containers:
- name: myapp
  envFrom:
  - configMapRef:
      name: myapp-config
  # Or individual keys
  env:
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: myapp-config
        key: LOG_LEVEL
```

**As volume mount**:
```yaml
containers:
- name: myapp
  volumeMounts:
  - name: config
    mountPath: /etc/config
    readOnly: true
volumes:
- name: config
  configMap:
    name: myapp-config
    items:
    - key: app.conf
      path: app.conf
```

---

## Secret Patterns

### Creating Secrets

**From literal values**:
```bash
kubectl create secret generic myapp-secrets \
  --from-literal=db-url='postgresql://user:pass@host/db' \
  --from-literal=api-key='secret-key-here'
```

**From files**:
```bash
kubectl create secret generic myapp-secrets \
  --from-file=db-url=./db-url.txt \
  --from-file=tls.crt \
  --from-file=tls.key
```

### Secret YAML (Base64 Encoded)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
  labels:
    app: myapp
type: Opaque
data:
  # Base64 encoded values
  db-url: cG9zdGdyZXNxbDovL3VzZXI6cGFzc0Bob3N0L2Ri
  api-key: c2VjcmV0LWtleS1oZXJl
```

**Encode/decode base64**:
```bash
# Encode
echo -n "postgresql://user:pass@host/db" | base64

# Decode
echo "cG9zdGdyZXNxbDovL3VzZXI6cGFzc0Bob3N0L2Ri" | base64 -d
```

### TLS Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
```

**Create from files**:
```bash
kubectl create secret tls tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

### Using Secrets in Deployment

```yaml
containers:
- name: myapp
  env:
  - name: DB_URL
    valueFrom:
      secretKeyRef:
        name: myapp-secrets
        key: db-url
  - name: API_KEY
    valueFrom:
      secretKeyRef:
        name: myapp-secrets
        key: api-key
```

**As volume mount** (for files):
```yaml
containers:
- name: myapp
  volumeMounts:
  - name: secrets
    mountPath: /etc/secrets
    readOnly: true
volumes:
- name: secrets
  secret:
    secretName: myapp-secrets
```

---

## Ingress Patterns

### Basic HTTP Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

### HTTPS Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

### Multi-Service Ingress (Path-Based Routing)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### Name-Based Virtual Hosting

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: virtual-host-ingress
spec:
  rules:
  - host: foo.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: foo-service
            port:
              number: 80
  - host: bar.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: bar-service
            port:
              number: 80
```

---

## HPA Patterns

### CPU-Based Autoscaling

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

### Multi-Metric Autoscaling

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
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
```

---

## Complete Examples

### Complete Production Stack

**namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    environment: production
```

**configmap.yaml**:
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

**secret.yaml** (apply via kubectl create secret):
```bash
kubectl create secret generic myapp-secrets \
  --namespace=production \
  --from-literal=db-url='postgresql://user:pass@host.neon.tech/db?sslmode=require' \
  --from-literal=api-key='your-api-key'
```

**deployment.yaml**: See "Level 3: Production Deployment" above

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
```

**ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: myapp-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

**hpa.yaml**: See "Multi-Metric Autoscaling" above

**pdb.yaml**:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
  namespace: production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: myapp
```

---

## Deployment Order

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Create configs and secrets
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml

# 3. Deploy application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 4. Set up ingress and autoscaling
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
kubectl apply -f pdb.yaml

# 5. Verify
kubectl get all -n production
kubectl describe deployment myapp -n production
```

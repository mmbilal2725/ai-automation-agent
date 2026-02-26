# Security Hardening for Container Images

Security best practices, vulnerability scanning, and attack surface minimization.

---

## Security Principles

### Minimal Attack Surface

**Principle**: Every package, binary, and file is a potential vulnerability vector.

**Strategy**: Include only what's necessary for runtime.

### Defense in Depth

**Principle**: Multiple security layers protect against compromise.

**Layers**:
1. Minimal base image (fewer vulnerabilities)
2. Non-root user (limited privileges if compromised)
3. No package manager (can't install malware)
4. Vulnerability scanning (detect known issues)
5. Network policies (limit blast radius)
6. Runtime monitoring (detect anomalies)

### Least Privilege

**Principle**: Container should have minimum permissions needed.

**Implementation**:
- Run as non-root user
- Drop unnecessary Linux capabilities
- Use read-only root filesystem where possible

---

## Non-Root Users

**Why**: If attacker escapes container, they inherit user privileges.

### Basic Pattern

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -u 10001 -m -s /bin/bash appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to non-root
USER appuser

CMD ["python", "app.py"]
```

### Advanced Pattern with Permissions

```dockerfile
FROM node:20-alpine

# Create user with specific UID/GID
RUN addgroup -g 10001 appgroup && \
    adduser -D -u 10001 -G appgroup appuser

# Install dependencies as root
COPY package*.json ./
RUN npm ci --only=production

# Setup application directory with correct ownership
WORKDIR /app
COPY --chown=appuser:appgroup . .

# Switch to non-root
USER appuser

CMD ["node", "server.js"]
```

### Why UID > 10000?

- UIDs below 1000 are system users
- UIDs 1000-9999 are typical human users
- UIDs 10000+ clearly indicate service accounts
- Avoids conflicts with host UIDs

### Kubernetes SecurityContext

Enforce non-root at Kubernetes level:

```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    fsGroup: 10001
  containers:
  - name: app
    image: myapp:v1.2.3
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
```

---

## Distroless Images

Google's distroless images contain only application and runtime dependencies.

### What's Excluded

- Package managers (apt, yum, apk)
- Shells (bash, sh)
- Utilities (curl, wget, netcat)
- Any files not required by application

### Size and Security Comparison

| Base | Size | Packages | Vulnerabilities (typical) |
|------|------|----------|---------------------------|
| ubuntu:22.04 | 77 MB | ~200 | 50-100 |
| debian:12-slim | 74 MB | ~100 | 30-60 |
| alpine:3.19 | 7 MB | ~20 | 5-15 |
| distroless/python3 | 50 MB | ~10 | 0-5 |

### Python Distroless Example

```dockerfile
# Build stage
FROM python:3.11 AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage - distroless
FROM gcr.io/distroless/python3-debian12
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["app.py"]
```

### Node.js Distroless Example

```dockerfile
# Build stage
FROM node:20 AS builder
WORKDIR /build
COPY package*.json ./
RUN npm ci --only=production
COPY . .

# Runtime stage - distroless
FROM gcr.io/distroless/nodejs20-debian12
WORKDIR /app
COPY --from=builder /build/node_modules ./node_modules
COPY --from=builder /build/dist ./dist
CMD ["dist/server.js"]
```

### Trade-offs

**Benefits**:
- Smallest attack surface
- Fewer vulnerabilities to patch
- Forces good practices (multi-stage builds)

**Limitations**:
- No shell debugging (can't `docker exec`)
- No package installation
- Requires well-structured build process

### Debugging Distroless Images

Use debug variants during development:

```dockerfile
# Production
FROM gcr.io/distroless/python3-debian12

# Development
FROM gcr.io/distroless/python3-debian12:debug
```

Debug variants include busybox shell for troubleshooting.

---

## Vulnerability Scanning

### Why Scan

- Detect known CVEs in packages
- Identify outdated dependencies
- Prevent deploying vulnerable images
- Meet compliance requirements

### Popular Scanners

| Tool | Type | Strengths |
|------|------|-----------|
| **Trivy** | Open source | Fast, accurate, easy to use |
| **Grype** | Open source | SBOM support, offline scanning |
| **Clair** | Open source | Registry integration |
| **Snyk** | Commercial | Developer-friendly, fix suggestions |
| **Aqua** | Commercial | Runtime protection, compliance |

### Trivy Usage

Install:
```bash
# MacOS
brew install trivy

# Linux
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install trivy
```

Scan image:
```bash
# Basic scan
trivy image myapp:v1.2.3

# Only high/critical
trivy image --severity HIGH,CRITICAL myapp:v1.2.3

# Output JSON for CI
trivy image --format json --output results.json myapp:v1.2.3

# Fail CI on critical vulnerabilities
trivy image --exit-code 1 --severity CRITICAL myapp:v1.2.3
```

### Grype Usage

```bash
# Install
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh

# Scan image
grype myapp:v1.2.3

# Scan with SBOM
grype sbom:./sbom.json

# Output table format
grype -o table myapp:v1.2.3
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: Container Scan
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          severity: HIGH,CRITICAL
          exit-code: 1  # Fail on vulnerabilities
```

#### GitLab CI

```yaml
container_scanning:
  image: docker:stable
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker run --rm -v /var/run/docker.sock:/var/run/docker.sock
        aquasec/trivy image --severity HIGH,CRITICAL
        $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Remediation Workflow

1. **Scan image**: Identify vulnerabilities
2. **Prioritize**: Focus on HIGH/CRITICAL in production code paths
3. **Update dependencies**: Upgrade vulnerable packages
4. **Rebuild**: Create new image with fixes
5. **Rescan**: Verify vulnerabilities resolved
6. **Deploy**: Push fixed image

---

## Secrets Management

### Never Include Secrets in Images

**Bad patterns to avoid**:

```dockerfile
# DON'T DO THIS
ENV API_KEY="secret123"
COPY .env .
ADD credentials.json /app/
```

**Why it fails**:
- Secrets stored in image layers forever
- Anyone with image access can extract secrets
- Rotation requires new image build

### Proper Secret Handling

#### 1. Environment Variables at Runtime

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: myapp:v1.2.3
    env:
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: api-key
```

#### 2. Mounted Secret Files

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: myapp:v1.2.3
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: app-secrets
```

#### 3. Build-Time Secrets (BuildKit)

For secrets needed during build:

```dockerfile
# Mount secret without storing in layer
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

### .dockerignore for Secrets

```
# Prevent accidental inclusion
.env
.env.*
*.key
*.pem
credentials.json
secrets.yaml
```

---

## Image Signing and Verification

Ensure image integrity and authenticity.

### Cosign (Sigstore)

```bash
# Install cosign
brew install cosign

# Generate key pair
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key myapp:v1.2.3

# Verify signature
cosign verify --key cosign.pub myapp:v1.2.3
```

### Kubernetes Admission Controller

Use admission controller to enforce signed images:

```yaml
apiVersion: v1
kind: Policy
metadata:
  name: require-signed-images
spec:
  rules:
  - name: verify-signature
    match:
      resources:
        kinds:
        - Pod
    validate:
      message: "Image must be signed with approved key"
      pattern:
        spec:
          containers:
          - image: "*:*@sha256:*"
```

---

## Read-Only Root Filesystem

Prevent runtime modifications to filesystem.

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN useradd -u 10001 -m appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

# Create writable temp directory
RUN mkdir -p /tmp/app && chown appuser:appuser /tmp/app

USER appuser
CMD ["python", "app.py"]
```

### Kubernetes SecurityContext

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: myapp:v1.2.3
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

**Benefits**:
- Prevents malware installation
- Stops privilege escalation attempts
- Forces stateless design

---

## Capability Dropping

Linux capabilities provide fine-grained privilege control.

### Drop All Capabilities

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: myapp:v1.2.3
    securityContext:
      capabilities:
        drop:
        - ALL
```

### Add Specific Capabilities

```yaml
securityContext:
  capabilities:
    drop:
    - ALL
    add:
    - NET_BIND_SERVICE  # Bind to ports < 1024
```

**Principle**: Drop all, add only what's needed.

---

## Security Scanning Checklist

### Image Build
- [ ] Multi-stage build (minimal final image)
- [ ] Distroless or Alpine base
- [ ] Non-root user (UID > 10000)
- [ ] No secrets in layers
- [ ] Pinned base image version
- [ ] .dockerignore prevents secret inclusion

### Vulnerability Management
- [ ] Scan with Trivy/Grype in CI
- [ ] Fail build on HIGH/CRITICAL CVEs
- [ ] Regular dependency updates
- [ ] SBOM generation enabled
- [ ] Scan on schedule (weekly)

### Runtime Security
- [ ] Kubernetes SecurityContext configured
- [ ] Non-root enforcement
- [ ] Read-only root filesystem
- [ ] Capabilities dropped
- [ ] Network policies defined
- [ ] Pod Security Standards enforced

### Supply Chain
- [ ] Image signing with Cosign
- [ ] Signature verification in admission
- [ ] Trusted registry only
- [ ] SBOM available
- [ ] Provenance attestation

---

## References

- [OWASP Docker Security](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Distroless Images](https://github.com/GoogleContainerTools/distroless)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Sigstore/Cosign](https://docs.sigstore.dev/)

# Docker Security for Python/FastAPI

Comprehensive security hardening guide for Docker containers, based on official best practices and production requirements.

## Core Security Principles

1. **Principle of Least Privilege** - Run as non-root, minimal permissions
2. **Minimal Attack Surface** - Fewer packages = fewer vulnerabilities
3. **Defense in Depth** - Multiple security layers
4. **Regular Updates** - Keep base images and dependencies current

## Critical Security Issues

### Issue 1: Running as Root (58% of containers)

**Problem:** By default, Docker containers run as root (UID 0). If the container is compromised, the attacker has root privileges.

**Impact:**
- Full system access within container
- Potential container escape
- Compliance violations (PCI-DSS, HIPAA, etc.)

**Solution:**

```dockerfile
# ❌ BAD: Default root user
FROM python:3.13-slim
WORKDIR /app
COPY . .
CMD ["uvicorn", "main:app"]  # Runs as root (UID 0)
```

```dockerfile
# ✅ GOOD: Non-root user
FROM python:3.13-slim
WORKDIR /app

# Create non-root user with specific UID
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

# Copy code with correct ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user BEFORE CMD
USER appuser

CMD ["uvicorn", "main:app"]  # Runs as appuser (UID 10001)
```

**Verify:**
```bash
# Check which user the container runs as
docker exec <container> whoami
# Should output: appuser

# Check UID
docker exec <container> id
# Should show: uid=10001(appuser)
```

### Issue 2: Using Full Base Images

**Problem:** `python:3.13` (not slim) is a full Debian system with many packages, increasing attack surface.

**Impact:**
- Large number of CVEs (Common Vulnerabilities and Exposures)
- Bigger image size (1GB vs 150MB)
- More packages to patch and maintain

**Solution:**

```dockerfile
# ❌ BAD: Full base image
FROM python:3.13  # ~1GB, full Debian system
```

```dockerfile
# ✅ GOOD: Minimal base image
FROM python:3.13-slim  # ~150MB, minimal Debian

# OR even smaller
FROM python:3.13-alpine  # ~50MB, minimal Alpine Linux
```

**Trade-offs:**

| Image | Size | Packages | Compatibility | Security |
|-------|------|----------|---------------|----------|
| python:3.13 | ~1GB | High | Best | Worst |
| python:3.13-slim | ~150MB | Low | Good | Good |
| python:3.13-alpine | ~50MB | Minimal | May have issues | Best |

**Recommendation:** Use `python:3.13-slim` for best balance.

### Issue 3: Secrets in Docker Layers

**Problem:** Secrets in Dockerfile or committed files become part of image layers and can be extracted.

**Impact:**
- Database credentials exposed
- API keys leaked
- Compliance violations

**Never Do This:**

```dockerfile
# ❌ BAD: Secret in Dockerfile
FROM python:3.13-slim
ENV DB_PASSWORD="supersecret123"  # EXPOSED IN LAYER
```

```dockerfile
# ❌ BAD: Copying .env file
FROM python:3.13-slim
COPY .env .  # .env contains secrets, now in image layer
```

**Solutions:**

```dockerfile
# ✅ GOOD: No secrets in Dockerfile
FROM python:3.13-slim
# Secrets passed at runtime via environment variables
```

**Runtime methods:**

```bash
# Method 1: Environment variables
docker run -e DB_PASSWORD="secret" app:latest

# Method 2: Env file (not committed to repo)
docker run --env-file .env app:latest

# Method 3: Docker secrets (Swarm/K8s)
docker service create --secret db-password app:latest
```

**Kubernetes Secrets:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  password: c3VwZXJzZWNyZXQxMjM=  # base64 encoded

---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
```

### Issue 4: Not Using .dockerignore

**Problem:** Copying entire directory includes secrets, caches, and unnecessary files.

**Impact:**
- .env files with secrets in image
- .git history in image
- Large image size
- Slow builds

**Solution:**

Create `.dockerignore`:

```
# .dockerignore

# Virtual environments
venv/
env/
.venv/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
pip-log.txt

# Environment files with secrets
.env
.env.local
.env.*.local
*.env

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Documentation
README.md
docs/

# CI/CD
.github/
.gitlab-ci.yml

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

**Verify:**
```bash
# Check what's being copied to image
docker build --no-cache -t app:test .

# Inspect image layers
docker history app:test
```

### Issue 5: Debug Mode in Production

**Problem:** Running FastAPI/Python apps with debug mode enabled in production.

**Impact:**
- Debugger allows arbitrary code execution from browser
- Detailed error messages expose internal structure
- Security incident waiting to happen

**Solution:**

```dockerfile
# ❌ BAD: Debug mode in production
FROM python:3.13-slim
# ...
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]  # --reload is debug mode
```

```dockerfile
# ✅ GOOD: Production mode
FROM python:3.13-slim
# ...
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]  # No --reload
```

**FastAPI Configuration:**

```python
# main.py

import os

# ❌ BAD: Always debug
app = FastAPI(debug=True)

# ✅ GOOD: Debug based on environment
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
app = FastAPI(debug=DEBUG)
```

### Issue 6: Not Scanning Images

**Problem:** Base images and dependencies contain known vulnerabilities (CVEs).

**Impact:**
- Exploitable vulnerabilities in production
- Compliance failures
- Security incidents

**Solution:**

```bash
# Scan image for vulnerabilities
docker scan app:latest

# OR use Trivy (more comprehensive)
trivy image app:latest

# OR use Snyk
snyk container test app:latest
```

**CI/CD Integration (GitHub Actions):**

```yaml
name: Security Scan

on: [push]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build image
      run: docker build -t app:${{ github.sha }} .

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: app:${{ github.sha }}
        format: 'table'
        exit-code: '1'  # Fail build on vulnerabilities
        severity: 'CRITICAL,HIGH'
```

## Security Hardening Checklist

### Level 1: Essential (Must Have)

```markdown
- [ ] Run as non-root user (USER instruction with UID > 10000)
- [ ] Use minimal base image (python:3.x-slim or alpine)
- [ ] No secrets in Dockerfile or layers
- [ ] .dockerignore file excludes .env, .git, secrets
- [ ] Debug mode disabled in production
- [ ] HEALTHCHECK configured
```

### Level 2: Recommended (Should Have)

```markdown
- [ ] Regular base image updates (rebuild weekly)
- [ ] Security scanning in CI/CD pipeline
- [ ] Read-only root filesystem (where possible)
- [ ] Drop unnecessary capabilities
- [ ] Use specific image tags (not :latest)
- [ ] Multi-stage builds (reduce attack surface)
- [ ] EXPOSE only necessary ports
```

### Level 3: Advanced (Nice to Have)

```markdown
- [ ] Use distroless images
- [ ] Content trust enabled (Docker Notary)
- [ ] Image signing
- [ ] Runtime security monitoring
- [ ] Network segmentation
- [ ] Resource limits (memory, CPU)
- [ ] AppArmor/SELinux profiles
```

## Production Dockerfile Template (Security Hardened)

```dockerfile
# ============================================
# Multi-stage build for minimal attack surface
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install only necessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files (layer caching)
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Runtime stage (minimal, non-root)
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Copy only virtual environment (no build tools)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user with specific UID
# UID 10001 is convention for non-root service users
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

# Copy application code with correct ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Document exposed port
EXPOSE 8000

# Production command (no --reload, no debug)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Kubernetes Security Context

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
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
      # Pod-level security
      securityContext:
        runAsNonRoot: true  # Enforce non-root
        runAsUser: 10001    # Must match Dockerfile USER
        fsGroup: 10001      # File system group

      containers:
      - name: app
        image: registry/app:latest

        # Container-level security
        securityContext:
          allowPrivilegeEscalation: false  # Prevent privilege escalation
          capabilities:
            drop:
            - ALL  # Drop all capabilities
          readOnlyRootFilesystem: true  # Read-only root filesystem

        # Resource limits (prevent DoS)
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"

        # Environment variables from secrets
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password

        # Volume mounts (for read-only root filesystem)
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: app-tmp
          mountPath: /app/tmp

      # Volumes for writable directories
      volumes:
      - name: tmp
        emptyDir: {}
      - name: app-tmp
        emptyDir: {}
```

## Common Security Vulnerabilities

### CVE Example: Python Package Vulnerability

```bash
# Check for known vulnerabilities
pip-audit

# Or in Dockerfile
RUN pip install pip-audit && pip-audit

# Update vulnerable packages
pip install --upgrade <package>
```

### Dependency Pinning

```dockerfile
# ❌ BAD: Unpinned versions
FROM python:3-slim  # Which 3.x?
RUN pip install fastapi  # Which version?
```

```dockerfile
# ✅ GOOD: Pinned versions
FROM python:3.13.1-slim  # Specific version
# requirements.txt with exact versions
# fastapi==0.109.0
# uvicorn[standard]==0.27.0
```

## Security Scanning Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| **Docker Scan** | Official Docker scanning | `docker scan app:latest` |
| **Trivy** | Comprehensive vulnerability scanner | `trivy image app:latest` |
| **Snyk** | Commercial scanner with free tier | `snyk container test app:latest` |
| **Clair** | Open-source vulnerability scanner | Integrated into registries |
| **Grype** | Vulnerability scanner by Anchore | `grype app:latest` |

## Advanced: Distroless Images

Distroless images contain only the application and runtime dependencies - no shell, package managers, or unnecessary tools.

```dockerfile
# ============================================
# Builder stage
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Distroless runtime (no shell, minimal tools)
# ============================================
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
COPY . .

# Distroless images run as non-root by default
# No USER instruction needed

# EXPOSE and CMD
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Distroless Benefits:**
- Smallest attack surface (no shell = no shell exploits)
- ~20MB smaller than slim images
- Reduced CVE count

**Distroless Limitations:**
- No shell (can't `docker exec -it container bash`)
- Harder to debug
- Limited tooling

## Compliance Standards

### PCI-DSS Requirements

```markdown
- [ ] Run as non-root user
- [ ] Minimal base images
- [ ] No secrets in images
- [ ] Regular vulnerability scanning
- [ ] Logging to stdout/stderr
- [ ] Network segmentation
```

### HIPAA Requirements

```markdown
- [ ] Encryption in transit (TLS)
- [ ] Encryption at rest
- [ ] Access control (non-root)
- [ ] Audit logging
- [ ] Vulnerability management
```

## Security Best Practices Summary

1. **Always run as non-root** - Use USER with UID > 10000
2. **Use minimal base images** - python:3.x-slim or alpine
3. **Never put secrets in images** - Use runtime env vars or secrets managers
4. **Create .dockerignore** - Exclude .env, .git, caches
5. **Disable debug mode** - No --reload, debug=False
6. **Scan images regularly** - CI/CD integration
7. **Pin versions** - Base images and dependencies
8. **Update regularly** - Rebuild images weekly
9. **Multi-stage builds** - Reduce attack surface
10. **Health checks** - Enable monitoring

## References

- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Snyk: Docker Best Practices for Python](https://snyk.io/blog/best-practices-containerizing-python-docker/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)

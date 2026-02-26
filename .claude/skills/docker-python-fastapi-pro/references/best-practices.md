# Docker Best Practices for Python/FastAPI

Comprehensive best practices guide based on official Docker documentation, FastAPI recommendations, and production experience.

## Image Building Best Practices

### 1. Use Specific Base Image Tags

```dockerfile
# ❌ Bad: Unpredictable, can break builds
FROM python:3

# ✅ Good: Specific, reproducible
FROM python:3.13.1-slim
```

**Why:**
- `:3` could be any 3.x version
- Updates can introduce breaking changes
- Specific tags ensure reproducible builds

### 2. Minimize Layers

```dockerfile
# ❌ Bad: 3 layers
RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get clean

# ✅ Good: 1 layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*
```

**Why:**
- Fewer layers = smaller image
- Cleanup in same layer removes files from that layer
- Each RUN creates a new layer

### 3. Order Instructions for Caching

```dockerfile
# ✅ Good: Least to most frequently changed
FROM python:3.13-slim
WORKDIR /app

# 1. System packages (rarely change)
RUN apt-get update && apt-get install -y curl

# 2. Dependencies (change occasionally)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3. Application code (changes frequently)
COPY . .

CMD ["uvicorn", "main:app"]
```

**Why:**
- Docker caches each layer
- Changing one layer invalidates all subsequent layers
- Ordering minimizes cache invalidation

### 4. Use .dockerignore

```
# .dockerignore
venv/
.git/
__pycache__/
*.pyc
.env
```

**Why:**
- Reduces build context size
- Speeds up builds
- Prevents secrets from entering image

### 5. Multi-Stage Builds

```dockerfile
# Stage 1: Build
FROM python:3.13-slim AS builder
RUN apt-get update && apt-get install -y build-essential
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim
COPY --from=builder /usr/local/lib/python3.13 /usr/local/lib/python3.13
COPY . .
CMD ["uvicorn", "main:app"]
```

**Why:**
- Reduces final image size by 60-80%
- Separates build dependencies from runtime
- Improves security (fewer packages)

## Security Best Practices

### 1. Run as Non-Root User

```dockerfile
# ❌ Bad: Runs as root (default)
FROM python:3.13-slim
COPY . .
CMD ["uvicorn", "main:app"]

# ✅ Good: Non-root user
FROM python:3.13-slim
RUN useradd -m -u 10001 appuser
COPY --chown=appuser:appuser . .
USER appuser
CMD ["uvicorn", "main:app"]
```

**Why:**
- Principle of least privilege
- Limits damage if container compromised
- Required for Kubernetes Pod Security Standards

### 2. Use Minimal Base Images

```dockerfile
# ❌ Avoid: Full OS (1GB+)
FROM python:3.13

# ✅ Good: Slim variant (150MB)
FROM python:3.13-slim

# ✅ Better: Alpine (50MB) if compatible
FROM python:3.13-alpine
```

**Why:**
- Smaller attack surface
- Fewer vulnerabilities
- Faster pulls and deployments

### 3. Don't Store Secrets in Images

```dockerfile
# ❌ Bad: Secret in image
FROM python:3.13-slim
ENV API_KEY="secret123"

# ✅ Good: Pass at runtime
FROM python:3.13-slim
# API_KEY passed via: docker run -e API_KEY="secret"
```

**Why:**
- Secrets in layers can be extracted
- Compliance violations
- Security breach if image is leaked

### 4. Scan Images for Vulnerabilities

```bash
# Scan with Trivy
trivy image app:latest

# Scan with Docker
docker scan app:latest

# Scan with Snyk
snyk container test app:latest
```

**Why:**
- Detect known CVEs
- Compliance requirements
- Proactive security

### 5. Keep Base Images Updated

```bash
# Rebuild regularly
docker build --no-cache -t app:latest .

# Update base image
docker pull python:3.13-slim
docker build -t app:latest .
```

**Why:**
- Get security patches
- Fix vulnerabilities
- Stay current with updates

## Performance Best Practices

### 1. Use BuildKit

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with BuildKit
DOCKER_BUILDKIT=1 docker build -t app:latest .
```

**Why:**
- Faster builds (parallel stages)
- Better caching
- Security features

### 2. Leverage Build Cache

```dockerfile
# Copy dependencies first
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (invalidates cache less often)
COPY . .
```

**Why:**
- Avoids reinstalling dependencies
- Speeds up rebuilds by 10-100x
- Reduces CI/CD time

### 3. Use pip --no-cache-dir

```dockerfile
# ❌ Bad: Stores cache in image
RUN pip install -r requirements.txt

# ✅ Good: No cache
RUN pip install --no-cache-dir -r requirements.txt
```

**Why:**
- Saves 20-50MB
- Cache not useful in immutable images
- Faster cleanup

### 4. Remove Unnecessary Files

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local/lib/python3.13 -name "*.pyc" -delete && \
    find /usr/local/lib/python3.13 -name "__pycache__" -type d -exec rm -rf {} +
```

**Why:**
- Reduces image size by 5-10%
- .pyc files regenerated at runtime
- Cleaner image

### 5. Use Virtual Environments in Multi-Stage

```dockerfile
FROM python:3.13-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt

FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

**Why:**
- Clean separation of dependencies
- Easy to copy entire environment
- No conflicts with system Python

## Application Best Practices

### 1. Listen on 0.0.0.0, Not 127.0.0.1

```python
# ❌ Bad: Only accessible inside container
uvicorn.run(app, host="127.0.0.1", port=8000)

# ✅ Good: Accessible from outside
uvicorn.run(app, host="0.0.0.0", port=8000)
```

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why:**
- 127.0.0.1 is localhost inside container
- 0.0.0.0 binds to all interfaces
- Required for Docker port mapping

### 2. Use Environment Variables for Configuration

```python
# config.py
import os

DATABASE_URL = os.getenv("DB_URL", "sqlite:///./app.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
```

**Why:**
- 12-factor app principle
- Easy to change without rebuilding
- Different configs for dev/prod

### 3. Implement Health Checks

```python
# main.py
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**Why:**
- Docker can monitor container health
- Kubernetes liveness/readiness probes
- Automatic restarts on failure

### 4. Handle Graceful Shutdown

```python
import signal
import sys

def signal_handler(sig, frame):
    print("Gracefully shutting down...")
    # Close connections, finish requests
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
```

**Why:**
- Kubernetes sends SIGTERM before killing
- Allows finishing in-flight requests
- Clean database connection closure

### 5. Use Connection Pooling

```python
from sqlmodel import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**Why:**
- Reuses database connections
- Better performance
- Handles connection failures

## Dockerfile Structure Best Practices

### Standard Order

```dockerfile
# 1. Base image
FROM python:3.13-slim

# 2. Metadata
LABEL maintainer="you@example.com"
LABEL version="1.0"

# 3. Environment variables (build-time)
ENV PYTHONUNBUFFERED=1

# 4. Working directory
WORKDIR /app

# 5. System dependencies
RUN apt-get update && apt-get install -y curl

# 6. Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Application code
COPY . .

# 8. User switch
USER appuser

# 9. Health check
HEALTHCHECK CMD curl -f http://localhost:8000/health

# 10. Port
EXPOSE 8000

# 11. Command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Use COPY, Not ADD

```dockerfile
# ❌ Bad: ADD has extra features (tar extraction, URLs)
ADD . /app

# ✅ Good: COPY is explicit
COPY . /app
```

**Why:**
- COPY is more explicit and predictable
- ADD has magical behavior (auto-extracts .tar)
- Use ADD only when needed for its features

### Use exec Form for CMD

```dockerfile
# ❌ Shell form: Runs in shell, PID != 1
CMD uvicorn main:app --host 0.0.0.0

# ✅ Exec form: Direct execution, PID = 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

**Why:**
- Exec form doesn't wrap in shell
- Process gets PID 1
- Receives signals directly (SIGTERM)

## CI/CD Best Practices

### 1. Use Specific Tags

```bash
# ❌ Bad: Overwrites tag
docker build -t app:latest .

# ✅ Good: Multiple tags
docker build -t app:latest -t app:v1.2.3 -t app:sha-abc123 .
```

### 2. Test Before Push

```bash
# Build
docker build -t app:test .

# Test
docker run -d --name test-app app:test
sleep 10
curl -f http://localhost:8000/health
docker stop test-app

# Push
docker push app:test
```

### 3. Use Registry Cache

```yaml
# GitHub Actions
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 4. Security Scan in Pipeline

```yaml
- name: Scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: app:latest
    severity: 'CRITICAL,HIGH'
    exit-code: '1'
```

## Production Deployment Best Practices

### 1. Use Multiple Replicas

```yaml
# Kubernetes
spec:
  replicas: 3  # Minimum 3 for HA
```

### 2. Set Resource Limits

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 3. Configure Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```

### 4. Use Rolling Updates

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### 5. Monitor and Log

```python
# Use structured logging
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        })

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## Common Anti-Patterns to Avoid

### 1. Using :latest Tag

```dockerfile
# ❌ Bad: Unpredictable
FROM python:latest

# ✅ Good: Specific version
FROM python:3.13.1-slim
```

### 2. Running as Root

```dockerfile
# ❌ Bad: Security risk
USER root

# ✅ Good: Non-root
USER appuser
```

### 3. Installing Unnecessary Packages

```dockerfile
# ❌ Bad: Includes recommended packages
RUN apt-get install -y build-essential

# ✅ Good: Only what's needed
RUN apt-get install -y --no-install-recommends build-essential
```

### 4. Not Cleaning Up in Same Layer

```dockerfile
# ❌ Bad: apt cache stays in earlier layer
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean

# ✅ Good: Cleaned in same layer
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
```

### 5. Copying Entire Directory Too Early

```dockerfile
# ❌ Bad: Code changes invalidate all layers
COPY . .
RUN pip install -r requirements.txt

# ✅ Good: Dependencies cached separately
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

## Quick Reference Checklist

```markdown
### Before Building
- [ ] .dockerignore file created
- [ ] Specific base image tag chosen
- [ ] Dependencies in requirements.txt

### In Dockerfile
- [ ] Multi-stage build (if production)
- [ ] Minimal base image used
- [ ] Dependencies copied before code
- [ ] pip --no-cache-dir used
- [ ] RUN commands combined
- [ ] Non-root user created
- [ ] Health check added
- [ ] Listen on 0.0.0.0

### After Building
- [ ] Image size reasonable (<200MB for simple apps)
- [ ] Security scan passed
- [ ] Test container runs successfully
- [ ] Health endpoint works
- [ ] Specific tags applied

### Before Production
- [ ] Resource limits set
- [ ] Probes configured
- [ ] Multiple replicas
- [ ] Monitoring enabled
- [ ] Logging to stdout
```

## References

- [Docker Official Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Official Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [12-Factor App](https://12factor.net/)
- [Python Docker Best Practices](https://snyk.io/blog/best-practices-containerizing-python-docker/)

# Docker Best Practices for Production

Official Docker optimization patterns and BuildKit features for production containers.

---

## Multi-Stage Builds

Multi-stage builds are the most impactful optimization technique, typically reducing image sizes by 75-90%.

### How They Work

Each `FROM` statement starts a new stage. Copy artifacts between stages, leaving build tools behind.

```dockerfile
# Stage 1: Build environment (can be large)
FROM python:3.11 AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime environment (must be minimal)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

### Benefits
- **Size reduction**: 75-90% smaller final images
- **Security**: No build tools in production image
- **Speed**: Faster pulls and deployments
- **Separation**: Clear boundary between build and runtime

### Naming Stages

Always name stages for clarity and maintainability:

```dockerfile
FROM node:20 AS dependencies
# Install deps

FROM node:20 AS builder
# Build app

FROM node:20-alpine AS runtime
# Final image
```

**Why**: If Dockerfile is reordered, stage references don't break.

---

## Base Image Selection

Choose the smallest base image that meets requirements.

### Image Size Comparison

| Base Image | Typical Size | Use When |
|------------|--------------|----------|
| `scratch` | 0 MB | Static binaries (Go, Rust) |
| `distroless` | 2-20 MB | No shell needed, maximum security |
| `alpine` | 5-50 MB | Need shell, package manager, good compatibility |
| `slim` (debian-slim) | 50-100 MB | Need more packages, better compatibility |
| `full` (ubuntu, debian) | 100-500 MB | Avoid unless specific requirement |

### Distroless Images

Google's distroless images contain only application and runtime dependencies.

```dockerfile
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /app /app
WORKDIR /app
CMD ["app.py"]
```

**Benefits**:
- Smallest possible image
- No shell, package manager, or unnecessary tools
- Minimal attack surface
- Official support for Python, Node.js, Java, Go

**Trade-offs**:
- Harder to debug (no shell)
- Can't install additional packages
- Requires multi-stage build

### Alpine Linux

Alpine uses musl libc instead of glibc, resulting in smaller images.

```dockerfile
FROM python:3.11-alpine
RUN apk add --no-cache gcc musl-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

**Benefits**:
- Very small base size (5MB)
- Package manager available (apk)
- Shell available for debugging

**Trade-offs**:
- Some packages may need compilation (slower builds)
- musl libc compatibility issues rare but possible
- Need to install build deps for native extensions

---

## Layer Caching Optimization

Docker caches layers. Order instructions by change frequency.

### The Pattern

```dockerfile
# 1. Base image (changes rarely)
FROM python:3.11-slim

# 2. System dependencies (change rarely)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Application dependencies (change occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Application code (changes frequently)
COPY . .

# 5. Runtime command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Why This Works

- Changes to code don't invalidate dependency layers
- Rebuilds only rerun steps after first change
- Can result in 10x faster rebuilds

### Bad Pattern (Avoid)

```dockerfile
# DON'T DO THIS
FROM python:3.11-slim
COPY . .  # Invalidates cache on ANY file change
RUN pip install -r requirements.txt  # Reinstalls every time
```

---

## BuildKit Features

Enable BuildKit for advanced features:

```bash
export DOCKER_BUILDKIT=1
docker build .
```

### Cache Mounts

Persist package manager caches between builds:

```dockerfile
# Python with pip cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Node with npm cache
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production
```

**Benefit**: Subsequent builds reuse downloaded packages even if layer invalidates.

### Secret Mounts

Inject secrets without storing in image:

```dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

**Benefit**: Secrets never appear in image layers or build cache.

### Bind Mounts

Mount files from build context without copying:

```dockerfile
RUN --mount=type=bind,source=package.json,target=/tmp/package.json \
    cat /tmp/package.json
```

---

## Dependency Management

Minimize dependencies in final image.

### Remove Package Manager Caches

```dockerfile
# Python
RUN pip install --no-cache-dir -r requirements.txt

# Node.js
RUN npm ci --only=production && npm cache clean --force

# Alpine
RUN apk add --no-cache package-name
```

### Production-Only Dependencies

```dockerfile
# Node.js: Exclude devDependencies
RUN npm ci --only=production

# Python: Use requirements.txt without dev packages
# Or poetry: poetry install --no-dev
```

### Combine Commands

Combine related commands to minimize layers:

```dockerfile
# Good: Single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends pkg && \
    rm -rf /var/lib/apt/lists/*

# Bad: Multiple layers with cleanup in wrong place
RUN apt-get update
RUN apt-get install -y pkg
RUN rm -rf /var/lib/apt/lists/*  # Doesn't reduce previous layer sizes
```

---

## .dockerignore

Prevent unnecessary files from entering build context.

### Essential Exclusions

```
# Version control
.git
.gitignore

# Dependencies (installed in container)
node_modules
__pycache__
*.pyc
.venv

# Development files
.env
.env.local
*.log
.DS_Store

# Tests and docs
tests
__tests__
*.test.js
docs
README.md

# Build artifacts
dist
build
*.egg-info

# IDE
.vscode
.idea
*.swp
```

### Benefits
- **Faster builds**: Smaller context = faster upload to daemon
- **Security**: Prevents accidentally copying secrets
- **Smaller images**: Prevents including unnecessary files

---

## Health Checks

Include health checks for container orchestration.

### HTTP Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### Command Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

### Parameters
- `--interval`: Time between checks (default 30s)
- `--timeout`: Max time for check to complete (default 30s)
- `--start-period`: Grace period before first check (default 0s)
- `--retries`: Consecutive failures before unhealthy (default 3)

---

## Security Best Practices

### Non-Root User

Always run as non-root user:

```dockerfile
# Create user with specific UID
RUN useradd -u 10001 -m appuser

# Set ownership
WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to user
USER appuser

CMD ["python", "app.py"]
```

**Why**: If container is compromised, attacker has limited privileges.

### Pin Base Image Versions

```dockerfile
# Good: Pinned to specific version
FROM python:3.11.7-slim-bookworm

# Bad: Unpredictable, can break builds
FROM python:latest
FROM python:3.11
```

### Scan for Vulnerabilities

Use tools like Trivy or Grype:

```bash
# Trivy
trivy image myimage:tag

# Grype
grype myimage:tag
```

Integrate into CI/CD to block vulnerable images.

---

## Build Arguments and Environment Variables

### Build Arguments (Build-Time)

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG APP_VERSION
LABEL version=${APP_VERSION}
```

```bash
docker build --build-arg APP_VERSION=1.0.0 .
```

### Environment Variables (Runtime)

```dockerfile
ENV PORT=8000
ENV LOG_LEVEL=info

EXPOSE ${PORT}
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
```

**Never put secrets in ENV** - they're stored in image metadata.

---

## Size Optimization Checklist

- [ ] Multi-stage build separating build and runtime
- [ ] Minimal base image (distroless, alpine, or slim)
- [ ] Combined RUN commands to minimize layers
- [ ] Removed package manager caches
- [ ] Only production dependencies included
- [ ] Comprehensive .dockerignore
- [ ] No unnecessary files copied to final stage
- [ ] Used BuildKit cache mounts where applicable

---

## References

- [Official Docker Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Best Practices](https://docs.docker.com/build/building/best-practices/)
- [BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Distroless Images](https://github.com/GoogleContainerTools/distroless)

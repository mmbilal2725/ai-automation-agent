# Docker Image Optimization for Python/FastAPI

Comprehensive guide to reducing Docker image size, improving build performance, and optimizing runtime efficiency.

## Image Size Optimization

### Goal: Reduce image size by 70-90%

Real-world example: FastAPI app with SQLModel + psycopg2
- Before optimization: 1.2GB
- After optimization: 180MB
- **Reduction: 85%**

## Strategy 1: Multi-Stage Builds

**Impact:** 60-80% size reduction

Multi-stage builds separate build dependencies from runtime, ensuring only necessary artifacts are in the final image.

**Before (Single-Stage):**
```dockerfile
FROM python:3.13
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential gcc
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]

# Result: ~1.2GB (includes gcc, build-essential, apt cache, pip cache)
```

**After (Multi-Stage):**
```dockerfile
# Builder stage
FROM python:3.13-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]

# Result: ~180MB (no build tools, no caches)
```

**Size Breakdown:**
- python:3.13 base: ~1GB
- python:3.13-slim base: ~150MB
- Build dependencies (gcc, etc.): ~200MB
- Installed packages: ~30MB
- App code: ~1MB

Multi-stage build: 150MB (base) + 30MB (packages) + 1MB (code) = **~180MB**

## Strategy 2: Use Minimal Base Images

**Impact:** 30-50% size reduction

| Base Image | Size | Pros | Cons |
|------------|------|------|------|
| `python:3.13` | ~1GB | All tools included | Huge size |
| `python:3.13-slim` | ~150MB | Good compatibility | Medium size |
| `python:3.13-alpine` | ~50MB | Smallest | musl libc compatibility issues |

**Recommendation:** Use `python:3.13-slim` for best balance.

**When to use Alpine:**
- Simple apps without C extensions
- Size is critical (e.g., edge computing)
- Team has experience with Alpine quirks

**Alpine Considerations:**

```dockerfile
# Alpine requires additional build dependencies
FROM python:3.13-alpine

# Must install these for many Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    # More deps than Debian
```

## Strategy 3: Layer Caching Optimization

**Impact:** 50-90% faster rebuilds

Docker caches layers - if a layer hasn't changed, it's reused. Order instructions from least to most frequently changed.

**❌ BAD: No caching benefit**
```dockerfile
FROM python:3.13-slim
WORKDIR /app

# Code changes frequently, invalidates cache
COPY . .

# Dependencies rarely change, but always rebuilt
COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app"]
```

**✅ GOOD: Maximum caching**
```dockerfile
FROM python:3.13-slim
WORKDIR /app

# Dependencies first (rarely change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code last (changes frequently)
COPY . .

CMD ["uvicorn", "main:app"]
```

**Layer order (least to most frequently changed):**
1. Base image (`FROM`)
2. System packages (`RUN apt-get install`)
3. Dependency files (`COPY requirements.txt`)
4. Dependency installation (`RUN pip install`)
5. Application code (`COPY . .`)
6. Runtime configuration (`CMD`, `ENTRYPOINT`)

**Build time comparison:**
- First build: 2m 30s
- Rebuild after code change (good caching): 5s
- Rebuild after code change (bad caching): 2m 30s

## Strategy 4: .dockerignore File

**Impact:** 10-30% size reduction, faster builds

`.dockerignore` excludes files from build context, reducing what's sent to Docker daemon and copied to image.

**Create `.dockerignore`:**

```
# Virtual environments (largest offender)
venv/
env/
.venv/
ENV/
env.bak/
venv.bak/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Pip cache
pip-log.txt
pip-delete-this-directory.txt

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Git
.git/
.gitignore
.gitattributes

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Documentation
README.md
docs/
*.md

# CI/CD
.github/
.gitlab-ci.yml
Jenkinsfile

# Environment files
.env
.env.*
*.env

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Build artifacts
dist/
build/
*.egg-info/
```

**Size impact example:**
- Without .dockerignore: 450MB (includes venv/, .git/, node_modules/ if present)
- With .dockerignore: 180MB (only necessary files)

**Build performance:**
```bash
# Without .dockerignore
$ docker build .
Sending build context to Docker daemon: 850MB
# Takes 30s just to send context

# With .dockerignore
$ docker build .
Sending build context to Docker daemon: 5MB
# Takes <1s to send context
```

## Strategy 5: Combine RUN Commands

**Impact:** 5-15% size reduction

Each `RUN` instruction creates a new layer. Files added in one layer are always there, even if deleted in a later layer.

**❌ BAD: Multiple layers**
```dockerfile
FROM python:3.13-slim

# Layer 1: Downloads 200MB of packages
RUN apt-get update

# Layer 2: Installs packages
RUN apt-get install -y build-essential

# Layer 3: Doesn't actually remove from previous layers
RUN apt-get clean

# Result: All 3 layers in image, total 200MB+ stays
```

**✅ GOOD: Single layer**
```dockerfile
FROM python:3.13-slim

# Everything in one layer - cleanup actually works
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Result: Only final state (after cleanup) in layer
```

**Why this matters:**

```
# Bad approach (3 layers):
Layer 1: +200MB (apt cache)
Layer 2: +150MB (packages)
Layer 3: +0MB (cleanup does nothing)
Total: 350MB

# Good approach (1 layer):
Layer 1: +150MB (packages only, cache cleaned in same layer)
Total: 150MB
```

## Strategy 6: Use --no-cache-dir with pip

**Impact:** 10-20MB reduction per build

Pip caches downloaded packages by default - unnecessary in Docker since images are immutable.

**❌ BAD: Stores pip cache**
```dockerfile
RUN pip install -r requirements.txt
# Adds ~50MB of cached wheels to image
```

**✅ GOOD: No cache**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
# Only installs packages, no cache
```

**Additional pip optimizations:**

```dockerfile
# Full optimization
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Remove unnecessary files
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "*.pyo" -delete && \
    find /opt/venv -name "__pycache__" -type d -exec rm -rf {} +
```

## Strategy 7: Remove Build Dependencies

**Impact:** 100-200MB reduction

Build dependencies (gcc, make, etc.) are only needed during package installation, not at runtime.

**❌ BAD: Build deps in final image**
```dockerfile
FROM python:3.13-slim
RUN apt-get update && apt-get install -y build-essential gcc
RUN pip install -r requirements.txt
# build-essential still in image (+200MB)
```

**✅ GOOD: Multi-stage removes build deps**
```dockerfile
# Builder: Install with build deps
FROM python:3.13-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc && \
    rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runtime: Only packages, no build deps
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
# build-essential not copied (+200MB saved)
```

## Strategy 8: Use UV for Faster Builds

**Impact:** 10-100x faster dependency installation

UV is a modern Python package manager written in Rust - significantly faster than pip.

**Before (pip):**
```dockerfile
FROM python:3.13-slim AS builder
COPY requirements.txt .
RUN pip install -r requirements.txt
# Takes 2m 30s for 50 packages
```

**After (uv):**
```dockerfile
FROM python:3.13-slim AS builder
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen
# Takes 15s for same 50 packages
```

**UV Benchmarks:**
- Small project (10 packages): pip 20s → uv 2s (10x faster)
- Medium project (50 packages): pip 2m 30s → uv 15s (10x faster)
- Large project (200 packages): pip 10m → uv 1m (10x faster)

## Build Performance Optimization

### Use BuildKit

BuildKit is Docker's new build system - faster and more efficient.

**Enable BuildKit:**

```bash
# One-time
export DOCKER_BUILDKIT=1

# Or in docker build command
DOCKER_BUILDKIT=1 docker build -t app:latest .

# Make permanent (Linux/Mac)
echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
```

**BuildKit benefits:**
- Parallel builds
- Better caching
- Faster dependency resolution
- Build secrets support

### Parallel Dependency Installation

```dockerfile
# Without BuildKit: Sequential
RUN pip install package1
RUN pip install package2
# Total: 60s (30s + 30s)

# With BuildKit: Can parallelize
RUN pip install package1 & \
    pip install package2 & \
    wait
# Total: 30s (parallel)
```

### Cache Mounts (BuildKit Feature)

```dockerfile
# Reuse pip cache across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# First build: Downloads packages (2m)
# Second build: Uses cache (10s)
```

## Runtime Performance Optimization

### Strategy 1: Workers Configuration

```dockerfile
# ❌ Single worker (can't use multiple CPU cores)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ✅ Multiple workers (uses all CPU cores)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ✅ Or dynamic based on CPU
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --workers $(nproc)"]
```

**Workers formula:** `(2 x CPU cores) + 1`

### Strategy 2: Connection Pooling

```python
# Database connection pooling for better performance
from sqlmodel import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # Max 5 connections
    max_overflow=10,      # Allow 10 more if needed
    pool_pre_ping=True,   # Verify connection before use
    pool_recycle=3600     # Recycle connections after 1 hour
)
```

### Strategy 3: Health Checks

```dockerfile
# Health check for monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

## Complete Optimized Dockerfile

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies (single layer, with cleanup)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files (layer caching)
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv

# Activate venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Remove unnecessary files
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "*.pyo" -delete && \
    find /opt/venv -name "__pycache__" -type d -exec rm -rf {} +

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Copy only virtual environment (no build tools)
COPY --from=builder /opt/venv /opt/venv

# Set PATH
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Production command with workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Final size: ~180MB (85% reduction from 1.2GB)
# Build time: ~1m 30s (first build), ~5s (cached rebuild)
```

## Size Comparison Table

| Optimization | Before | After | Reduction |
|--------------|--------|-------|-----------|
| Multi-stage build | 1.2GB | 450MB | 62% |
| + Slim base image | 450MB | 300MB | 33% |
| + .dockerignore | 300MB | 250MB | 17% |
| + Combined RUN | 250MB | 220MB | 12% |
| + No pip cache | 220MB | 200MB | 9% |
| + Remove .pyc files | 200MB | 180MB | 10% |
| **Total** | **1.2GB** | **180MB** | **85%** |

## Optimization Checklist

```markdown
### Build Time
- [ ] Layer caching optimized (dependencies before code)
- [ ] .dockerignore file created
- [ ] BuildKit enabled
- [ ] Cache mounts used (if BuildKit)
- [ ] UV package manager (optional, for speed)

### Image Size
- [ ] Multi-stage build implemented
- [ ] Minimal base image (slim or alpine)
- [ ] RUN commands combined with cleanup
- [ ] pip --no-cache-dir flag used
- [ ] .pyc/.pyo files removed
- [ ] Build dependencies not in final stage

### Runtime Performance
- [ ] Multiple workers configured
- [ ] Connection pooling enabled
- [ ] Health checks configured
- [ ] Non-root user set
- [ ] Resource limits defined (K8s)

### Target Metrics
- [ ] Image size <200MB (simple apps)
- [ ] Build time <2min (with cache <30s)
- [ ] Startup time <5s
- [ ] 0 critical vulnerabilities
```

## Debugging Size Issues

### Inspect Image Layers

```bash
# See layer sizes
docker history app:latest

# Human-readable sizes
docker history app:latest --human

# See what's taking up space
docker history app:latest --no-trunc
```

### Analyze Image with Dive

```bash
# Install dive
brew install dive  # Mac
apt install dive   # Linux

# Analyze image
dive app:latest

# Shows:
# - Layer contents
# - Wasted space
# - Efficiency score
```

### Check Image Size

```bash
# List images with sizes
docker images

# Get specific image size
docker inspect app:latest --format='{{.Size}}' | numfmt --to=iec
```

## References

- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Python Speed: Smaller Docker Images](https://pythonspeed.com/articles/smaller-docker-images/)
- [DevOpsCube: Reduce Docker Image Size](https://devopscube.com/reduce-docker-image-size/)
- [Docker BuildKit](https://docs.docker.com/build/buildkit/)

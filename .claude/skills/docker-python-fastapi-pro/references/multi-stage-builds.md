# Multi-Stage Builds for Python/FastAPI

Multi-stage builds are Docker's solution to creating minimal production images by separating build dependencies from runtime requirements.

## Core Concept

From Docker official documentation: "With multi-stage builds, you use multiple `FROM` statements in your Dockerfile. Each `FROM` instruction can use a different base, and each begins a new stage of the build. You can selectively copy artifacts from one stage to another, leaving behind everything you don't want in the final image."

For interpreted languages like Python, multi-stage builds allow you to:
- Build and install dependencies in a full-featured environment
- Copy only the runtime artifacts to a minimal final image
- Reduce image size by 70%+ compared to single-stage builds

## Benefits

| Benefit | Impact |
|---------|--------|
| **Size Reduction** | 70-90% smaller images (500MB → 150MB typical) |
| **Security** | Fewer packages = smaller attack surface |
| **Performance** | Faster pulls from registry, quicker deployments |
| **Clean Separation** | Build tools stay in builder stage |

## Architecture

```
┌─────────────────────────────────────────┐
│ Stage 1: Builder (python:3.13-slim)     │
│ - Install build dependencies (gcc, etc) │
│ - Create virtual environment            │
│ - Install Python packages                │
│ - Compile wheels if needed               │
└─────────────────────────────────────────┘
              ↓ COPY artifacts only
┌─────────────────────────────────────────┐
│ Stage 2: Runtime (python:3.13-slim)     │
│ - Copy virtual environment only          │
│ - Copy application code                  │
│ - Set non-root user                      │
│ - No build tools                         │
└─────────────────────────────────────────┘
```

## Pattern 1: Standard Multi-Stage (pip)

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies (needed for compiling packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (layer caching optimization)
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
# --no-cache-dir: Don't store pip cache (saves space)
# --upgrade pip: Get latest pip with bug fixes
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Copy ONLY the virtual environment (not build tools)
COPY --from=builder /opt/venv /opt/venv

# Activate virtual environment in runtime
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check for Kubernetes
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why this works:**
- Builder stage has gcc and build-essential for compiling packages
- Runtime stage is clean - only Python and installed packages
- Virtual environment isolates dependencies
- Final image doesn't include build tools (100-200MB saved)

## Pattern 2: UV Package Manager (Faster)

UV is a modern Python package manager written in Rust - significantly faster than pip.

```dockerfile
# ============================================
# Stage 1: Builder with UV
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies with uv
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen --no-dev

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**UV Advantages:**
- 10-100x faster than pip for installing packages
- Better dependency resolution
- Lock files for reproducible builds
- Drop-in replacement for pip

## Pattern 3: Alpine-Based (Smallest)

Alpine Linux produces the smallest images (~50MB base vs ~150MB for slim).

```dockerfile
# ============================================
# Stage 1: Builder (Alpine)
# ============================================
FROM python:3.13-alpine AS builder

WORKDIR /app

# Alpine uses apk instead of apt
# Build dependencies for compiling Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime (Alpine)
# ============================================
FROM python:3.13-alpine

WORKDIR /app

# Install only runtime dependencies (not build deps)
# postgresql-libs: runtime lib for psycopg2
RUN apk add --no-cache postgresql-libs

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user
RUN adduser -D -u 10001 appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Alpine Considerations:**
- **Pros:** Smallest size (50-100MB final image)
- **Cons:** Uses musl libc instead of glibc (some packages may have issues)
- **When to use:** Simple apps without complex C extensions

## Pattern 4: Poetry Package Manager

Poetry is popular for Python dependency management.

```dockerfile
# ============================================
# Stage 1: Builder with Poetry
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Configure Poetry to not create virtual environment (we'll do it manually)
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN poetry install --no-dev --no-interaction --no-ansi

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Pattern 5: Three-Stage Build (Dev → Build → Runtime)

For complex applications with development dependencies, testing, and production.

```dockerfile
# ============================================
# Stage 1: Development dependencies
# ============================================
FROM python:3.13-slim AS dev-deps

WORKDIR /app

COPY requirements-dev.txt requirements.txt ./

RUN python -m venv /opt/venv-dev
ENV PATH="/opt/venv-dev/bin:$PATH"

RUN pip install --no-cache-dir -r requirements-dev.txt

# ============================================
# Stage 2: Builder (production dependencies)
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 3: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Size Comparison

Real-world example: FastAPI app with SQLModel, psycopg2, httpx

| Approach | Image Size | Build Time | Complexity |
|----------|-----------|------------|------------|
| Single-stage (python:3.13) | 1.2 GB | 3m 20s | Low |
| Single-stage (python:3.13-slim) | 450 MB | 2m 45s | Low |
| Multi-stage (slim) | 180 MB | 2m 50s | Medium |
| Multi-stage (alpine) | 95 MB | 3m 10s | Medium-High |
| Multi-stage + UV | 175 MB | 1m 30s | Medium |

**Recommendation:** Multi-stage with python:3.13-slim for best balance of size, compatibility, and complexity.

## Common Mistakes

### Mistake 1: Not Using Virtual Environment

```dockerfile
# ❌ BAD: Installing directly to system Python
FROM python:3.13-slim AS builder
RUN pip install -r requirements.txt
# Problem: Hard to copy only installed packages to runtime stage
```

```dockerfile
# ✅ GOOD: Using virtual environment
FROM python:3.13-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt
# COPY --from=builder /opt/venv works cleanly
```

### Mistake 2: Copying Build Tools to Runtime

```dockerfile
# ❌ BAD: Copying entire /usr/local
FROM python:3.13-slim AS builder
RUN pip install -r requirements.txt

FROM python:3.13-slim
COPY --from=builder /usr/local /usr/local  # Copies gcc, build tools, etc.
```

```dockerfile
# ✅ GOOD: Copy only virtual environment
FROM python:3.13-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt

FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv  # Only packages, no build tools
```

### Mistake 3: Installing Dependencies as Root in Final Stage

```dockerfile
# ❌ BAD: Installing in final stage
FROM python:3.13-slim
COPY requirements.txt .
RUN pip install -r requirements.txt  # Installs as root, no separation
COPY . .
```

```dockerfile
# ✅ GOOD: Installing in builder stage
FROM python:3.13-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt

FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv  # Clean separation
```

### Mistake 4: Wrong PATH Configuration

```dockerfile
# ❌ BAD: Copying venv but not setting PATH
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
CMD ["uvicorn", "main:app"]  # Won't find uvicorn
```

```dockerfile
# ✅ GOOD: Set PATH to venv
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
CMD ["uvicorn", "main:app"]  # Finds uvicorn in venv
```

## Advanced: Named Stages for Testing

You can build specific stages for different purposes:

```dockerfile
# Stage 1: Base with common setup
FROM python:3.13-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base AS deps
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Test (includes dev dependencies)
FROM deps AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN pytest

# Stage 4: Production (default)
FROM base AS production
COPY --from=deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN useradd -m -u 10001 appuser
COPY --chown=appuser:appuser . .
USER appuser
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build specific stages:
```bash
# Build and run tests
docker build --target test -t app:test .

# Build production (default)
docker build -t app:production .
```

## Debugging Multi-Stage Builds

### View Intermediate Stages

```bash
# List all images including intermediate stages
docker images -a

# Intermediate stages show as <none>
```

### Build and Inspect Specific Stage

```bash
# Build only the builder stage
docker build --target builder -t app:builder .

# Run the builder stage to inspect
docker run -it app:builder /bin/bash

# Check what's installed
ls -la /opt/venv/lib/python3.13/site-packages/
```

### Check Virtual Environment PATH

```bash
# Inside container
echo $PATH
# Should include /opt/venv/bin

# Check which python is being used
which python
# Should be /opt/venv/bin/python

# Verify packages are in venv
pip list
```

## Best Practices

1. **Always use virtual environments** in builder stage for clean artifact copying
2. **Set PATH correctly** in runtime stage to use venv Python
3. **Copy only artifacts** (venv, not build tools) to final stage
4. **Use `--no-cache-dir`** with pip to avoid storing unnecessary cache
5. **Install system dependencies** in builder, not runtime
6. **Name your stages** with `AS builder` for clarity
7. **Order instructions** for optimal layer caching (dependencies before code)
8. **Use slim base images** for both builder and runtime unless Alpine is needed

## References

- [Docker Official Docs - Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Python Speed - Multi-stage Docker builds for Python](https://pythonspeed.com/articles/multi-stage-docker-python/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)

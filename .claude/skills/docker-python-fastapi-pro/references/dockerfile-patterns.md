# Dockerfile Implementation Patterns

Ready-to-use Dockerfile patterns for Python/FastAPI applications.

## Pattern 1: FastAPI Multi-Stage Production Build

Complete production-ready pattern with security hardening and optimization.

```dockerfile
# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .
# OR for uv: COPY pyproject.toml uv.lock ./

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# OR for uv: RUN pip install uv && uv sync --frozen

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
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
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Benefits:**
- Image size: ~180MB (85% reduction from single-stage)
- Security: Non-root user, no build tools in final image
- Performance: Layer caching optimized

## Pattern 2: Development with Hot Reload

Optimized for local development with fast iteration.

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code (will be overridden by volume in docker-compose)
COPY . .

# Run with reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Usage with Docker Compose:**
```yaml
services:
  app:
    build:
      dockerfile: dev.Dockerfile
    volumes:
      - ./:/app  # Hot-reload on code changes
    ports:
      - "8000:8000"
```

## Pattern 3: Kubernetes-Ready with Probes

Compliant with Kubernetes Pod Security Standards.

```dockerfile
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user for K8s security
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser . .

# Health endpoint for K8s probes
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Kubernetes Deployment:**
```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: app
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
    readinessProbe:
      httpGet:
        path: /health
        port: 8000
```

## Pattern 4: UV Package Manager (Fast Builds)

Uses UV for 10-100x faster dependency installation.

```dockerfile
# Stage 1: Builder with UV
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install with uv
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen --no-dev

# Stage 2: Runtime
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

**Build time comparison:**
- pip: 2m 30s
- uv: 15s (10x faster)

## Pattern 5: Alpine-Based (Smallest Size)

Minimal image size (~50-100MB) using Alpine Linux.

```dockerfile
# Stage 1: Builder
FROM python:3.13-alpine AS builder

WORKDIR /app

# Alpine-specific build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-alpine

WORKDIR /app

# Runtime dependencies only
RUN apk add --no-cache postgresql-libs

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN adduser -D -u 10001 appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Trade-offs:**
- Pros: Smallest size (50-100MB)
- Cons: musl libc compatibility issues with some packages

## Pattern 6: Poetry Package Manager

For projects using Poetry for dependency management.

```dockerfile
# Stage 1: Builder with Poetry
FROM python:3.13-slim AS builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Don't create virtualenv (we'll do it manually)
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Create venv and install
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN poetry install --no-dev --no-interaction --no-ansi

# Stage 2: Runtime
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

## Pattern Selection Guide

| Use Case | Pattern | File Size | Build Time | Complexity |
|----------|---------|-----------|------------|------------|
| Hello World | Single-stage slim | ~200MB | 1min | Low |
| Local Dev | Pattern 2 (Hot reload) | ~200MB | 1min | Low |
| Production (pip) | Pattern 1 (Multi-stage) | ~180MB | 2.5min | Medium |
| Production (fast) | Pattern 4 (UV) | ~175MB | 15sec | Medium |
| Size-critical | Pattern 5 (Alpine) | ~95MB | 3min | High |
| Kubernetes | Pattern 3 (K8s-ready) | ~180MB | 2.5min | Medium |

## Pattern Customization

### Adding Database Drivers

```dockerfile
# PostgreSQL
RUN apt-get install -y libpq-dev  # Builder stage
RUN pip install psycopg2-binary

# MySQL
RUN apt-get install -y default-libmysqlclient-dev
RUN pip install mysqlclient

# MongoDB
RUN pip install motor  # No system dependencies needed
```

### Multiple Workers

```dockerfile
# Static worker count
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--workers", "4"]

# Dynamic based on CPU cores
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --workers $(nproc)"]

# Production formula: (2 x cores) + 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --workers $(($(nproc) * 2 + 1))"]
```

### Environment-Specific Configuration

```dockerfile
# Accept build argument
ARG ENV=production

# Use in RUN commands
RUN if [ "$ENV" = "development" ]; then \
        pip install -r requirements-dev.txt; \
    else \
        pip install -r requirements.txt; \
    fi

# Build with: docker build --build-arg ENV=development -t app:dev .
```

## See Also

- `multi-stage-builds.md` - Detailed multi-stage build guide
- `optimization.md` - Image size optimization techniques
- `security.md` - Security hardening patterns
- `../assets/dockerfiles/` - Complete example files

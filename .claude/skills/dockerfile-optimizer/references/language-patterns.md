# Language-Specific Optimization Patterns

Python, FastAPI, and Node.js Dockerfile patterns optimized for production Kubernetes deployment.

---

## Python / FastAPI Patterns

### Pattern 1: Minimal with python:slim

**Best for**: Most production applications
**Size**: ~150-200 MB
**Security**: Good

```dockerfile
# Build stage: Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-warn-script-location \
    -r requirements.txt

# Runtime stage: Minimal production image
FROM python:3.11-slim

# Install runtime dependencies only (e.g., for psycopg2, Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -u 10001 -m -s /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Update PATH to include user packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 2: Ultra-Minimal with Distroless

**Best for**: Maximum security requirements
**Size**: ~80-120 MB
**Security**: Excellent (no shell, no package manager)

```dockerfile
# Build stage
FROM python:3.11 AS builder

WORKDIR /build

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-warn-script-location \
    -r requirements.txt

# Runtime stage: Distroless
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copy Python packages
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Set PATH
ENV PATH=/root/.local/bin:$PATH

# Distroless runs as non-root by default
EXPOSE 8000

# Note: No shell available, debugging requires :debug variant
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 3: Poetry for Dependency Management

**Best for**: Projects using Poetry
**Size**: ~150-200 MB

```dockerfile
# Build stage
FROM python:3.11-slim AS builder

# Install poetry
RUN pip install --no-cache-dir poetry==1.7.1

WORKDIR /build

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies (export to requirements.txt for compatibility)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

RUN useradd -u 10001 -m appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 4: Alpine for Maximum Size Reduction

**Best for**: Size-critical deployments
**Size**: ~50-80 MB
**Trade-off**: Slower builds (compile packages), potential musl libc issues

```dockerfile
# Build stage
FROM python:3.11-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-alpine

# Install runtime dependencies only
RUN apk add --no-cache \
    libpq \
    && adduser -D -u 10001 appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### FastAPI-Specific Optimizations

#### Production ASGI Server Configuration

```dockerfile
# Use gunicorn with uvicorn workers for production
CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

#### Health Check Endpoint

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### requirements.txt for FastAPI

```
# Production dependencies only
fastapi==0.109.0
uvicorn[standard]==0.27.0
gunicorn==21.2.0
pydantic==2.5.0
# Add your app dependencies
```

---

## Node.js / TypeScript Patterns

### Pattern 1: Multi-Stage with node:alpine

**Best for**: Production Node.js apps
**Size**: ~50-100 MB
**Security**: Good

```dockerfile
# Build stage: Install dependencies and build
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build application (if using TypeScript or build step)
RUN npm run build

# Prune dev dependencies
RUN npm prune --production

# Runtime stage: Minimal production image
FROM node:20-alpine

# Create non-root user
RUN addgroup -g 10001 appgroup && \
    adduser -D -u 10001 -G appgroup appuser

WORKDIR /app

# Copy production dependencies
COPY --from=builder --chown=appuser:appgroup /build/node_modules ./node_modules

# Copy built application
COPY --from=builder --chown=appuser:appgroup /build/dist ./dist
COPY --from=builder --chown=appuser:appgroup /build/package*.json ./

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["node", "dist/server.js"]
```

### Pattern 2: Distroless Node.js

**Best for**: Maximum security
**Size**: ~80-120 MB
**Security**: Excellent

```dockerfile
# Build stage
FROM node:20 AS builder

WORKDIR /build

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build && npm prune --production

# Runtime stage: Distroless
FROM gcr.io/distroless/nodejs20-debian12

WORKDIR /app

# Copy production dependencies and built app
COPY --from=builder /build/node_modules ./node_modules
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/package*.json ./

EXPOSE 3000

CMD ["dist/server.js"]
```

### Pattern 3: Next.js Production Build

**Best for**: Next.js applications
**Size**: ~150-250 MB

```dockerfile
# Dependencies stage
FROM node:20-alpine AS deps

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

# Builder stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage
FROM node:20-alpine

RUN addgroup -g 10001 appgroup && \
    adduser -D -u 10001 -G appgroup appuser

WORKDIR /app

# Copy production dependencies
COPY --from=deps --chown=appuser:appgroup /app/node_modules ./node_modules

# Copy built Next.js app
COPY --from=builder --chown=appuser:appgroup /app/.next ./.next
COPY --from=builder --chown=appuser:appgroup /app/public ./public
COPY --from=builder --chown=appuser:appgroup /app/package*.json ./

USER appuser

EXPOSE 3000

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

CMD ["npm", "start"]
```

### Pattern 4: pnpm for Faster Builds

**Best for**: Monorepos, faster CI builds
**Size**: Similar to npm
**Speed**: 2x faster installs

```dockerfile
# Build stage
FROM node:20-alpine AS builder

# Install pnpm
RUN npm install -g pnpm@8

WORKDIR /build

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies with pnpm
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

# Prune dev dependencies
RUN pnpm prune --prod

# Runtime stage
FROM node:20-alpine

RUN npm install -g pnpm@8 && \
    adduser -D -u 10001 appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /build/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /build/dist ./dist
COPY --from=builder --chown=appuser:appuser /build/package*.json ./

USER appuser

EXPOSE 3000

CMD ["node", "dist/server.js"]
```

### Node.js-Specific Optimizations

#### Use .dockerignore

```
node_modules
npm-debug.log
.env
.env.*
dist
build
coverage
.git
.vscode
.idea
*.md
.DS_Store
```

#### BuildKit Cache Mounts

```dockerfile
# Use npm cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production
```

#### Production Environment Variables

```dockerfile
ENV NODE_ENV=production
ENV NPM_CONFIG_LOGLEVEL=warn
ENV NODE_OPTIONS="--max-old-space-size=2048"
```

---

## Comparison Matrix

### Python

| Pattern | Size | Security | Build Time | Best For |
|---------|------|----------|------------|----------|
| python:slim | 150-200 MB | Good | Fast | General production |
| Distroless | 80-120 MB | Excellent | Fast | High security requirements |
| Alpine | 50-80 MB | Good | Slow | Size-critical |
| Poetry | 150-200 MB | Good | Medium | Poetry projects |

### Node.js

| Pattern | Size | Security | Build Time | Best For |
|---------|------|----------|------------|----------|
| node:alpine | 50-100 MB | Good | Fast | General production |
| Distroless | 80-120 MB | Excellent | Fast | High security requirements |
| Next.js | 150-250 MB | Good | Medium | Next.js apps |
| pnpm | 50-100 MB | Good | Very Fast | Monorepos, CI optimization |

---

## Common Optimization Patterns

### Layer Caching for Package Installation

**Always copy package manifests first**:

```dockerfile
# Python
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Node.js
COPY package*.json ./
RUN npm ci
COPY . .
```

**Why**: Code changes don't invalidate dependency layer.

### Multi-Stage Build Template

```dockerfile
# Stage 1: Build (full tooling)
FROM <language>:<version> AS builder
WORKDIR /build
# Install all dependencies including dev
# Build/compile application
# Prepare production artifacts

# Stage 2: Runtime (minimal)
FROM <language>:<version>-slim|alpine|distroless
# Create non-root user
# Copy only production dependencies
# Copy built application
# Set security context
USER nonroot
CMD [...]
```

### Health Check Examples

```dockerfile
# Python FastAPI
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Node.js with curl
HEALTHCHECK CMD curl -f http://localhost:3000/health || exit 1

# Alpine (use wget)
HEALTHCHECK CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1
```

---

## Production Checklist by Language

### Python/FastAPI

- [ ] Multi-stage build (python → python:slim/distroless)
- [ ] `pip install --user --no-cache-dir`
- [ ] Non-root user (UID 10001+)
- [ ] uvicorn or gunicorn+uvicorn in production
- [ ] Health check endpoint implemented
- [ ] Requirements.txt or Poetry lock file
- [ ] No __pycache__ or .pyc in final image
- [ ] Installed packages in /home/appuser/.local
- [ ] PATH includes user packages

### Node.js/TypeScript

- [ ] Multi-stage build (node → node:alpine/distroless)
- [ ] `npm ci --only=production` or `npm prune --production`
- [ ] Non-root user (UID 10001+)
- [ ] node_modules optimized (prod only)
- [ ] Built artifacts copied (dist/)
- [ ] NODE_ENV=production set
- [ ] Health check endpoint implemented
- [ ] .dockerignore excludes dev files
- [ ] Source maps excluded from production

---

## Size Optimization Tips

### Python

1. **Use wheels**: Pre-compile packages with C extensions
   ```dockerfile
   RUN pip wheel --wheel-dir=/wheels -r requirements.txt
   RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
   ```

2. **Remove unnecessary files**:
   ```dockerfile
   RUN find /usr/local -type d -name "tests" -exec rm -rf {} + && \
       find /usr/local -type d -name "__pycache__" -exec rm -rf {} +
   ```

3. **Use uv for faster installs**:
   ```dockerfile
   RUN pip install uv && \
       uv pip install --system -r requirements.txt
   ```

### Node.js

1. **Use npm ci instead of npm install**:
   ```dockerfile
   RUN npm ci --only=production
   ```

2. **Clean npm cache**:
   ```dockerfile
   RUN npm ci && npm cache clean --force
   ```

3. **Remove unnecessary files**:
   ```dockerfile
   RUN rm -rf /app/node_modules/*/test /app/node_modules/*/tests
   ```

---

## References

- [Python Docker Best Practices](https://docs.docker.com/language/python/build-images/)
- [Node.js Docker Best Practices](https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Next.js Docker Example](https://github.com/vercel/next.js/tree/canary/examples/with-docker)

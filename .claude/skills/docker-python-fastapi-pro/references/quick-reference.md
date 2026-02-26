# Docker Quick Reference

Fast lookup for common Dockerfile instructions, base images, and commands.

## Dockerfile Instructions

| Instruction | Purpose | Example | Notes |
|-------------|---------|---------|-------|
| `FROM` | Base image | `FROM python:3.13-slim` | Use specific versions |
| `WORKDIR` | Set working directory | `WORKDIR /app` | Creates if doesn't exist |
| `COPY` | Copy files | `COPY requirements.txt .` | Use for simple file copy |
| `ADD` | Copy with extras | `ADD archive.tar.gz /app` | Can extract archives, fetch URLs |
| `RUN` | Execute command | `RUN pip install -r requirements.txt` | Creates new layer |
| `ENV` | Set environment variable | `ENV PATH="/opt/venv/bin:$PATH"` | Available at build and runtime |
| `ARG` | Build argument | `ARG ENV=production` | Only available at build time |
| `USER` | Switch user | `USER appuser` | Subsequent commands run as this user |
| `EXPOSE` | Document port | `EXPOSE 8000` | Documentation only, doesn't publish |
| `VOLUME` | Create mount point | `VOLUME /data` | For persistent data |
| `CMD` | Default command | `CMD ["uvicorn", "main:app"]` | Can be overridden at runtime |
| `ENTRYPOINT` | Fixed command | `ENTRYPOINT ["python"]` | Not easily overridden |
| `HEALTHCHECK` | Health check | `HEALTHCHECK CMD curl http://localhost:8000/health` | For Docker/K8s monitoring |
| `LABEL` | Add metadata | `LABEL version="1.0"` | For organization |
| `ONBUILD` | Trigger on child build | `ONBUILD COPY . /app` | For base images |

### Instruction Best Practices

```dockerfile
# Use exec form (not shell form) for CMD/ENTRYPOINT
CMD ["uvicorn", "main:app"]  # ✅ Good (exec form)
CMD uvicorn main:app          # ❌ Bad (shell form, PID != 1)

# Chain RUN commands to reduce layers
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*  # ✅ Good (1 layer)

RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*  # ❌ Bad (3 layers, cache not removed)

# Copy dependencies before code (layer caching)
COPY requirements.txt .           # ✅ Good (dependencies cached)
RUN pip install -r requirements.txt
COPY . .                          # Code changes don't invalidate dependency layer

COPY . .                          # ❌ Bad (code changes invalidate everything)
RUN pip install -r requirements.txt
```

## Base Image Selection

### Python Base Images

| Image | Size | Packages | Use Case | Notes |
|-------|------|----------|----------|-------|
| `python:3.13` | ~1GB | Full Debian | Development, all tools | Includes gcc, make, etc. |
| `python:3.13-slim` | ~150MB | Minimal Debian | **Production (recommended)** | Good balance |
| `python:3.13-alpine` | ~50MB | Alpine Linux | Size-critical | musl libc, may have issues |
| `python:3.13-slim-bullseye` | ~150MB | Debian 11 | Specific Debian version | For compatibility |
| `python:3.13-slim-bookworm` | ~150MB | Debian 12 | Latest Debian | Newer packages |

### Size Comparison

```bash
# Check actual sizes
docker pull python:3.13 && docker images python:3.13
docker pull python:3.13-slim && docker images python:3.13-slim
docker pull python:3.13-alpine && docker images python:3.13-alpine
```

**Results:**
- `python:3.13`: ~1.01GB
- `python:3.13-slim`: ~147MB
- `python:3.13-alpine`: ~51MB

### Selection Guide

```
Choose python:3.13-slim IF:
- Production deployment
- Need good package compatibility
- Balance of size and features
- RECOMMENDED for most use cases

Choose python:3.13-alpine IF:
- Size is critical (<100MB required)
- Simple dependencies only
- Team has Alpine experience
- Willing to troubleshoot musl libc issues

Choose python:3.13 IF:
- Development only
- Need all build tools
- Image size not a concern
- NOT for production
```

## Common Docker Commands

### Build

```bash
docker build -t app:latest .                    # Standard build
DOCKER_BUILDKIT=1 docker build -t app:latest .  # With BuildKit (faster)
docker build --no-cache -t app:latest .         # Force rebuild
docker build -f Dockerfile.prod -t app:prod .   # Custom Dockerfile
```

### Run

```bash
docker run -d -p 8000:8000 --name app app:latest              # Detached
docker run -it -p 8000:8000 app:latest                        # Interactive
docker run -d -p 8000:8000 -e DB_URL="..." --name app app:latest  # With env var
docker run -d -p 8000:8000 --env-file .env --name app app:latest  # With env file
docker run -d -p 8000:8000 -v $(pwd):/app --name app app:latest   # With volume
```

### Manage

```bash
docker ps                    # List running containers
docker ps -a                 # List all containers
docker stop app              # Stop container
docker start app             # Start stopped container
docker restart app           # Restart container
docker rm app                # Remove stopped container
docker rm -f app             # Force remove running container
```

### Debug

```bash
docker logs -f app           # Follow logs
docker logs --tail 100 app   # Last 100 lines
docker exec -it app bash     # Interactive shell
docker exec app whoami       # Check user
docker top app               # Running processes
docker inspect app           # Full details
docker stats app             # Resource usage
docker cp app:/app/file .    # Copy file from container
```

### Clean Up

```bash
docker stop $(docker ps -aq)        # Stop all containers
docker rm $(docker ps -aq)          # Remove all containers
docker rmi $(docker images -q)      # Remove all images
docker system prune                 # Remove unused data
docker system prune -a --volumes    # Remove everything unused
docker system df                    # Check disk usage
```

## Environment Variables

### Common FastAPI Environment Variables

```bash
# Application
ENV=production              # Environment (dev/staging/production)
DEBUG=false                 # Debug mode
LOG_LEVEL=info              # Logging level (debug/info/warning/error)
WORKERS=4                   # Number of Uvicorn workers

# Database
DB_URL=postgresql://user:pass@host:5432/db    # Database connection
DB_POOL_SIZE=5              # Connection pool size
DB_MAX_OVERFLOW=10          # Max overflow connections
DB_ECHO=false               # Log SQL queries

# Security
SECRET_KEY=your-secret-key  # Application secret
ALLOWED_HOSTS=*             # Allowed hosts (comma-separated)
CORS_ORIGINS=*              # CORS origins (comma-separated)

# External Services
REDIS_URL=redis://redis:6379/0     # Redis connection
CACHE_TTL=3600              # Cache TTL in seconds
```

### Setting in Dockerfile

```dockerfile
# Build-time (ARG)
ARG ENV=production
ARG PYTHON_VERSION=3.13

# Runtime (ENV)
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV WORKERS=4
```

### Passing at Runtime

```bash
# Single variable
docker run -e DB_URL="postgresql://..." app:latest

# Multiple variables
docker run \
  -e DB_URL="postgresql://..." \
  -e LOG_LEVEL="debug" \
  -e WORKERS="2" \
  app:latest

# From file
docker run --env-file .env app:latest
```

## Port Mapping

```bash
# Host port : Container port
-p 8000:8000       # Map host 8000 to container 8000
-p 80:8000         # Map host 80 to container 8000
-p 9000:8000       # Map host 9000 to container 8000

# Multiple ports
-p 8000:8000 -p 9000:9000

# Bind to specific interface
-p 127.0.0.1:8000:8000    # Only localhost
-p 0.0.0.0:8000:8000      # All interfaces (default)

# Random host port
-p 8000              # Docker assigns random host port

# Check port mapping
docker port <container>
```

## Volume Mounts

```bash
# Bind mount (development)
-v $(pwd):/app                    # Mount current directory
-v /host/path:/container/path     # Explicit paths
-v /host/path:/container/path:ro  # Read-only

# Named volume (data persistence)
-v app-data:/app/data             # Named volume
docker volume create app-data     # Create volume first

# Anonymous volume
-v /container/path                # Docker manages location

# List volumes
docker volume ls

# Inspect volume
docker volume inspect app-data

# Remove unused volumes
docker volume prune
```

## Health Checks

### In Dockerfile

```dockerfile
# HTTP check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Python check (no curl needed)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Custom script
HEALTHCHECK --interval=30s --timeout=3s \
    CMD /app/healthcheck.sh
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--interval` | 30s | Time between checks |
| `--timeout` | 30s | Max time for check |
| `--start-period` | 0s | Grace period on startup |
| `--retries` | 3 | Failed checks before unhealthy |

### Check Status

```bash
# View health status
docker inspect app --format='{{.State.Health.Status}}'

# View health log
docker inspect app --format='{{json .State.Health}}' | jq
```

## .dockerignore Patterns

```
# Virtual environments
venv/
.venv/
env/
*.egg-info/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/
*.swp

# Environment files
.env
.env.*
*.env

# Documentation
README.md
docs/
*.md

# CI/CD
.github/
.gitlab-ci.yml

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
```

## Network Types

```bash
# Bridge (default)
docker network create mynet
docker run --network mynet app:latest

# Host (container uses host network)
docker run --network host app:latest

# None (no network)
docker run --network none app:latest

# Container (share another container's network)
docker run --network container:other-container app:latest

# List networks
docker network ls

# Inspect network
docker network inspect mynet

# Remove network
docker network rm mynet
```

## Multi-Stage Build Template

```dockerfile
# Stage 1: Builder
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

## Success Metrics

| Metric | Target | Command |
|--------|--------|---------|
| Image size | <200MB | `docker images app:latest` |
| Build time | <2min | `time docker build -t app:latest .` |
| Startup time | <5s | `docker logs app` (check first log timestamp) |
| Layer count | <15 | `docker history app:latest \| wc -l` |
| Security scan | 0 critical | `trivy image app:latest` |

## Troubleshooting Quick Checks

```bash
# Is container running?
docker ps | grep app

# Why did it stop?
docker ps -a | grep app

# Check logs
docker logs --tail 50 app

# Check exit code
docker inspect app --format='{{.State.ExitCode}}'

# Enter container
docker exec -it app bash

# Check as root (if needed)
docker exec -it --user root app bash

# Check which user
docker exec app whoami

# Check environment
docker exec app env

# Check processes
docker exec app ps aux

# Check ports
docker port app

# Check disk space
docker exec app df -h
```

## See Also

- `docker-commands.md` - Complete command reference
- `dockerfile-patterns.md` - Dockerfile templates
- `troubleshooting.md` - Detailed troubleshooting
- `best-practices.md` - Best practices guide

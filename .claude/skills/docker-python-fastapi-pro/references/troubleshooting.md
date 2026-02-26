# Docker Troubleshooting for Python/FastAPI

Common Docker issues with Python applications and step-by-step solutions based on production experience and official documentation.

## Issue 1: ModuleNotFoundError in Container

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'uvicorn'
```

**Root Causes:**
1. Multiple Python interpreters in image
2. Dependencies installed with wrong Python/pip
3. Virtual environment not activated
4. PATH not configured correctly

**Diagnosis:**

```bash
# Check which Python is being used
docker exec <container> which python
docker exec <container> which pip

# Check where packages are installed
docker exec <container> pip list

# Check PATH
docker exec <container> echo $PATH
```

**Solutions:**

```dockerfile
# ❌ Problem: Installing with system pip, running with venv Python
FROM python:3.13-slim AS builder
RUN pip install -r requirements.txt  # Installs to system

FROM python:3.13-slim
COPY --from=builder /usr/local /usr/local
RUN python -m venv /opt/venv  # Creates venv
ENV PATH="/opt/venv/bin:$PATH"
CMD ["uvicorn", "main:app"]  # Uses venv Python, can't find system packages
```

```dockerfile
# ✅ Solution 1: Install in venv in builder
FROM python:3.13-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt  # Installs to venv

FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"  # CRITICAL: Set PATH
CMD ["uvicorn", "main:app"]  # Works: Uses venv Python with packages
```

```dockerfile
# ✅ Solution 2: Use absolute path
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
CMD ["/opt/venv/bin/uvicorn", "main:app"]  # Absolute path to uvicorn
```

**Quick Fix:**

```bash
# Temporary: Exec into container and install
docker exec <container> pip install fastapi uvicorn

# Permanent: Fix Dockerfile and rebuild
```

## Issue 2: Container Exits Immediately

**Symptoms:**
```bash
$ docker run -d app:latest
abc123def456

$ docker ps
# Container not running

$ docker ps -a
CONTAINER ID   STATUS
abc123def456   Exited (0) 2 seconds ago
```

**Root Causes:**
1. CMD/ENTRYPOINT completes immediately
2. Application crashes on startup
3. Wrong command syntax
4. Missing environment variables

**Diagnosis:**

```bash
# Check exit code
docker ps -a
# Look at STATUS: Exited (0) = normal exit, Exited (1) = error

# Check logs
docker logs <container>

# Run interactively to see error
docker run -it app:latest /bin/bash

# Or run command directly
docker run -it app:latest uvicorn main:app
```

**Common Causes:**

```dockerfile
# ❌ Cause 1: Wrong CMD syntax (doesn't wait)
CMD python -m uvicorn main:app  # Exits immediately
```

```dockerfile
# ✅ Fix: Use exec form
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# ❌ Cause 2: Background process
CMD ["uvicorn", "main:app", "&"]  # Runs in background, container exits
```

```dockerfile
# ✅ Fix: Remove & (foreground process)
CMD ["uvicorn", "main:app"]
```

**Solution: Application crashes on startup**

```bash
# Check logs for error
docker logs <container>

# Common errors:
# - FileNotFoundError: main.py not found
# - ImportError: Module not installed
# - Connection error: Database not accessible
# - Permission denied: Running as wrong user

# Fix based on error, rebuild, and retry
```

## Issue 3: Port Not Accessible

**Symptoms:**
```bash
$ docker run -d -p 8000:8000 app:latest
$ curl http://localhost:8000
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Root Causes:**
1. Application listening on wrong host (127.0.0.1 instead of 0.0.0.0)
2. Port mapping incorrect
3. Application not started
4. Firewall blocking

**Diagnosis:**

```bash
# Check if container is running
docker ps

# Check logs
docker logs <container>

# Check what ports are exposed
docker port <container>

# Check if app is listening
docker exec <container> netstat -tulpn | grep 8000
```

**Solutions:**

```dockerfile
# ❌ Problem: Listening on localhost only
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
# App listens on 127.0.0.1:8000 (inside container only)
```

```dockerfile
# ✅ Solution: Listen on all interfaces
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# App listens on 0.0.0.0:8000 (accessible from outside container)
```

```bash
# Check port mapping
docker run -d -p 8000:8000 app:latest  # Host 8000 → Container 8000

# Or use different host port
docker run -d -p 9000:8000 app:latest  # Host 9000 → Container 8000
```

## Issue 4: Permission Denied Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/logs'
OSError: [Errno 13] Permission denied: '/tmp/file'
```

**Root Causes:**
1. Running as non-root user without proper ownership
2. Directory not writable by app user
3. Volume mounted with wrong permissions

**Diagnosis:**

```bash
# Check which user the app runs as
docker exec <container> whoami

# Check file ownership
docker exec <container> ls -la /app

# Check directory permissions
docker exec <container> ls -ld /app/logs
```

**Solutions:**

```dockerfile
# ❌ Problem: Files owned by root, app runs as appuser
FROM python:3.13-slim
COPY . .  # Copied as root
RUN useradd -m -u 10001 appuser
USER appuser
CMD ["uvicorn", "main:app"]  # Can't write to /app (owned by root)
```

```dockerfile
# ✅ Solution: Set ownership when copying
FROM python:3.13-slim
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app
COPY --chown=appuser:appuser . .  # Copied as appuser
USER appuser
CMD ["uvicorn", "main:app"]  # Can write to /app
```

**Volume Permissions:**

```bash
# Problem: Volume mounted with root ownership
docker run -v $(pwd)/logs:/app/logs app:latest
# /app/logs owned by root on host

# Solution: Create directory with correct permissions first
mkdir -p logs
sudo chown 10001:10001 logs  # Match UID in container
docker run -v $(pwd)/logs:/app/logs app:latest
```

## Issue 5: Database Connection Errors

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
psycopg2.OperationalError: connection to server at "localhost", port 5432 failed
```

**Root Causes:**
1. Using "localhost" instead of host IP
2. Database not running
3. Wrong connection string
4. Network not configured

**Diagnosis:**

```bash
# Check if database is accessible from container
docker exec <container> ping postgres-host

# Check environment variables
docker exec <container> env | grep DB

# Try connecting manually
docker exec <container> psql -h postgres-host -U user -d db
```

**Solutions:**

```dockerfile
# ❌ Problem: localhost refers to container itself
ENV DB_URL="postgresql://user:pass@localhost:5432/db"
```

```dockerfile
# ✅ Solution 1: Use host IP or hostname
ENV DB_URL="postgresql://user:pass@192.168.1.100:5432/db"

# ✅ Solution 2: Use Docker network
# docker run --network my-network app:latest
ENV DB_URL="postgresql://user:pass@postgres:5432/db"
# "postgres" is service name in network

# ✅ Solution 3: Pass at runtime
# docker run -e DB_URL="..." app:latest
```

**Docker Compose Solution:**

```yaml
version: '3.8'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s

  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      DB_URL: "postgresql://postgres:secret@db:5432/mydb"
    # "db" resolves to database container
```

## Issue 6: Image Build Fails

### 6a: "No space left on device"

**Symptoms:**
```
ERROR: failed to solve: failed to copy: write /var/lib/docker/...: no space left on device
```

**Solutions:**

```bash
# Check disk space
df -h

# Clean up Docker resources
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

### 6b: Package Installation Fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement somepackage
```

**Solutions:**

```dockerfile
# ❌ Problem: No network access during build
RUN pip install somepackage
```

```bash
# Check network
docker build --network=host -t app:latest .

# Or check if package name is correct
pip search somepackage
```

### 6c: Build Dependency Missing

**Symptoms:**
```
error: command 'gcc' failed with exit status 1
```

**Solutions:**

```dockerfile
# ❌ Missing build dependencies
RUN pip install psycopg2  # Needs gcc, postgresql-dev
```

```dockerfile
# ✅ Install build dependencies first
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install psycopg2
```

**Or use binary packages:**

```dockerfile
# Binary version (no compilation needed)
RUN pip install psycopg2-binary
```

## Issue 7: Slow Build Times

**Symptoms:**
- First build takes >5 minutes
- Rebuilds after code changes take >2 minutes
- Large build context

**Solutions:**

### Create .dockerignore

```
# .dockerignore
venv/
.venv/
__pycache__/
.git/
.pytest_cache/
node_modules/
```

### Optimize Layer Caching

```dockerfile
# ❌ Bad order: code changes invalidate dependency cache
COPY . .
RUN pip install -r requirements.txt

# ✅ Good order: dependencies cached separately
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### Enable BuildKit

```bash
export DOCKER_BUILDKIT=1
docker build -t app:latest .
```

## Issue 8: Environment Variables Not Working

**Symptoms:**
```
KeyError: 'DB_URL'
Config value missing
```

**Diagnosis:**

```bash
# Check env vars in container
docker exec <container> env

# Check if .env file was copied (it shouldn't be)
docker exec <container> ls -la | grep .env
```

**Solutions:**

```bash
# ❌ Don't copy .env file
# .env should be in .dockerignore

# ✅ Pass env vars at runtime
docker run -e DB_URL="postgresql://..." app:latest

# ✅ Or use env file
docker run --env-file .env app:latest

# ✅ Or in docker-compose.yml
services:
  app:
    environment:
      DB_URL: "postgresql://..."
    # Or
    env_file:
      - .env
```

## Issue 9: Container Running but App Not Working

**Symptoms:**
- Container status: Up
- Logs show no errors
- But API returns 500 errors or no response

**Diagnosis:**

```bash
# Check logs
docker logs -f <container>

# Check app health
docker exec <container> curl http://localhost:8000/health

# Check running processes
docker top <container>

# Enter container and debug
docker exec -it <container> /bin/bash
# Then manually test
python -m uvicorn main:app --host 0.0.0.0
```

**Common Causes:**

1. **Wrong working directory**
```dockerfile
# ❌ App code not in WORKDIR
WORKDIR /app
COPY . /code  # Copied to /code, not /app
CMD ["uvicorn", "main:app"]  # Looks in /app, finds nothing
```

2. **Import errors**
```python
# main.py
from app import routes  # Module 'app' not found

# Fix: Check PYTHONPATH or restructure imports
```

3. **Database migrations not run**
```bash
# Solution: Run migrations on startup
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0"]
```

## Issue 10: Memory/CPU Issues

**Symptoms:**
- Container killed (OOM)
- Slow response times
- High CPU usage

**Diagnosis:**

```bash
# Check resource usage
docker stats <container>

# Check limits
docker inspect <container> | grep -i memory

# Check logs for OOM
docker logs <container> | grep -i "killed"
```

**Solutions:**

```bash
# Set memory limit
docker run -m 512m app:latest

# Set CPU limit
docker run --cpus="1.5" app:latest

# Kubernetes resource limits
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Optimize application:**

```python
# Reduce workers if memory-constrained
# CMD ["uvicorn", "main:app", "--workers", "2"]

# Add connection pooling
engine = create_engine(
    DB_URL,
    pool_size=5,  # Don't create too many connections
    max_overflow=10
)
```

## Debugging Workflow

```bash
# 1. Check if container is running
docker ps -a

# 2. Check logs
docker logs <container>

# 3. Check last 50 lines
docker logs --tail 50 <container>

# 4. Follow logs in real-time
docker logs -f <container>

# 5. Enter container
docker exec -it <container> /bin/bash

# 6. Inside container, check:
whoami  # Which user?
pwd     # Where are we?
ls -la  # What files exist?
env     # What env vars?
python -c "import fastapi; print(fastapi.__version__)"  # Imports work?

# 7. Try running app manually
uvicorn main:app --host 0.0.0.0 --port 8000

# 8. If manual run works, check CMD/ENTRYPOINT
docker inspect <container> | grep -A 10 Cmd

# 9. Rebuild with verbose output
docker build --progress=plain --no-cache -t app:debug .

# 10. Run with interactive terminal
docker run -it app:debug /bin/bash
```

## Common Error Messages

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `ModuleNotFoundError` | Packages not installed or wrong Python | Check PATH, venv |
| `Permission denied` | Wrong file ownership | Use --chown, match UIDs |
| `Connection refused` | App not listening on 0.0.0.0 | Use --host 0.0.0.0 |
| `No space left` | Disk full | docker system prune |
| `Cannot find module 'main'` | Wrong WORKDIR or COPY | Check paths |
| `Container exits immediately` | CMD completes or crashes | Check logs, run interactively |
| `Database connection failed` | Wrong host or network | Use container names, check network |
| `Port already allocated` | Port in use | Use different port or stop conflicting container |

## Quick Fixes Reference

```bash
# Clean restart
docker stop <container> && docker rm <container>
docker run -d -p 8000:8000 --name app app:latest

# View real-time logs
docker logs -f app

# Execute command in running container
docker exec app uvicorn main:app

# Copy file from container
docker cp app:/app/logs/error.log .

# Inspect container config
docker inspect app

# Check resource usage
docker stats app

# Clean up everything
docker system prune -a --volumes
```

## References

- [Docker Docs: Troubleshoot](https://docs.docker.com/config/containers/troubleshoot/)
- [Python Speed: Debugging ImportErrors](https://pythonspeed.com/articles/importerror-docker/)
- [DigitalOcean: Debug Docker Issues](https://www.digitalocean.com/community/tutorials/how-to-debug-and-fix-common-docker-issues)

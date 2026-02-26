---
name: docker-python-fastapi-pro
description: |
  Comprehensive Docker skill for containerizing Python/FastAPI applications from hello world to production-ready deployments. Covers multi-stage builds, security hardening, image optimization, Kubernetes readiness, troubleshooting, and CI/CD integration. This skill should be used when users want to containerize Python applications, create Dockerfiles, optimize Docker images, debug container issues, or prepare applications for Kubernetes deployment. Handles all experience levels with progressive guidance.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Docker Python FastAPI Pro

Containerize Python/FastAPI applications from prototype to production with Docker best practices, security, optimization, and Kubernetes readiness.

---

## What This Skill Does

- Creates Dockerfiles for Python/FastAPI applications (hello world → production)
- Implements multi-stage builds for minimal image sizes
- Applies security hardening (non-root users, minimal attack surface)
- Optimizes images (layer caching, size reduction, build performance)
- Prepares containers for Kubernetes (health checks, probes, configuration)
- Troubleshoots common Docker-Python issues
- Provides CI/CD integration patterns

## What This Skill Does NOT Do

- Deploy containers to production infrastructure (use deployment tools)
- Manage container orchestration (use Kubernetes/Docker Compose skills)
- Replace Docker CLI (provides guidance, not a Docker wrapper)
- Handle non-Python languages (focused on Python/FastAPI)

---

## Before Implementation

Gather context to ensure successful containerization:

| Source | Gather |
|--------|--------|
| **Codebase** | Application structure, dependencies (requirements.txt, pyproject.toml, uv), entry points, environment variables |
| **Conversation** | User's deployment target (local, K8s, cloud), performance requirements, security constraints |
| **Skill References** | Docker best practices from `references/` (multi-stage patterns, security, optimization) |
| **User Guidelines** | Organization's Docker standards, base image policies, registry requirements |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (Docker expertise is in this skill).

---

## Implementation Workflow

### Phase 1: Discover Context

**Automatic Discovery** (no user input needed):

1. **Detect Application Type**
   ```bash
   # Check for FastAPI patterns
   grep -r "from fastapi import" . --include="*.py"

   # Identify dependency manager
   ls -la | grep -E "requirements.txt|pyproject.toml|uv.lock"

   # Find entry points
   grep -r "if __name__ == '__main__':" . --include="*.py"
   grep -r "app = FastAPI" . --include="*.py"
   ```

2. **Identify Dependencies**
   - Package manager: pip, poetry, uv
   - Python version requirement
   - System dependencies (databases, compilers)
   - Build vs runtime dependencies

3. **Determine Complexity Level**
   - Hello world: Single file, no external deps
   - Simple: FastAPI + database client
   - Production: Multi-service, secrets, monitoring

### Phase 2: Ask User for Requirements

**Required Clarifications** (always ask):

1. **Deployment target**: Where will this run?
   - Local development environment
   - Kubernetes cluster
   - Cloud platform (AWS/GCP/Azure)
   - Other (specify)

2. **Security requirements**: What security standards apply?
   - Compliance requirements (PCI-DSS, HIPAA, SOC2)
   - Non-root user mandatory
   - Security scanning required
   - No specific requirements

**Optional Clarifications** (ask if not clear from context):

3. **Performance priorities** (if not obvious from context):
   - Minimize image size
   - Optimize build speed
   - Optimize runtime performance
   - Balance all three

4. **Existing constraints** (if organization has standards):
   - Required base image or version
   - Registry requirements
   - Image naming conventions
   - Resource limits

**Question Pacing**: Ask Required questions (1-2) first. Ask Optional questions (3-4) only if context doesn't provide clear answers.

**Graceful Handling**: If user doesn't specify optional items, use sensible defaults:
- Performance: Balance all three
- Constraints: No specific constraints

### Phase 3: Select Dockerfile Strategy

Based on discovered context:

| Scenario | Strategy | Template |
|----------|----------|----------|
| **Hello World** | Single-stage, standard Python image | `assets/dockerfiles/hello-world.Dockerfile` |
| **Development** | Hot-reload, debugger, volumes | `assets/dockerfiles/dev.Dockerfile` |
| **Production** | Multi-stage, slim image, non-root | `assets/dockerfiles/production.Dockerfile` |
| **Kubernetes** | Health checks, signals, non-root | `assets/dockerfiles/kubernetes.Dockerfile` |

See `references/dockerfile-patterns.md` for complete patterns (6 variations).

### Phase 4: Implement Dockerfile

Follow implementation checklist:

```markdown
- [ ] Choose base image (python:3.x vs python:3.x-slim vs alpine)
- [ ] Configure multi-stage build (builder + runtime)
- [ ] Set working directory and non-root user
- [ ] Copy dependency files first (layer caching)
- [ ] Install dependencies with --no-cache-dir
- [ ] Copy application code
- [ ] Set environment variables
- [ ] Configure health check endpoint
- [ ] Set CMD/ENTRYPOINT
- [ ] Add .dockerignore file
```

### Phase 5: Optimize and Harden

Apply optimization techniques from `references/optimization.md`:

**Size Optimization:**
- Multi-stage builds (reduce by 70%+)
- Slim/alpine base images
- Remove build dependencies from final stage
- Use .dockerignore

**Security Hardening:**
- Run as non-root user (UID 10001)
- Use minimal base images
- No secrets in layers
- Regular security scanning

**Build Performance:**
- Layer caching strategy
- Dependency installation before code copy
- BuildKit features

### Phase 6: Test and Validate

```bash
# Build image
docker build -t app-name:test .

# Check image size
docker images app-name:test

# Run container
docker run -d -p 8000:8000 --name app-test app-name:test

# Test health endpoint
curl http://localhost:8000/health

# Check logs
docker logs app-test

# Inspect as non-root
docker exec app-test whoami
```

See `references/docker-commands.md` for complete command reference.

---

## Troubleshooting Guide

### Issue: ModuleNotFoundError in Container

**Symptoms:** `ModuleNotFoundError: No module named 'fastapi'`

**Causes:**
- Dependencies not installed in correct Python environment
- Multiple Python interpreters in image
- Virtual environment not activated

**Solutions:**
```dockerfile
# Ensure virtual environment is in PATH
ENV PATH="/opt/venv/bin:$PATH"

# OR use absolute path to Python
CMD ["/opt/venv/bin/uvicorn", "main:app", ...]
```

See `references/troubleshooting.md` for 20+ common issues with solutions.

### Issue: Container Exits Immediately

**Symptoms:** Container starts then exits with code 0 or 1

**Diagnosis:**
```bash
# Check logs
docker logs app

# Run interactively to see error
docker run -it app-name:latest /bin/bash
```

**Common Causes:**
- Wrong CMD/ENTRYPOINT
- Application crashes on startup
- Missing environment variables

### Issue: Image Too Large

**Symptoms:** Image size >500MB for simple FastAPI app

**Solutions:**
1. Use multi-stage builds
2. Switch to python:3.x-slim (vs standard)
3. Remove build dependencies from final stage
4. Add .dockerignore file

See `references/optimization.md` for detailed optimization strategies.

---

## Security Checklist

Before deploying to production:

```markdown
- [ ] Running as non-root user (USER instruction)
- [ ] Using minimal base image (slim or alpine)
- [ ] No secrets in Dockerfile or layers
- [ ] .dockerignore excludes .env, .git, secrets
- [ ] Regular base image updates
- [ ] Security scanning enabled (docker scan)
- [ ] Health checks configured
- [ ] Resource limits set (memory, CPU)
- [ ] Read-only root filesystem (if possible)
- [ ] Capabilities dropped (if using K8s security contexts)
```

See `references/security.md` for complete security hardening guide.

---

## Output Checklist

After creating/optimizing Dockerfile:

**Functionality:**
- [ ] Image builds successfully
- [ ] Container starts and serves traffic
- [ ] Health endpoint responds
- [ ] Environment variables work
- [ ] Database connections succeed

**Optimization:**
- [ ] Image size <200MB for simple apps
- [ ] Build cache working effectively
- [ ] .dockerignore file present
- [ ] Multi-stage build (if applicable)

**Security:**
- [ ] Non-root user configured
- [ ] Minimal base image used
- [ ] No secrets in layers
- [ ] Security scan passes

**Production-Ready:**
- [ ] Health checks configured
- [ ] Logging to stdout/stderr
- [ ] Graceful shutdown handling
- [ ] Resource limits documented
- [ ] K8s manifests provided (if needed)

---

## Examples by Complexity

### Hello World FastAPI

```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production with Database

See `assets/dockerfiles/production.Dockerfile` for complete example with:
- Multi-stage build
- Non-root user
- Health checks
- Optimized layers

### Multi-Service with Docker Compose

See `assets/docker-compose.yml` for FastAPI + PostgreSQL + Redis example.

---

## Success Metrics

Track these metrics to measure Docker optimization:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Image size | <200MB (simple apps) | `docker images` |
| Build time | <2min (with cache) | Time `docker build` |
| Startup time | <5s | Check container logs |
| Security scan | 0 critical vulns | `docker scan` |
| Layer count | <15 layers | `docker history` |

---

## Reference Files

| File | Content | Use When |
|------|---------|----------|
| `references/dockerfile-patterns.md` | 6 complete Dockerfile patterns | Implementing any scenario |
| `references/multi-stage-builds.md` | Multi-stage patterns, examples, size comparisons | Building production images |
| `references/optimization.md` | Layer caching, image size reduction, build speed | Optimizing images |
| `references/security.md` | Security hardening, scanning, compliance | Hardening for production |
| `references/troubleshooting.md` | 20+ common issues with solutions | Debugging container issues |
| `references/kubernetes.md` | K8s manifests, probes, security contexts | Deploying to Kubernetes |
| `references/cicd.md` | CI/CD pipeline examples | Automating builds |
| `references/best-practices.md` | Docker best practices for Python | General guidance |
| `references/docker-commands.md` | Complete Docker command reference | Running/debugging containers |
| `references/quick-reference.md` | Quick lookup tables and cheat sheet | Fast reference |

### Finding Specific Topics

Use grep to find content efficiently in large reference files:

```bash
# Find multi-stage patterns
grep -n "Pattern" references/dockerfile-patterns.md

# Find security issues
grep -n "Issue\|Problem" references/security.md

# Find troubleshooting for specific error
grep -n "ModuleNotFoundError\|ExitCode\|Permission" references/troubleshooting.md

# Find optimization techniques
grep -n "Strategy\|Optimization" references/optimization.md

# Find Kubernetes examples
grep -n "apiVersion\|Deployment" references/kubernetes.md

# Find CI/CD examples
grep -n "GitHub Actions\|GitLab\|Jenkins" references/cicd.md

# Find Docker commands
grep -n "docker build\|docker run\|docker exec" references/docker-commands.md

# Find quick reference tables
grep -n "Image\|Size\|Command" references/quick-reference.md
```

---

## Resources

- [Docker Official Docs - Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/concepts/containers/)

See `references/` directory for embedded domain expertise gathered from official sources.

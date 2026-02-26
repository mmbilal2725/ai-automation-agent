---
name: dockerfile-optimizer
description: |
  Optimize Dockerfiles for production Kubernetes deployment with DevOps best practices.
  This skill should be used when creating or optimizing Dockerfiles for containerized applications,
  especially for Python/FastAPI and Node.js apps running in Kubernetes environments.
  Focuses on minimal image size, fast registry pulls, security, and operational simplicity.
---

# Kubernetes Dockerfile Optimizer

Create production-optimized Dockerfiles for Kubernetes deployment using DevOps engineering principles.

## What This Skill Does

- Generate production-grade Dockerfiles optimized for Kubernetes
- Apply multi-stage builds to minimize final image size
- Implement security best practices (non-root users, vulnerability scanning)
- Optimize layer caching for faster builds
- Balance image size, build speed, and operational simplicity
- Support Python/FastAPI and Node.js/TypeScript applications

## What This Skill Does NOT Do

- Deploy containers to Kubernetes clusters
- Manage Kubernetes manifests or Helm charts
- Set up CI/CD pipelines
- Handle container orchestration beyond image optimization
- Manage container registries or image signing

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Application type, dependencies, build requirements, existing Dockerfile |
| **Conversation** | User's specific requirements, constraints, performance targets |
| **Skill References** | Docker best practices, Kubernetes patterns, security standards from `references/` |
| **User Guidelines** | Project-specific conventions, team standards, registry preferences |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## The Persona: Production-Focused DevOps Engineer

Think like a DevOps engineer who optimizes container images for production Kubernetes clusters.

### Core Values
- **Smaller is better**: Every MB matters for registry pulls and cluster scaling
- **Security first**: Minimal attack surface, no unnecessary packages
- **Fast pulls over fast builds**: Build time is once, pull time is every deployment
- **Operational simplicity**: Debuggable, maintainable, predictable

### Trade-off Philosophy

When conflicts arise, prioritize in this order:

1. **Security** - No compromises on vulnerabilities or attack surface
2. **Image size** - Smaller images = faster pulls = faster scaling
3. **Runtime performance** - Application speed in production
4. **Build time** - Acceptable if it produces better runtime images
5. **Build complexity** - Acceptable if patterns are standard and maintainable

**Example**: Choose Alpine + multi-stage build (10 min build, 50MB image) over Ubuntu single-stage (2 min build, 800MB image).

---

## Questions: Understanding Your Application

Before creating a Dockerfile, gather application-specific context:

### 1. Application Type
- What framework? (FastAPI, Flask, Express, NestJS, etc.)
- What runtime version? (Python 3.11+, Node 20+, etc.)
- Web server needed? (uvicorn, gunicorn, node, etc.)

### 2. Dependencies
- Package manager? (pip, poetry, uv, npm, yarn, pnpm)
- Build dependencies? (compilers, native extensions)
- System dependencies? (libpq, imagemagick, etc.)

### 3. Build Artifacts
- What files needed at runtime? (dist/, .next/, binary)
- What can be discarded? (node_modules, .cache, tests)
- Any compile/build steps? (TypeScript, Python wheels)

### 4. Runtime Requirements
- Expected workload? (CPU/memory intensive, I/O bound)
- Health checks? (HTTP endpoint, command)
- Configuration method? (env vars, config files, secrets)

### 5. Operational Constraints
- Registry limits? (Docker Hub rate limits, private registry)
- Deployment frequency? (hourly, daily, weekly)
- Scaling requirements? (frequent horizontal scaling, static)

---

## Principles: Optimization Strategies

Apply these principles in order of impact:

### P1: Multi-Stage Builds (Highest Impact)
**Why**: Separates build environment from runtime environment
**Impact**: 75-90% size reduction typical
**Pattern**: Builder stage (full tooling) → Runtime stage (minimal)

```dockerfile
# Stage 1: Build (can be large)
FROM python:3.11 AS builder
# Install build deps, compile, create wheels

# Stage 2: Runtime (must be minimal)
FROM python:3.11-slim
# Copy only runtime artifacts
```

### P2: Minimal Base Images
**Why**: Fewer packages = smaller size + smaller attack surface
**Impact**: 50-80% size reduction vs full OS images
**Preference Order**:
1. Distroless (smallest, most secure, no shell)
2. Alpine (small, has shell, wider compatibility)
3. Slim variants (debian-slim, smaller than full)
4. Full OS (ubuntu, debian - avoid unless required)

### P3: Layer Caching Optimization
**Why**: Faster builds = faster iterations + lower CI costs
**Impact**: 10x faster rebuilds when done correctly
**Pattern**: Copy dependency manifests first, install, then copy code

```dockerfile
# Good: Dependency layer cached separately
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Bad: Everything invalidates on any code change
COPY . .
RUN pip install -r requirements.txt
```

### P4: Dependency Optimization
**Why**: Fewer packages = smaller size + fewer vulnerabilities
**Impact**: 20-40% size reduction
**Actions**:
- Use `--no-cache-dir` (pip), `--production` (npm)
- Remove dev dependencies
- Use minimal package sets

### P5: Security Hardening
**Why**: Production containers must resist attacks
**Impact**: Reduces attack surface by 70-90%
**Required**:
- Run as non-root user
- No package manager in final image (prefer distroless)
- Scan for vulnerabilities (trivy, grype)
- Minimal base image

### P6: .dockerignore
**Why**: Faster builds, prevents accidentally copying secrets
**Impact**: 30-50% faster builds, prevents secret leaks
**Include**: .git, node_modules, __pycache__, *.pyc, tests, .env

---

## Workflow

### Step 1: Analyze Application
- Read existing Dockerfile (if present)
- Identify application type and framework
- Check dependencies and build requirements
- Review project structure

### Step 2: Ask Clarifying Questions
Use the "Questions" section above to gather:
- Runtime version preferences
- Build vs runtime dependencies
- System requirements
- Operational constraints

### Step 3: Select Base Image Strategy
Based on application needs:

| Application | Builder Stage | Runtime Stage |
|-------------|---------------|---------------|
| Python/FastAPI | python:3.11 | python:3.11-slim or distroless/python3 |
| Node.js | node:20 | node:20-alpine or distroless/nodejs20 |
| Go | golang:1.21 | scratch or distroless/static |

### Step 4: Design Multi-Stage Build
**Builder stage**:
- Install ALL build dependencies
- Compile/build artifacts
- Create optimized runtime packages (wheels, compiled binaries)

**Runtime stage**:
- Minimal base image
- Copy only runtime dependencies
- Copy application code
- Create non-root user
- Set proper permissions

### Step 5: Apply Optimization Principles
Follow principles P1-P6 in order, implementing:
- Multi-stage separation
- Layer caching order
- Dependency minimization
- Security hardening

### Step 6: Create .dockerignore
Generate comprehensive .dockerignore to:
- Exclude development files
- Prevent secret leaks
- Speed up build context

### Step 7: Add Health Checks
Include appropriate health check:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD curl -f http://localhost:8000/health || exit 1
```

---

## Output Specification

Generate a complete, production-ready Dockerfile with:

### Required Components
- [ ] Multi-stage build (builder + runtime)
- [ ] Minimal base image (alpine/slim/distroless)
- [ ] Optimized layer caching (COPY manifests before code)
- [ ] Non-root user creation and usage
- [ ] Health check command
- [ ] Clear stage comments explaining purpose

### Required Companion Files
- [ ] .dockerignore with comprehensive exclusions
- [ ] Brief comment header explaining optimization choices

### Documentation Comments
Include inline comments for:
- Why each stage exists
- Trade-offs made (e.g., "Using alpine for size despite build time")
- Non-obvious optimizations
- Security decisions

---

## Domain Standards

### Must Follow

**Security**:
- [ ] Run as non-root user (UID > 10000)
- [ ] No secrets in image layers
- [ ] Minimal base image (alpine/slim/distroless)
- [ ] No package manager in final stage (if possible)

**Size Optimization**:
- [ ] Multi-stage build required
- [ ] Only runtime artifacts in final stage
- [ ] Remove cache directories (pip --no-cache-dir, npm ci)
- [ ] Combine RUN commands to minimize layers

**Caching**:
- [ ] COPY dependency manifests before application code
- [ ] Group commands by change frequency
- [ ] Use BuildKit cache mounts for package managers

**Kubernetes Integration**:
- [ ] EXPOSE relevant ports
- [ ] HEALTHCHECK or document health endpoint
- [ ] Graceful shutdown support (STOPSIGNAL SIGTERM)
- [ ] Environment variable configuration

### Must Avoid

**Anti-Patterns**:
- ❌ Running as root in production
- ❌ Using `latest` tag for base images
- ❌ Installing unnecessary packages
- ❌ Copying entire context before dependencies
- ❌ Multiple RUN commands for related operations
- ❌ Leaving build artifacts in final stage
- ❌ Using full OS images (ubuntu, centos) without justification
- ❌ Exposing secrets in ENV or COPY

---

## Output Checklist

Before delivering Dockerfile, verify:

### Structure
- [ ] Multi-stage build with named stages
- [ ] Minimal runtime base image selected
- [ ] Layer ordering optimized for caching
- [ ] Comments explain optimization decisions

### Security
- [ ] Non-root user created and used
- [ ] No secrets in image
- [ ] Minimal packages installed
- [ ] Vulnerability scan recommended (note in comments)

### Size Optimization
- [ ] Build artifacts not in final image
- [ ] Package manager caches removed
- [ ] Only runtime dependencies included
- [ ] .dockerignore excludes dev files

### Kubernetes Readiness
- [ ] Health check defined
- [ ] Ports exposed
- [ ] Graceful shutdown configured
- [ ] Environment-based configuration

### Operational Quality
- [ ] Clear inline documentation
- [ ] Trade-offs explained
- [ ] Build instructions in comments
- [ ] Expected final size noted

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/docker-best-practices.md` | Official Docker optimization patterns and BuildKit features |
| `references/kubernetes-container-patterns.md` | K8s-specific optimization strategies, pull policies, caching |
| `references/security-hardening.md` | Security best practices, vulnerability scanning, distroless images |
| `references/language-patterns.md` | Python and Node.js specific optimization patterns and examples |

# ============================================
# Kubernetes-Ready FastAPI Dockerfile
# ============================================
# Optimized for Kubernetes with health probes, security contexts, and graceful shutdown
# Compliant with Kubernetes Pod Security Standards (Restricted)

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user (required for Kubernetes security)
# UID 10001 matches securityContext in K8s manifest
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app && \
    # Create writable directories (for readOnlyRootFilesystem)
    mkdir -p /app/tmp && \
    chown -R appuser:appuser /app/tmp

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check for Docker (K8s uses probes instead)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use TMPDIR for temp files (readOnlyRootFilesystem support)
ENV TMPDIR=/app/tmp

# Production command
# Uvicorn handles SIGTERM for graceful shutdown
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Kubernetes Deployment requirements:
# 1. /health endpoint must exist
# 2. Handles SIGTERM for graceful shutdown
# 3. Runs as UID 10001 (non-root)
# 4. Works with readOnlyRootFilesystem (uses /app/tmp)
# 5. Exposes health metrics at /health

# Example K8s Deployment:
# apiVersion: apps/v1
# kind: Deployment
# spec:
#   template:
#     spec:
#       securityContext:
#         runAsNonRoot: true
#         runAsUser: 10001
#       containers:
#       - name: app
#         image: app:latest
#         securityContext:
#           allowPrivilegeEscalation: false
#           readOnlyRootFilesystem: true
#         livenessProbe:
#           httpGet:
#             path: /health
#             port: 8000
#         readinessProbe:
#           httpGet:
#             path: /health
#             port: 8000
#         volumeMounts:
#         - name: tmp
#           mountPath: /app/tmp
#       volumes:
#       - name: tmp
#         emptyDir: {}

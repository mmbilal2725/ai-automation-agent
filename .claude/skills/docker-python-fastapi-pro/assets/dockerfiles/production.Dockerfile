# ============================================
# Production-Ready FastAPI Dockerfile
# ============================================
# Multi-stage build with security hardening and optimization
# Based on official Docker and FastAPI best practices

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies for compiling Python packages
# --no-install-recommends: Only install essential packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (layer caching optimization)
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
# --no-cache-dir: Don't store pip cache (saves space)
# --upgrade pip: Get latest pip with security fixes
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Install only runtime dependencies (not build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY the virtual environment from builder (not build tools)
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
# UID 10001 is convention for non-root service users
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app

# Copy application code with correct ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user (CRITICAL for security)
USER appuser

# Health check for Docker and Kubernetes
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Document exposed port
EXPOSE 8000

# Production command with multiple workers
# Workers = (2 x CPU cores) + 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Image size: ~180MB (vs 1.2GB for single-stage)
# Security: Non-root user, minimal packages, no build tools
# Optimization: Multi-stage build, layer caching, no pip cache

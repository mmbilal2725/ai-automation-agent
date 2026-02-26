# ============================================
# Development FastAPI Dockerfile
# ============================================
# Hot-reload enabled, debugging tools, not optimized for size
# Use with docker-compose and volume mounts for development

FROM python:3.13-slim

WORKDIR /app

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt requirements-dev.txt* ./

# Install all dependencies (including dev dependencies)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# Copy application code (will be overridden by volume mount)
COPY . .

# Expose port
EXPOSE 8000

# Development command with hot-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Usage with docker-compose.yml:
# services:
#   app:
#     build:
#       context: .
#       dockerfile: dev.Dockerfile
#     volumes:
#       - ./:/app  # Mount code for hot-reload
#     ports:
#       - "8000:8000"
#     environment:
#       - DEBUG=true

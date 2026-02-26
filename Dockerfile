# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies using uv (cached layer)
COPY pyproject.toml ./
RUN uv sync --no-dev --frozen

# Copy source code
COPY app/ ./app/
COPY data/ ./data/

# Load FAQ knowledge base into ChromaDB at build time
RUN uv run python -m app.scripts.load_knowledge --csv data/faq.csv

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies using uv (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Copy source code
COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

# Load FAQ into ChromaDB at startup (needs OPENAI_API_KEY available at runtime)
# then start the server
CMD ["sh", "-c", "uv run python -m app.scripts.load_knowledge --csv data/faq.csv && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]

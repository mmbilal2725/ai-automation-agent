# Quickstart — Local Development

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker Desktop (for PostgreSQL)
- A Meta Developer account (for Messenger/Instagram)
- A SendGrid account (for email)

---

## 1. Install dependencies

```bash
uv sync
uv sync --dev   # includes pytest
```

## 2. Configure environment

```bash
cp .env.example .env
# Fill in your keys in .env
```

## 3. Start PostgreSQL

```bash
docker compose up db -d
```

## 4. Load the FAQ knowledge base

```bash
uv run python -m app.scripts.load_knowledge
```

This reads `data/faq.csv` and builds the ChromaDB vector store at `./chroma_db/`.

## 5. Run the app

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`.
Auto-docs: `http://localhost:8000/docs`

## 6. Expose locally for Meta webhooks (dev only)

Meta needs a public HTTPS URL to send webhooks. Use [ngrok](https://ngrok.com):

```bash
ngrok http 8000
# Gives you: https://abc123.ngrok-free.app
```

Register these URLs in the Meta App Dashboard:
- Messenger: `https://abc123.ngrok-free.app/webhooks/messenger`
- Instagram: `https://abc123.ngrok-free.app/webhooks/instagram`

## 7. Run tests

```bash
uv run pytest                        # all tests
uv run pytest tests/unit/            # unit only (no DB/network needed)
uv run pytest tests/integration/     # integration only
uv run pytest -v                     # verbose
```

## 8. Full Docker build

```bash
docker compose up --build
```

---

## Key commands

| What | Command |
|---|---|
| Install deps | `uv sync` |
| Run server | `uv run uvicorn app.main:app --reload` |
| Load FAQ | `uv run python -m app.scripts.load_knowledge` |
| Run tests | `uv run pytest` |
| Docker up | `docker compose up --build` |

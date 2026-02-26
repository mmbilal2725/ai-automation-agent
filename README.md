# AI Automation Agent

An intelligent customer service agent that handles real-time inquiries across **Facebook Messenger**, **Instagram DMs**, and **Email** — powered by RAG (Retrieval-Augmented Generation) and OpenAI.

---

## Features

- **Multi-channel**: Messenger, Instagram, and Email from one unified backend
- **RAG-powered responses**: Answers grounded in your FAQ knowledge base via ChromaDB — no hallucinations
- **Human escalation**: Automatically detects low-confidence answers and explicit "speak to a human" requests
- **Brand voice**: System prompt enforces your tone and style on every response
- **Conversation memory**: Full session history passed to the LLM on every turn
- **Webhook security**: HMAC-SHA256 signature validation on all Meta webhooks
- **Async-first**: FastAPI BackgroundTasks ensure webhooks return 200 instantly; AI runs after
- **48 tests**: Unit + integration coverage across all channels and services

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              CHANNELS (Inbound)                      │
│   Facebook Messenger │ Instagram DMs │ Email         │
└──────────┬───────────┴──────┬─────────┴──────┬───────┘
           │                  │                │
           ▼                  ▼                ▼
┌──────────────────────────────────────────────────────┐
│             FASTAPI WEBHOOK SERVER                    │
│  Validate signature → 200 OK → BackgroundTask        │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              CHANNEL ADAPTER LAYER                    │
│     Normalizes all formats → unified Message         │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                AI SERVICE (Brain)                     │
│  1. Load session history  (PostgreSQL)                │
│  2. Retrieve FAQ context  (ChromaDB / RAG)            │
│  3. Generate response     (gpt-5-nano)                │
│  4. Check escalation      (keywords + confidence)     │
└──────────────────────┬───────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
   Send reply (same channel)   Escalate to human
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| AI / LLM | OpenAI gpt-5-nano |
| RAG pipeline | LangChain (LCEL) |
| Vector store | ChromaDB |
| Embeddings | text-embedding-3-small |
| Database | PostgreSQL (SQLAlchemy async) |
| HTTP client | httpx |
| Email | SendGrid Inbound Parse |
| Package manager | uv |
| Testing | pytest + pytest-asyncio |
| Deployment | Docker + docker-compose |

---

## Project Structure

```
ai-automation-agent/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # Settings from .env
│   ├── database.py              # Async SQLAlchemy engine
│   ├── channels/                # Messenger, Instagram, Email adapters
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic schemas (unified Message)
│   ├── services/
│   │   ├── ai_service.py        # LangChain RAG + LLM pipeline
│   │   ├── knowledge_service.py # ChromaDB FAQ loader/querier
│   │   ├── session_service.py   # Conversation memory
│   │   ├── escalation_service.py# Human handoff logic
│   │   └── message_processor.py # Full pipeline orchestrator
│   ├── routers/                 # Webhook endpoints (one per channel)
│   └── scripts/
│       └── load_knowledge.py    # CLI: load FAQ CSV → ChromaDB
├── data/
│   └── faq.csv                  # Your FAQ knowledge base
├── tests/
│   ├── unit/                    # Adapter, escalation, AI service tests
│   └── integration/             # Webhook endpoint tests
├── specs/main/                  # Architecture docs (spec, plan, data-model)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml               # uv-managed dependencies
└── .env.example                 # Environment variable template
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `pip install uv`
- Docker Desktop (for PostgreSQL)
- OpenAI API key
- Meta Developer account (for Messenger + Instagram)
- SendGrid account (for email)

### 1. Clone and install

```bash
git clone https://github.com/your-username/ai-automation-agent.git
cd ai-automation-agent
uv sync --group dev
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
OPENAI_API_KEY=sk-...
META_APP_SECRET=...
META_PAGE_ACCESS_TOKEN=...
META_VERIFY_TOKEN=your_random_string
SENDGRID_API_KEY=SG....
DATABASE_URL=postgresql+asyncpg://agent:agent@localhost:5432/agent_db
BRAND_VOICE_PROMPT=You are a friendly, professional customer service agent for Acme Co...
```

### 3. Start the database

```bash
docker compose up db -d
```

### 4. Load your FAQ knowledge base

Edit `data/faq.csv` with your business FAQs (columns: `category`, `question`, `answer`), then:

```bash
uv run python -m app.scripts.load_knowledge
```

### 5. Run the server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

---

## Connecting Channels

### Facebook Messenger & Instagram

1. Go to [developers.facebook.com](https://developers.facebook.com) → Your App → Webhooks
2. Use [ngrok](https://ngrok.com) to get a public HTTPS URL for local dev:
   ```bash
   ngrok http 8000
   ```
3. Register your webhook URLs:
   - Messenger: `https://your-url.ngrok.app/webhooks/messenger`
   - Instagram: `https://your-url.ngrok.app/webhooks/instagram`
4. Set `META_VERIFY_TOKEN` in `.env` to match what you enter in the Meta dashboard
5. Subscribe to `messages` events

### Email (SendGrid Inbound Parse)

1. Add a SendGrid Inbound Parse webhook pointing to:
   `https://your-domain.com/webhooks/email`
2. Configure your domain MX records as per [SendGrid's docs](https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook)

---

## Running Tests

```bash
uv run pytest                    # all 48 tests
uv run pytest tests/unit/        # unit tests only (no DB/network)
uv run pytest tests/integration/ # integration tests only
uv run pytest -v                 # verbose output
```

---

## Deployment

### Docker (local full stack)

```bash
docker compose up --build
```

### Railway / Render

1. Push to GitHub
2. Connect the repo to [Railway](https://railway.app) or [Render](https://render.com)
3. Add a PostgreSQL plugin/service
4. Set all environment variables from `.env.example`
5. Deploy — your public URL is your webhook base URL

---

## Customisation

| What to change | Where |
|---|---|
| FAQ content | `data/faq.csv` → re-run `load_knowledge` |
| Brand voice / tone | `BRAND_VOICE_PROMPT` in `.env` |
| Escalation threshold | `ESCALATION_CONFIDENCE_THRESHOLD` in `.env` (default: `0.6`) |
| Escalation keywords | `app/services/escalation_service.py` → `ESCALATION_PATTERNS` |
| LLM model | `app/services/ai_service.py` → `model=` |

---

## Architecture Decision Records

Significant design decisions are documented in `specs/main/`:

- `spec.md` — Feature requirements and acceptance criteria
- `plan.md` — Full architecture plan and project structure
- `data-model.md` — Entity relationships and data flow
- `research.md` — Technology choices and rationale
- `quickstart.md` — Local dev setup reference

---

## License

MIT

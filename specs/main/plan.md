# Implementation Plan: AI Customer Service Agent

**Branch**: `main` | **Date**: 2026-02-25 | **Spec**: `specs/main/spec.md`
**Input**: Feature specification from `specs/main/spec.md`

---

## Summary

Build an intelligent customer service agent that receives inbound messages from Facebook Messenger, Instagram DMs, and Email; uses a RAG pipeline over a FAQ knowledge base to generate accurate, brand-voiced responses; detects escalation conditions; and routes replies back through the originating channel. The backend is a FastAPI service backed by PostgreSQL for sessions and ChromaDB for the knowledge base.

---

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, LangChain, OpenAI (gpt-5-nano + text-embedding-3-small), ChromaDB, SQLAlchemy (async), asyncpg, httpx, SendGrid
**Storage**: PostgreSQL (sessions, events) + ChromaDB (vector/FAQ)
**Testing**: pytest + pytest-asyncio + httpx AsyncClient
**Target Platform**: Linux server (Docker container on Railway/Render)
**Project Type**: Web application (API-only backend)
**Performance Goals**: p95 response < 3s (Messenger/Instagram), < 60s (email)
**Constraints**: Meta webhook must receive 200 OK within 5s; no PII stored beyond session continuity; webhook signatures validated on every request
**Scale/Scope**: v1 target — 50 concurrent users, single-server deployment

---

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. API-First, Channel-Agnostic | PASS | All channels normalize to unified Message schema |
| II. RAG Over Fine-Tuning | PASS | ChromaDB + LangChain retrieval chain |
| III. Test-First | PASS | pytest suite required before implementation |
| IV. Human-in-the-Loop | PASS | Escalation logic in spec FR-007 |
| V. Secrets Never in Code | PASS | All keys in .env |
| VI. Observability | PASS | Correlation IDs + structured logging planned |
| VII. Simplicity | PASS | Single FastAPI app, no microservices for v1 |

---

## Project Structure

### Documentation

```text
specs/main/
├── spec.md           Done
├── plan.md           This file
├── research.md       Done
├── data-model.md     Done
├── contracts/        Phase 1 output
│   ├── webhook.openapi.yaml
│   └── channel-adapter.md
├── quickstart.md     Phase 1 output
└── tasks.md          /sp.tasks output
```

### Source Code Structure

```text
ai-automation-agent/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # Settings via pydantic-settings + .env
│   ├── database.py              # SQLAlchemy async engine + session
│   │
│   ├── channels/                # Channel adapters (inbound normalizers + outbound senders)
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract ChannelAdapter
│   │   ├── messenger.py         # Facebook Messenger webhook + sender
│   │   ├── instagram.py         # Instagram webhook + sender
│   │   └── email.py             # SendGrid inbound + outbound
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── session.py           # Session model
│   │   ├── escalation.py        # EscalationEvent model
│   │   └── response.py          # ChannelResponse model
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── message.py           # Unified Message schema
│   │   └── webhook.py           # Raw webhook payload schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py        # LangChain RAG pipeline + gpt-5-nano
│   │   ├── knowledge_service.py # ChromaDB load, query, manage
│   │   ├── session_service.py   # Session CRUD + history management
│   │   └── escalation_service.py# Escalation detection + event creation
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── messenger.py         # POST /webhooks/messenger
│   │   ├── instagram.py         # POST /webhooks/instagram
│   │   ├── email.py             # POST /webhooks/email
│   │   └── health.py            # GET /health
│   │
│   └── scripts/
│       └── load_knowledge.py    # CLI: load FAQ CSV into ChromaDB
│
├── data/
│   └── faq.csv                  # FAQ knowledge base (category,question,answer)
│
├── tests/
│   ├── conftest.py              # Test DB, mock clients, fixtures
│   ├── unit/
│   │   ├── test_ai_service.py
│   │   ├── test_escalation_service.py
│   │   └── test_channel_adapters.py
│   └── integration/
│       ├── test_messenger_webhook.py
│       ├── test_instagram_webhook.py
│       └── test_email_webhook.py
│
├── .env                         # Secrets (never committed)
├── .env.example                 # Template for secrets (committed)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml           # Local dev: app + postgres
└── README.md
```

**Structure Decision**: Web application (Option 2 variant) — API-only backend, no frontend. All channel interfaces are webhook receivers.

---

## Architecture: Message Processing Flow

```
1. INBOUND WEBHOOK
   Validate signature (HMAC-SHA256 for Meta, API key for SendGrid)
   Return 200 OK immediately
   Dispatch to BackgroundTask

2. NORMALIZE (Channel Adapter)
   Raw payload → unified Message schema

3. SESSION MANAGEMENT
   Look up existing session by (channel, sender_id)
   Create new session if first contact

4. RAG PIPELINE (AI Service)
   Embed user message (text-embedding-3-small)
   Query ChromaDB for top-3 relevant FAQ entries
   Build prompt: system_prompt + brand_voice + faq_context + conversation_history + user_message
   Call gpt-5-nano → get response text + confidence metadata

5. ESCALATION CHECK (Escalation Service)
   Check for explicit escalation keywords
   Check AI confidence score < 0.6 threshold
   If escalation: create EscalationEvent, update session status, notify human

6. OUTBOUND RESPONSE (Channel Adapter)
   Send response via originating channel API
   Log ChannelResponse

7. SESSION UPDATE
   Append message + response to session.message_history
```

---

## Phase 0: Research — Complete
See `research.md` — all technology decisions resolved.

## Phase 1: Design & Contracts — Complete

### Deliverables
- [x] `data-model.md` — entities and relationships
- [ ] `contracts/webhook.openapi.yaml` — OpenAPI spec for all webhook endpoints
- [ ] `contracts/channel-adapter.md` — channel adapter interface contract
- [ ] `quickstart.md` — local dev setup guide

### API Contracts Summary

**POST /webhooks/messenger**
- Input: Meta webhook payload (JSON) + X-Hub-Signature-256 header
- Output: {"status": "ok"} (200) or {"error": "invalid signature"} (401)
- Processing: async background

**POST /webhooks/instagram**
- Same as Messenger (same Meta format)

**POST /webhooks/email**
- Input: SendGrid Inbound Parse multipart form
- Output: {"status": "ok"} (200)
- Processing: async background

**GET /webhooks/messenger** (Meta verification challenge)
- Input: ?hub.mode=subscribe&hub.verify_token=X&hub.challenge=Y
- Output: hub.challenge value as plain text (200)

**GET /health**
- Output: {"status": "healthy", "version": "1.0.0"}

---

## Risk Analysis

| Risk | Blast Radius | Mitigation |
|---|---|---|
| Meta webhook 5s timeout | All real-time channels | BackgroundTasks pattern; acknowledge immediately |
| OpenAI API rate limits | All AI responses | Exponential backoff with tenacity; queue depth monitoring |
| Wrong FAQ answers | Customer trust | Confidence scoring; low-confidence triggers escalation |
| API key exposure | Full account compromise | .env only, .gitignore enforced, rotate keys periodically |

# Phase 0 Research: AI Customer Service Agent

**Date**: 2026-02-25
**Status**: Complete

---

## 1. LLM Provider Choice

**Decision**: OpenAI gpt-5-nano via the `openai` Python SDK
**Rationale**: gpt-5-nano has the best balance of speed, cost, and instruction-following for customer service. It supports function calling (needed for escalation detection) and has a large context window (handles long conversation history). The project already has an OpenAI API key.
**Alternatives Considered**:
- Anthropic Claude API — excellent reasoning but slightly slower for real-time chat; can be added as a fallback
- Local models (Llama 3, Mistral) — no API cost but require GPU hardware and add deployment complexity; ruled out for v1
- Google Gemini — viable but less mature Python tooling

---

## 2. AI Framework: LangChain vs Direct SDK

**Decision**: LangChain (`langchain`, `langchain-openai`, `langchain-community`)
**Rationale**: LangChain provides ready-made abstractions for RAG pipelines (retrieval chains), conversation memory, and agent tools. Using it directly would require reimplementing these patterns. The overhead is justified.
**Alternatives Considered**:
- Raw OpenAI SDK only — more control, less boilerplate, but we'd have to build RAG and memory from scratch
- LlamaIndex — better for pure document indexing but weaker for multi-turn conversation management
- Haystack — mature but heavier and less Python-idiomatic

---

## 3. Vector Store for RAG

**Decision**: ChromaDB (local, embedded mode for dev; persistent mode for prod)
**Rationale**: ChromaDB is zero-configuration, runs in-process, and has first-class LangChain integration. For v1 with a small FAQ (< 10k entries), there is no need for a hosted vector DB.
**Alternatives Considered**:
- Pinecone — fully managed, great at scale, but adds cost and network latency for a small FAQ
- pgvector (PostgreSQL extension) — good if we want one DB, but adds Postgres dependency complexity for v1
- Weaviate — powerful but heavyweight for a small knowledge base
- FAISS — fast but not persistent without custom code; ChromaDB wraps FAISS

---

## 4. Web Framework (Webhook Receiver)

**Decision**: FastAPI with Uvicorn
**Rationale**: FastAPI is async-native (critical for handling concurrent webhooks without blocking), has automatic OpenAPI docs, request validation via Pydantic, and is the de-facto standard for Python AI service backends.
**Alternatives Considered**:
- Flask — simpler but synchronous by default; would need `gevent` for concurrency
- Django — too heavy for a webhook service
- n8n/Make — no-code but lacks the customisation needed for signature validation, custom RAG, and session management

---

## 5. Facebook Messenger + Instagram Integration

**Decision**: Meta Graph API v21.0 via direct `httpx` async HTTP calls
**Rationale**: Meta has no official Python SDK. The Graph API is straightforward REST — we call `POST /{phone_number_id}/messages` for Messenger and `POST /me/messages` for Instagram. Webhook verification uses `X-Hub-Signature-256` (HMAC-SHA256).
**Key Facts**:
- Both Messenger and Instagram use the same Meta Graph API and webhook format
- Webhooks must respond with `200 OK` within **5 seconds** or Meta will retry (up to 3 times)
- This means AI processing must be async — receive webhook → acknowledge → process in background → send reply
- Meta requires a webhook verification challenge (`hub.verify_token`) during setup

---

## 6. Email Integration

**Decision**: SendGrid Inbound Email Parse webhook
**Rationale**: SendGrid's Inbound Parse forwards incoming emails as HTTP POST to our webhook endpoint. It handles the MX record, SMTP reception, and multipart parsing — we just receive a clean JSON/form payload. Sending replies uses the SendGrid Send API.
**Alternatives Considered**:
- Mailgun Inbound Routes — equally good, slightly more complex setup
- IMAP polling — polling introduces latency and requires managing IMAP state; webhook is far better
- AWS SES + Lambda — more powerful but much more infrastructure

---

## 7. Session / Conversation Memory

**Decision**: PostgreSQL (via SQLAlchemy async + asyncpg) for persistent sessions; in-process dict for dev
**Rationale**: Conversation history must survive server restarts. Each session stores message history as JSONB. PostgreSQL is the most battle-tested option and we will likely need it for other data anyway.
**Alternatives Considered**:
- Redis — fast but requires explicit serialization; better used for caching/rate limiting
- SQLite — fine for dev/single-server but can't scale horizontally
- MongoDB — flexible schema but PostgreSQL JSONB is equally flexible without adding a second DB paradigm

---

## 8. Asynchronous Task Handling (Webhook Response Time)

**Decision**: Python `asyncio` background tasks via FastAPI `BackgroundTasks`
**Rationale**: Meta webhooks require a `200 OK` within 5 seconds. AI + DB calls can take 2-8 seconds. Solution: acknowledge the webhook immediately, then process in a background task. FastAPI's built-in `BackgroundTasks` is sufficient for v1. No external queue needed.
**Alternatives Considered**:
- Celery + Redis — robust but adds operational complexity; overkill for v1
- RQ (Redis Queue) — lighter than Celery but still requires Redis as a broker
- FastAPI `BackgroundTasks` — simple, in-process, zero configuration; chosen for v1

---

## 9. Deployment

**Decision**: Docker + Railway (or Render)
**Rationale**: Single `Dockerfile` packages the app. Railway and Render both support one-command deploys from GitHub, auto-HTTPS (needed for Meta webhooks), and environment variable management. No infrastructure expertise required.
**Alternatives Considered**:
- AWS ECS/EC2 — production-grade but requires VPC, IAM, and significant DevOps setup
- Heroku — familiar but expensive and being phased out
- Fly.io — excellent but slightly more complex CLI

---

## 10. Embeddings Model

**Decision**: `text-embedding-3-small` (OpenAI)
**Rationale**: 1536-dimension embeddings, low cost ($0.02/1M tokens), excellent for semantic similarity on short FAQ texts. Same API key as gpt-5-nano.
**Alternatives Considered**:
- `text-embedding-3-large` — higher quality but 3072 dimensions and 5x cost; unnecessary for FAQ-scale
- `sentence-transformers` (local) — free but requires local compute and adds model management

---

## Technology Stack Summary

| Layer | Technology |
|---|---|
| AI Core | OpenAI gpt-5-nano + `text-embedding-3-small` |
| AI Framework | LangChain (chains, memory, retrieval) |
| Vector Store | ChromaDB |
| Web Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy async |
| Channel: Messenger | Meta Graph API v21.0 (httpx) |
| Channel: Instagram | Meta Graph API v21.0 (httpx) |
| Channel: Email | SendGrid Inbound Parse + Send API |
| Async Tasks | FastAPI BackgroundTasks |
| Deployment | Docker + Railway/Render |
| Testing | pytest + httpx (async test client) |
| Python Version | 3.11 |

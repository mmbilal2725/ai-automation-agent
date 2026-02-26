# How to Build an AI Automation Agent
## A Step-by-Step Teaching Guide

**Project**: AI Customer Service Agent (Messenger + Instagram + Email)
**Updated**: 2026-02-25

---

## Table of Contents

1. [What Is an AI Automation Agent?](#1-what-is-an-ai-automation-agent)
2. [The Architecture at a Glance](#2-the-architecture-at-a-glance)
3. [Key Concepts You Must Understand](#3-key-concepts-you-must-understand)
4. [The Technology Stack — and Why](#4-the-technology-stack--and-why)
5. [Step 1: Project Setup](#5-step-1-project-setup)
6. [Step 2: The AI Core (LLM + RAG)](#6-step-2-the-ai-core-llm--rag)
7. [Step 3: The Webhook Server (FastAPI)](#7-step-3-the-webhook-server-fastapi)
8. [Step 4: Channel Integrations](#8-step-4-channel-integrations)
9. [Step 5: Session Memory](#9-step-5-session-memory)
10. [Step 6: Human Escalation Logic](#10-step-6-human-escalation-logic)
11. [Step 7: Email Integration](#11-step-7-email-integration)
12. [Step 8: Testing Strategy](#12-step-8-testing-strategy)
13. [Step 9: Deployment](#13-step-9-deployment)
14. [Key Patterns Reference](#14-key-patterns-reference)
15. [Common Mistakes to Avoid](#15-common-mistakes-to-avoid)
16. [Running the Project — Step-by-Step](#16-running-the-project--step-by-step)

---

## 1. What Is an AI Automation Agent?

An AI automation agent is a program that:
1. **Receives** input from a user (via chat, email, API, etc.)
2. **Thinks** — uses an LLM (Large Language Model) to understand intent and generate a response
3. **Acts** — sends a reply, calls a tool, escalates to a human, or triggers another workflow

The difference from a simple chatbot is **intelligence** — it doesn't use pre-scripted decision trees. It understands natural language, retrieves relevant context, and generates fluent, contextual responses.

### The three parts of every AI agent:

```
[Input Channel] → [AI Brain] → [Output Action]

- Input:  Webhook, API call, scheduled trigger
- Brain:  LLM + context (RAG, memory, tools)
- Output: Reply message, DB write, API call, human handoff
```

---

## 2. The Architecture at a Glance

```
┌─────────────────────────────────────────────────────┐
│                  CHANNELS (Input)                    │
│  Facebook Messenger │ Instagram DMs │ Email          │
└──────────┬──────────┴──────┬────────┴──────┬─────────┘
           │                 │               │
           ▼                 ▼               ▼
┌──────────────────────────────────────────────────────┐
│              FASTAPI WEBHOOK SERVER                   │
│  • Validates webhook signatures                       │
│  • Returns 200 OK immediately (< 1ms)                 │
│  • Hands off to background processing                 │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              CHANNEL ADAPTER LAYER                    │
│  Normalizes all channel formats → unified Message     │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                 AI SERVICE (Brain)                    │
│                                                       │
│  1. Load conversation history (PostgreSQL)            │
│  2. Search FAQ knowledge base (ChromaDB / RAG)        │
│  3. Build prompt with context                         │
│  4. Call gpt-5-nano → get response                        │
│  5. Check escalation conditions                       │
└──────────────────────┬───────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
  ┌─────────────────┐    ┌──────────────────┐
  │  SEND RESPONSE  │    │  ESCALATE        │
  │  (same channel) │    │  (notify human)  │
  └─────────────────┘    └──────────────────┘
```

---

## 3. Key Concepts You Must Understand

### 3.1 RAG — Retrieval-Augmented Generation

**The problem**: LLMs don't know your business's specific FAQs, policies, or products.

**The solution**: Before asking the LLM, search a database of your FAQ content for relevant entries, then inject them into the prompt.

```
User asks: "What are your return policies?"
                    │
                    ▼
[Search vector DB] → finds: "Returns accepted within 30 days with receipt"
                    │
                    ▼
[Prompt to LLM]: "Using this context: [Returns accepted within 30 days...]
                  Answer the customer's question: What are your return policies?"
                    │
                    ▼
[LLM response]: "You can return items within 30 days as long as you have your receipt."
```

**Why "vector" database?** Text is converted into a list of numbers (embedding) that represents its meaning. Semantically similar texts have numerically similar embeddings. This lets you find "return policy" even if the user asked "can I get my money back?"

### 3.2 Webhooks

Instead of your server polling "did any messages arrive?", **channels push messages to you** via webhooks — an HTTP POST to a URL you provide.

```
Meta sends:  POST https://yourapp.com/webhooks/messenger
             Body: { "sender": "...", "message": "Hello" }

You must:    1. Respond 200 OK within 5 seconds
             2. Then do your AI processing
```

**Critical**: Never do slow work (AI calls, DB queries) before returning the 200. Use async background tasks.

### 3.3 Conversation Memory

LLMs are stateless — they don't remember previous messages. You must manually:
1. Store every message in a database
2. Load previous messages before each new LLM call
3. Pass them as the conversation history in the prompt

```python
# Each LLM call includes history:
messages = [
    {"role": "system", "content": "You are a helpful customer service agent..."},
    {"role": "user", "content": "What are your hours?"},           # previous turn
    {"role": "assistant", "content": "We're open 9am-5pm EST."},   # previous reply
    {"role": "user", "content": "What about weekends?"},           # current message
]
```

### 3.4 Embeddings

An embedding is a numerical representation of text (a vector of floats).

```python
# "I want to return my order" → [0.023, -0.456, 0.891, ...]  (1536 numbers)
# "What is the refund policy?"  → [0.019, -0.441, 0.876, ...]  (similar numbers!)

# Cosine similarity between these two vectors ≈ 0.94 (very similar)
# → RAG correctly links both questions to the same FAQ answer
```

### 3.5 Escalation Detection

Two triggers for handing off to a human:
1. **Explicit**: User says "speak to a human", "real agent", "manager", etc.
2. **Implicit**: AI's confidence score is below a threshold (0.6)

Confidence is estimated by asking the LLM to rate its own certainty, or by measuring the similarity score of the best RAG match.

---

## 4. The Technology Stack — and Why

| What | Tool | Why |
|---|---|---|
| Python version | 3.11 | Best async support, LangChain requires 3.9+ |
| Web framework | FastAPI | Async-native, auto docs, Pydantic validation |
| AI framework | LangChain | RAG chains, memory, tool use — don't reinvent |
| LLM | OpenAI gpt-5-nano | Best speed/quality, you already have the key |
| Embeddings | text-embedding-3-small | Cheap, fast, great quality for FAQ-scale |
| Vector DB | ChromaDB | Zero-config, runs local, great LangChain support |
| SQL Database | PostgreSQL | Session history, audit logs, proven reliability |
| ORM | SQLAlchemy (async) | Type-safe, async, industry standard |
| HTTP client | httpx | Async HTTP, needed to call Meta Graph API |
| Channel SDK | Meta Graph API (REST) | No official Python SDK; just REST calls |
| Email | SendGrid Inbound Parse | Handles MX + SMTP, sends you a clean webhook |
| Deployment | Docker + Railway | One `Dockerfile`, auto-HTTPS, simple deploys |
| Testing | pytest + pytest-asyncio | Async test support, fixtures |

---

## 5. Step 1: Project Setup

### 5.1 Create the directory structure

```bash
mkdir -p app/{channels,models,schemas,services,routers,scripts}
mkdir -p tests/{unit,integration}
mkdir -p data
touch app/__init__.py
touch app/channels/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/routers/__init__.py
```

### 5.2 Install dependencies

```bash
pip install fastapi uvicorn[standard] langchain langchain-openai langchain-community \
    chromadb openai sqlalchemy[asyncio] asyncpg alembic httpx sendgrid \
    python-dotenv pydantic-settings tenacity pytest pytest-asyncio
```

### 5.3 Create requirements.txt

```text
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
chromadb>=0.5.0
openai>=1.50.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
httpx>=0.27.0
sendgrid>=6.11.0
python-dotenv>=1.0.0
pydantic-settings>=2.5.0
tenacity>=9.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

### 5.4 .env file structure

```bash
# AI
OPENAI_API_KEY=sk-...

# Meta (Facebook + Instagram)
META_APP_SECRET=...           # Used to verify webhook signatures
META_PAGE_ACCESS_TOKEN=...    # Used to send messages
META_VERIFY_TOKEN=...         # A random string you choose during webhook setup

# SendGrid (Email)
SENDGRID_API_KEY=...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agent_db

# App
APP_ENV=development
ESCALATION_CONFIDENCE_THRESHOLD=0.6
BRAND_VOICE_PROMPT="You are a friendly, professional customer service agent for [Company]. Always be concise, helpful, and warm."
```

### 5.5 Config (pydantic-settings)

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    meta_app_secret: str
    meta_page_access_token: str
    meta_verify_token: str
    sendgrid_api_key: str
    database_url: str
    escalation_confidence_threshold: float = 0.6
    brand_voice_prompt: str = "You are a helpful customer service agent."

    class Config:
        env_file = ".env"

settings = Settings()
```

**Teaching point**: `pydantic-settings` reads from `.env` automatically and validates types. If `OPENAI_API_KEY` is missing, the app won't start — fail fast, fail clearly.

---

## 6. Step 2: The AI Core (LLM + RAG)

This is the most important part. Everything else is plumbing.

### 6.1 Load your FAQ knowledge base into ChromaDB

```python
# app/scripts/load_knowledge.py
import csv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from app.config import settings

def load_faq(csv_path: str = "data/faq.csv"):
    """Load FAQ CSV into ChromaDB vector store."""

    # Read CSV
    documents = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)  # columns: category, question, answer
        for row in reader:
            # Combine Q+A so the embedding captures both
            content = f"Q: {row['question']}\nA: {row['answer']}"
            documents.append(Document(
                page_content=content,
                metadata={"category": row["category"], "question": row["question"]}
            ))

    # Create embeddings + store in ChromaDB
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key
    )
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    vectorstore.persist()
    print(f"Loaded {len(documents)} FAQ entries into ChromaDB")

if __name__ == "__main__":
    load_faq()
```

**Run with**: `python -m app.scripts.load_knowledge`

### 6.2 The RAG + LLM pipeline

```python
# app/services/ai_service.py
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from app.config import settings

class AIService:
    def __init__(self):
        # LLM
        self.llm = ChatOpenAI(
            model="gpt-5-nano",
            temperature=0.3,          # Lower = more consistent, less creative
            openai_api_key=settings.openai_api_key
        )

        # Embeddings + vector store
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 3}    # Return top 3 relevant FAQ entries
        )

    async def get_response(
        self,
        user_message: str,
        conversation_history: list[dict],
        session_id: str
    ) -> tuple[str, float]:
        """
        Returns (response_text, confidence_score).
        confidence_score is 0.0 to 1.0.
        """

        # Build LangChain memory from our stored history
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        for msg in conversation_history:
            if msg["role"] == "user":
                memory.chat_memory.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                memory.chat_memory.add_ai_message(msg["content"])

        # Build the RAG chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=memory,
            return_source_documents=True,
            verbose=False
        )

        # Run it
        result = await chain.ainvoke({
            "question": user_message,
            "chat_history": memory.chat_memory.messages
        })

        response = result["answer"]

        # Estimate confidence from retrieval scores
        source_docs = result.get("source_documents", [])
        confidence = self._estimate_confidence(source_docs, response)

        return response, confidence

    def _estimate_confidence(self, source_docs: list, response: str) -> float:
        """
        Simple heuristic: if we found relevant FAQ docs, confidence is higher.
        In production, you could ask the LLM to rate its own confidence.
        """
        if not source_docs:
            return 0.3  # No FAQ match → low confidence

        # Check if response contains hedging language
        hedging_phrases = ["i'm not sure", "i don't know", "cannot find", "unable to"]
        if any(phrase in response.lower() for phrase in hedging_phrases):
            return 0.4

        return 0.85  # Found FAQ context + no hedging → high confidence
```

**Teaching points**:
- `temperature=0.3` — lower temperature makes responses more consistent and less "creative". For customer service, you want reliable, not poetic.
- `k=3` — retrieve 3 FAQ entries. Too few misses context; too many fills the prompt with noise.
- `ConversationalRetrievalChain` — LangChain's built-in chain that combines retrieval + conversation history. Saves you writing ~100 lines of plumbing.

---

## 7. Step 3: The Webhook Server (FastAPI)

### 7.1 The critical pattern: acknowledge first, process second

```python
# app/routers/messenger.py
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.services.message_processor import process_message
from app.channels.messenger import MessengerAdapter

router = APIRouter()
adapter = MessengerAdapter()

@router.post("/webhooks/messenger")
async def messenger_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    # STEP 1: Validate signature BEFORE anything else
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not adapter.validate_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # STEP 2: Return 200 IMMEDIATELY — Meta requires this within 5 seconds
    payload = await request.json()
    background_tasks.add_task(process_message, payload, "messenger")
    return {"status": "ok"}   # ← This returns instantly

@router.get("/webhooks/messenger")
async def messenger_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """Meta calls this once during webhook setup to verify ownership."""
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")
```

**Teaching point**: `BackgroundTasks.add_task()` schedules work to run after the response is sent. The AI processing happens async, in the background. The user's channel sees a response in < 100ms. Your AI takes 2-8 seconds — that's fine, it runs after.

### 7.2 Webhook signature validation

```python
# app/channels/messenger.py
import hmac
import hashlib
from app.config import settings

def validate_signature(body: bytes, signature_header: str) -> bool:
    """
    Meta sends: X-Hub-Signature-256: sha256=<HMAC>
    We recompute the HMAC and compare. If they don't match → reject the request.
    This prevents anyone from sending fake webhooks to your endpoint.
    """
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header[7:]  # Remove "sha256=" prefix

    computed = hmac.new(
        settings.meta_app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    # Use hmac.compare_digest to prevent timing attacks
    return hmac.compare_digest(computed, expected_signature)
```

**Teaching point**: Always use `hmac.compare_digest()` not `==` for comparing secrets. Regular `==` can be vulnerable to timing attacks where an attacker measures response time to guess characters.

---

## 8. Step 4: Channel Integrations

### 8.1 The Adapter Pattern

Every channel has different payload formats, but your AI core should only ever see one format. The adapter pattern handles this:

```python
# app/channels/base.py
from abc import ABC, abstractmethod
from app.schemas.message import Message

class ChannelAdapter(ABC):
    @abstractmethod
    def normalize(self, raw_payload: dict) -> list[Message]:
        """Convert raw webhook payload to unified Message objects."""
        pass

    @abstractmethod
    async def send(self, recipient_id: str, text: str) -> bool:
        """Send a reply back through this channel."""
        pass

    @abstractmethod
    def validate_signature(self, body: bytes, signature: str) -> bool:
        """Verify the webhook came from the legitimate source."""
        pass
```

### 8.2 Messenger adapter

```python
# app/channels/messenger.py
import httpx
from app.channels.base import ChannelAdapter
from app.schemas.message import Message
from app.config import settings

class MessengerAdapter(ChannelAdapter):
    GRAPH_API_URL = "https://graph.facebook.com/v21.0/me/messages"

    def normalize(self, raw_payload: dict) -> list[Message]:
        """Extract messages from Meta's nested webhook format."""
        messages = []
        for entry in raw_payload.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" not in event:
                    continue  # Skip delivery receipts, read receipts, etc.
                messages.append(Message(
                    channel="messenger",
                    sender_id=event["sender"]["id"],
                    content=event["message"].get("text", ""),
                    raw_payload=event
                ))
        return messages

    async def send(self, recipient_id: str, text: str) -> bool:
        """Send a message back via Messenger Graph API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GRAPH_API_URL,
                params={"access_token": settings.meta_page_access_token},
                json={
                    "recipient": {"id": recipient_id},
                    "message": {"text": text}
                }
            )
            return response.status_code == 200
```

**Teaching point**: Meta's webhook format is deeply nested: `entry[].messaging[].message`. Always iterate carefully and skip non-message events (delivery receipts, etc.).

---

## 9. Step 5: Session Memory

### 9.1 Why you need it

LLMs have no memory between calls. If a customer says "I want to return my blue jacket" and then asks "how long will it take?" — the second question only makes sense with the first. You need to store and replay the conversation.

### 9.2 Session model (PostgreSQL)

```python
# app/models/session.py
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel = Column(String, nullable=False)       # "messenger" | "instagram" | "email"
    sender_id = Column(String, nullable=False)     # Platform-specific user ID
    status = Column(String, default="active")      # "active" | "escalated" | "closed"
    message_history = Column(JSON, default=list)   # [{"role": "user", "content": "..."}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 9.3 Session service

```python
# app/services/session_service.py
from sqlalchemy import select
from app.models.session import Session
from app.database import AsyncSessionLocal

async def get_or_create_session(channel: str, sender_id: str) -> Session:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.channel == channel,
                Session.sender_id == sender_id,
                Session.status == "active"
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            session = Session(channel=channel, sender_id=sender_id)
            db.add(session)
            await db.commit()
            await db.refresh(session)

        return session

async def append_to_history(session_id, role: str, content: str):
    async with AsyncSessionLocal() as db:
        session = await db.get(Session, session_id)
        history = session.message_history or []
        history.append({"role": role, "content": content})
        session.message_history = history
        await db.commit()
```

---

## 10. Step 6: Human Escalation Logic

```python
# app/services/escalation_service.py
import re
from app.config import settings

ESCALATION_KEYWORDS = [
    r"\bhuman\b", r"\breal person\b", r"\bagent\b", r"\bmanager\b",
    r"\bspeak to someone\b", r"\btalk to someone\b", r"\bsupport team\b"
]

def should_escalate(user_message: str, confidence: float) -> tuple[bool, str]:
    """
    Returns (should_escalate: bool, trigger: str).
    trigger is "explicit_request" or "low_confidence".
    """
    # Check for explicit escalation request
    for pattern in ESCALATION_KEYWORDS:
        if re.search(pattern, user_message.lower()):
            return True, "explicit_request"

    # Check confidence threshold
    if confidence < settings.escalation_confidence_threshold:
        return True, "low_confidence"

    return False, ""

async def handle_escalation(session, trigger: str, confidence: float):
    """Log escalation event and notify human team."""
    # 1. Update session status
    session.status = "escalated"

    # 2. Log the event (see EscalationEvent model)
    # 3. Notify human (email, Slack, ticketing system - depends on your setup)
    # For now: just log it
    print(f"[ESCALATION] Session {session.id} | Trigger: {trigger} | Confidence: {confidence}")

    return "I'm connecting you with a member of our team right now. They'll be with you shortly."
```

**Teaching point**: Escalation logic is intentionally kept as configuration, not complex code. The keyword list and confidence threshold live in `.env` — you can tune them without deploying new code.

---

## 11. Step 7: Email Integration

### 11.1 SendGrid Inbound Parse setup

1. Add a domain MX record pointing to SendGrid
2. In SendGrid dashboard → Settings → Inbound Parse → add your webhook URL
3. SendGrid POSTs to your endpoint with email data as multipart form

```python
# app/routers/email.py
from fastapi import APIRouter, Form, BackgroundTasks

router = APIRouter()

@router.post("/webhooks/email")
async def email_webhook(
    background_tasks: BackgroundTasks,
    from_email: str = Form(alias="from"),
    subject: str = Form(default=""),
    text: str = Form(default=""),          # Plain text body
    html: str = Form(default=""),          # HTML body (use text instead)
    headers: str = Form(default=""),       # Raw email headers (for threading)
):
    payload = {
        "from": from_email,
        "subject": subject,
        "body": text or html,
        "headers": headers
    }
    background_tasks.add_task(process_message, payload, "email")
    return {"status": "ok"}
```

### 11.2 Sending email replies (SendGrid)

```python
import sendgrid
from sendgrid.helpers.mail import Mail
from app.config import settings

async def send_email_reply(to_email: str, subject: str, body: str):
    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    message = Mail(
        from_email="support@yourcompany.com",
        to_emails=to_email,
        subject=f"Re: {subject}",
        plain_text_content=body
    )
    sg.send(message)
```

---

## 12. Step 8: Testing Strategy

### 12.1 Test philosophy

- **Unit tests**: Test each service in isolation with mocked dependencies
- **Integration tests**: Send real HTTP requests to the running app with a test database

### 12.2 Example: Test the webhook endpoint

```python
# tests/integration/test_messenger_webhook.py
import pytest
import hmac, hashlib, json
from httpx import AsyncClient
from app.main import app

def make_signature(body: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"

@pytest.mark.asyncio
async def test_messenger_webhook_valid():
    payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": "user123"},
                "recipient": {"id": "page123"},
                "message": {"text": "What are your hours?"}
            }]
        }]
    }
    body = json.dumps(payload).encode()
    sig = make_signature(body, "test_secret")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhooks/messenger",
            content=body,
            headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"}
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_messenger_webhook_invalid_signature():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhooks/messenger",
            content=b'{"test": "data"}',
            headers={"X-Hub-Signature-256": "sha256=invalidsig"}
        )
    assert response.status_code == 401
```

### 12.3 Example: Test the AI service

```python
# tests/unit/test_ai_service.py
from unittest.mock import AsyncMock, patch
from app.services.ai_service import AIService

@pytest.mark.asyncio
async def test_get_response_returns_text_and_confidence():
    service = AIService()

    with patch.object(service, '_run_chain', new_callable=AsyncMock) as mock_chain:
        mock_chain.return_value = ("Your hours are 9am-5pm.", [])

        response, confidence = await service.get_response(
            user_message="What are your hours?",
            conversation_history=[],
            session_id="test-session"
        )

    assert isinstance(response, str)
    assert len(response) > 0
    assert 0.0 <= confidence <= 1.0
```

---

## 13. Step 9: Deployment

### 13.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Load FAQ into ChromaDB at build time (or use a startup script)
RUN python -m app.scripts.load_knowledge

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 13.2 Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=sk-...
railway variables set META_APP_SECRET=...
# etc.
```

Railway auto-generates a public HTTPS URL like `https://yourapp.up.railway.app`. Use this as your Meta webhook URL.

### 13.3 Register your webhook with Meta

1. Go to developers.facebook.com → Your App → Webhooks
2. Subscribe to `messages` events
3. Enter your webhook URL: `https://yourapp.up.railway.app/webhooks/messenger`
4. Enter your `META_VERIFY_TOKEN` value
5. Meta will call `GET /webhooks/messenger?hub.mode=subscribe&hub.challenge=...` — your app must echo back the challenge

---

## 14. Key Patterns Reference

| Pattern | What It Solves | Where Used |
|---|---|---|
| **Adapter Pattern** | Different channel formats → unified schema | `channels/` |
| **BackgroundTasks** | Return webhook 200 before processing | All webhook routers |
| **RAG** | Ground LLM in your FAQ knowledge | `ai_service.py` |
| **HMAC Verification** | Reject fake webhook requests | All channel adapters |
| **Conversation Memory** | LLM has no memory — you must provide it | `session_service.py` |
| **Confidence Scoring** | Know when to escalate vs respond | `escalation_service.py` |
| **pydantic-settings** | Type-safe config from .env | `config.py` |

---

## 15. Common Mistakes to Avoid

1. **Doing AI work before returning 200** — Meta will retry and you'll get duplicate messages
2. **Not validating webhook signatures** — anyone can send fake messages to your endpoint
3. **Storing secrets in code or git** — use `.env` only, add to `.gitignore`
4. **Fine-tuning instead of RAG** — updating a fine-tuned model takes hours and costs money; updating ChromaDB takes seconds
5. **Forgetting conversation history** — the LLM will give context-blind responses if you don't pass prior messages
6. **Not testing escalation** — always write tests for the escalation path; it's a safety feature
7. **Using `==` to compare HMAC hashes** — use `hmac.compare_digest()` to prevent timing attacks
8. **Hardcoding the confidence threshold** — put it in `.env` so you can tune it without redeploying
9. **Responding with "I don't know" and stopping** — always offer an escalation path when the agent can't help
10. **Single-channel testing** — test all three channels independently; they have subtle format differences

---

---

## 16. Running the Project — Step-by-Step

This section tells you exactly what you can run right now vs. what needs external setup first.

### What's ready immediately (no accounts needed)

```bash
# Run the full test suite — works with no external services
uv run pytest -v
```

All 48 tests pass instantly. This confirms your code and dependencies are correctly installed.

---

### Step 1 — Fill in your `.env` file

Your `.env` currently only has `OPENAI_API_KEY` set. Open it and add the remaining values:

```env
# Already set
OPENAI_API_KEY=sk-...

# Choose any random string — you will paste this into the Meta dashboard
META_VERIFY_TOKEN=my_secret_token_123

# From: developers.facebook.com → Your App → Settings → Basic
META_APP_SECRET=xxxxxxxxxxxxxxxx

# From: developers.facebook.com → Your App → Messenger → Page Access Tokens
META_PAGE_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxx

# From: sendgrid.com → Settings → API Keys
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=support@yourdomain.com

# Leave exactly as shown for local Docker setup
DATABASE_URL=postgresql+asyncpg://agent:agent@localhost:5432/agent_db

# Write your business name and tone here
BRAND_VOICE_PROMPT=You are a friendly customer service agent for [Your Business Name]. Be concise, helpful, and warm.
```

---

### Step 2 — Start PostgreSQL (Docker)

```bash
docker compose up db -d
```

This starts a PostgreSQL container. The app will create its tables automatically on first run.

---

### Step 3 — Load your FAQ knowledge base

Edit `data/faq.csv` with your own questions and answers (the file has 20 sample entries to get you started), then run:

```bash
uv run python -m app.scripts.load_knowledge
```

This reads the CSV, generates embeddings via OpenAI, and stores them in ChromaDB at `./chroma_db/`. **You only need to re-run this when your FAQs change.**

---

### Step 4 — Start the server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API is now live. Open your browser:
- **API docs (interactive)**: `http://localhost:8000/docs`
- **Health check**: `http://localhost:8000/health`

---

### Step 5 — Expose your local server for Meta webhooks

Meta needs a public HTTPS URL to send webhooks to your local machine. Use ngrok:

```bash
# Install ngrok from https://ngrok.com then run:
ngrok http 8000
```

Copy the HTTPS URL it gives you (e.g. `https://abc123.ngrok-free.app`). You'll use this in the next step.

---

### Step 6 — Connect Facebook Messenger

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create a new App → choose **Business** type
3. Add the **Messenger** product
4. Under Webhooks → **Add Callback URL**:
   - URL: `https://abc123.ngrok-free.app/webhooks/messenger`
   - Verify Token: paste your `META_VERIFY_TOKEN` value from `.env`
5. Subscribe to the `messages` event
6. Connect a Facebook Page and generate a **Page Access Token** → paste it into `META_PAGE_ACCESS_TOKEN` in `.env`
7. Restart the server

Test it: send a message to your Facebook Page. The agent will reply.

---

### Step 7 — Connect Instagram

1. In the same Meta App, add the **Instagram** product
2. Connect your Instagram Business account to a Facebook Page
3. Under Webhooks → **Add Callback URL**:
   - URL: `https://abc123.ngrok-free.app/webhooks/instagram`
   - Verify Token: same `META_VERIFY_TOKEN`
4. Subscribe to `messages`

Instagram uses the same `META_PAGE_ACCESS_TOKEN` — no extra token needed.

---

### Step 8 — Connect Email (SendGrid)

1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Go to **Settings → Inbound Parse → Add Host & URL**:
   - Host: your email domain (e.g. `mail.yourdomain.com`)
   - URL: `https://your-deployed-url.com/webhooks/email`
3. Update your domain DNS MX records to point to SendGrid (instructions in the SendGrid dashboard)
4. Set `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL` in `.env`

Note: Email requires a real deployed URL (not ngrok) because MX records need a permanent address. Deploy first (see Step 9), then set this up.

---

### Step 9 — Deploy to production (Railway)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialise
railway login
railway init

# Add PostgreSQL
railway add --database postgresql

# Deploy
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=sk-...
railway variables set META_APP_SECRET=...
railway variables set META_PAGE_ACCESS_TOKEN=...
railway variables set META_VERIFY_TOKEN=...
railway variables set SENDGRID_API_KEY=...
railway variables set SENDGRID_FROM_EMAIL=...
railway variables set BRAND_VOICE_PROMPT="You are a helpful agent for..."
```

Railway gives you a permanent HTTPS URL (e.g. `https://yourapp.up.railway.app`). Use this as your webhook base URL in Meta and SendGrid.

---

### Readiness Checklist

| Component | Ready when |
|---|---|
| Tests | Immediately — `uv run pytest` |
| API server | `.env` filled + `docker compose up db -d` done |
| FAQ knowledge base | `load_knowledge` script run |
| Messenger | Meta App set up + webhook registered |
| Instagram | Instagram Business account connected to Meta App |
| Email | Deployed to production + SendGrid MX configured |

---

### Updating your FAQ

When you want to change or add FAQ answers:

1. Edit `data/faq.csv`
2. Run: `uv run python -m app.scripts.load_knowledge`
3. No server restart needed — ChromaDB is reloaded on next query

---

*This notes file is updated as the project progresses. See `specs/main/plan.md` for the full architecture and `specs/main/tasks.md` for implementation tasks.*

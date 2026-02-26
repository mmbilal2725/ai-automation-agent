# AI Automation Agent Constitution

## Core Principles

### I. API-First, Channel-Agnostic
Every feature is built as a standalone service behind a clean API. Channel integrations (Messenger, Instagram, Email) are adapters — they translate channel-specific formats into a unified message schema. No channel logic bleeds into the AI core.

### II. RAG Over Fine-Tuning (Knowledge First)
Customer responses are grounded in a FAQ/knowledge base via Retrieval-Augmented Generation (RAG). We do NOT fine-tune models. The knowledge base is the source of truth and must be updatable without redeployment.

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: tests written → user approved → tests fail → then implement. Red-Green-Refactor cycle enforced. Every webhook handler, every AI response path, every escalation rule must have a test.

### IV. Human-in-the-Loop Escalation
The agent must always have a clear, reliable escalation path to a human. Escalation rules are configuration, not code. When confidence is low or the user requests a human, handoff is immediate and lossless (full conversation context passed).

### V. Secrets Never in Code
All API keys, tokens, and credentials live in `.env` only. Never hardcoded, never committed. Use python-dotenv for loading. Rotate keys without code changes.

### VI. Observability by Default
Every inbound message, AI decision, and escalation event is logged with a correlation ID. Structured JSON logs. Response times tracked. Unknown intents flagged for review.

### VII. Simplicity Over Abstraction
Start with the simplest implementation that works. No premature abstractions. A single FastAPI app with clear modules is better than a microservices architecture until scale demands it.

## Security Requirements
- Validate all webhook signatures (Meta uses X-Hub-Signature-256; verify every request)
- Rate limiting on all public endpoints
- No PII stored beyond what is needed for conversation continuity
- Conversation logs retained for 30 days by default (configurable)

## Development Workflow
- Feature branches off `main`
- All changes must pass tests before merge
- Constitution supersedes all other practices

**Version**: 1.0.0 | **Ratified**: 2026-02-25 | **Last Amended**: 2026-02-25

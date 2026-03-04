---
id: "001"
title: "Add WhatsApp Channel"
stage: general
date: "2026-03-04"
surface: agent
model: claude-sonnet-4-6
feature: whatsapp
branch: master
user: MyCom
command: "Implement the following plan: Add WhatsApp Channel"
labels: ["whatsapp", "channel", "adapter", "meta", "webhook"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - app/channels/whatsapp.py
  - app/routers/whatsapp.py
  - app/schemas/message.py
  - app/config.py
  - app/main.py
  - .env.example
tests: []
---

## Prompt

Implement the following plan:

# Plan: Add WhatsApp Channel

The project already has Messenger, Instagram, and Email channels following a clean adapter pattern. WhatsApp is a natural addition — it uses the same Meta Graph API infrastructure. The pattern to follow is identical to Messenger/Instagram: a channel adapter + webhook router, registered in main.py.

WhatsApp Cloud API (Meta-hosted) differences vs Messenger:
- Different webhook payload structure (nested under `entry[].changes[].value.messages[]`)
- Different send endpoint: `/{phone_number_id}/messages` not `/me/messages`
- Requires `messaging_product: "whatsapp"` in send body
- Recipient is a phone number string, not a numeric user ID
- Same HMAC-SHA256 signature validation with same `X-Hub-Signature-256` header
- Requires two new env vars: `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_ACCESS_TOKEN`

## Response

Created `app/channels/whatsapp.py` — WhatsAppAdapter with validate_signature, normalize (handles `entry[].changes[].value.messages[]`), and send (POSTs to `/{phone_number_id}/messages` with `messaging_product: "whatsapp"`).

Created `app/routers/whatsapp.py` — GET `/webhooks/whatsapp` for verification, POST `/webhooks/whatsapp` for inbound messages with signature check.

Modified:
- `app/schemas/message.py`: added `"whatsapp"` to channel Literal
- `app/config.py`: added `whatsapp_phone_number_id` and `whatsapp_access_token` fields
- `app/main.py`: imported and registered whatsapp router; updated app description
- `.env.example`: added WhatsApp section with `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_ACCESS_TOKEN`

## Outcome

All 6 files created/modified. WhatsApp channel is fully wired in following the same adapter pattern as Messenger and Instagram.
---

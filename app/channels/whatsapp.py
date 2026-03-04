import hashlib
import hmac
import logging

import httpx

from app.channels.base import ChannelAdapter
from app.config import settings
from app.schemas.message import Message

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v21.0/{phone_number_id}/messages"


class WhatsAppAdapter(ChannelAdapter):
    def validate_signature(self, body: bytes, signature_header: str) -> bool:
        if not signature_header.startswith("sha256="):
            return False
        expected = signature_header[7:]
        computed = hmac.new(
            settings.meta_app_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, expected)

    def normalize(self, raw_payload: dict) -> list[Message]:
        messages = []
        for entry in raw_payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    if msg.get("type") != "text":
                        continue  # skip media, reactions, etc.
                    text = msg.get("text", {}).get("body", "").strip()
                    if not text:
                        continue
                    messages.append(
                        Message(
                            channel="whatsapp",
                            sender_id=msg["from"],  # phone number e.g. "14155238886"
                            content=text,
                            raw_payload=msg,
                        )
                    )
        return messages

    async def send(self, recipient_id: str, text: str) -> bool:
        url = GRAPH_API_URL.format(phone_number_id=settings.whatsapp_phone_number_id)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": recipient_id,
                    "type": "text",
                    "text": {"body": text},
                },
            )
        if resp.status_code != 200:
            logger.error("WhatsApp send failed: %s %s", resp.status_code, resp.text)
            return False
        return True

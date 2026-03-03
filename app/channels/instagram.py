import hashlib
import hmac
import logging

import httpx

from app.channels.base import ChannelAdapter
from app.config import settings
from app.schemas.message import Message

logger = logging.getLogger(__name__)

# Instagram uses the same Graph API; note endpoint differs slightly
GRAPH_API_URL = "https://graph.facebook.com/v21.0/me/messages"


class InstagramAdapter(ChannelAdapter):
    def validate_signature(self, body: bytes, signature_header: str) -> bool:
        if not signature_header.startswith("sha256="):
            return False
        expected = signature_header[7:]
        # Try instagram_app_secret first, then meta_app_secret
        for secret in [settings.instagram_app_secret, settings.meta_app_secret]:
            if not secret:
                continue
            computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            logger.info(
                "Instagram sig — secret: %s | received: %s | computed: %s | match: %s",
                secret[:8] + "...", expected[:16], computed[:16], computed == expected,
            )
            if hmac.compare_digest(computed, expected):
                return True
        return False

    def normalize(self, raw_payload: dict) -> list[Message]:
        messages = []
        for entry in raw_payload.get("entry", []):
            for event in entry.get("messaging", []):
                msg = event.get("message", {})
                text = msg.get("text", "").strip()
                if not text:
                    continue
                messages.append(
                    Message(
                        channel="instagram",
                        sender_id=event["sender"]["id"],
                        content=text,
                        raw_payload=event,
                    )
                )
        return messages

    async def send(self, recipient_id: str, text: str) -> bool:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                GRAPH_API_URL,
                params={"access_token": settings.meta_page_access_token},
                json={"recipient": {"id": recipient_id}, "message": {"text": text}},
            )
        if resp.status_code != 200:
            logger.error("Instagram send failed: %s %s", resp.status_code, resp.text)
            return False
        return True

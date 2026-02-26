import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.channels.base import ChannelAdapter
from app.config import settings
from app.schemas.message import Message

logger = logging.getLogger(__name__)


class EmailAdapter(ChannelAdapter):
    def validate_signature(self, body: bytes, signature_header: str) -> bool:
        # SendGrid Inbound Parse does not use HMAC signatures by default.
        # In production, restrict to SendGrid IP ranges via firewall/proxy.
        return True

    def normalize(self, raw_payload: dict) -> list[Message]:
        from_email = raw_payload.get("from", "").strip()
        body = (raw_payload.get("text") or raw_payload.get("html") or "").strip()
        if not from_email or not body:
            return []
        return [
            Message(
                channel="email",
                sender_id=from_email,
                content=body,
                raw_payload=raw_payload,
            )
        ]

    async def send(self, recipient_id: str, text: str) -> bool:
        subject = "Re: Your enquiry"
        mail = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=recipient_id,
            subject=subject,
            plain_text_content=text,
        )
        try:
            sg = SendGridAPIClient(settings.sendgrid_api_key)
            sg.send(mail)
            return True
        except Exception as exc:
            logger.error("Email send failed: %s", exc)
            return False

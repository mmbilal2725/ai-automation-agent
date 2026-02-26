from abc import ABC, abstractmethod

from app.schemas.message import Message


class ChannelAdapter(ABC):
    """Abstract base for all channel integrations."""

    @abstractmethod
    def normalize(self, raw_payload: dict) -> list[Message]:
        """Convert a raw webhook payload into unified Message objects."""

    @abstractmethod
    async def send(self, recipient_id: str, text: str) -> bool:
        """Send a text reply back through this channel. Returns True on success."""

    @abstractmethod
    def validate_signature(self, body: bytes, signature_header: str) -> bool:
        """Verify the webhook request is genuine. Returns True if valid."""

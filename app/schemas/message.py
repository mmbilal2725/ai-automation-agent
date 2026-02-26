import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Unified inbound message schema — channel-agnostic."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID | None = None
    channel: Literal["messenger", "instagram", "email"]
    sender_id: str
    content: str
    raw_payload: dict = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: uuid.UUID = Field(default_factory=uuid.uuid4)

    model_config = {"arbitrary_types_allowed": True}

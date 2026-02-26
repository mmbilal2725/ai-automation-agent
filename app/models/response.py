import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChannelResponse(Base):
    __tablename__ = "channel_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sessions.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="sent")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

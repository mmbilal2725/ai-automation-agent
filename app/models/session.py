import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    message_history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

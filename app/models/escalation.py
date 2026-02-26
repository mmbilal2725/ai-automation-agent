import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EscalationEvent(Base):
    __tablename__ = "escalation_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sessions.id"), nullable=False
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversation_snapshot: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

import logging
import uuid
from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.session import Session

logger = logging.getLogger(__name__)


async def get_or_create_session(channel: str, sender_id: str) -> Session:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.channel == channel,
                Session.sender_id == sender_id,
                Session.status == "active",
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            session = Session(channel=channel, sender_id=sender_id)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            logger.info("New session %s created for %s/%s", session.id, channel, sender_id)

        return session


async def append_to_history(session_id: uuid.UUID, role: str, content: str) -> None:
    async with AsyncSessionLocal() as db:
        session = await db.get(Session, session_id)
        if not session:
            logger.warning("append_to_history: session %s not found", session_id)
            return
        history = list(session.message_history or [])
        history.append({"role": role, "content": content})
        session.message_history = history
        session.updated_at = datetime.utcnow()
        await db.commit()


async def mark_escalated(session_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        session = await db.get(Session, session_id)
        if session:
            session.status = "escalated"
            session.escalated_at = datetime.utcnow()
            await db.commit()

import logging
import re
import uuid
from datetime import datetime

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.escalation import EscalationEvent

logger = logging.getLogger(__name__)

ESCALATION_PATTERNS = [
    r"\bhuman\b",
    r"\breal person\b",
    r"\breal agent\b",
    r"\bspeak to (someone|a person|an agent)\b",
    r"\btalk to (someone|a person|an agent)\b",
    r"\bmanager\b",
    r"\bsupervisor\b",
    r"\bsupport team\b",
    r"\blive (chat|agent|support)\b",
]

ESCALATION_REPLY = (
    "I'm connecting you with a member of our team right now. "
    "They'll have full context of our conversation and will be with you shortly. "
    "Thank you for your patience."
)

LOW_CONFIDENCE_REPLY = (
    "I want to make sure you get the right answer. "
    "Let me connect you with one of our team members who can help you further."
)


def check_explicit_escalation(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in ESCALATION_PATTERNS)


def should_escalate(user_message: str, confidence: float) -> tuple[bool, str]:
    """Returns (escalate: bool, trigger: str)."""
    if check_explicit_escalation(user_message):
        return True, "explicit_request"
    if confidence < settings.escalation_confidence_threshold:
        return True, "low_confidence"
    return False, ""


async def record_escalation(
    session_id: uuid.UUID,
    trigger: str,
    confidence: float | None,
    conversation_snapshot: list,
) -> EscalationEvent:
    async with AsyncSessionLocal() as db:
        event = EscalationEvent(
            session_id=session_id,
            trigger=trigger,
            confidence_score=confidence,
            conversation_snapshot=conversation_snapshot,
            notified_at=datetime.utcnow(),  # extend: integrate Slack/email notify here
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        logger.info(
            "Escalation recorded: session=%s trigger=%s confidence=%s",
            session_id, trigger, confidence,
        )
        return event


def escalation_reply(trigger: str) -> str:
    if trigger == "explicit_request":
        return ESCALATION_REPLY
    return LOW_CONFIDENCE_REPLY

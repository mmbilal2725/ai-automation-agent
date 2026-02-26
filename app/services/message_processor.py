import logging

from app.channels.base import ChannelAdapter
from app.schemas.message import Message
from app.services import ai_service as ai_module
from app.services import escalation_service as esc
from app.services import session_service as sess

logger = logging.getLogger(__name__)


async def process_message(raw_payload: dict, channel: str, adapter: ChannelAdapter) -> None:
    """
    Full pipeline: normalize → session → RAG/LLM → escalation check → reply.
    Called as a BackgroundTask so the webhook already returned 200.
    """
    messages: list[Message] = adapter.normalize(raw_payload)
    if not messages:
        logger.info("No processable messages in %s payload", channel)
        return

    ai = ai_module.get_ai_service()

    for message in messages:
        correlation = str(message.correlation_id)
        logger.info("[%s] Inbound from %s on %s", correlation, message.sender_id, channel)

        # 1. Session
        session = await sess.get_or_create_session(channel, message.sender_id)
        message.session_id = session.id
        history: list[dict] = list(session.message_history or [])

        # 2. Persist inbound turn
        await sess.append_to_history(session.id, "user", message.content)

        # 3. AI
        try:
            response_text, confidence = await ai.get_response(message.content, history)
        except Exception as exc:
            logger.error("[%s] AI error: %s", correlation, exc, exc_info=True)
            response_text = (
                "I'm having trouble processing your request right now. "
                "Please try again in a moment or contact us directly."
            )
            confidence = 0.0

        # 4. Escalation check
        escalate, trigger = esc.should_escalate(message.content, confidence)
        if escalate:
            await esc.record_escalation(
                session_id=session.id,
                trigger=trigger,
                confidence=confidence,
                conversation_snapshot=history,
            )
            await sess.mark_escalated(session.id)
            response_text = esc.escalation_reply(trigger)
            logger.info("[%s] Escalated: %s", correlation, trigger)

        # 5. Send reply
        sent = await adapter.send(message.sender_id, response_text)
        if not sent:
            logger.error("[%s] Failed to send reply to %s", correlation, message.sender_id)

        # 6. Persist assistant turn
        await sess.append_to_history(session.id, "assistant", response_text)

        logger.info("[%s] Done. escalated=%s", correlation, escalate)

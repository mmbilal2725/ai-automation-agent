import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.channels.messenger import MessengerAdapter
from app.config import settings
from app.services.message_processor import process_message

logger = logging.getLogger(__name__)
router = APIRouter()
adapter = MessengerAdapter()


@router.get("/webhooks/messenger", response_class=PlainTextResponse)
async def messenger_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta calls this once during webhook setup to verify ownership."""
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        logger.info("Messenger webhook verified")
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/messenger")
async def messenger_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not adapter.validate_signature(body, signature):
        logger.warning("Messenger webhook: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    background_tasks.add_task(process_message, payload, "messenger", adapter)
    return {"status": "ok"}

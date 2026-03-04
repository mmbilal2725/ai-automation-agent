import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.channels.whatsapp import WhatsAppAdapter
from app.config import settings
from app.services.message_processor import process_message

router = APIRouter()
adapter = WhatsAppAdapter()
logger = logging.getLogger(__name__)


@router.get("/webhooks/whatsapp", response_class=PlainTextResponse)
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        logger.info("WhatsApp webhook verified")
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not adapter.validate_signature(body, signature):
        logger.warning("WhatsApp webhook: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    payload = await request.json()
    background_tasks.add_task(process_message, payload, "whatsapp", adapter)
    return {"status": "ok"}

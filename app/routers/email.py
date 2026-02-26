import logging

from fastapi import APIRouter, BackgroundTasks, Form

from app.channels.email import EmailAdapter
from app.services.message_processor import process_message

logger = logging.getLogger(__name__)
router = APIRouter()
adapter = EmailAdapter()


@router.post("/webhooks/email")
async def email_webhook(
    background_tasks: BackgroundTasks,
    from_email: str = Form(alias="from", default=""),
    subject: str = Form(default=""),
    text: str = Form(default=""),
    html: str = Form(default=""),
):
    """SendGrid Inbound Parse posts multipart form data here."""
    payload = {
        "from": from_email,
        "subject": subject,
        "text": text,
        "html": html,
    }
    background_tasks.add_task(process_message, payload, "email", adapter)
    return {"status": "ok"}

"""Integration tests for the Instagram webhook endpoint."""
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def mock_processor():
    with patch("app.routers.instagram.process_message", new_callable=AsyncMock):
        yield


from app.main import app


def sign(body: bytes, secret: str = "test_app_secret") -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


SAMPLE_PAYLOAD = {
    "object": "instagram",
    "entry": [{
        "id": "ig_page_789",
        "messaging": [{
            "sender": {"id": "ig_user_456"},
            "recipient": {"id": "ig_page_789"},
            "timestamp": 1700000000,
            "message": {"mid": "m2", "text": "Do you ship internationally?"},
        }]
    }]
}


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_instagram_webhook_valid_signature(client):
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    async with client as c:
        resp = await c.post(
            "/webhooks/instagram",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sign(body),
            },
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_instagram_webhook_invalid_signature(client):
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    async with client as c:
        resp = await c.post(
            "/webhooks/instagram",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=invalid",
            },
        )
    assert resp.status_code == 401

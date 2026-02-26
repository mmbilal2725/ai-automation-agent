"""Integration tests for the Messenger webhook endpoint."""
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Patch process_message so background tasks don't hit the DB or AI APIs
pytestmark = pytest.mark.usefixtures("mock_processor")


@pytest.fixture(autouse=True)
def mock_processor():
    with patch("app.routers.messenger.process_message", new_callable=AsyncMock):
        yield


from app.main import app


def sign(body: bytes, secret: str = "test_app_secret") -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


SAMPLE_PAYLOAD = {
    "object": "page",
    "entry": [{
        "id": "page123",
        "messaging": [{
            "sender": {"id": "user123"},
            "recipient": {"id": "page123"},
            "timestamp": 1700000000,
            "message": {"mid": "m1", "text": "What are your shipping times?"},
        }]
    }]
}


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_messenger_webhook_returns_200_on_valid_signature(client):
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    async with client as c:
        resp = await c.post(
            "/webhooks/messenger",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sign(body),
            },
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_messenger_webhook_returns_401_on_bad_signature(client):
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    async with client as c:
        resp = await c.post(
            "/webhooks/messenger",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=badhash",
            },
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_messenger_verify_challenge(client):
    async with client as c:
        resp = await c.get(
            "/webhooks/messenger",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token",
                "hub.challenge": "abc123",
            },
        )
    assert resp.status_code == 200
    assert resp.text == "abc123"


@pytest.mark.asyncio
async def test_messenger_verify_rejects_wrong_token(client):
    async with client as c:
        resp = await c.get(
            "/webhooks/messenger",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "WRONG_TOKEN",
                "hub.challenge": "abc123",
            },
        )
    assert resp.status_code == 403

"""Integration tests for the Email webhook endpoint."""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def mock_processor():
    with patch("app.routers.email.process_message", new_callable=AsyncMock):
        yield


from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_email_webhook_returns_200(client):
    async with client as c:
        resp = await c.post(
            "/webhooks/email",
            data={
                "from": "customer@example.com",
                "subject": "Return question",
                "text": "How do I return an item?",
            },
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_email_webhook_accepts_html_body(client):
    async with client as c:
        resp = await c.post(
            "/webhooks/email",
            data={
                "from": "customer@example.com",
                "subject": "Shipping question",
                "text": "",
                "html": "<p>When will my order arrive?</p>",
            },
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint(client):
    async with client as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data

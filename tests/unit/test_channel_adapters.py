"""Unit tests for channel adapters."""
import hashlib
import hmac

import pytest

from app.channels.messenger import MessengerAdapter
from app.channels.instagram import InstagramAdapter
from app.channels.email import EmailAdapter


# ── Messenger ────────────────────────────────────────────────────────────────

class TestMessengerAdapter:
    def setup_method(self):
        self.adapter = MessengerAdapter()

    def _make_sig(self, body: bytes, secret: str = "test_app_secret") -> str:
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def test_validate_signature_valid(self):
        body = b'{"test": "payload"}'
        sig = self._make_sig(body)
        assert self.adapter.validate_signature(body, sig) is True

    def test_validate_signature_invalid(self):
        body = b'{"test": "payload"}'
        assert self.adapter.validate_signature(body, "sha256=wrongsig") is False

    def test_validate_signature_missing_prefix(self):
        assert self.adapter.validate_signature(b"body", "invalidsig") is False

    def test_normalize_extracts_text_message(self):
        payload = {
            "entry": [{
                "messaging": [{
                    "sender": {"id": "user123"},
                    "recipient": {"id": "page123"},
                    "message": {"text": "Hello, what are your hours?"}
                }]
            }]
        }
        messages = self.adapter.normalize(payload)
        assert len(messages) == 1
        assert messages[0].channel == "messenger"
        assert messages[0].sender_id == "user123"
        assert messages[0].content == "Hello, what are your hours?"

    def test_normalize_skips_empty_text(self):
        payload = {
            "entry": [{
                "messaging": [{
                    "sender": {"id": "user123"},
                    "recipient": {"id": "page123"},
                    "message": {"text": ""}   # delivery receipt / sticker
                }]
            }]
        }
        messages = self.adapter.normalize(payload)
        assert messages == []

    def test_normalize_skips_non_message_events(self):
        payload = {
            "entry": [{
                "messaging": [{
                    "sender": {"id": "user123"},
                    "delivery": {"watermark": 123}   # delivery event — no "message" key
                }]
            }]
        }
        messages = self.adapter.normalize(payload)
        assert messages == []

    def test_normalize_multiple_messages(self):
        payload = {
            "entry": [
                {
                    "messaging": [
                        {"sender": {"id": "u1"}, "recipient": {}, "message": {"text": "Hi"}},
                        {"sender": {"id": "u2"}, "recipient": {}, "message": {"text": "Hello"}},
                    ]
                }
            ]
        }
        messages = self.adapter.normalize(payload)
        assert len(messages) == 2


# ── Instagram ─────────────────────────────────────────────────────────────────

class TestInstagramAdapter:
    def setup_method(self):
        self.adapter = InstagramAdapter()

    def test_normalize_extracts_message(self):
        payload = {
            "entry": [{
                "messaging": [{
                    "sender": {"id": "ig_user_456"},
                    "recipient": {"id": "ig_page_789"},
                    "message": {"text": "Do you ship internationally?"}
                }]
            }]
        }
        messages = self.adapter.normalize(payload)
        assert len(messages) == 1
        assert messages[0].channel == "instagram"
        assert messages[0].sender_id == "ig_user_456"
        assert messages[0].content == "Do you ship internationally?"


# ── Email ─────────────────────────────────────────────────────────────────────

class TestEmailAdapter:
    def setup_method(self):
        self.adapter = EmailAdapter()

    def test_validate_signature_always_true(self):
        assert self.adapter.validate_signature(b"any", "any") is True

    def test_normalize_from_text_body(self):
        payload = {
            "from": "customer@example.com",
            "subject": "Shipping question",
            "text": "How long does standard shipping take?",
        }
        messages = self.adapter.normalize(payload)
        assert len(messages) == 1
        assert messages[0].channel == "email"
        assert messages[0].sender_id == "customer@example.com"
        assert "shipping" in messages[0].content.lower()

    def test_normalize_falls_back_to_html(self):
        payload = {
            "from": "customer@example.com",
            "text": "",
            "html": "<p>What is your return policy?</p>",
        }
        messages = self.adapter.normalize(payload)
        assert len(messages) == 1

    def test_normalize_skips_empty_body(self):
        payload = {"from": "someone@example.com", "text": "", "html": ""}
        messages = self.adapter.normalize(payload)
        assert messages == []

    def test_normalize_skips_missing_sender(self):
        payload = {"from": "", "text": "Some message"}
        messages = self.adapter.normalize(payload)
        assert messages == []

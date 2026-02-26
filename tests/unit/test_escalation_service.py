"""Unit tests for escalation detection logic."""
import pytest

from app.services.escalation_service import should_escalate, check_explicit_escalation


class TestExplicitEscalationDetection:
    @pytest.mark.parametrize("text", [
        "I want to speak to a human",
        "Can I talk to a real person?",
        "Let me speak to an agent",
        "I need a manager",
        "Connect me to your support team",
        "I want live chat",
        "Please get me a supervisor",
    ])
    def test_detects_escalation_keywords(self, text: str):
        assert check_explicit_escalation(text) is True

    @pytest.mark.parametrize("text", [
        "What are your shipping times?",
        "How do I return an item?",
        "I'd like to cancel my order",
        "Thank you for your help",
    ])
    def test_does_not_flag_normal_messages(self, text: str):
        assert check_explicit_escalation(text) is False


class TestShouldEscalate:
    def test_escalates_on_explicit_request(self):
        escalate, trigger = should_escalate("I need to speak to a human", confidence=0.9)
        assert escalate is True
        assert trigger == "explicit_request"

    def test_escalates_on_low_confidence(self):
        escalate, trigger = should_escalate("Tell me about your enterprise plan", confidence=0.4)
        assert escalate is True
        assert trigger == "low_confidence"

    def test_no_escalation_on_high_confidence_normal_message(self):
        escalate, trigger = should_escalate("What are your shipping times?", confidence=0.88)
        assert escalate is False
        assert trigger == ""

    def test_explicit_request_overrides_high_confidence(self):
        # Even if confidence is high, explicit request must trigger escalation
        escalate, trigger = should_escalate("Talk to a real person please", confidence=0.95)
        assert escalate is True
        assert trigger == "explicit_request"

    def test_confidence_at_exact_threshold_does_not_escalate(self):
        # threshold is 0.6; exactly 0.6 should NOT escalate
        escalate, _ = should_escalate("When will my order arrive?", confidence=0.6)
        assert escalate is False

    def test_confidence_just_below_threshold_escalates(self):
        escalate, trigger = should_escalate("Something unusual query", confidence=0.59)
        assert escalate is True
        assert trigger == "low_confidence"

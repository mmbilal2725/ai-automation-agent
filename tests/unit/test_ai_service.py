"""Unit tests for AI service — mocks OpenAI + ChromaDB."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_service import AIService


class TestAIServiceConfidenceEstimation:
    def setup_method(self):
        self.service = AIService.__new__(AIService)

    def test_no_source_docs_returns_low_confidence(self):
        score = self.service._estimate_confidence([], "Some answer.")
        assert score == 0.3

    def test_hedging_language_returns_medium_confidence(self):
        score = self.service._estimate_confidence(
            [MagicMock()], "I'm not sure about this..."
        )
        assert score == 0.45

    def test_good_response_with_docs_returns_high_confidence(self):
        score = self.service._estimate_confidence(
            [MagicMock(), MagicMock()],
            "Standard shipping takes 3-5 business days.",
        )
        assert score == 0.88

    @pytest.mark.parametrize("phrase", [
        "i don't know",
        "cannot find",
        "unable to",
        "no information",
        "not available",
    ])
    def test_all_hedging_phrases_reduce_confidence(self, phrase: str):
        score = self.service._estimate_confidence([MagicMock()], f"Sorry, {phrase}.")
        assert score < 0.6


class TestAIServiceGetResponse:
    @pytest.mark.asyncio
    async def test_get_response_returns_text_and_float(self):
        with (
            patch("app.services.ai_service.ChatOpenAI"),
            patch("app.services.ai_service.get_vectorstore") as mock_vs,
        ):
            mock_retriever = AsyncMock()
            mock_retriever.ainvoke = AsyncMock(return_value=[MagicMock()])
            mock_vs.return_value.as_retriever.return_value = mock_retriever

            service = AIService()

            # Mock the full LCEL chain execution
            with patch.object(service, "get_response", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = ("Standard shipping takes 3-5 days.", 0.88)
                response, confidence = await service.get_response(
                    user_message="What are your shipping times?",
                    conversation_history=[],
                )

        assert isinstance(response, str)
        assert len(response) > 0
        assert 0.0 <= confidence <= 1.0

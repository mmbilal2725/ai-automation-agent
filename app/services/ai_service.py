import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.knowledge_service import get_vectorstore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "{brand_voice}\n\n"
    "Use the FAQ context below to answer the customer's question accurately. "
    "If the context does not contain a relevant answer, say so honestly and "
    "offer to connect the customer with a team member.\n\n"
    "FAQ Context:\n{context}"
)


def _format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


def _build_history(conversation_history: list[dict]) -> list:
    messages = []
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages


class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-5-nano",
            temperature=0.3,
            openai_api_key=settings.openai_api_key,
        )

    async def get_response(
        self,
        user_message: str,
        conversation_history: list[dict],
    ) -> tuple[str, float]:
        """
        Generate a response using RAG + LLM (LCEL pipeline).
        Returns (response_text, confidence_score 0.0–1.0).
        """
        vectorstore = get_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        history_messages = _build_history(conversation_history)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                *[(m.type, m.content) for m in history_messages],
                ("human", "{question}"),
            ]
        )

        chain = (
            {
                "context": retriever | _format_docs,
                "question": RunnablePassthrough(),
                "brand_voice": lambda _: settings.brand_voice_prompt,
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        # Retrieve docs separately to estimate confidence
        source_docs = await retriever.ainvoke(user_message)
        response: str = await chain.ainvoke(user_message)
        confidence = self._estimate_confidence(source_docs, response)

        logger.info(
            "AI response generated: confidence=%.2f sources=%d",
            confidence,
            len(source_docs),
        )
        return response, confidence

    @staticmethod
    def _estimate_confidence(source_docs: list, response: str) -> float:
        if not source_docs:
            return 0.3
        hedging = [
            "i'm not sure",
            "i don't know",
            "cannot find",
            "unable to",
            "no information",
            "not available",
        ]
        if any(phrase in response.lower() for phrase in hedging):
            return 0.45
        return 0.88


_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

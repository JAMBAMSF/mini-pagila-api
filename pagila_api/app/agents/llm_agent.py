from __future__ import annotations

from domain.services import AIService, DomainError


class LLMAgent:
    """Fallback agent that delegates to the LLM via the AIService."""

    def __init__(self, ai_service: AIService):
        self._ai_service = ai_service

    async def answer(self, question: str) -> str:
        chunks: list[str] = []
        async for chunk in self._ai_service.ask(question):
            chunks.append(chunk)

        response = "".join(chunks).strip()
        if not response:
            raise DomainError("LLM produced an empty response.")
        return response

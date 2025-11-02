from __future__ import annotations

from typing import Callable

from .llm_agent import LLMAgent
from .search_agent import SearchAgent


class HandoffOrchestration:
    """Coordinates SearchAgent and LLMAgent according to the assignment specification."""

    def __init__(self, search_agent: SearchAgent, llm_factory: Callable[[], LLMAgent]):
        self._search_agent = search_agent
        self._llm_factory = llm_factory

    async def handle(self, question: str) -> tuple[str, str]:
        search_answer = await self._search_agent.try_answer(question)
        if search_answer:
            return "SearchAgent", search_answer

        llm_agent = self._llm_factory()
        answer = await llm_agent.answer(question)
        return "LLMAgent", answer

from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional

from domain.models import FilmOut
from domain.services import FilmService


class SearchAgent:
    """Attempts to answer questions about specific films by querying the database."""

    def __init__(self, film_service: FilmService):
        self._film_service = film_service

    async def try_answer(self, question: str) -> Optional[str]:
        if "film" not in question.lower():
            return None

        title = self._extract_title(question)
        if not title:
            return None

        film: Optional[FilmOut] = await self._film_service.find_by_title(title)
        if film is None:
            return None

        category = film.category or "Unknown"
        rate = self._format_rate(film.rental_rate)
        return f"{film.title} ({category}) rents for ${rate}."

    @staticmethod
    def _format_rate(rate: Decimal) -> str:
        return f"{rate:.2f}"

    @staticmethod
    def _extract_title(question: str) -> Optional[str]:
        text = question.strip()
        if not text:
            return None

        quoted = re.findall(r'"([^"]+)"', text)
        if quoted:
            return quoted[0].strip()

        match = re.search(r"film\s+([^?.!]+)", text, flags=re.IGNORECASE)
        if not match:
            return None

        candidate = match.group(1)
        candidate = re.sub(r"\(.*?\)", "", candidate)
        candidate = re.split(r"[?.!,]", candidate)[0]
        candidate = candidate.strip(" '\"")
        return candidate or None

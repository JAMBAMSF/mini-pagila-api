from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import AsyncIterator, Callable, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_agent import LLMAgent
from app.agents.orchestration import HandoffOrchestration
from app.agents.search_agent import SearchAgent
from core.ai_kernel import get_kernel, load_prompt_config
from core.config import Settings, get_settings
from core.db import get_session
from domain.models import (
    AIHandoffRequest,
    AIHandoffResponse,
    AISummaryRequest,
    SummaryOut,
)
from domain.services import AIService, DomainError, FilmService, MissingDependencyError, NotFoundError

router = APIRouter(tags=["ai"])


def _prompt_folder() -> Path:
    return Path(__file__).resolve().parents[2] / "core" / "prompts" / "summary"


@lru_cache()
def _summary_prompt_config() -> dict[str, Any]:
    return load_prompt_config(_prompt_folder())


def _kernel_provider(settings: Settings) -> Callable[[], Any]:
    def _provider() -> Any:
        return get_kernel(settings)

    return _provider


def get_film_service(session: AsyncSession = Depends(get_session)) -> FilmService:
    return FilmService(session)


def get_ai_service(
    settings: Settings = Depends(get_settings),
    film_service: FilmService = Depends(get_film_service),
) -> AIService:
    return AIService(_kernel_provider(settings), _summary_prompt_config(), film_service)


def get_handoff_orchestration(
    film_service: FilmService = Depends(get_film_service),
    ai_service: AIService = Depends(get_ai_service),
) -> HandoffOrchestration:
    search_agent = SearchAgent(film_service)

    def _llm_factory() -> LLMAgent:
        return LLMAgent(ai_service)

    return HandoffOrchestration(search_agent, _llm_factory)


@router.get(
    "/ai/ask",
    summary="Stream AI answer for a question",
)
async def ai_ask(
    question: str = Query(..., min_length=1),
    service: AIService = Depends(get_ai_service),
) -> StreamingResponse:
    try:
        service.ensure_ready()
    except (MissingDependencyError, ImportError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    async def event_stream() -> AsyncIterator[str]:
        async for chunk in service.ask(question):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post(
    "/ai/summary",
    response_model=SummaryOut,
    summary="Return structured summary for a film",
)
async def ai_summary(
    payload: AISummaryRequest,
    service: AIService = Depends(get_ai_service),
) -> SummaryOut:
    try:
        summary = await service.summary(payload.film_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (MissingDependencyError, ImportError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return summary


@router.post(
    "/ai/handoff",
    response_model=AIHandoffResponse,
    summary="Run SearchAgent then fall back to LLMAgent",
)
async def ai_handoff(
    payload: AIHandoffRequest,
    orchestration: HandoffOrchestration = Depends(get_handoff_orchestration),
) -> AIHandoffResponse:
    try:
        agent, answer = await orchestration.handle(payload.question)
    except (MissingDependencyError, ImportError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return AIHandoffResponse(agent=agent, answer=answer)

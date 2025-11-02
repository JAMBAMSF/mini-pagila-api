from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from domain.models import FilmListParams, FilmOut, Paginated
from domain.services import FilmService

router = APIRouter(tags=["films"])


def get_film_service(session: AsyncSession = Depends(get_session)) -> FilmService:
    return FilmService(session)


@router.get(
    "/films",
    response_model=Paginated[FilmOut],
    summary="List films with pagination and optional category filter",
)
async def list_films(
    params: FilmListParams = Depends(),
    service: FilmService = Depends(get_film_service),
) -> Paginated[FilmOut]:
    return await service.list_films(params)

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import require_admin_token
from core.db import get_session
from domain.models import RentalCreate, RentalCreatedResponse
from domain.services import NotFoundError, RentalService

router = APIRouter(tags=["rentals"])


def get_rental_service(session: AsyncSession = Depends(get_session)) -> RentalService:
    return RentalService(session)


@router.post(
    "/customers/{customer_id}/rentals",
    status_code=status.HTTP_201_CREATED,
    response_model=RentalCreatedResponse,
    dependencies=[Depends(require_admin_token)],
    summary="Create a rental for a customer",
)
async def create_rental(
    customer_id: int = Path(..., ge=1),
    payload: RentalCreate = ...,
    service: RentalService = Depends(get_rental_service),
) -> RentalCreatedResponse:
    try:
        return await service.create_rental(customer_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

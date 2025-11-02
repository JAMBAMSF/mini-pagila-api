from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Customer,
    Category,
    Film,
    FilmCategory,
    FilmListParams,
    FilmOut,
    Inventory,
    Paginated,
    Rental,
    RentalCreate,
    RentalCreatedResponse,
)


class FilmRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def paginate(self, params: FilmListParams) -> Paginated[FilmOut]:
        category_value = params.category.strip().lower() if params.category else None

        category_subquery = (
            select(
                FilmCategory.film_id.label("film_id"),
                func.min(Category.name).label("category_name"),
            )
            .join(Category, Category.category_id == FilmCategory.category_id)
            .group_by(FilmCategory.film_id)
            .subquery()
        )

        filter_clause = (
            func.lower(category_subquery.c.category_name) == category_value if category_value else None
        )

        base_stmt = (
            select(Film, category_subquery.c.category_name)
            .select_from(Film)
            .join(category_subquery, Film.film_id == category_subquery.c.film_id, isouter=True)
        )
        count_stmt = (
            select(Film.film_id)
            .select_from(Film)
            .join(category_subquery, Film.film_id == category_subquery.c.film_id, isouter=True)
        )

        if filter_clause is not None:
            base_stmt = base_stmt.where(filter_clause)
            count_stmt = count_stmt.where(filter_clause)

        total_stmt = select(func.count()).select_from(count_stmt.distinct().subquery())
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar_one()

        stmt = (
            base_stmt.order_by(Film.title.asc(), Film.film_id.asc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        items = [
            FilmOut(
                film_id=film.film_id,  # type: ignore[arg-type]
                title=film.title,
                description=film.description,
                rating=film.rating,
                rental_rate=film.rental_rate,
                category=category_name,
                streaming_available=film.streaming_available,
            )
            for film, category_name in rows
        ]

        return Paginated(
            items=items,
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    async def get_film(self, film_id: int) -> Optional[Film]:
        stmt = select(Film).where(Film.film_id == film_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_title(self, title: str) -> Optional[FilmOut]:
        title_value = title.strip()
        if not title_value:
            return None

        category_subquery = (
            select(
                FilmCategory.film_id.label("film_id"),
                func.min(Category.name).label("category_name"),
            )
            .join(Category, Category.category_id == FilmCategory.category_id)
            .group_by(FilmCategory.film_id)
            .subquery()
        )

        stmt = (
            select(Film, category_subquery.c.category_name)
            .select_from(Film)
            .join(category_subquery, Film.film_id == category_subquery.c.film_id, isouter=True)
            .where(Film.title.ilike(f"%{title_value}%"))
            .order_by(Film.film_id.asc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None

        film, category_name = row
        return FilmOut(
            film_id=film.film_id,  # type: ignore[arg-type]
            title=film.title,
            description=film.description,
            rating=film.rating,
            rental_rate=film.rental_rate,
            category=category_name,
            streaming_available=film.streaming_available,
        )


class RentalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_customer(self, customer_id: int) -> Optional[int]:
        stmt = select(Customer.customer_id).where(Customer.customer_id == customer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_inventory(self, inventory_id: int) -> Optional[int]:
        stmt = select(Inventory.inventory_id).where(Inventory.inventory_id == inventory_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_rental(
        self,
        customer_id: int,
        payload: RentalCreate,
    ) -> RentalCreatedResponse:
        # Use naive UTC to match Pagila's TIMESTAMP WITHOUT TIME ZONE columns
        now = datetime.utcnow()
        rental = Rental(
            rental_date=now,
            inventory_id=payload.inventory_id,
            customer_id=customer_id,
            staff_id=payload.staff_id,
            last_update=now,
        )
        self.session.add(rental)
        await self.session.flush()
        return RentalCreatedResponse(rental_id=rental.rental_id or 0)

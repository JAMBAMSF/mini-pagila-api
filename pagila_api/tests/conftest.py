from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from app.main import app
from core.config import get_settings
from core.db import dispose_engine, get_engine, get_session_factory, init_engine
from domain.models import Category, Customer, Film, FilmCategory, Inventory, SummaryOut
from domain.services import FilmService


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def test_env(tmp_path_factory: pytest.TempPathFactory) -> AsyncIterator[None]:
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["OPENAI_API_KEY"] = "sk-test"
    os.environ["OPENAI_MODEL"] = "gpt-test"
    os.environ["ADMIN_BEARER_TOKEN"] = "dvd_admin"
    os.environ["LOG_JSON"] = "false"
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def database(test_env: None) -> AsyncIterator[None]:
    settings = get_settings()
    engine = init_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await dispose_engine()


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


class FakeAIService:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    def ensure_ready(self) -> None:
        return None

    async def ask(self, question: str):
        lower = question.lower()
        if "fifa" in lower:
            chunks = [
                "Argentina won the 2022 FIFA World Cup after defeating France."
            ]
        else:
            chunks = ["Hello from the test assistant."]
        for chunk in chunks:
            yield chunk

    async def summary(self, film_id: int) -> SummaryOut:
        async with self._session_factory() as session:
            service = FilmService(session)
            context = await service.get_summary_context(film_id)

        rating = context["rating"]
        try:
            rental_rate = float(context["rental_rate"])
        except ValueError:
            rental_rate = 999.0

        recommended = rating.upper() in {"R", "NC-17"} and rental_rate < 3.0
        return SummaryOut(title=context["title"], rating=rating, recommended=recommended)


@pytest_asyncio.fixture
async def client(db_session) -> AsyncIterator[AsyncClient]:
    from api.v1 import ai_routes

    session_factory = get_session_factory()
    fake_ai_service = FakeAIService(session_factory)
    app.dependency_overrides[ai_routes.get_ai_service] = lambda: fake_ai_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client

    app.dependency_overrides.clear()


async def seed_base_data(session: AsyncSession) -> dict[str, int | str]:
    now = datetime.now(timezone.utc)
    film = Film(
        title="Alien",
        description="A crew faces an extraterrestrial threat.",
        release_year=1979,
        language_id=1,
        rental_duration=3,
        rental_rate=Decimal("2.99"),
        length=117,
        replacement_cost=Decimal("19.99"),
        rating="R",
        streaming_available=True,
    )
    category = Category(name="Horror")
    customer = Customer(
        store_id=1,
        first_name="Ellen",
        last_name="Ripley",
        email="ripley@example.com",
        active=True,
        create_date=now,
        last_update=now,
    )
    session.add(film)
    session.add(category)
    session.add(customer)
    await session.flush()

    film_category = FilmCategory(film_id=film.film_id, category_id=category.category_id)
    session.add(film_category)

    inventory = Inventory(film_id=film.film_id, store_id=1, last_update=now)
    session.add(inventory)
    await session.commit()

    return {
        "film_id": film.film_id,
        "category": category.name,
        "customer_id": customer.customer_id,
        "inventory_id": inventory.inventory_id,
    }

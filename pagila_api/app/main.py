from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import Settings, get_settings
from core.db import dispose_engine, init_engine
from core.logging import configure_logging
from api.v1 import ai_routes, film_routes, rental_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    configure_logging(settings)
    init_engine(settings)
    yield
    await dispose_engine()


app = FastAPI(
    title="Mini Pagila API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(film_routes.router, prefix="/v1")
app.include_router(rental_routes.router, prefix="/v1")
app.include_router(ai_routes.router, prefix="/v1")

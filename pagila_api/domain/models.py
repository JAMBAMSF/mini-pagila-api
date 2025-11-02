from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field, field_serializer
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


class Film(SQLModel, table=True):
    __tablename__ = "film"

    film_id: int | None = SQLField(default=None, primary_key=True)
    title: str
    description: str | None = None
    release_year: int | None = None
    language_id: int
    rental_duration: int
    rental_rate: Decimal = SQLField(default=Decimal("0"))
    length: int | None = None
    replacement_cost: Decimal = SQLField(default=Decimal("0"))
    rating: str | None = None
    streaming_available: bool = SQLField(default=False, nullable=False)


class Category(SQLModel, table=True):
    __tablename__ = "category"

    category_id: int | None = SQLField(default=None, primary_key=True)
    name: str


class FilmCategory(SQLModel, table=True):
    __tablename__ = "film_category"

    film_id: int = SQLField(primary_key=True, foreign_key="film.film_id")
    category_id: int = SQLField(primary_key=True, foreign_key="category.category_id")


class Inventory(SQLModel, table=True):
    __tablename__ = "inventory"

    inventory_id: int | None = SQLField(default=None, primary_key=True)
    film_id: int = SQLField(foreign_key="film.film_id")
    store_id: int
    last_update: datetime


class Customer(SQLModel, table=True):
    __tablename__ = "customer"

    customer_id: int | None = SQLField(default=None, primary_key=True)
    store_id: int
    first_name: str
    last_name: str
    email: str | None = None
    active: bool = SQLField(default=True)
    create_date: datetime
    last_update: datetime | None = None


class Rental(SQLModel, table=True):
    __tablename__ = "rental"

    rental_id: int | None = SQLField(default=None, primary_key=True)
    rental_date: datetime
    inventory_id: int = SQLField(foreign_key="inventory.inventory_id")
    customer_id: int = SQLField(foreign_key="customer.customer_id")
    return_date: datetime | None = None
    staff_id: int
    last_update: datetime


class StreamingSubscription(SQLModel, table=True):
    __tablename__ = "streaming_subscription"

    id: int | None = SQLField(default=None, primary_key=True)
    customer_id: int = SQLField(foreign_key="customer.customer_id")
    plan_name: str
    start_date: date
    end_date: date | None = None


class FilmOut(BaseModel):
    film_id: int
    title: str
    description: str | None = None
    rating: str | None = None
    rental_rate: Decimal
    category: str | None = None
    streaming_available: bool

    @field_serializer("rental_rate")
    def serialize_rental_rate(self, value: Decimal) -> float:
        return float(value)


T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    page: int = Field(gt=0)
    page_size: int = Field(gt=0)
    total: int = Field(ge=0)


class FilmListParams(BaseModel):
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=20, gt=0, le=100)
    category: Optional[str] = Field(default=None, max_length=25)


class RentalCreate(BaseModel):
    inventory_id: int = Field(gt=0)
    staff_id: int = Field(gt=0)


class RentalCreatedResponse(BaseModel):
    rental_id: int
    status: str = "created"


class AISummaryRequest(BaseModel):
    film_id: int = Field(gt=0)


class SummaryOut(BaseModel):
    title: str
    rating: str | None = None
    recommended: bool


class AIAskResponseChunk(BaseModel):
    data: str


class AIHandoffRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AIHandoffResponse(BaseModel):
    agent: Literal["SearchAgent", "LLMAgent"]
    answer: str

import pytest
from sqlmodel import select

from domain.models import Rental
from tests.conftest import seed_base_data


@pytest.mark.asyncio
async def test_create_rental_happy_path(client, db_session):
    data = await seed_base_data(db_session)

    response = await client.post(
        f"/v1/customers/{data['customer_id']}/rentals",
        json={"inventory_id": data["inventory_id"], "staff_id": 1},
        headers={"Authorization": "Bearer dvd_admin"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "created"
    assert payload["rental_id"] > 0

    result = await db_session.execute(select(Rental).where(Rental.rental_id == payload["rental_id"]))
    rental = result.scalar_one()
    assert rental.inventory_id == data["inventory_id"]
    assert rental.customer_id == data["customer_id"]

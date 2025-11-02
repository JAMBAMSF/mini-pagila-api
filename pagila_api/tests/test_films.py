import pytest

from tests.conftest import seed_base_data


@pytest.mark.asyncio
async def test_list_films_returns_paginated_results(client, db_session):
    await seed_base_data(db_session)

    response = await client.get("/v1/films", params={"category": "Horror", "page": 1, "page_size": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 10
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    film = payload["items"][0]
    assert film["title"] == "Alien"
    assert film["category"] == "Horror"
    assert film["streaming_available"] is True

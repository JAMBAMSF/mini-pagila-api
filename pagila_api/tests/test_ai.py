import pytest

from tests.conftest import seed_base_data


@pytest.mark.asyncio
async def test_ai_ask_streams(client, db_session):
    await seed_base_data(db_session)

    async with client.stream("GET", "/v1/ai/ask", params={"question": "Hello"}) as response:
        assert response.status_code == 200
        chunks = []
        async for text in response.aiter_text():
            chunks.append(text)

    joined = "".join(chunks)
    assert "data: Hello from the test assistant." in joined


@pytest.mark.asyncio
async def test_ai_summary_json(client, db_session):
    data = await seed_base_data(db_session)

    response = await client.post("/v1/ai/summary", json={"film_id": data["film_id"]})
    assert response.status_code == 200

    payload = response.json()
    assert set(payload.keys()) == {"title", "rating", "recommended"}
    assert payload["title"] == "Alien"
    assert payload["rating"] == "R"
    assert payload["recommended"] is True


@pytest.mark.asyncio
async def test_handoff_search_agent(client, db_session):
    await seed_base_data(db_session)

    response = await client.post(
        "/v1/ai/handoff",
        json={"question": "What is the rental rate for the film Alien?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "SearchAgent"
    assert "Alien" in payload["answer"]


@pytest.mark.asyncio
async def test_handoff_llm_agent(client, db_session):
    await seed_base_data(db_session)

    response = await client.post(
        "/v1/ai/handoff",
        json={"question": "Who won the FIFA World Cup in 2022?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "LLMAgent"
    assert "Argentina won the 2022 FIFA World Cup" in payload["answer"]

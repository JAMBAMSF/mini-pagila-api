# Mini Pagila API — One‑Page Rubric Mapping

Repo: https://github.com/JAMBAMSF/mini-pagila-api
Release: v1.0

## Endpoints & Acceptance Criteria

- Films Listing (200 OK, pagination + category filter)
  - Endpoint: GET `/v1/films`
  - Implementation: `pagila_api/api/v1/film_routes.py:1`
  - Models/params: `pagila_api/domain/models.py:1`
  - DB/session: `pagila_api/core/db.py:1`
  - Evidence: README curl returns items with `page`, `page_size`, `total` and category filter applied.

- Create Rental (201 Created, bearer auth)
  - Endpoint: POST `/v1/customers/{customer_id}/rentals`
  - Implementation: `pagila_api/api/v1/rental_routes.py:1`
  - Auth: `pagila_api/core/auth.py:1` (expects `Authorization: Bearer dvd_admin`)
  - Domain flow: `pagila_api/domain/services.py:153`
  - Evidence: README curl returns `{ "rental_id": <int>, "status": "created" }`.

- AI Ask (SSE streaming)
  - Endpoint: GET `/v1/ai/ask?question=...`
  - Implementation: `pagila_api/api/v1/ai_routes.py:67` (StreamingResponse)
  - Evidence: README curl `-N` streams `data: ...` chunks.

- AI Summary (strict JSON from LLM)
  - Endpoint: POST `/v1/ai/summary`
  - Implementation: `pagila_api/api/v1/ai_routes.py:91`
  - Prompt template: `pagila_api/core/prompts/summary/prompt.skprompt:1`
  - Prompt config: `pagila_api/core/prompts/summary/config.json:1`
  - Kernel & parsing: `pagila_api/domain/services.py:169`
  - Evidence: returns `{ "title", "rating", "recommended" }` only.

- AI Handoff (SearchAgent → LLMAgent fallback)
  - Endpoint: POST `/v1/ai/handoff`
  - Implementation: `pagila_api/api/v1/ai_routes.py:114`
  - Orchestration: `pagila_api/app/agents/orchestration.py:1`
  - Agents: `pagila_api/app/agents/search_agent.py:1`, `pagila_api/app/agents/llm_agent.py:1`
  - Evidence: returns `{ "agent": "SearchAgent" | "LLMAgent", "answer": <str> }`.

## Platform & Data

- App bootstrap: `pagila_api/app/main.py:1` (lifespan, routers)
- Database: SQLModel models `pagila_api/domain/models.py:1`; Alembic env `pagila_api/migrations/env.py:1`
- SQL dataset loader: `pagila_sql/pagila-schema.sql`, `pagila_sql/pagila-data.sql`
- Config & logging: `pagila_api/core/config.py:1`, `pagila_api/core/logging.py:1`
- Semantic Kernel + OpenAI integration: `pagila_api/core/ai_kernel.py:1`, `pagila_api/domain/services.py:169`

## Tests

- Test suite: `pagila_api/tests/test_ai.py:1`, fixtures `pagila_api/tests/conftest.py:1`
- Coverage highlights: AI streaming, summary shape, handoff path, rental creation
- Command: `cd pagila_api && poetry run pytest -q` (6 passed)

## Runbook (Quickstart)

- Python 3.11 + Poetry
- Create DB: `createdb pagila`
- Load SQL: `psql -d pagila -f pagila_sql/pagila-schema.sql` and `pagila_sql/pagila-data.sql`
- Env: `cp pagila_api/.env.example pagila_api/.env` and set `OPENAI_API_KEY`
- Migrate: `cd pagila_api && poetry run alembic upgrade head`
- Run: `poetry run uvicorn app.main:app --reload` → http://127.0.0.1:8000/docs

## Notes

- No secrets in repo; use `.env.example`.
- AI endpoints require an OpenAI key; non‑AI endpoints work without it.

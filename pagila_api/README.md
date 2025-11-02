# Mini Pagila API

Async FastAPI service backed by Pagila, featuring semantic endpoints powered by Semantic Kernel.

## Highlights
- FastAPI + SQLModel (async) with vertical-slice layout.
- Alembic migrations adding `film.streaming_available` and a `streaming_subscription` table.
- Token-protected rental creation with bearer guard.
- Semantic Kernel endpoints: streaming `/v1/ai/ask`, structured JSON `/v1/ai/summary`, and Phase 2 handoff `/v1/ai/handoff`.
- Structured logging, dependency-injected async sessions, and pytest coverage for films, rentals, and AI flows.

## Prerequisites
- Python 3.12.6 (pyenv recommended)
- Poetry 1.7+
- PostgreSQL 12+ with Pagila sample data

### Python & Dependencies
```bash
pyenv install 3.12.6
pyenv local 3.12.6
poetry install
poetry shell
```

### Environment Variables
Copy the template and customise as needed:
```bash
cp .env.example .env
```
Set `DATABASE_URL`, `ADMIN_BEARER_TOKEN`, and OpenAI credentials before running the app.

## Database Setup
Restore the Pagila schema and data into a Postgres database:
```bash
createdb pagila
psql -d pagila -f /path/to/pagila-schema.sql
psql -d pagila -f /path/to/pagila-data.sql
```

Run Alembic migrations to apply the new column and table:
```bash
poetry run alembic upgrade head
```

## Running the API
```bash
poetry run uvicorn app.main:app --reload
```
The server listens on `http://localhost:8000`.

## Tests
Tests use pytest-asyncio with a disposable SQLite database and dependency overrides for Semantic Kernel:
```bash
poetry run pytest -q
```

## Example Requests
```bash
# Films
curl "http://localhost:8000/v1/films?category=Horror&page=1&page_size=10"

# Create rental (token protected)
curl -X POST http://localhost:8000/v1/customers/1/rentals \
  -H "Authorization: Bearer dvd_admin" \
  -H "Content-Type: application/json" \
  -d '{"inventory_id": 1, "staff_id": 1}'

# AI ask (streaming)
curl -N "http://localhost:8000/v1/ai/ask?question=Hello"

# AI summary (strict JSON)
curl -X POST http://localhost:8000/v1/ai/summary \
  -H "Content-Type: application/json" \
  -d '{"film_id": 1}'

# Phase 2 — handoff: SearchAgent chosen
curl -X POST http://localhost:8000/v1/ai/handoff \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the rental rate for the film Alien?"}'

# Phase 2 — handoff: LLMAgent chosen
curl -X POST http://localhost:8000/v1/ai/handoff \
  -H "Content-Type: application/json" \
  -d '{"question":"Who won the FIFA World Cup in 2022?"}'
```

## Tooling
- Pre-commit hooks: `poetry run pre-commit install`
- Linters/formatters: Ruff, Black, Mypy
- Logging: structlog (JSON in prod via `LOG_JSON=true`)

## Notes
- Semantic Kernel requires valid OpenAI API access; tests stub the kernel to avoid external calls.
- Replace the bearer token and API keys before deploying.
- Alembic metadata comes from SQLModel models; use `poetry run alembic revision --autogenerate` for future schema changes.

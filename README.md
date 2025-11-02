# mini-pagila-api

Mini Pagila API built with FastAPI + SQLModel + SQLAlchemy + Alembic, with optional AI endpoints powered by Semantic Kernel and OpenAI.

- App code: `pagila_api/`
- SQL dataset: `pagila_sql/`

## Prerequisites

- Python 3.11
- Poetry
- PostgreSQL (Postgres.app or Homebrew)
- OpenAI API key (only required for live AI endpoints)

## Setup

1) Install dependencies

- `cd pagila_api`
- `poetry install`

2) Create and load the Pagila database

- Start Postgres locally
- Create DB: `createdb pagila`
- Load schema/data (from repo root):
  - `psql -d pagila -f pagila_sql/pagila-schema.sql`
  - `psql -d pagila -f pagila_sql/pagila-data.sql`

3) Configure environment

- `cp pagila_api/.env.example pagila_api/.env`
- Edit `pagila_api/.env`:
  - `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pagila`
  - `ADMIN_BEARER_TOKEN=dvd_admin`
  - `OPENAI_API_KEY=...` (required for AI routes)
  - `OPENAI_MODEL=gpt-4o-mini`

4) Run DB migrations

- From `pagila_api/`: `poetry run alembic upgrade head`

5) Launch the API

- From `pagila_api/`: `poetry run uvicorn app.main:app --reload`
- Docs: http://127.0.0.1:8000/docs

## Quick Smoke Tests

- Films listing:
  - `curl -i "http://127.0.0.1:8000/v1/films?category=Horror&page=1&page_size=10"`
- Create rental:
  - `curl -i -X POST "http://127.0.0.1:8000/v1/customers/1/rentals" -H "Authorization: Bearer dvd_admin" -H "Content-Type: application/json" -d '{"inventory_id":1,"staff_id":1}'`
- AI ask (SSE):
  - `curl -N "http://127.0.0.1:8000/v1/ai/ask?question=Hello"`
- AI summary (JSON):
  - `curl -i -X POST "http://127.0.0.1:8000/v1/ai/summary" -H "Content-Type: application/json" -d '{"film_id":1}'`
- AI handoff:
  - `curl -i -X POST "http://127.0.0.1:8000/v1/ai/handoff" -H "Content-Type: application/json" -d '{"question":"Who won the FIFA World Cup in 2022?"}'`

## Tests

- From `pagila_api/`: `poetry run pytest -q`

## Notes

- Do not commit real secrets. Use `.env.example` as a template and keep `.env` local.
- If an OpenAI key was ever shared or committed, rotate it in the OpenAI dashboard.

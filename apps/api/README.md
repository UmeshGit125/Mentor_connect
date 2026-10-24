# Mentor Connect API

FastAPI + SQLAlchemy 2. SQLite by default, Postgres through `DATABASE_URL`. Contract: `docs/CONTRACT.md`.

## Run

```bash
cd apps/api
cp .env.example .env        # optional; export the variables or pass --env-file .env
uv sync
uv run uvicorn app.main:app --reload --env-file .env
```

The first start creates the tables, cleans `data/Mentor_Sample_50_Anonymised.xlsx`, seeds the
mentors and prints a cleaning report. Docs are at http://localhost:8000/docs. All routes are under `/api`.

For Postgres set `DATABASE_URL=postgresql://user:pass@host/db` (the driver is a normal dependency). On a serverless host set `AUTO_SETUP=0` and run `uv run python -m app.seed` once against that database instead of seeding on every cold start. Re-run it to refresh the sample slots, which cover the next 7 days.

## Live AI

Set `OPENROUTER_API_KEY` to use an OpenRouter model for intake, match reasons, briefs and write-ups
(`OPENROUTER_MODEL`, default `openai/gpt-4o-mini`; `USE_LIVE_AI=0` forces the fallback).
`GET /api/health` then reports `"ai": "live"`, otherwise `"fallback"`. If a model call fails for
any reason, that one step uses the deterministic implementation, so students never see an AI error.

## Seed

```bash
uv run python -m app.seed   # safe to repeat: upserts mentors, tops up sample slots, prints the report
```

Slots are sample data generated per mentor for the next 7 days (`app/data/slots.py`).

## Test and lint

```bash
uv run pytest
uv run ruff check
```

## Layout

- `app/data/clean.py`: sheet cleaning. Email, Contact and LinkedIn are never read.
- `app/ai/`: `interface.py` Protocols, deterministic `fake.py`, and `live.py` (OpenRouter, prompts in `prompts.py`, write-up quote check in `verify_writeup.py`).
- `app/matching/`: `retrieve.py` scores mentors, `verify.py` drops any reason not backed by the row.
- `app/services/`: chat, bookings (atomic slot claim) and admin summary.

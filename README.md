# Mentor Connect

A student describes a career problem in a chat. The assistant recommends up to 3 mentors from a fixed list of 50 and explains each pick using only fields from the mentor sheet. The student books a slot and the call happens outside the app. The mentor closes the call and pastes notes. The student gets a write-up (discussed, work on, next steps), and the Mesa team sees the whole funnel in an admin page.

Built for students in India early in their careers, often on a phone. The core idea is **evidence first**: every recommendation reason shows the field name and the exact value from the sheet (for example "Sector: Fintech"). Blank fields show as "Not stated" and are never guessed.

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Data model](#data-model)
- [How matching works](#how-matching-works)
- [Testing](#testing)
- [Deployment](#deployment)
- [Known limits](#known-limits)
- [Documentation](#documentation)

## Features

| Area | What it does |
|---|---|
| Chat intake | Asks up to 3 clarifying questions, then returns matches or `no_match`. Redirects off-topic and sensitive messages. |
| Evidence-based matching | Deterministic scoring over the mentor sheet. A verifier drops any model output whose mentor id or cited value is not in the row. |
| Browse | Filterable mentor list and profile pages. |
| Booking | Slot picker, atomic slot claim, caps of 3 active bookings per student and 5 per mentor per week. |
| Mentor link | Private per-booking link where the mentor closes the call (completed or no-show) and adds notes. |
| Write-ups | Notes become a structured write-up. Never generated from empty notes. |
| Admin | Password-gated funnel, bookings by status, stuck bookings, unmatched problems, mentor load. |
| Contact form | Public form, rate limited to 5 per 10 minutes per IP. |
| AI with fallback | Live model through OpenRouter. Any failed step falls back to the deterministic implementation, so students never see an AI error. |
| Privacy | Email, phone and LinkedIn are never read from the sheet and never appear in a response or prompt. |

## Architecture

```
 Student / Mentor / Admin (browser)
              │
              ▼
   ┌─────────────────────┐        HTTPS, JSON         ┌──────────────────────────────┐
   │  apps/web           │ ─────────────────────────► │  apps/api                    │
   │  Next.js 15 (React) │   <NEXT_PUBLIC_API_URL>    │  FastAPI                     │
   │  App Router, TS     │ ◄───────────────────────── │                              │
   │  Tailwind v4        │                            │  routers → services          │
   └─────────────────────┘                            │      │          │            │
      (mock mode: typed fixtures,                     │      ▼          ▼            │
       no backend needed)                             │  matching/   ai/ (interfaces)│
                                                      │  retrieve    fake  │  live   │
                                                      │  verify            │         │
                                                      └──────┬─────────────┼─────────┘
                                                             │             │
                                                             ▼             ▼
                                              SQLite (dev) / Postgres   OpenRouter
                                              (prod, Neon) via          (optional)
                                              SQLAlchemy 2
                                                             ▲
                                              Mentor_Sample_50_Anonymised.xlsx
                                              cleaned and seeded by app.seed
```

### Components

| Component | Location | Responsibility |
|---|---|---|
| Web app | `apps/web` | UI for students, mentors and admins. Calls the API at `<NEXT_PUBLIC_API_URL>/api`. |
| API | `apps/api/app` | Business rules, validation, booking, admin summary. One Vercel Function in production. |
| Routers | `apps/api/app/routers` | HTTP layer for mentors, students, chat, bookings, mentor link, admin, contact. |
| Services | `apps/api/app/services` | Chat flow, bookings (atomic slot claim), admin summary. |
| Matching | `apps/api/app/matching` | `retrieve.py` scores mentors, `verify.py` drops reasons not backed by the row, `vocabulary.py` builds tags from the mentor table. |
| AI seam | `apps/api/app/ai` | Protocols in `interface.py`, deterministic `fake.py`, live `live.py` + `openrouter.py`, prompts, write-up quote check. |
| Data cleaning | `apps/api/app/data` | `clean.py` normalises the sheet, `slots.py` generates sample slots. |
| Database | `apps/api/app/db.py`, `models.py` | SQLAlchemy 2 models. SQLite in dev, Postgres via `DATABASE_URL`. |

### The AI seam

All model calls sit behind four Protocols in `app/ai/interface.py`:

| Interface | Job |
|---|---|
| `IntakeAnalyzer` | Reads the student's messages and returns a verdict (`ok`, `vague`, `off_topic`, `sensitive`) and a `Need`. |
| `MatchExplainer` | Writes 1 to 3 reasons per candidate mentor. |
| `BriefWriter` | Writes the problem brief shown to the mentor. |
| `WriteupWriter` | Turns mentor notes into discussed / work on / next steps. |

Model output is untrusted until it passes verification. `GET /api/health` reports `"ai": "live"` or `"ai": "fallback"`.

### Request flow

1. Student signs in with name and email (`POST /students`, then sends `X-Student-Id`).
2. `POST /chat`: intake analysis → deterministic retrieval of up to 8 candidates → explainer → verifier → up to 3 `Match` results.
3. `POST /bookings`: atomically claims the slot, writes the brief, issues a private mentor token.
4. Mentor opens `/m/{token}` and closes the call with optional notes.
5. Notes go to the write-up writer. The student reads the write-up under `/sessions/{id}`.
6. `GET /admin/summary` aggregates the funnel.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript 5, Tailwind CSS v4, `next/font` |
| Backend | Python 3.12+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, httpx, openpyxl |
| Database | SQLite (dev), Postgres on Neon (prod, via `psycopg`) |
| AI | OpenRouter (default model `openai/gpt-4o-mini`), deterministic fallback |
| Tooling | `uv`, pytest, Ruff, ESLint, Playwright |
| Hosting | Vercel (two projects), Neon |

## Repository layout

```
mentor-connect/
├── apps/
│   ├── api/                  FastAPI service
│   │   ├── app/              routers, services, matching, ai, data, models, config
│   │   ├── data/             Mentor_Sample_50_Anonymised.xlsx (bundled with the deploy)
│   │   ├── evals/            scripted conversations against the real model
│   │   ├── tests/            pytest suite
│   │   └── pyproject.toml
│   └── web/                  Next.js app
│       ├── src/app/          routes
│       ├── src/components/   UI components
│       ├── src/lib/          API client, types, helpers
│       ├── src/mocks/        typed fixtures for mock mode
│       ├── e2e/              Playwright tests
│       └── TESTIDS.md        test id reference
├── data/                     source mentor sheet
├── docs/                     CONTRACT, DEPLOY, DESIGN, BUILD_RULES, REDESIGN_PLAN
├── neon.ts                   Neon branch policy
└── package.json
```

### Web routes

| Route | Purpose |
|---|---|
| `/` | Chat with example problems |
| `/mentors`, `/mentors/[id]` | Browse and filter, mentor profile with slots |
| `/book/[mentorId]` | Slot picker and confirmation |
| `/sessions`, `/sessions/[id]` | Student bookings with status pills, booking detail and write-up |
| `/m/[token]` | Mentor page: brief, time, close call, notes |
| `/admin` | Password gate, funnel and operations view |
| `/signin`, `/contact`, `/faqs`, `/privacy`, `/terms` | Supporting pages |

## Getting started

### Prerequisites

- Node.js 20+ and npm
- Python 3.12 to 3.14 and [`uv`](https://docs.astral.sh/uv/)

### 1. Run the API

```bash
cd apps/api
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --env-file .env
```

The first start creates the tables, cleans the mentor sheet, seeds the mentors and prints a cleaning report. Interactive docs are at http://localhost:8000/docs. All routes are under `/api`.

### 2. Run the web app

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev            # http://localhost:3000
```

`.env.example` sets `NEXT_PUBLIC_USE_MOCKS=1`, which runs the UI on fixtures with no backend. To use the real API, remove that line (or leave it empty) and keep `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### Mock mode

| Trigger | Result |
|---|---|
| Chat message under 5 words | `clarify` (max 3 times) |
| "poem", "joke", "weather" | `redirect` |
| "depressed", "hopeless" | sensitive `redirect` |
| "astronaut", "plumber" | `no_match` |
| Anything else | `matches` (keywords like product, data, fintech, marketing pick mentors) |
| First slot on the first day | `slot_taken` |
| Mentor `M007` | `mentor_cap_reached` |
| 4th active booking | `booking_cap_reached` |

Mock admin password: `mesa-admin`. Mock data persists in localStorage under `mc_mock_db`.

## Configuration

### API (`apps/api/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./mentor_connect.db` | SQLAlchemy URL. Use `postgresql://user:pass@host:5432/db` for Postgres. |
| `ADMIN_PASSWORD` | `change-me` | Sent as `X-Admin-Password`. **Change it outside local dev.** |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins. |
| `OPENROUTER_API_KEY` | empty | Enables live AI. Empty means deterministic fallback. |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model used for live AI. |
| `USE_LIVE_AI` | `1` | `0` forces the fallback even when a key is set. |
| `AUTO_SETUP` | `1` | Create tables and seed at startup. Set `0` on serverless and seed once instead. |
| `MENTORS_XLSX` | bundled sheet | Path to an alternative mentor sheet. |

### Web (`apps/web/.env.local`)

| Variable | Default | Meaning |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL. The app appends `/api`. |
| `NEXT_PUBLIC_USE_MOCKS` | unset | `1` runs on fixtures in `src/mocks`. |

`NEXT_PUBLIC_*` values are baked in at build time. Never commit secrets. `.env`, `.env.local` and database files are git-ignored.

### Seeding

```bash
cd apps/api
uv run python -m app.seed   # safe to repeat: upserts mentors, tops up sample slots
```

Sample slots cover the next 7 days, so re-run this before a demo.

## API reference

Base path `/api`. JSON in and out, times are ISO 8601 UTC. The full types are in [`docs/CONTRACT.md`](docs/CONTRACT.md), which is the source of truth for both apps.

| Method and path | Auth | Purpose |
|---|---|---|
| `GET /health` | none | `{ ok, ai: "live" \| "fallback" }` |
| `GET /mentors` | none | List mentors. Query: `q`, `domain`, `sector`, `city`. |
| `GET /mentors/{id}` | none | One mentor. |
| `GET /mentors/{id}/slots` | none | Open slots in the next 7 days. |
| `POST /students` | none | Create or return a student (idempotent on email). |
| `POST /chat` | `X-Student-Id` | Send a message, get a `ChatReply`. |
| `GET /chat/{session_id}` | none | Conversation history. |
| `POST /bookings` | `X-Student-Id` | Book a slot. |
| `GET /bookings`, `GET /bookings/{id}` | `X-Student-Id` | The student's bookings. |
| `POST /bookings/{id}/cancel` | `X-Student-Id` | Cancel a `confirmed` booking and free the slot. |
| `GET /bookings/{id}/writeup` | `X-Student-Id` | Write-up for a booking. |
| `GET /m/{token}` | mentor token | Mentor view of a booking. |
| `POST /m/{token}/close` | mentor token | Close as `completed` or `no_show`, with optional notes. |
| `POST /m/{token}/notes` | mentor token | Add notes to a completed booking. |
| `POST /contact` | none | Public contact form. |
| `GET /admin/summary` | `X-Admin-Password` | Funnel and operations summary. |

### Error shape

```json
{ "error": { "code": "slot_taken", "message": "That slot was just booked. Pick another time." } }
```

| Code | Status |
|---|---|
| `validation_error` | 422 |
| `unauthorized` | 401 |
| `not_found` | 404 |
| `slot_taken`, `booking_cap_reached`, `mentor_cap_reached`, `invalid_state` | 409 |
| `rate_limited` | 429 (contact form) |
| `ai_unavailable` | 503 (only when the fallback also failed) |

## Data model

| Table | Key fields |
|---|---|
| `mentors` | `id`, `name`, `city`, `domain`, `company`, `sector`, `sectors[]`, `roles[]`, `seniority`, `built_ai`, `ai_tools[]`, `tools{}`, `quality`, `activities` |
| `students` | `id`, `name`, `email` (unique) |
| `chat_sessions` | `student_id`, `clarify_count`, `last_kind`, `ever_matched`, `need`, `last_reply` |
| `messages` | `session_id`, `role`, `text` |
| `slots` | `mentor_id`, `start`, `end`, `status` (unique on mentor and start) |
| `bookings` | `student_id`, `mentor_id`, `slot_id`, `session_id`, `status`, `brief`, `mentor_token` (unique) |
| `writeups` | `booking_id` (unique), `notes`, `status`, `discussed[]`, `work_on[]`, `next_steps[]` |
| `contact_messages` | `name`, `email`, `message` |

Booking status: `confirmed`, `completed`, `no_show`, `cancelled`. Write-up status: `none`, `notes_received`, `ready`.

## How matching works

1. **Intake**: classify the message as `ok`, `vague`, `off_topic` or `sensitive`, and extract a `Need` (domains, sectors, tools, wants AI). Tags come only from the vocabulary built from the mentor table.
2. **Retrieve**: score every mentor by weighted overlap with the need (domain 3.0, sector 2.0, role or sector list 1.5, tools and AI tools 1.0, small bonus for `Excellent` or `Good` quality) and keep the top 8.
3. **Explain**: the explainer returns 1 to 3 reasons per mentor.
4. **Verify**: drop any reason whose field is null or whose value differs from the stored row, and any mentor id not in the sheet.
5. **Respond**: up to 3 matches, or `clarify`, `no_match`, `redirect`.

Behaviours covered by tests: gibberish and unsupported niches return `no_match`, vague input returns `clarify`, duplicate sheet rows (M013, M023) appear once, and contact details never leak.

## Testing

```bash
# API
cd apps/api
uv run pytest
uv run ruff check

# Web
cd apps/web
npm run lint
npm run build

# End to end (Playwright, mock mode by default)
cd apps/web/e2e
npm install
npm run install:browsers
npm test

# End to end against a running API
REAL_API=1 API_URL=http://localhost:8000 npm test

# Scripted conversations against the real model (needs OPENROUTER_API_KEY)
cd apps/api
uv run python evals/run_evals.py
```

## Deployment

Two Vercel projects from this repo plus a Neon Postgres database.

| Project | Root directory | Notes |
|---|---|---|
| `mentor-connect-web` | `apps/web` | Next.js. Set `NEXT_PUBLIC_API_URL` and do **not** set `NEXT_PUBLIC_USE_MOCKS`. |
| `mentor-connect-api` | `apps/api` | One Vercel Function (`app/main.py`, up to 60 s). Set `DATABASE_URL`, `ADMIN_PASSWORD`, `ALLOWED_ORIGINS`, `AUTO_SETUP=0`, and optionally `OPENROUTER_API_KEY`. |

Order: seed the database once, deploy the API, deploy the web app, then set `ALLOWED_ORIGINS` on the API to the web URL and redeploy. Full steps, smoke test and troubleshooting are in [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Known limits

- Booking caps can be exceeded by simultaneous requests on Postgres. Slot claiming itself is atomic.
- The mentor link is returned to the student as a demo stand-in for email, so a student can close their own call.
- Sample slots run out after 7 days. Re-run the seed.
- The first request after a quiet period is slow (cold start).
- Audio upload is a disabled "Coming soon" option.
- The deploy steps in `docs/DEPLOY.md` have not been verified against a live Vercel project.

## Documentation

| File | Content |
|---|---|
| [`docs/CONTRACT.md`](docs/CONTRACT.md) | API contract and types (source of truth) |
| [`docs/DEPLOY.md`](docs/DEPLOY.md) | Vercel and Neon deployment guide |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Design brief, tokens, pages |
| [`docs/BUILD_RULES.md`](docs/BUILD_RULES.md) | Rules for contributors and agents |
| [`docs/REDESIGN_PLAN.md`](docs/REDESIGN_PLAN.md) | Redesign plan |
| [`apps/web/TESTIDS.md`](apps/web/TESTIDS.md) | Test id reference |

## Contributing

Read [`docs/CONTRACT.md`](docs/CONTRACT.md) first. Change it only by adding to it and noting the change in its log. Keep the non-negotiables from [`docs/BUILD_RULES.md`](docs/BUILD_RULES.md): no invented mentor data, no contact details in responses or prompts, validated input, contract-shaped errors, no secrets in the repo.

# Build rules for every agent

Read `docs/CONTRACT.md` first. It is the only agreement between the API and the web app.

## Product in one paragraph

Mentor Connect: a student describes a career problem in a chat, the assistant recommends up to 3 mentors from a fixed list of 50 (`data/Mentor_Sample_50_Anonymised.xlsx`) and explains why using only fields from that sheet, the student books a slot, the call happens outside the app, the mentor closes the call and pastes notes, the student gets a write-up (discussed, work on, next steps), and the Mesa team sees a funnel in an admin page. Audio upload is a disabled "Coming soon" option.

## Who owns what

| Directory | Owner | Others may |
|---|---|---|
| `apps/api/` (not `tests/`) | api-builder | read |
| `apps/api/tests/` | test-writer | read |
| `apps/web/` (not `e2e/`) | web-builder | read |
| `apps/web/e2e/` | test-writer | read |
| `docs/CONTRACT.md` | anyone, additive only, log the change at the bottom | |

Never edit another owner's files. If you need a change there, write it in your final report.

## Stack

- API: Python, FastAPI, SQLAlchemy 2, Pydantic v2, SQLite in dev and Postgres in production (read `DATABASE_URL`). Code must run on Python 3.11 to 3.15. Manage with `uv` (installed) inside `apps/api`.
- Web: Next.js (App Router, TypeScript), Tailwind. Deploys on Vercel. Node 26 and npm are installed.
- The web app calls the API at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## The AI seam

All model calls sit behind interfaces in `apps/api/app/ai/interface.py`: `IntakeAnalyzer`, `MatchExplainer`, `BriefWriter`, `WriteupWriter`. This phase ships only `Fake*` implementations: deterministic, no network, based on keyword and tag overlap. A live Claude implementation is added later, so do not call any LLM API. `GET /health` reports `"ai": "fallback"` for now. The deterministic retrieval and the verifier (drop any model output whose mentor id or cited field value is not in the row) are real code, built now.

## Non-negotiables

1. No invented mentor data. Blank sheet fields are `null`, never guessed.
2. Never expose email, phone or LinkedIn in a response or prompt.
3. Handle every edge case in the PRD table (vague problem, no match, off-topic or sensitive, slot taken, double close, empty notes, caps, duplicate rows).
4. Validate all input. Return the contract error shape, never a stack trace.
5. No secrets in the repo. Use `.env.example`.
6. Keep code plain and commented where non-obvious. No dead code, no unused dependencies.

## Definition of done

- API: `uv run pytest` passes, `uv run ruff check` is clean, server starts with `uv run uvicorn app.main:app`.
- Web: `npm run build` and `npm run lint` pass.
- A short report listing what was built, how to run it, what is missing, and any contract change.

# Deploying Mentor Connect on Vercel

Two Vercel projects from one folder, plus a Neon Postgres database.

| Project | Root directory | What it is |
|---|---|---|
| `mentor-connect-web` | `apps/web` | Next.js app |
| `mentor-connect-api` | `apps/api` | FastAPI app, one Vercel Function (entrypoint `app/main.py`, up to 60 s per request, set in `apps/api/vercel.json`) |

Why a real database: Vercel Functions do not keep local files between runs, so the SQLite file used in development would lose every booking. SQLAlchemy reads `DATABASE_URL`, so the same code runs on Postgres.

## What you need

- A Vercel account (free is enough for a prototype).
- A Postgres database. Easiest: in the Vercel dashboard open Storage, then add Neon. Or create one at neon.tech. Copy the connection string.
- An OpenRouter API key (optional: without it the app runs on the no-AI matcher and `/api/health` says `"ai": "fallback"`).
- A strong admin password you choose.

Never paste keys into chat or commit them. Add them with `vercel env add`, which prompts for the value.

## Steps

All commands run from `mentor-connect/`. The CLI runs through `npx`, nothing to install.

### 1. Log in

```bash
npx vercel login
```

### 2. Seed the database once

Seeding on every cold start can race on a shared database, so production sets `AUTO_SETUP=0` and you seed from your machine:

```bash
cd apps/api
DATABASE_URL='postgresql://...your Neon string...' uv run python -m app.seed
```

This creates the tables, loads the 50 cleaned mentors and adds sample slots for the next 7 days. The slots are sample data and run out after a week, so run the same command again before the demo or recording.

### 3. Deploy the API

```bash
cd apps/api
npx vercel link            # create the project, name it mentor-connect-api
npx vercel env add DATABASE_URL production
npx vercel env add ADMIN_PASSWORD production
npx vercel env add OPENROUTER_API_KEY production      # optional
npx vercel env add AUTO_SETUP production              # enter 0
npx vercel env add ALLOWED_ORIGINS production         # enter a placeholder for now, fixed in step 5
npx vercel deploy --prod
```

Check it: `curl https://<api-url>/api/health` should return `{"ok":true,"ai":"live"}` (or `"fallback"` with no key), and `curl https://<api-url>/api/mentors` should list 50 mentors.

### 4. Deploy the web app

`NEXT_PUBLIC_*` values are baked in at build time, so set them before deploying:

```bash
cd apps/web
npx vercel link            # name it mentor-connect-web
npx vercel env add NEXT_PUBLIC_API_URL production     # https://<api-url>  (no trailing slash, no /api)
npx vercel deploy --prod
```

Do not set `NEXT_PUBLIC_USE_MOCKS`. The local `.env.local` that turns mocks on is excluded by `apps/web/.vercelignore`.

### 5. Allow the web origin on the API

```bash
cd apps/api
npx vercel env rm ALLOWED_ORIGINS production
npx vercel env add ALLOWED_ORIGINS production         # https://<web-url>
npx vercel deploy --prod
```

### 6. Smoke test the live site

1. Open the web URL, sign in, describe a fintech product problem, see up to 3 matches.
2. Book a slot, copy the demo mentor link, open it, close the call as completed with a few lines of notes.
3. Back as the student, open the session and read the write-up.
4. Open `/admin`, enter your admin password, check the funnel moved.
5. Send a gibberish message and a self-harm style message. Expect no mentor cards.

## Known limits

- The booking caps (3 active per student, 5 per mentor per week) can be exceeded by simultaneous requests on Postgres. Slot claiming itself is atomic.
- The mentor link is returned to the student as a demo stand-in for email, so a student can close their own call.
- The first request after a quiet period is slow (cold start).
- A deploy of the API bundles the mentor sheet from `apps/api/data/`. Replace that file to change the mentor list, then run the seed again.
- I read Vercel's FastAPI and Python docs while preparing this. Nothing has been deployed from this machine yet, so every step above is untested against a live project.

## If something fails

- `/api/health` 500: open the function logs in the Vercel dashboard. The usual cause is a wrong `DATABASE_URL` or tables missing because step 2 was skipped.
- Web shows network errors in the browser console: `ALLOWED_ORIGINS` does not match the web URL exactly (scheme and host, no trailing slash).
- Web shows demo data: the build ran with mocks on. Check `NEXT_PUBLIC_USE_MOCKS` is not set in the Vercel project, and redeploy.

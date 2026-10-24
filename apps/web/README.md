# Mentor Connect web

Next.js (App Router, TypeScript, Tailwind v4). Fonts via `next/font`.

## Run

```
npm install
cp .env.example .env.local
npm run dev        # http://localhost:3000
npm run build && npm run lint
```

## Env vars

| Name | Default | Meaning |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI base URL; the app calls `<url>/api/...` |
| `NEXT_PUBLIC_USE_MOCKS` | unset | `1` runs on fixtures in `src/mocks`, no backend needed |

## Mock mode triggers

- Chat: fewer than 5 words gives clarify (3 times max); "poem", "joke", "weather" gives redirect; "depressed", "hopeless" gives a sensitive redirect; "astronaut", "plumber" gives no_match; anything else gives matches (keywords such as product, data, fintech, marketing pick the mentors).
- Booking: the first slot on the first day is `slot_taken`; mentor M007 gives `mentor_cap_reached`; a 4th active booking gives `booking_cap_reached`.
- Admin password: `mesa-admin`. Mock data persists in localStorage key `mc_mock_db`.

Test ids are listed in `TESTIDS.md`. Student id is in localStorage (`mc_student`); the admin password only in sessionStorage.

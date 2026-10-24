# Mentor Connect: API contract (v1)

Source of truth for `apps/api` (FastAPI) and `apps/web` (Next.js). Change it only by adding to it and noting the change at the bottom. All paths are under `/api`. JSON in and out. Times are ISO 8601 UTC.

## Errors

Every error uses one shape and the right HTTP status:

```json
{ "error": { "code": "slot_taken", "message": "That slot was just booked. Pick another time." } }
```

Codes: `validation_error` (422), `not_found` (404), `unauthorized` (401), `slot_taken` (409), `booking_cap_reached` (409), `mentor_cap_reached` (409), `invalid_state` (409), `ai_unavailable` (503, only when the fallback also failed), `rate_limited` (429, contact form only).

## Types

```ts
type PublicMentor = {
  id: string                 // "M013"
  name: string
  city: string | null        // normalised, "Bengaluru", null if unknown
  domain: string             // normalised, e.g. "Product Management"
  company: string | null
  sector: string | null      // Master Sector
  sectors: string[]          // Sectors of Expertise, split and normalised
  roles: string[]            // Roles of Expertise, split
  seniority: "Mid-career" | "Senior" | null
  built_ai: boolean | null
  ai_tools: string[]
  tools: { tableau: boolean|null, hubspot: boolean|null, google_analytics: boolean|null, jira: boolean|null, excel: boolean|null, mixpanel: boolean|null }
  quality: "Excellent" | "Good" | null
  activities: number | null
}
// NEVER include email, phone (Contact) or LinkedIn in any response or any model prompt.

type Reason = { field: string; value: string; text: string }
// field is a PublicMentor key (e.g. "sector"), value is the exact value from the row, text is one short sentence.
// A reason may only cite a field that is non-null on that mentor.

type Match = { mentor: PublicMentor; reasons: Reason[] }  // 1 to 3 reasons

type Need = { summary: string; domains: string[]; sectors: string[]; tools: string[]; wants_ai: boolean }

type ChatReply = {
  session_id: string
  kind: "clarify" | "matches" | "no_match" | "redirect"
  message: string               // assistant text shown to the student
  matches: Match[]              // 1 to 3 when kind = "matches", else []
  need: Need | null
}

type Slot = { id: string; mentor_id: string; start: string; end: string; status: "open" | "booked" }

type BookingStatus = "confirmed" | "completed" | "no_show" | "cancelled"
type WriteupStatus = "none" | "notes_received" | "ready"

type Booking = {
  id: string; student_id: string; mentor: PublicMentor; slot: Slot
  status: BookingStatus; brief: string       // problem brief shown to the mentor
  created_at: string; writeup_status: WriteupStatus
  mentor_token: string | null   // DEMO ONLY: the private mentor link token. Returned in the POST /bookings response and in the owning student's own booking views, null everywhere else (admin, mentor page, lists of other students). In production it would be emailed to the mentor, but the sheet only has placeholder emails.
}

type Writeup = {
  status: WriteupStatus
  discussed: string[]; work_on: string[]; next_steps: string[]   // empty unless status = "ready"
}
```

## Endpoints

| Method and path | Body | Returns | Notes |
|---|---|---|---|
| GET `/health` | | `{ "ok": true, "ai": "live" or "fallback" }` | |
| GET `/mentors` | query: `q`, `domain`, `sector`, `city` | `PublicMentor[]` | Browse view. |
| GET `/mentors/{id}` | | `PublicMentor` | 404 `not_found` |
| POST `/students` | `{ name, email }` | `{ id, name, email }` | Idempotent on email. Client then sends header `X-Student-Id`. |
| POST `/chat` | `{ session_id?: string, message: string }` + `X-Student-Id` | `ChatReply` | Max 3 clarify turns per session, then must return matches or no_match. Message 1 to 2000 chars. |
| GET `/chat/{session_id}` | | `{ messages: {role: "student"|"assistant", text: string}[], last: ChatReply or null }` | |
| GET `/mentors/{id}/slots` | | `Slot[]` open slots in the next 7 days | Seeded sample data. |
| POST `/bookings` | `{ mentor_id, slot_id, session_id? }` (empty string or missing = booked from the browse page, brief is then "Booked without a chat") + `X-Student-Id` | `Booking` (201) | Errors: `slot_taken`, `booking_cap_reached` (3 active per student), `mentor_cap_reached` (5 per mentor per week). The brief is written from the chat. |
| GET `/bookings` | | `Booking[]` for the student | |
| GET `/bookings/{id}` | | `Booking` | |
| POST `/bookings/{id}/cancel` | | `Booking` | Only from `confirmed`, frees the slot. |
| GET `/bookings/{id}/writeup` | | `Writeup` | |
| GET `/m/{token}` | | `{ booking: Booking, student_name: string }` | Mentor private link. Token is per booking, unguessable. |
| POST `/m/{token}/close` | `{ outcome: "completed" or "no_show", notes?: string }` | `Booking` | Only from `confirmed`. Notes 0 to 8000 chars. Completed with notes sets writeup_status to `ready` (or `notes_received` while generating). No notes: stays `none`. |
| POST `/m/{token}/notes` | `{ notes: string }` | `Booking` | Add notes later to a completed booking. |
| POST `/contact` | `{ name, email, message }` (message 1 to 4000 chars) | `{ id, status: "received" }` (201) | Public contact form. 422 `validation_error`, 429 `rate_limited` (5 per 10 minutes per IP). |
| GET `/admin/summary` | header `X-Admin-Password` | see below | 401 `unauthorized` |

```ts
type AdminSummary = {
  funnel: { chats_started: number; matched: number; booked: number; completed: number; writeups_ready: number; rebooked: number }
  bookings_by_status: Record<BookingStatus, number>
  stuck: Booking[]                       // confirmed, slot ended more than 2 days ago
  unmatched: { id: string; created_at: string; summary: string }[]   // chats that ended in no_match
  mentor_load: { mentor_id: string; name: string; active: number; completed: number }[]
}
```

## Behaviour that tests will check

- Chat never returns a mentor id that is not in the sheet. Reasons only cite non-null fields with the exact stored value.
- Emails, phones and LinkedIn URLs never appear in any response.
- Booking a taken slot returns 409 `slot_taken` and does not change state. Two parallel bookings for one slot: exactly one succeeds.
- Closing a booking twice returns 409 `invalid_state`.
- A write-up is never generated from empty or whitespace-only notes.
- Duplicate sheet rows (M013, M023) appear once in `/mentors`.

- Every mentor has at least 6 open slots in the next 7 days (seeded sample data), so cap tests are reachable.
- `rebooked` in the admin funnel counts bookings where the student already had a completed booking with the same mentor.
- The chat must treat gibberish (for example "asdkjh qweoiu") and an unsupported niche (for example "deep sea welder") as `no_match`, and "help with my career" as `clarify`.

## Changes log

- v1: initial.
- v1.2: `session_id` on POST /bookings is optional and an empty string is accepted.
- v1.1: added `Booking.mentor_token` (demo only), minimum 6 open slots per mentor, defined `rebooked`, listed chat triggers.

# Design brief for apps/web

Follow the `frontend-design` skill process (plan, review against the brief, build, critique), then check the result against the `web-design-guidelines` skill and the `vercel-react-best-practices` skill (Next.js and React performance rules: no waterfalls, direct imports, server components by default, `next/dynamic` for heavy parts, `next/font`).

## Subject

Students in India early in their careers, often unsure, often on a phone. The page has one job: get from "I'm stuck" to a booked call without feeling like a form. Trust is the main feeling to build, because the product's promise is that every recommendation is real.

## Idea: evidence first

The memorable moment is the mentor recommendation. Each reason is a row that shows the field name and the exact value from the mentor sheet (for example "Sector: Fintech"). Fields the sheet leaves blank appear as "Not stated" in a dashed outline, never hidden and never guessed. Everything else on the page stays quiet so this moment carries the brand.

## Tokens (start here, adjust with reasons)

- Colors: ink `#12161F`, paper `#F5F6F8`, surface `#FFFFFF`, cobalt `#2442E6` (actions), signal green `#12805C` (value confirmed from the sheet), marigold `#F0B429` (needs attention, stuck, no-show). Neutrals lean slightly cool. Light theme first. Contrast must pass AA.
- Type: Bricolage Grotesque for headlines (tight, medium weight), Instrument Sans for body, tabular numerals for times and counts. Sentence case everywhere. No all-caps labels, no eyebrow labels above headings, no numbered markers except real sequences.
- Shape: one radius for controls, a larger one for the recommendation card, hairline borders instead of shadows.
- Layout: left aligned. Desktop chat page is two columns: conversation on the left, a "Mentors for you" panel on the right that fills as matches arrive. Mobile stacks and the panel becomes a sheet under the last message. Lines under 70 characters.
- Motion: one moment only, the match cards settling in after the assistant replies. Everything else answers a click. Respect `prefers-reduced-motion`.

## Patterns borrowed from competitors (from help pages and reviews, not seen visually)

- ADPList: mentor cards in a filterable grid. Use for a secondary "Browse all mentors" page.
- GrowthMentor: three recommendations with a reason each. This is our core result.
- MentorCruise: clear status labels on every booking. Use status pills with a plain word, never color alone.
- Calendly-style slot picker: day tabs, time buttons, local time shown with time zone.

## Pages

1. `/` chat, with a short intro and a row of example problems the student can tap.
2. `/mentors` browse and filter, `/mentors/[id]` profile with slots.
3. `/book/[mentorId]` slot picker and confirmation.
4. `/sessions` the student's bookings with status pills, `/sessions/[id]` booking detail with write-up (or "No write-up yet" and a clear reason).
5. `/m/[token]` mentor page: brief, time, close as completed or no-show, notes box with a disabled "Upload audio, coming soon" option next to it.
6. `/admin` password gate, funnel, bookings by status, stuck bookings, unmatched problems, mentor load. Marigold marks anything that needs a human.

Every screen needs a designed empty state, loading state and error state. Errors say what happened and what to do next, with no apology.

## Data while the API is unfinished

Build against typed fixtures in `apps/web/src/mocks/` that match `docs/CONTRACT.md`, switched by `NEXT_PUBLIC_USE_MOCKS=1`. Switch to the real API when `apps/api` is ready.

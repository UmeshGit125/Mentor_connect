# Redesign plan: Connect Mentor look (green, Poppins, white)

Source of truth for the look: `docs/reference/spec.txt` (text of the user's design spec) and the screenshots `docs/reference/image1.jpg` to `image11.jpg`. This plan **replaces** the earlier coral/Urbanist/dark-card theme (`Docs/design.md`). Read both reference files first, and look at every image before writing CSS.

## Decisions already made (do not re-ask)
- Same visual system as the reference: Poppins, emerald green `#0DBB7C`, white canvas, charcoal ink, thin borders, small radius, very soft shadows. Tokens are in section 1 of the spec.
- **Skip Blogs and Jobs.** No nav items, routes or footer links for them.
- Desktop first, but keep it usable at phone width (hamburger header, single column).
- Product behaviour does not change. Chat matching, evidence cards, booking, sessions, mentor link `/m/[token]` and `/admin` keep working, and every `data-testid` in `apps/web/TESTIDS.md` stays.
- Do not copy the source site's logo, photos or text. Use our own wordmark ("Mentor Connect" with a simple green mark). Mentor "photos" are initials avatars, because the sheet has no photos.
- `docs/BUILD_RULES.md` non-negotiables still apply: **no invented mentor data** (no fake experience years, attendance %, countries, verified badges, ratings); blank fields show "Not stated" or are omitted; never show email, phone or LinkedIn.

## Scope: `apps/web` only (plus one small additive API endpoint, see step 6)
Do not edit `apps/api` except step 6, and `docs/CONTRACT.md` only additively with a log line.

## Steps

### 1. Tokens and fonts
- `src/app/globals.css`: replace the `@theme` tokens with the spec palette (`brand #0DBB7C`, `brand-bright #17CE85`, `ink #272C32`, `muted #636B75`, `surface #fff`, `surface-muted #F7F8F8`, `border #E4E9E8`, `mint #E9F9F2`, `alert #D90016`), radius 6px for cards and 8px for controls, shadow `0 10px 35px rgba(20,35,51,.04)`, container 1180px.
- `layout.tsx`: load Poppins (400/500/600/700) via `next/font/google`, drop Urbanist and Inter.
- Keep the existing token **names** where components already use them (`ink`, `paper`, `surface`, `line`, `muted`, `signal`, `cobalt` as the accent) only if that avoids touching many files; otherwise rename and update usages. Remove the `.dark-card` theme and the coral and pill styles.
- Buttons: primary = solid green, white text, 44-48px tall, 8px radius; ghost = 1px border, ink text, green on hover. Inputs: 1px border, 8px radius, 44-52px tall, visible green focus ring.

### 2. Shared chrome
- `SiteHeader` (in `layout.tsx` or `components/site-header.tsx`): wordmark left; centered links **Home, Mentors, My sessions, FAQs, Contact, Pages ▾**; right side: student name + Sign out when signed in, otherwise a ghost **Sign in** and a solid green **Get started** (both open the existing name+email sign-in; do not build a password flow). Active route text is green (use `usePathname`, so the header becomes a client component or uses a small client child).
- `Pages ▾` dropdown: Terms and Condition, Privacy Policy. Works with click and keyboard, closes on Escape, outside click and route change. Hover optional.
- `SiteFooter`: wordmark + one-line mission, link groups **Services** (Mentors, FAQs, Sessions, Contact) and **Pages** (Terms and Condition, Privacy Policy), copyright strip. No social icons unless they are plain outlined placeholders with no fake URLs.
- Hamburger menu below 1024px.

### 3. Home (`/`)
Keep the AI chat as the core of the hero. Order of sections:
1. Hero: left-aligned, 3-line H1 (Poppins 700, 52-58px). Keep our own copy, for example "Get matched with the right mentor", and the intro paragraph. The chat composer sits in the wide white search-style module with a soft shadow and a green **Send** button; example prompts become small outlined chips under it. Airy right half with subtle geometric/green background art (CSS or SVG only).
2. Once the student sends a message, switch to the existing two-column chat layout (conversation left, "Mentors for you" right) in the new style. Recommendation cards become white cards with a thin border, initials avatar, the green evidence rows from the sheet (mint background, green tick), and green primary / ghost buttons.
3. Workflow strip: "Workflow" eyebrow, heading, 3 cards (Describe your problem, See why each mentor fits, Book a call and get a write-up) with simple mint line icons (inline SVG).
4. Categories on `#F7F8F8`: "Browse Mentors by Categories", a 4-column grid of tiles built from the **real `domain` values and counts** returned by `GET /api/mentors` (compute client or server side; no invented categories). Each tile links to `/mentors?domain=<value>`. Zero-count tiles are not needed.
5. Feature tiles (3 columns, outlined cards, only features this product really has): Evidence-based matching, Search and filter, Slot booking, Call write-ups, Privacy (no contact details shared), Admin funnel for the Mesa team.
6. "Discover our mentors": a row of 4 real mentors from the sheet (first 4, or the 4 with the highest `activities` if present) as `MentorCard`s with a "View all mentors" link.
7. Footer.

### 4. Mentors (`/mentors`, `/mentors/[id]`)
- Small left-aligned "Mentors" H1, one compact filter row (Search, Domain, Sector, City, green outlined Search button, Clear). Keep the GET-form behaviour and test ids.
- 4-column card grid (2 on tablet, 1 on phone). `MentorCard`: large square initials avatar block on `#E9F9F2` with green initials, name, `domain`, then a two-column footer showing real fields only, for example **Company** and **City** (or **Seniority** and **Sessions done** when present). Missing value shows "Not stated". No verified pill, flag or rating.
- Mentor profile and booking pages (`/mentors/[id]`, `/book/[mentorId]`): same card, field and button styles; slot picker uses green selected state.

### 5. Remaining existing pages, restyled only
`/sessions` and `/sessions/[id]` (use the spec's bordered table look with green links for the list: columns Mentor, Topic/Brief, When, Status; status pills use mint/green, neutral and red variants with a word and glyph), booking confirmation, `/m/[token]`, `/admin` (funnel tiles as white bordered cards with green numbers), sign-in form, loading, empty and error states. Same fonts, colours and spacing everywhere. Alerts use `#D90016`.

### 6. New static pages
- `/faqs`: centered H1 "Frequently Asked Questions", narrow stack of accordion tiles (button with `aria-expanded` and `aria-controls`, mint circular plus that becomes a minus, single-open, Enter/Space work). 5 to 6 Q&As written for **this** product (how matching works, what data is shown, how booking works, what the write-up is, privacy, cost).
- `/contact`: centered H1 "Get In Touch", ~620px form: Your full name + Your email in two columns, Message textarea, Submit button. Validate required fields and email format with clear field errors, disable while submitting, one success or error notice in an `aria-live` region. Backend: add `POST /api/contact` (additive, stores name, email, message in a `contact_messages` table, returns 201 `{id, status:"received"}`, 422 on bad input, simple per-IP rate limit, contract error shape, tests, ruff clean) and log it in `docs/CONTRACT.md`. If the API change cannot be finished, fall back to a clearly disabled-looking success-less form and say so in the report.
- `/terms` and `/privacy`: simple readable legal-style pages, plain placeholder-quality but sensible text for a prototype, with a note that it is a prototype.

### 7. Quality
- One H1 per page, landmarks, visible focus ring, labels on all inputs, `prefers-reduced-motion` respected, AA contrast (green `#0DBB7C` on white is below AA for small text, so use a darker green such as `#0A9A66` for text-size green and keep `#0DBB7C` for fills).
- Update `apps/web/TESTIDS.md` for new ids. Keep mocks in `src/mocks` working for the new endpoint.
- Do not break `apps/web/e2e` tests. If a selector must change, tell the test owner in the report instead of editing `e2e/` yourself... unless the only failure is a text/class change, in which case fix that one line and say so.

## Definition of done
- `npm run lint`, `npx tsc --noEmit` and `npm run build` pass in `apps/web`; `uv run pytest` and `uv run ruff check` pass in `apps/api` if step 6 is done.
- Playwright screenshots at 1440x900 of: `/` (before and after one chat message), `/mentors`, a mentor profile, `/book/<id>`, `/sessions`, `/faqs`, `/contact`, `/admin`, plus `/` at 390px wide. Compare each against the reference images and fix visible differences in spacing, type size, colour and alignment.
- No blogs or jobs anywhere.
- Final report: what changed per route, anything in the plan you could not do, and any contract change.

## How to run
API: `cd apps/api && OPENROUTER_API_KEY=... uv run uvicorn app.main:app --port 8000` (already running on :8000 in the user's terminal). Web dev server is already running on :3000 and hot-reloads (`apps/web/.env.local` has no mocks flag). Do not start a second dev server on the same port, and do not run `npm run build` while the dev server is running without stopping it first, because both write `.next`.

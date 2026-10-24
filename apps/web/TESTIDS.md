# Test ids

Stable `data-testid` values in `apps/web/src`. Mock triggers are in `src/mocks/handlers.ts` (mock admin password: `mesa-admin`).

| Area | Test id | Notes |
|---|---|---|
| Header | `student-name` | Signed-in student's name |
| Sign-in | `signin-form`, `signin-name`, `signin-email`, `signin-submit`, `signin-error` | Labels: Name, Email. Button: Continue |
| Chat | `chat-input`, `chat-send`, `chat-log`, `msg-student`, `msg-assistant` (`data-kind`), `chat-typing`, `chat-error`, `chat-retry`, `chat-empty`, `example-0`..`example-3`, `match-panel`, `match-empty` | Routes `/` and `/chat` are the same screen |
| Recommendation card | `mentor-card` (`data-mentor-id`), `mentor-name`, `reason-row` (`data-field`), `reason-value`, `reason-missing` (`data-field`, "Not stated"), `book-mentor`, `view-profile` | `mentor-card` is also used on `/mentors` |
| Browse | `mentor-filters`, `filter-q`, `filter-domain`, `filter-sector`, `filter-city`, `filter-apply`, `mentor-count`, `empty-state` | Filters are a GET form (query params) |
| Profile | `mentor-name`, `fact` (`data-field`), `continue-booking` | |
| Slots | `day-tab`, `slot` (`aria-pressed` when chosen), `slots-empty` | |
| Booking | `selected-slot`, `confirm-booking`, `booking-error`, `booking-confirmation`, `booking-when`, `view-booking`, `demo-mentor-link`, `mentor-link-url`, `copy-mentor-link` | |
| Status | `booking-status` (`data-status`), `writeup-status` (`data-status`) | Pill carries a word and a glyph |
| Sessions | `session-row` (`data-booking-id`), `booking-brief`, `writeup`, `writeup-discussed`, `writeup-work-on`, `writeup-next-steps`, `writeup-none`, `cancel-booking`, `cancel-confirm` | Cancelling asks to confirm first |
| Mentor page `/m/[token]` | `mentor-call-time`, `mentor-brief`, `notes-box` (label Notes), `audio-upload` (disabled), `close-completed`, `close-no-show`, `save-notes`, `mentor-error`, `mentor-closed` | |
| Admin | `admin-gate`, `admin-password` (label Password), `admin-submit`, `admin-error`, `funnel-chats_started`, `funnel-matched`, `funnel-booked`, `funnel-completed`, `funnel-writeups_ready`, `funnel-rebooked`, `status-count-<status>`, `stuck-list`, `stuck-row`, `unmatched-list`, `unmatched-row`, `mentor-load` | |
| Contact `/contact` | `contact-form`, `contact-name`, `contact-email`, `contact-message`, `contact-submit`, `contact-notice` | Notice is an aria-live region |
| States | `error-state`, `empty-state`, `loading` | |

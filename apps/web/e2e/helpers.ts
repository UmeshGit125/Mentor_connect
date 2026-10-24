import { expect, type Page } from "@playwright/test";

/*
 * Selectors prefer data-testid names that already exist in apps/web/src/components
 * (mentor-card, reason-row, reason-missing, booking-status, error-state, ...) and fall
 * back to accessible roles and labels. When apps/web/TESTIDS.md appears, tighten the
 * `.or(...)` fallbacks here, in one place.
 *
 * Mock triggers (apps/web/src/mocks/handlers.ts):
 *   chat: <5 words clarify; "astronaut" no_match; "poem"/"hopeless" redirect
 *   booking: first slot of day 1 (the first listed slot) is slot_taken
 *   admin password: mesa-admin
 */
export const ADMIN_PASSWORD = "mesa-admin";
export const CLEAR_MESSAGE =
  "I am a final year student and I want to become a product manager at a fintech company";

export const chatInput = (p: Page) =>
  p.getByTestId("chat-input").or(p.getByRole("textbox", { name: /message|problem|describe|ask|type/i })).first();
export const sendButton = (p: Page) =>
  p.getByTestId("chat-send").or(p.getByRole("button", { name: /^(send|ask|submit)/i })).first();
export const mentorCards = (p: Page) => p.getByTestId("mentor-card");
export const slotOptions = (p: Page) =>
  p.getByTestId("slot").or(p.getByRole("radio")).or(p.getByTestId("slot-option"));
export const confirmButton = (p: Page) => p.getByRole("button", { name: /confirm/i }).first();

export async function signIn(page: Page, name = "Test Student", email = "test.student@students.test") {
  await page.goto("/");
  // The form is server-rendered before React hydrates; a click before hydration is lost.
  // Retry the whole fill+submit until the header shows the student.
  await expect(async () => {
    await page.getByTestId("signin-name").fill(name);
    await page.getByTestId("signin-email").fill(email);
    await page.getByTestId("signin-submit").click();
    await expect(page.getByTestId("student-name")).toHaveText(name, { timeout: 3_000 });
  }).toPass({ timeout: 20_000 });
}

export async function sendChat(page: Page, text: string) {
  if (!/\/chat/.test(page.url())) await page.goto("/chat");
  await chatInput(page).fill(text);
  await sendButton(page).click();
}

/** Sign in, chat, open the first match's booking page. Returns after landing on /book/<id>. */
export async function reachBooking(page: Page) {
  await signIn(page);
  await sendChat(page, CLEAR_MESSAGE);
  await expect(mentorCards(page)).toHaveCount(3);
  await mentorCards(page).first().getByTestId("book-mentor").click();
  await expect(page).toHaveURL(/\/book\//);
}

/** Full happy path booking via the UI (picks the LAST slot to avoid the mock's slot_taken trigger). */
export async function bookViaUi(page: Page) {
  await reachBooking(page);
  await slotOptions(page).last().click();
  await confirmButton(page).click();
  await expect(page.getByTestId("booking-status").first()).toBeVisible();
}

/** The mock keeps the mentor link token in localStorage; the real app would show/send a link. */
export async function mentorToken(page: Page): Promise<string> {
  return page.evaluate(() => JSON.parse(localStorage.getItem("mc_mock_db") ?? "{}").bookings[0].token);
}

export async function noHorizontalScroll(page: Page) {
  const { sw, cw } = await page.evaluate(() => ({
    sw: document.documentElement.scrollWidth,
    cw: document.documentElement.clientWidth,
  }));
  expect(sw, `scrollWidth ${sw} > clientWidth ${cw}`).toBeLessThanOrEqual(cw);
}

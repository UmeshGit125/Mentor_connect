import { expect, test } from "@playwright/test";
import {
  CLEAR_MESSAGE, bookViaUi, confirmButton, mentorCards, reachBooking, chatInput, sendButton, sendChat, signIn, slotOptions,
} from "../helpers";

test("sign in, describe a problem, see 3 match cards with evidence rows", async ({ page }) => {
  await signIn(page);
  await sendChat(page, CLEAR_MESSAGE);
  await expect(mentorCards(page)).toHaveCount(3);
  for (let i = 0; i < 3; i++) {
    const card = mentorCards(page).nth(i);
    await expect(card.getByTestId("mentor-name")).not.toBeEmpty();
    expect(await card.getByTestId("reason-row").count()).toBeGreaterThanOrEqual(1);
    await expect(card.getByTestId("reason-value").first()).not.toBeEmpty();
  }
});

test("a field the sheet leaves blank shows 'Not stated', never a guess", async ({ page }) => {
  await signIn(page);
  // The mock's marketing rule returns M011, whose company is blank in the fixture.
  await sendChat(page, "I want to get into marketing and growth roles after college");
  await expect(mentorCards(page)).toHaveCount(3);
  const missing = page.getByTestId("reason-missing");
  expect(await missing.count()).toBeGreaterThanOrEqual(1);
  await expect(missing.first()).toContainText(/not stated/i);
});

test("pick a slot, confirm, and see the booking in sessions", async ({ page }) => {
  await bookViaUi(page);
  await page.goto("/sessions");
  await expect(page.getByTestId("booking-status").first()).toHaveAttribute("data-status", "confirmed");
});

test("slot_taken shows a helpful message and lets the student pick another slot", async ({ page }) => {
  await reachBooking(page);
  await slotOptions(page).first().click(); // the mock marks the first listed slot as taken
  await confirmButton(page).click();
  const err = page.getByTestId("error-state").or(page.getByRole("alert")).first();
  await expect(err).toContainText(/just booked|pick another/i);
  await expect(page).toHaveURL(/\/book\//); // still on the picker, not an error page
  await slotOptions(page).last().click();
  await confirmButton(page).click();
  await expect(page.getByTestId("booking-status").first()).toBeVisible();
});

test("vague message gets a clarifying question", async ({ page }) => {
  await signIn(page);
  await sendChat(page, "help me");
  await expect(mentorCards(page)).toHaveCount(0);
  await expect(page.getByText(/say more|tell me|which kind|what/i).first()).toBeVisible();
});

test("no-match message is honest and offers a way forward", async ({ page }) => {
  await signIn(page);
  await sendChat(page, "I want to become an astronaut and need a mentor for it");
  await expect(mentorCards(page)).toHaveCount(0);
  await expect(page.getByText(/none of our 50 mentors|won't guess/i)).toBeVisible();
  await expect(page.getByRole("link", { name: /browse/i }).first()).toBeVisible();
});

test("sensitive message redirects with no mentor cards", async ({ page }) => {
  await signIn(page);
  await sendChat(page, "I feel hopeless about everything lately");
  await expect(mentorCards(page)).toHaveCount(0);
  await expect(page.getByText(/helpline|someone you trust/i)).toBeVisible();
});

test("off-topic message redirects back to career questions", async ({ page }) => {
  await signIn(page);
  await sendChat(page, "tell me a joke about cats please");
  await expect(mentorCards(page)).toHaveCount(0);
  await expect(page.getByText(/only help with career/i)).toBeVisible();
});

test("an over-long message is blocked or answered with a validation message, never a crash", async ({ page }) => {
  await signIn(page);
  await page.goto("/chat");
  const box = chatInput(page);
  await box.fill("x".repeat(2001));
  // The textarea has maxLength=2000, so the extra character is blocked at input. If a client
  // ever lets it through, the server's validation message must show instead.
  const kept = (await box.inputValue()).length;
  if (kept <= 2000) {
    expect(kept).toBe(2000);
  } else {
    await sendButton(page).click();
    await expect(page.getByText(/2000|too long|between 1 and/i).first()).toBeVisible();
  }
  await expect(mentorCards(page)).toHaveCount(0);
});

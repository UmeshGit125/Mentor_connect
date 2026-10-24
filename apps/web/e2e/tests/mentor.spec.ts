import { expect, test } from "@playwright/test";
import { bookViaUi, mentorToken } from "../helpers";

test("unknown mentor link shows a clear not-valid message", async ({ page }) => {
  await page.goto("/m/not-a-real-token");
  await expect(page.getByText(/not valid|ask the student/i)).toBeVisible();
});

test("mentor closes a call as completed with notes and the student sees a ready write-up", async ({ page }) => {
  await bookViaUi(page);
  const token = await mentorToken(page);
  await page.goto(`/m/${token}`);
  await expect(page.getByText(/Test Student/)).toBeVisible();
  await page.getByLabel(/notes/i).fill(
    "We discussed moving into product. She should write a spec this week. Next, interview two PMs.",
  );
  await page.getByRole("button", { name: /completed|mark.*complete|close/i }).first().click();
  await expect(page.getByTestId("booking-status").first()).toHaveAttribute("data-status", "completed");
  await page.goto("/sessions");
  await expect(page.getByTestId("writeup-status").first()).toHaveAttribute("data-status", "ready");
});

test("closing with whitespace-only notes leaves the write-up empty", async ({ page }) => {
  await bookViaUi(page);
  const token = await mentorToken(page);
  await page.goto(`/m/${token}`);
  await page.getByLabel(/notes/i).fill("   \n  ");
  await page.getByRole("button", { name: /completed|mark.*complete|close/i }).first().click();
  await expect(page.getByTestId("booking-status").first()).toHaveAttribute("data-status", "completed");
  // The write-up pill is shown on the student's sessions page, not on the mentor page.
  await page.goto("/sessions");
  await expect(page.getByTestId("writeup-status").first()).toHaveAttribute("data-status", "none");
});

test("a closed call cannot be closed again from the page", async ({ page }) => {
  await bookViaUi(page);
  const token = await mentorToken(page);
  await page.goto(`/m/${token}`);
  await page.getByRole("button", { name: /no.?show/i }).first().click();
  await expect(page.getByTestId("booking-status").first()).toHaveAttribute("data-status", "no_show");
  await page.reload();
  await expect(page.getByRole("button", { name: /^(mark.*complete|completed|close call)/i })).toHaveCount(0);
});

test("audio upload is a disabled 'Coming soon' option", async ({ page }) => {
  await bookViaUi(page);
  const token = await mentorToken(page);
  await page.goto(`/m/${token}`);
  await expect(page.getByText(/coming soon/i).first()).toBeVisible();
  const audio = page.getByRole("button", { name: /audio/i })
    .or(page.getByRole("radio", { name: /audio/i }))
    .or(page.getByLabel(/audio/i))
    .first();
  await expect(audio).toBeDisabled();
});

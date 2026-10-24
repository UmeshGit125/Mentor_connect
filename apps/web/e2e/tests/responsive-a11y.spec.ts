import { expect, test } from "@playwright/test";
import {
  CLEAR_MESSAGE, bookViaUi, chatInput, mentorCards, mentorToken, noHorizontalScroll, signIn,
} from "../helpers";

test.use({ viewport: { width: 390, height: 844 } });

test("sign-in page does not scroll horizontally at 390px", async ({ page }) => {
  await page.goto("/");
  await noHorizontalScroll(page);
});

test("admin gate does not scroll horizontally at 390px", async ({ page }) => {
  await page.goto("/admin");
  await noHorizontalScroll(page);
});

test("signed-in pages do not scroll horizontally at 390px", async ({ page }) => {
  await signIn(page);
  for (const path of ["/chat", "/mentors", "/sessions"]) {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    await noHorizontalScroll(page);
  }
});

test("chat results (match cards), booking and mentor pages fit at 390px", async ({ page }) => {
  await bookViaUi(page); // leaves us on the booking confirmation
  await noHorizontalScroll(page);
  const token = await mentorToken(page);
  await page.goto("/chat");
  await page.getByRole("textbox").first().fill(CLEAR_MESSAGE);
  await page.getByRole("button", { name: /^(send|ask|submit)/i }).first().click();
  await expect(mentorCards(page)).toHaveCount(3);
  await noHorizontalScroll(page);
  await page.goto(`/m/${token}`);
  await noHorizontalScroll(page);
});

test("keyboard only: reach the chat box, send with Enter, reach a match action, activate it", async ({ page }) => {
  await signIn(page);
  await page.goto("/chat");
  // Tab until the chat input has focus (bounded so a keyboard trap fails the test).
  let focused = false;
  for (let i = 0; i < 25 && !focused; i++) {
    await page.keyboard.press("Tab");
    focused = await chatInput(page).evaluate((el) => el === document.activeElement);
  }
  expect(focused, "chat input should be reachable with Tab").toBe(true);
  await page.keyboard.type(CLEAR_MESSAGE);
  await page.keyboard.press("Enter");
  await expect(mentorCards(page)).toHaveCount(3);
  // Tab forward until the first "Book a call" link has focus, then activate it with Enter.
  const book = mentorCards(page).first().getByTestId("book-mentor");
  let onBook = false;
  for (let i = 0; i < 40 && !onBook; i++) {
    await page.keyboard.press("Tab");
    onBook = await book.evaluate((el) => el === document.activeElement);
  }
  expect(onBook, "book link should be reachable with Tab").toBe(true);
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/book\//);
});

test("focus is visibly styled on the chat input", async ({ page }) => {
  await signIn(page);
  await page.goto("/chat");
  await chatInput(page).focus();
  const outline = await chatInput(page).evaluate((el) => {
    const s = getComputedStyle(el);
    return `${s.outlineStyle}|${s.outlineWidth}|${s.boxShadow}`;
  });
  expect(outline).not.toBe("none|0px|none");
});

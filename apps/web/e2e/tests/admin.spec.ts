import { expect, test } from "@playwright/test";
import { ADMIN_PASSWORD } from "../helpers";

test("admin gate rejects a wrong password and shows nothing", async ({ page }) => {
  await page.goto("/admin");
  await page.getByTestId("admin-password").fill("wrong-password");
  await page.getByTestId("admin-submit").click();
  await expect(page.getByTestId("admin-error")).toBeVisible();
  await expect(page.getByText(/chats started/i)).toHaveCount(0);
});

test("admin gate accepts the right password and shows the funnel", async ({ page }) => {
  await page.goto("/admin");
  await page.getByTestId("admin-password").fill(ADMIN_PASSWORD);
  await page.getByTestId("admin-submit").click();
  await expect(page.getByText(/chats started/i)).toBeVisible();
  await expect(page.getByText(/unmatched|stuck/i).first()).toBeVisible();
});

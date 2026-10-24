import { expect, test, type APIRequestContext } from "@playwright/test";
import { CLEAR_MESSAGE, mentorCards, sendChat, signIn } from "../helpers";

/*
 * Runs against the REAL API, no mocks. Needs the API up with ADMIN_PASSWORD and with the web
 * origin in ALLOWED_ORIGINS. Run: REAL_API=1 npx playwright test (see playwright.config.ts).
 */
const API = process.env.API_URL ?? "http://localhost:8000";
const WEB_ORIGIN = "http://localhost:3100";
const ADMIN_PW = process.env.ADMIN_PASSWORD ?? "mesa-admin";
const unique = () => `${Date.now()}${Math.floor(Math.random() * 1000)}`;

type Funnel = Record<"chats_started" | "matched" | "booked" | "completed" | "writeups_ready" | "rebooked", number>;
async function funnel(request: APIRequestContext): Promise<Funnel> {
  const r = await request.get(`${API}/api/admin/summary`, { headers: { "X-Admin-Password": ADMIN_PW } });
  expect(r.status()).toBe(200);
  return (await r.json()).funnel;
}

test("full journey: match, book, mentor closes, write-up, admin funnel moves", async ({ page, browser, request }) => {
  test.setTimeout(120_000);
  const before = await funnel(request);
  const ctx = page.context();
  await ctx.grantPermissions(["clipboard-read", "clipboard-write"], { origin: WEB_ORIGIN });

  await signIn(page, "Real Student", `real.${unique()}@students.test`);
  await sendChat(page, CLEAR_MESSAGE);

  // 1 to 3 matches, each with evidence rows whose values are not empty.
  await expect(mentorCards(page).first()).toBeVisible({ timeout: 20_000 });
  const n = await mentorCards(page).count();
  expect(n).toBeGreaterThanOrEqual(1);
  expect(n).toBeLessThanOrEqual(3);
  for (let i = 0; i < n; i++) {
    const card = mentorCards(page).nth(i);
    expect(await card.getByTestId("reason-row").count()).toBeGreaterThanOrEqual(1);
    await expect(card.getByTestId("reason-value").first()).not.toBeEmpty();
  }
  // Never leak contact details into the page.
  const body = (await page.locator("body").innerText()).toLowerCase();
  expect(body).not.toMatch(/linkedin|[a-z0-9._-]+@[a-z0-9-]+\.[a-z]{2,}/);

  // Book the last open slot of the first card's mentor.
  await mentorCards(page).first().getByTestId("book-mentor").click();
  await expect(page).toHaveURL(/\/book\//);
  await page.getByTestId("slot").last().click();
  await page.getByTestId("confirm-booking").click();
  await expect(page.getByTestId("booking-confirmation")).toBeVisible();

  // Copy the demo mentor link and check the clipboard holds the same URL.
  const href = await page.getByTestId("mentor-link-url").getAttribute("href");
  expect(href).toMatch(/^\/m\/.+/);
  await page.getByTestId("copy-mentor-link").click();
  await expect(page.getByTestId("copy-mentor-link")).toHaveText("Copied");
  const clip = await page.evaluate(() => navigator.clipboard.readText());
  expect(clip).toBe(`${WEB_ORIGIN}${href}`);
  await page.getByTestId("view-booking").click();
  await expect(page).toHaveURL(/\/sessions\/[^/]+$/);
  await expect(page.getByTestId("booking-status").first()).toHaveAttribute("data-status", "confirmed");
  const sessionUrl = page.url();

  // Open the link as the mentor, in a fresh context (no student identity).
  const mentorCtx = await browser.newContext();
  const mentor = await mentorCtx.newPage();
  await mentor.goto(clip);
  await expect(mentor.getByText(/Real Student/).first()).toBeVisible();
  await expect(mentor.getByTestId("mentor-brief")).toBeVisible();
  await mentor.getByTestId("notes-box").fill(
    "We discussed moving into fintech product management. She should write a one page spec this week. Next, interview two product managers and apply to three internships.",
  );
  await mentor.getByTestId("close-completed").click();
  await expect(mentor.getByTestId("mentor-closed")).toContainText(/completed/i);
  await mentorCtx.close();

  // Student sees the completed booking and the write-up.
  await page.goto(sessionUrl);
  await expect(page.getByTestId("booking-status").first()).toHaveAttribute("data-status", "completed");
  await expect(page.getByTestId("writeup")).toBeVisible({ timeout: 20_000 });
  for (const id of ["writeup-discussed", "writeup-work-on", "writeup-next-steps"]) {
    await expect(page.getByTestId(id).locator("li").first()).toBeVisible();
  }

  // Admin page: log in through the UI and see the funnel moved by at least one step each.
  const admin = await browser.newContext();
  const ap = await admin.newPage();
  await ap.goto("/admin");
  await expect(async () => {
    await ap.getByTestId("admin-password").fill(ADMIN_PW);
    await ap.getByTestId("admin-submit").click();
    await expect(ap.getByTestId("funnel-chats_started")).toBeVisible({ timeout: 3_000 });
  }).toPass({ timeout: 20_000 });
  for (const k of ["chats_started", "matched", "booked", "completed", "writeups_ready"] as const) {
    const shown = Number(await ap.getByTestId(`funnel-${k}`).innerText());
    expect(shown, `funnel ${k} shown`).toBeGreaterThanOrEqual(before[k] + 1);
  }
  await admin.close();
});

test("gibberish gets a no-match message and no mentor cards", async ({ page }) => {
  await signIn(page, "Gibber Student", `gib.${unique()}@students.test`);
  await sendChat(page, "asdkjh qweoiu");
  await expect(page.getByTestId("msg-assistant").last()).toHaveAttribute("data-kind", "no_match", { timeout: 20_000 });
  await expect(mentorCards(page)).toHaveCount(0);
  await expect(page.getByTestId("msg-assistant").last()).not.toBeEmpty();
});

test("self-harm style message redirects with no mentor cards", async ({ page }) => {
  await signIn(page, "Care Student", `care.${unique()}@students.test`);
  await sendChat(page, "I feel hopeless and I want to end my life");
  await expect(page.getByTestId("msg-assistant").last()).toHaveAttribute("data-kind", "redirect", { timeout: 20_000 });
  await expect(mentorCards(page)).toHaveCount(0);
  await expect(page.getByTestId("msg-assistant").last()).toContainText(/helpline|someone you trust|talk to|support/i);
});

test("CORS: browser on the web origin can call the API; preflight and foreign origins behave", async ({ page, request }) => {
  await page.goto("/");
  // A real cross-origin fetch from the page, with the custom header that forces a preflight.
  const res = await page.evaluate(async (api) => {
    const r = await fetch(`${api}/api/students`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Student-Id": "x" },
      body: JSON.stringify({ name: "Cors Check", email: `cors.${Date.now()}@students.test` }),
    });
    return { status: r.status, body: await r.json() };
  }, API);
  expect(res.status).toBe(200);
  expect(res.body.id).toBeTruthy();

  const pre = await request.fetch(`${API}/api/bookings`, {
    method: "OPTIONS",
    headers: {
      Origin: WEB_ORIGIN,
      "Access-Control-Request-Method": "POST",
      "Access-Control-Request-Headers": "content-type,x-student-id,x-admin-password",
    },
  });
  expect(pre.status()).toBeLessThan(300);
  expect(pre.headers()["access-control-allow-origin"]).toBe(WEB_ORIGIN);
  expect((pre.headers()["access-control-allow-headers"] ?? "").toLowerCase()).toContain("x-student-id");
  expect((pre.headers()["access-control-allow-headers"] ?? "").toLowerCase()).toContain("x-admin-password");

  const foreign = await request.get(`${API}/api/health`, { headers: { Origin: "https://evil.example" } });
  expect(foreign.headers()["access-control-allow-origin"]).toBeUndefined();
});

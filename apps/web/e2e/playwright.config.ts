import { defineConfig, devices } from "@playwright/test";

const PORT = 3100;
// REAL_API=1 builds the web app without mocks against the API at API_URL (default http://localhost:8000).
// Default is mock mode. A production build is used because the dev server compiles pages on
// demand, which makes parallel tests time out on first load.
const REAL = process.env.REAL_API === "1";
const API_URL = process.env.API_URL ?? "http://localhost:8000";

// Starts the Next dev server in mock mode (no API needed). Run from apps/web/e2e.
export default defineConfig({
  testDir: "./tests",
  // The real-API journey needs a live API and a non-mock build: run it with REAL_API=1.
  testMatch: REAL ? /real-api\.spec\.ts/ : undefined,
  testIgnore: REAL ? undefined : /real-api\.spec\.ts/,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `npm run build && npm run start -- -p ${PORT}`,
    cwd: "..",
    url: `http://localhost:${PORT}`,
    reuseExistingServer: false,
    timeout: 300_000,
    // Process env overrides .env.local in Next, so an empty string disables mocks there.
    env: REAL
      ? { NEXT_PUBLIC_USE_MOCKS: "", NEXT_PUBLIC_API_URL: API_URL }
      : { NEXT_PUBLIC_USE_MOCKS: "1" },
  },
});

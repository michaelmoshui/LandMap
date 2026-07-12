import { defineConfig, devices } from "@playwright/test";

// The app is served by the Caddy proxy. In CI/containers E2E_BASE_URL points at
// the `proxy` service; locally it defaults to http://localhost.
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});

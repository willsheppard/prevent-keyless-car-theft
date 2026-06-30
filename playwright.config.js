// Playwright e2e config. Builds the static site and serves dist/ over HTTP, then
// runs the tests against it -- the same artifact the deploy workflow ships.
const { defineConfig, devices } = require("@playwright/test");

const PORT = 4173;
const PY = process.env.PYTHON || ".venv/bin/python";

module.exports = defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: `${PY} build.py && ${PY} -m http.server ${PORT} -d dist`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});

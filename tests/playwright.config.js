// Playwright config for the escape-rooms browser integration tests.
// Serves the site root (websites/thebustalab.github.io) with a plain static server — the same way
// GitHub Pages serves it — so play.html + shared/ + scenario.json load exactly as in production.
// WebR boot is slow (~20-40s first time), so timeouts are generous.
const { defineConfig, devices } = require("@playwright/test");
const path = require("path");

module.exports = defineConfig({
  testDir: "./e2e",
  timeout: 120_000,            // WebR-heavy tests can be slow
  expect: { timeout: 30_000 },
  fullyParallel: false,        // one shared static server; keep it simple
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:8060",
    headless: true,
    trace: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // Serve the SITE root so URLs match production (/escape_rooms/...). Site root = two levels up
      // from tests/ (tests -> escape_rooms -> thebustalab.github.io).
      command: "python3 -m http.server 8060",
      cwd: "../..",
      url: "http://localhost:8060/escape_rooms/rooms/data_vis/alaska/play.html",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      // The authoring harness (harness_gpt.html + /api/* + /scene/*) on :8751, for the harness-UI
      // spec. Reuses the running tmux `harness_ui` server if it's up, else launches a fresh one. The
      // read/pick paths this test drives need no OPENAI key (that's only read at art-generation time).
      command: `python3 ${path.resolve(__dirname, "../authoring/harness_server.py")}`,
      url: "http://localhost:8751/harness_gpt.html",
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});

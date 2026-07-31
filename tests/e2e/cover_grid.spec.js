// e2e harness-UI test — regression guard for the "cover candidates vanish on reload" bug
// (fixed 2026-07-30). buildCover() cleared #coverGrid on every load/refresh but never repopulated it;
// refreshCoverGrid() (which lists the existing gpt_cover_* candidates from _scratch) was only called
// after a live "Generate cover" click. So reloading the harness showed just the selected-cover preview
// and an empty candidate grid — you couldn't re-pick among already-generated candidates. The fix:
// buildCover() now calls refreshCoverGrid() so the staged candidates list on load.
//
// The clean signature of the fix: after selecting a scenario that HAS staged cover candidates, the
// #coverGrid holds candidate cards WITHOUT anyone clicking Generate. Under the bug the grid stayed empty.
//
// Drives the live authoring harness on :8751 (see playwright.config.js — reuses the tmux server if up).
const { test, expect } = require("@playwright/test");

const HARNESS = "http://127.0.0.1:8751/harness_gpt.html";
const SCENARIO = "data_vis/alaska";                 // has gpt_cover_* candidates staged in _scratch

test("harness: cover candidates list on load, not only after Generate", async ({ page }) => {
  await page.goto(HARNESS);
  await page.waitForSelector(`#scenarioPick option[value="${SCENARIO}"]`, { state: "attached", timeout: 20_000 });
  await page.selectOption("#scenarioPick", SCENARIO);

  // buildCover() → refreshCoverGrid() should populate the grid on load — WITHOUT clicking "Generate cover".
  // Auto-retrying so we don't read count() during the mid-load clear/refill window: under the fix the
  // grid becomes non-empty on its own; under the bug it never does (refreshCoverGrid was never called on
  // load), so this times out and fails.
  await expect(page.locator("#coverGrid .card")).not.toHaveCount(0, { timeout: 20_000 });

  // sanity: we never touched the Generate button — the grid filled from the staged pool alone
  await expect(page.locator("#coverStatus")).not.toContainText("generating");
});

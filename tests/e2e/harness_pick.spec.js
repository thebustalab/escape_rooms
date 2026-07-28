// e2e harness-UI test — regression guard for the "picking a candidate reloads the whole grid" bug
// (fixed 2026-07-20). In Step 3 (build rooms), clicking a candidate image used to call renderGrid(),
// which rebuilt every card (grid.innerHTML = "") with a fresh `?t=<Date.now()>` cache-buster, so the
// whole column refetched and flashed on each click. The fix: a pick now only re-highlights — markPicked
// toggles `.sel` on the EXISTING nodes, and the grid images carry no cache-buster.
//
// The clean, confound-free signature of the fix is DOM identity: after a pick, the clicked <img> node
// must still be the same connected node (markPicked mutates it in place). Under the bug, renderGrid
// blew the grid away and rebuilt it, so the original node would be detached. This avoids network/cache
// and door-preview confounds that a request-count would trip over.
//
// Drives the live authoring harness on :8751 (see playwright.config.js — reuses the tmux server if up).
const { test, expect } = require("@playwright/test");

const HARNESS = "http://127.0.0.1:8751/harness_gpt.html";
const SCENARIO = "data_vis/alaska";                 // has candidate images in _scratch

test("harness: picking a candidate re-highlights in place, without rebuilding the grid", async ({ page }) => {
  await page.goto(HARNESS);
  // an <option> is never "visible" until the select opens, so wait for it ATTACHED
  await page.waitForSelector(`#scenarioPick option[value="${SCENARIO}"]`, { state: "attached", timeout: 20_000 });
  await page.selectOption("#scenarioPick", SCENARIO);

  // a candidate card must render before we can pick one
  await expect(page.locator(".scenes .card").first()).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(2000);                   // let load-time re-renders (buildStep2 + refreshAll) settle
  await expect(page.locator(".scenes .card.sel")).toHaveCount(0);   // nothing picked yet

  // grab a handle to the exact <img> node, then pick it
  const firstImg = page.locator(".scenes .card img").first();
  const node = await firstImg.elementHandle();
  await firstImg.click();
  await page.waitForTimeout(800);

  // the fix: markPicked mutated the existing node in place — it's still connected (the bug would have
  // detached it by rebuilding the grid)
  const stillConnected = await page.evaluate((el) => !!(el && el.isConnected), node).catch(() => false);
  expect(stillConnected, "picking must not rebuild the grid (node stayed connected)").toBe(true);

  // …and exactly the clicked card is now selected
  await expect(page.locator(".scenes .card.sel")).toHaveCount(1);
});

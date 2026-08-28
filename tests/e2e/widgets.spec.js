// Browser test for the two hotspot types added 2026-08-26 — the deduction `ledger` (temple's escape)
// and the `elevmap` (canyon's draggable transcription map). The pure logic already has node tests
// (ledger_rule.test.mjs / elev_scale.test.mjs); THIS covers the layer those cannot reach — the DOM, the
// pointer drags, and the wiring between them.
//
// FAILURE MODES UNDER TEST, i.e. the ones that survive a green unit suite:
//   - the ledger locks a group but never disables the rows, so the player can un-pick a confirmed group;
//   - the wrong-feedback leaks which row is wrong (it must say nothing per row);
//   - a drag moves the node but not the recorded value, or vice versa, so the plot and the state diverge;
//   - a node whose benchmark has NOT been read is still draggable, breaking the visit-it-to-record-it rule;
//   - the world-state counter the escape gate reads (`heights_placed`) never actually updates.
//
// Run: npx playwright test e2e/widgets.spec.js  (from escape_rooms/tests/).
const { test, expect } = require("@playwright/test");

const FIXTURE = "/escape_rooms/tests/e2e/widgets_fixture.html";

test.beforeEach(async ({ page }) => {
  await page.goto(FIXTURE);
  await page.waitForSelector(".ledgercard");
  await page.waitForSelector(".elevmapcard");
});

// ---------------------------------------------------------------- ledger

async function assign(page, map) {
  for (const [row, verdict] of Object.entries(map)) {
    await page.selectOption(`select.verdict[data-row="${row}"]`, verdict);
  }
}

test("ledger: a correct group locks and its rows go read-only", async ({ page }) => {
  await assign(page, { s1: "Sea", s2: "Sea" });
  await page.click(".ledgercard .qsubmit");
  await expect(page.locator(".ledgercard .qfeedback")).toHaveText("GROUP CONFIRMED");
  await expect(page.locator(".ledgerprog")).toHaveText("1 of 3 groups confirmed");
  // read-only is the point: a confirmed group must not be un-pickable
  await expect(page.locator('select.verdict[data-row="s1"]')).toBeDisabled();
  await expect(page.locator('select.verdict[data-row="s2"]')).toBeDisabled();
  await expect(page.locator('tr[data-row="s1"]')).toHaveClass(/locked/);
  await expect(page.locator('select.verdict[data-row="s3"]')).toBeEnabled();
});

test("ledger: a stray row keeps its group open, and the feedback names no row", async ({ page }) => {
  await assign(page, { s1: "Sea", s2: "Sea", s3: "Sea" });   // s3 is a Hearth shrine
  await page.click(".ledgercard .qsubmit");
  const fb = page.locator(".ledgercard .qfeedback");
  await expect(fb).toHaveText("NOTHING CLOSES");
  await expect(page.locator(".ledgerprog")).toHaveText("0 of 3 groups confirmed");
  // the mechanic dies the moment it tells you WHICH row is wrong
  const text = await fb.textContent();
  for (const row of ["Red", "Yellow", "Green", "s1", "s2", "s3"]) {
    expect(text).not.toContain(row);
  }
  await expect(page.locator('select.verdict[data-row="s1"]')).toBeEnabled();
});

test("ledger: all three groups right solves, and reports the attempt count", async ({ page }) => {
  await assign(page, { s1: "Sea", s2: "Sea", s3: "Hearth", s4: "Hearth", s5: "Hearth",
                       s6: "Grove", s7: "Grove", s8: "Grove", s9: "Grove" });
  await page.click(".ledgercard .qsubmit");
  await expect(page.locator(".ledgercard .qfeedback")).toHaveText("ALL CONFIRMED");
  await expect(page.locator(".ledgerprog")).toHaveText("3 of 3 groups confirmed");
  await page.waitForFunction(() => window.__solved !== null);
  expect(await page.evaluate(() => window.__solved)).toEqual({ answer: 1, attempts: 1 });
});

test("ledger: groups can be confirmed one press at a time and stay locked", async ({ page }) => {
  await assign(page, { s1: "Sea", s2: "Sea" });
  await page.click(".ledgercard .qsubmit");
  await assign(page, { s6: "Grove", s7: "Grove", s8: "Grove", s9: "Grove" });
  await page.click(".ledgercard .qsubmit");
  await expect(page.locator(".ledgerprog")).toHaveText("2 of 3 groups confirmed");
  await expect(page.locator('select.verdict[data-row="s1"]')).toBeDisabled();   // still locked
  expect(await page.evaluate(() => window.__solved)).toBeNull();                 // not done yet
});

// ---------------------------------------------------------------- elevmap

const node = (id) => `.elevnode[data-node="${id}"]`;

async function dragTo(page, id, elevation) {
  // Drive it the way a player does — a real pointer drag — rather than calling the handler.
  // Scroll first: page.mouse works in VIEWPORT coordinates, and the fixture stacks the map under a
  // nine-row ledger, so without this the target sits below the fold and every drag silently misses.
  await page.locator(".elevplot").scrollIntoViewIfNeeded();
  const plot = await page.locator(".elevplot").boundingBox();
  const el = await page.locator(node(id)).boundingBox();
  const PADT = 14, PADB = 26;
  const frac = (elevation - 800) / (1500 - 800);
  const y = plot.y + PADT + (plot.height - PADT - PADB) * (1 - frac);
  await page.mouse.move(el.x + el.width / 2, el.y + el.height / 2);
  await page.mouse.down();
  await page.mouse.move(plot.x + plot.width / 2, y, { steps: 8 });
  await page.mouse.up();
}

test("elevmap: an unread junction is shown but not draggable", async ({ page }) => {
  await expect(page.locator(node("c2"))).toHaveClass(/unread/);
  await expect(page.locator(node("c2"))).not.toHaveClass(/draggable/);
  await expect(page.locator(`${node("c2")} .nval`)).toHaveText("?");
  // and a read one is
  await expect(page.locator(node("c1"))).toHaveClass(/draggable/);
  await expect(page.locator(`${node("c1")} .nval`)).toHaveText("—");
});

test("elevmap: dragging records the height, moves the node, and updates the counter", async ({ page }) => {
  await expect(page.locator(".elevprog")).toHaveText("0 of 7 junction heights marked");
  await dragTo(page, "c1", 1400);
  await expect(page.locator(`${node("c1")} .nval`)).toHaveText("1400 m");
  await expect(page.locator(node("c1"))).toHaveClass(/onmark/);   // sitting on its surveyed height
  await expect(page.locator(".elevprog")).toHaveText("1 of 7 junction heights marked");
  // the state the escape gate reads must move with the pixels, not just the label
  expect(await page.evaluate(() => window.__gameState.heights_placed)).toBe(1);
  expect(await page.evaluate(() => window.__gameState.canyon_heights.c1)).toBe(1400);
});

test("elevmap: the axis is inverted — a higher junction sits above a lower one", async ({ page }) => {
  await dragTo(page, "c1", 1400);
  await dragTo(page, "c7", 850);
  const hi = await page.locator(node("c1")).boundingBox();
  const lo = await page.locator(node("c7")).boundingBox();
  expect(hi.y).toBeLessThan(lo.y);
});

test("elevmap: the waterline reports the cut off the player's own plot", async ({ page }) => {
  await dragTo(page, "c1", 1400);      // above 1125
  await dragTo(page, "c3", 1050);      // below
  await dragTo(page, "c7", 850);       // below
  await expect(page.locator(".waterline .wlab"))
    .toHaveText("flood height 1125 m — 1 junction still above it");
});

test("elevmap: keyboard moves a node, so the escape is reachable without a mouse", async ({ page }) => {
  await page.locator(node("c1")).focus();
  await page.keyboard.press("ArrowUp");
  await expect(page.locator(`${node("c1")} .nval`)).not.toHaveText("—");
  expect(await page.evaluate(() => window.__gameState.heights_placed)).toBe(1);
});

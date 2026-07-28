// e2e test for the test-play mixer's SOLVE/DOOR sting API (added 2026-07-21): PanoMixer.solveSounds()
// must return the current room's solve stings — resolved per-gate (puzzle+lock hotspots) with the
// room- then scenario-level fallback, deduped by src — so the mixer can fire each door-open one-shot
// WITHOUT solving the puzzle, and PanoMixer.fireSolve(src) must play one without throwing.
//
// Data-driven off scenario.json (we recompute the expected resolved stings straight from the room's
// hotspots and compare to what the live engine returns), so it survives answer/audio re-authoring. The
// two code paths — this recompute vs the engine's closure over `room`/`SCENARIO` — are independent, so a
// break in the resolution or dedup logic makes them diverge. PanoMixer is defined in pano-player.js on
// every play.html (the SFX_MIXER overlay is test_play-only, but the API it drives is always present).
const { test, expect } = require("@playwright/test");

const ALASKA = "/escape_rooms/rooms/data_vis/alaska/play.html";

test("alaska room 1: PanoMixer exposes the room's solve stings, deduped, and can fire one", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto(ALASKA);

  // Recompute the expected resolved solve stings for the first BUILT room straight from scenario.json,
  // mirroring the engine's resolution (per-gate solveSfx → room.solveSfx → SCENARIO.solveSfx, deduped).
  const expected = await page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    const rooms = d.rooms || [];
    const r1 = rooms.find((r) => r.panorama);                        // first BUILT room
    const gates = (r1.hotspots || []).filter((h) => h.type === "puzzle" || h.type === "lock");
    const seen = new Set(), out = [];
    const add = (ss) => {
      if (!ss) return;
      const src = typeof ss === "string" ? ss : ss.src;
      if (!src || seen.has(src)) return;
      seen.add(src);
      out.push(src);
    };
    gates.forEach((h) => add(h.solveSfx || r1.solveSfx || d.solveSfx));
    if (!out.length) add(r1.solveSfx || d.solveSfx);
    return out;                                                      // ordered, deduped list of srcs
  });
  // Alaska room 1 has a puzzle sting, so there is at least one to test (guards a vacuous pass).
  expect(expected.length).toBeGreaterThan(0);

  // enter the scenario and wait for the room to come up
  await page.fill("#x500", "test0001");
  await page.locator("#enter").click();
  await expect(page.locator(".hsmark.puzzle")).not.toHaveCount(0, { timeout: 30_000 });

  // the live engine's mixer API returns the same resolved, deduped set…
  const got = await page.evaluate(() => (window.PanoMixer.solveSounds() || []).map((s) => s.src));
  expect(got).toEqual(expected);

  // …every entry carries a human label for the fire button…
  const labelled = await page.evaluate(() =>
    (window.PanoMixer.solveSounds() || []).every((s) => typeof s.label === "string" && s.label.length));
  expect(labelled).toBe(true);

  // …and firing one goes through the real playOneShot path without throwing.
  const fired = await page.evaluate(() => {
    try { window.PanoMixer.fireSolve(window.PanoMixer.solveSounds()[0].src, 0.9); return true; }
    catch (e) { return String(e); }
  });
  expect(fired).toBe(true);

  expect(errors, `no uncaught page errors:\n${errors.join("\n")}`).toEqual([]);
});

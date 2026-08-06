// e2e smoke test — loads each built scenario in a real headless browser and checks it comes up:
// scenario.json parses, pano-player.js runs without throwing, the landing screen shows, and after
// Enter the Pannellum panorama renders with clickable hotspots. This catches the big regressions a
// static presence-check can't — a malformed scenario.json, a JS error in the shared player, a missing
// asset, or a hotspot that never renders. It does NOT drive a full WebR puzzle-solve — a solve/advance
// e2e (click puzzle -> boot WebR -> answer -> assert door swap + advance) is the planned next test.
const { test, expect } = require("@playwright/test");

// The scenarios to smoke. Add a row when a new one is built.
const SCENARIOS = [
  { name: "alaska", path: "/escape_rooms/rooms/data_vis/alaska/play.html" },
  { name: "hawaii", path: "/escape_rooms/rooms/data_vis/hawaii/play.html" },
  { name: "trees", path: "/escape_rooms/rooms/wrangling/trees/play.html" },
];

for (const sc of SCENARIOS) {
  test(`${sc.name}: loads, enters, and renders a hotspot`, async ({ page }) => {
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));

    await page.goto(sc.path);

    // Landing screen: the Enter button carries the scenario's enterLabel (proves scenario.json loaded).
    const enter = page.locator("#enter");
    await expect(enter).toBeVisible();
    await expect(enter).not.toHaveText("");

    // Begin — no x500 needed here anymore (it's collected on the submission-prep screen).
    await enter.click();

    // We're now in a room: the panorama container is showing.
    await expect(page.locator("#pano")).toBeVisible();

    // Pannellum renders each hotspot as a .hsmark div (cssClass "hsmark <type>") once the WebGL
    // panorama is up. Assert PRESENCE, not viewport-visibility: you enter facing the door, so
    // hotspots across the room are rotated out of view (Pannellum hides out-of-arc ones) — that's a
    // camera-yaw detail, not a regression. At least one built-room hotspot being attached proves the
    // scene loaded and hotspots registered.
    await expect(page.locator(".hsmark")).not.toHaveCount(0, { timeout: 30_000 });

    // The persistent field-notebook chip is present in every room.
    await expect(page.locator("#notebookChip")).toBeVisible();

    expect(errors, `no uncaught page errors:\n${errors.join("\n")}`).toEqual([]);
  });
}

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
  { name: "temple", path: "/escape_rooms/rooms/hierarchical_clustering/temple/play.html" },
  // hospital + airship are PUBLISHED (status: ready) and were going into a live course uncovered here
  // (2026-08-28). Every `ready` scenario belongs in this list — that is the point of the smoke.
  { name: "hospital", path: "/escape_rooms/rooms/data_vis2/hospital/play.html" },
  { name: "airship", path: "/escape_rooms/rooms/data_vis2/airship/play.html" },
  { name: "egypt", path: "/escape_rooms/rooms/wrangling/egypt/play.html" },
  { name: "canyon", path: "/escape_rooms/rooms/hierarchical_clustering/canyon/play.html" },
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

// The submission code exists ONLY inside the downloaded PDF, so a CDN outage for jsPDF means a student
// simply cannot submit — there is no other route to the code. jsPDF is therefore vendored (2026-08-28).
// This pins that: with every CDN hard-blocked at the network layer, jsPDF must still load and produce a
// real PDF. If someone ever points a shell back at a CDN, this fails.
test("jsPDF is vendored: a PDF still generates with every CDN blocked", async ({ page }) => {
  await page.route("**://*/**", route =>
    /cdn\.jsdelivr\.net|unpkg\.com|cdnjs/.test(route.request().url()) ? route.abort() : route.continue());
  await page.goto("/escape_rooms/rooms/data_vis/alaska/play.html");
  const out = await page.evaluate(() => {
    const J = window.jspdf && window.jspdf.jsPDF;
    if (!J) return null;
    const doc = new J({ unit: "pt", format: "a4" });
    doc.text("submission smoke test", 40, 40);
    return doc.output("datauristring").slice(0, 30);
  });
  expect(out, "jsPDF did not load with CDNs blocked — is a shell still pointing at one?").toBeTruthy();
  expect(out.startsWith("data:application/pdf")).toBe(true);
});

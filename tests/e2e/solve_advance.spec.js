// e2e solve/advance test — the first REAL end-to-end drive of a room in a headless browser:
// enter the scenario, click the first room's puzzle hotspot, answer the multiple-choice correctly,
// and assert the whole solve pipeline fires — the answer auto-logs to the field notebook, the forward
// door swaps to its OPEN state, and walking through it advances to the next room. This is the
// behaviour the parent AGENTS.md flagged as manual-verify-only (door-nav + swap + advance).
//
// MCQ grading is pure JS (a selected-index compare) — it does NOT need WebR to finish booting — so this
// runs fast and deterministically. It's data-driven off scenario.json (the correct index, option count,
// and door target are read live), so it keeps passing when answer keys or wording are re-authored.
//
// Hotspots are clicked via dispatchEvent('click'), not a real mouse click: you enter a room facing the
// door, so the puzzle marker is rotated out of Pannellum's arc (its div is present but hidden). A
// dispatched click still fires the hotspot's handler, which is what we're exercising.
const { test, expect } = require("@playwright/test");

const ALASKA = "/escape_rooms/rooms/data_vis/alaska/play.html";

test("alaska room 1: correct MCQ logs the answer, swaps the door, and advances", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto(ALASKA);

  // Read the room's own answer key + door target from scenario.json, so the test tracks re-authoring.
  const info = await page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    const rooms = d.rooms || [];
    const r1 = rooms.find((r) => r.panorama);                       // first BUILT room
    const puz = (r1.hotspots || []).find((h) => h.type === "puzzle");
    const door = (r1.hotspots || []).find(
      (h) => h.type === "door" && (h.direction || "forward") === "forward");
    const target = door && door.to ? rooms.find((r) => r.key === door.to) : null;
    const entryText = (t) => (!t ? "" : typeof t === "string" ? t : t.text || "");
    return {
      correct: puz.question.correct,
      nopts: (puz.question.options || []).length,
      targetTitle: target ? target.title || "" : "",
      targetHasEntry: target ? !!entryText(target.entry) : false,
    };
  });
  expect(info.nopts).toBeGreaterThanOrEqual(6);                     // house rule: ≥6 options

  // enter the scenario (x500 is now collected at submission, not here)
  await page.locator("#enter").click();

  // the room is up once its puzzle hotspot has registered (present, not necessarily in-view)
  const puzzle = page.locator(".hsmark.puzzle").first();
  await expect(page.locator(".hsmark.puzzle")).not.toHaveCount(0, { timeout: 30_000 });
  await puzzle.dispatchEvent("click");

  // the multiple-choice modal opens with the authored options
  await expect(page.locator("#modal.open")).toBeVisible();
  const opts = page.locator("#modal .qopt input[type=radio]");
  await expect(opts).toHaveCount(info.nopts);

  // answer correctly and submit
  await opts.nth(info.correct).check();
  await page.locator("#modal .qsubmit").click();
  await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });

  // the solve pipeline ran end-to-end: the confirmed answer auto-logged to the field notebook
  await expect(page.locator("#notebookCount")).toHaveText(/\(1\)/, { timeout: 10_000 });

  // and the forward door swapped to its OPEN state (present in the DOM; may be rotated out of view)
  await expect(page.locator(".hsmark.door.open")).not.toHaveCount(0, { timeout: 10_000 });

  // walking through the open door advances into the next room
  await page.locator(".hsmark.door.open").first().dispatchEvent("click");
  if (info.targetHasEntry) {
    // the next room fires its interstitial "loading" card first — continue past it
    await expect(page.locator("#loading.open")).toBeVisible({ timeout: 10_000 });
    await page.locator("#loadBtn").click();
  }
  if (info.targetTitle) {
    await expect(page.locator("#hudroom")).toHaveText(info.targetTitle, { timeout: 10_000 });
  }

  expect(errors, `no uncaught page errors:\n${errors.join("\n")}`).toEqual([]);
});

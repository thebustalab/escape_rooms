// e2e harness-UI test — regression guard for "committing a room's planned hotspots throws you back to
// the top of the page" (fixed 2026-09-01).
//
// WHAT BROKE. The gallery's Hotspots tab (build_world_v2.html, tab 4) draws every built room's committed
// still at full width with its hotspot boxes over it. Its per-room `Commit N planned →` button called
// `refresh()` when it was done. refresh() re-renders EVERY pane and hands back brand new <img> elements;
// a fresh `loading="lazy"` image has no height until it decodes, so the document momentarily collapses
// and the browser has no scroll position left to keep. On canyon — nine 3072x1024 panoramas — committing
// the eighth room dumped you at the top and you scrolled the whole way back down.
//
// THE FIX. commitPlanned() now updates that ONE room in place: it re-reads the room, redraws its boxes,
// and swaps its count pills and its button. The <img> is never touched. This is only safe because tab 4
// is the sole consumer of committed-hotspot data in this page — if a fifth consumer appears, this
// assumption needs revisiting (noted in authoring_v2/AGENTS.md).
//
// THE CLEAN SIGNATURE. Across a commit: window.scrollY is unchanged, document height is unchanged, and
// the <img> elements are the SAME nodes as before (tagged with an expando that a re-render would drop).
//
// WHICH ASSERTION IS LOAD-BEARING — measured, not assumed. Negative control (restoring `await refresh()`
// in commitPlanned) fails on **imgsKept**, not on scrollY: headless Chromium re-decodes the already-
// cached panoramas fast enough that the document often never visibly collapses, so scroll and height can
// survive the very bug this guards. They are kept because they are the symptom Lucas actually reported,
// but do NOT weaken the image-identity check on the theory that the scroll assertions cover it — in this
// environment they do not.
//
// WHY IT COMMITS AN ALREADY-COMMITTED ROOM. Every scenario in the corpus is now fully promoted, so there
// are no planned hotspots left to commit anywhere. Committing a room whose planned entries are all live
// is a genuine server-side no-op (`created: []`, `already: [...]`, and the scenario file is left
// byte-identical — pinned by test_harness_server.py::test_commit_planned_is_idempotent_...), while
// driving the ENTIRE client path this bug lived in. So the test exercises the fix without needing, or
// creating, un-promoted state.
//
// Drives the live authoring harness on :8752 (see playwright.config.js — reuses the tmux server if up).
const { test, expect } = require("@playwright/test");

const GALLERY = "http://127.0.0.1:8752/build_world_v2.html";
const SCENARIO = "hierarchical_clustering/canyon";   // 9 built rooms — a long enough scroll to lose

test("gallery: committing planned hotspots holds your scroll position", async ({ page }) => {
  await page.goto(GALLERY);
  await page.waitForSelector(`#scenPick option[value="${SCENARIO}"]`, { state: "attached", timeout: 30_000 });
  await page.selectOption("#scenPick", SCENARIO);

  await page.click('#tabs button[data-tab="hotspots"]');
  await page.waitForSelector("#pane-hotspots .hsframe", { timeout: 30_000 });
  // wait for the boxes themselves — the frames exist before /api/scenario has been read
  await page.waitForFunction(
    () => document.querySelectorAll("#pane-hotspots .hsbox").length > 0, null, { timeout: 30_000 });

  // Scroll deep into the pane, then tag the images. A re-render replaces the nodes and the tag goes
  // with them, which is the root cause stated directly rather than inferred from the scroll number.
  const room = await page.evaluate(() => {
    const f = document.querySelectorAll("#pane-hotspots .hsframe");
    const target = f[Math.max(0, f.length - 2)];
    target.scrollIntoView({ block: "center" });
    document.querySelectorAll("#pane-hotspots img").forEach((im, n) => { im.__tag = "orig" + n; });
    return target.dataset.room;
  });
  await page.waitForTimeout(500);

  const before = await page.evaluate(() => ({
    y: Math.round(window.scrollY), h: Math.round(document.body.scrollHeight),
  }));
  expect(before.y, "the test must actually be scrolled down, or it proves nothing").toBeGreaterThan(300);

  // Await commitPlanned's own promise rather than watching for its status text: under the bug the full
  // refresh() destroys the status element, so a text watcher would time out instead of reaching — and
  // reporting — the assertions that say what actually went wrong.
  await page.evaluate((r) => window.commitPlanned(r), room);
  await page.waitForTimeout(700);          // let any (buggy) re-render settle before measuring

  const after = await page.evaluate(() => ({
    y: Math.round(window.scrollY), h: Math.round(document.body.scrollHeight),
    imgsKept: Array.from(document.querySelectorAll("#pane-hotspots img")).every((im) => im.__tag),
  }));

  expect(after.y, "commit must not move the scroll position").toBe(before.y);
  expect(after.h, "commit must not change the document height").toBe(before.h);
  expect(after.imgsKept, "commit must not replace the room images").toBe(true);
});

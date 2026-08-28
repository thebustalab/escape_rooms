// temple: the altar stair is SEALED until all four registers are rebuilt.
//
// WHAT THIS GUARDS. temple is a true open world — every door is `open`/`back`, nothing was gated — so a
// player could walk gate_stair → crawl → vault → altar and do the ungraded ESCAPE before solving a single
// graded puzzle (2026-08-27). One door is now gated: `inner_vault/to_altar` carries
// `availableWhen:{allSolved:[the four graded rooms]}` + a diegetic `lockedBody`, and the vault's base
// panorama was re-generated with the stair head SEALED by a stone slab. The open view is the ORIGINAL
// panorama, stamped back through a state VARIANT when the gate opens.
//
// Three ways that can silently fail, one assertion each:
//   1. the gate doesn't hold  → the door renders `.open` from the start and the escape is reachable early;
//   2. the gate never RELEASES → the door stays locked after all four solves and the scenario is unfinishable;
//   3. the art doesn't swap    → the door opens but the stair still looks sealed (the variant's `when`,
//      `box` or `panorama` is wrong), so the player is told to walk into a wall.
// (3) is the one no other test would catch: nothing else in the corpus composites a variant onto a door
// that is gated rather than switch-driven.
//
// It then walks the FINALE, which was half-wired until 2026-08-27 and read as broken in play: the ledger
// closes → the carried flame (a `dial`) becomes available → tipping it lights the ring (a full-frame state
// variant) → and only then does the canopy bridge unlash, ending the escape. Every step was missing
// something (the dial had no `states` at all, so it rendered a gauge with no buttons and the engine's
// generic fallback hint; nothing carried `endsEscape`, so `escapeDone` could never fire). The bridge is
// LAST on purpose: the player crosses it looking at the fires they just lit.
const { test, expect } = require("@playwright/test");

const URL = "/escape_rooms/rooms/hierarchical_clustering/temple/play.html";
const GRADED = ["sun_gallery", "lamp_hall", "sealed_cell", "inner_vault"];

test("temple: sealed altar stair, then the whole finale — register, flame, fires, bridge", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  // The variant art is proven by a NETWORK REQUEST, not by pixels: compositeVariants `_loadImg`s the
  // variant's panorama, so a fetch of scene_open.png is the engine actually stamping the open stair back
  // in. (Reading the rendered texture is not an option — Pannellum draws in WebGL without
  // preserveDrawingBuffer, so `toDataURL` returns the same blank buffer before and after, which is
  // exactly the vacuous pass this comment exists to prevent.)
  const openArtHits = [];
  page.on("request", (r) => { if (r.url().includes("scene_open.png")) openArtHits.push(r.url()); });
  await page.goto(URL);

  // Read the plan live off scenario.json so the spec survives re-authoring (answers, door order, wording).
  const plan = await page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    const rooms = {};
    d.rooms.forEach((r) => {
      const hs = (r.hotspots || []).filter((h) => h.type !== "ambient");
      rooms[r.key] = {
        title: r.title,
        // index of each door AMONG THE DOOR MARKERS, which is how the spec has to click them
        doors: (r.hotspots || []).filter((h) => h.type === "door")
          .map((h, i) => ({ id: h.id, i, to: h.to })),
        puzzle: (() => {
          const p = hs.find((h) => h.type === "puzzle");
          return p ? { id: p.id, correct: p.question.correct } : null;
        })(),
        altar: (() => {
          const a = (r.hotspots || []).find((h) => h.id === "to_altar");
          return a ? { lockedBody: a.lockedBody, variant: (a.variants || [])[0] } : null;
        })(),
      };
    });
    return { rooms, story: !!d.story };
  });
  expect(plan.rooms.inner_vault.altar.variant.panorama).toBe("inner_vault/scene_open.png");

  // Address hotspots by their own `hs-<id>` marker class — never by position. Counting `.hsmark.door`
  // siblings silently picks a DIFFERENT door whenever the viewer rebuilds mid-composite or a room is
  // re-authored, which is exactly how this spec first went wrong (it walked into the lamp hall).
  const mark = (id) => page.locator(`.hsmark.hs-${id}`);
  const walk = async (_roomKey, doorId, expectTitle) => {
    await mark(doorId).dispatchEvent("click");
    if (expectTitle) await expect(page.locator("#hudroom")).toHaveText(expectTitle, { timeout: 15_000 });
  };
  const solve = async (roomKey) => {
    const p = plan.rooms[roomKey].puzzle;
    await mark(p.id).dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    await page.locator("#modal input[type=radio]").nth(p.correct).check();
    await page.locator("#modal .qsubmit").click();
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 15_000 });
    // the solve fires on a ~900ms timeout AFTER the tick — waiting for the auto-close is the signal
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 15_000 });
  };

  await page.locator("#enter").click();
  await expect(page.locator("#hudroom")).toHaveText(plan.rooms.gate_stair.title, { timeout: 30_000 });

  // --- 1. the gate HOLDS: reach the vault with nothing solved; the stair must be shut ---------------
  await walk("gate_stair", "crawl_hatch", plan.rooms.root_crawl.title);
  await walk("root_crawl", "hatch_vault", plan.rooms.inner_vault.title);
  const altar = mark("to_altar");
  await expect(altar).toHaveClass(/locked/);
  await altar.dispatchEvent("click");
  // a gated door toasts its diegetic lockedBody rather than opening a modal
  await expect(page.locator("#toast")).toContainText(plan.rooms.inner_vault.altar.lockedBody.slice(0, 40));
  await expect(page.locator("#hudroom")).toHaveText(plan.rooms.inner_vault.title);   // did NOT navigate

  // sealed: the open-stair art must not have been fetched at all yet
  expect(openArtHits).toEqual([]);

  // --- 2. solve all four, in an order that walks the real door graph -------------------------------
  await solve("inner_vault");
  await walk("inner_vault", "back_crawl_vault", plan.rooms.root_crawl.title);
  await walk("root_crawl", "hatch_lamps", plan.rooms.lamp_hall.title);
  await solve("lamp_hall");
  await walk("lamp_hall", "back_crawl_lamps", plan.rooms.root_crawl.title);
  await walk("root_crawl", "hatch_cistern", plan.rooms.cistern_stair.title);
  await walk("cistern_stair", "down_stair", plan.rooms.sealed_cell.title);
  await solve("sealed_cell");
  await walk("sealed_cell", "back_cistern", plan.rooms.cistern_stair.title);
  await walk("cistern_stair", "back_crawl_cistern", plan.rooms.root_crawl.title);
  await walk("root_crawl", "hatch_stair", plan.rooms.gate_stair.title);
  await walk("gate_stair", "gallery_door", plan.rooms.sun_gallery.title);
  await solve("sun_gallery");

  // The fourth solve completes the ANALYSIS objective, so the engine shows the analysis-finish card over
  // the room. That card only appears at all because the scenario now has a pending escape (the bridge is
  // flagged `endsEscape`) — without one the engine jumps straight to the submission screen. A player
  // closes it and carries on to the altar; so does this spec.
  await expect(page.locator("#done.open")).toBeVisible({ timeout: 15_000 });
  await page.locator("#doneClose").click();
  await expect(page.locator("#done.open")).toBeHidden();

  // --- 3. the gate RELEASES, and the ART follows ---------------------------------------------------
  await walk("sun_gallery", "back_stair", plan.rooms.gate_stair.title);
  await walk("gate_stair", "crawl_hatch", plan.rooms.root_crawl.title);
  await walk("root_crawl", "hatch_vault", plan.rooms.inner_vault.title);
  const altar2 = mark("to_altar");
  await expect(altar2).toHaveClass(/open/, { timeout: 15_000 });
  // the variant composited — the open-stair art is now being loaded and stamped over the sealed base
  await expect(async () => { expect(openArtHits.length).toBeGreaterThan(0); }).toPass({ timeout: 15_000 });
  // and it actually leads somewhere. RETRY the click: compositing the variant rebuilds the Pannellum
  // viewer, and a click that lands during that rebuild is dropped (seen once). A player just clicks
  // again; the spec must not go red for it.
  await expect(async () => {
    await altar2.dispatchEvent("click");
    await expect(page.locator("#hudroom")).toHaveText(plan.rooms.sun_altar.title, { timeout: 4_000 });
  }).toPass({ timeout: 20_000 });

  // --- 4. the finale: register → flame → fires → out over the bridge -------------------------------
  const dialCard = page.locator("#modal .dialface");

  // the flame is not available until the sacred register is closed
  await mark("flame_dial").dispatchEvent("click");
  await expect(page.locator("#modal.open")).toBeVisible();
  await expect(dialCard).toHaveCount(0);                       // shows the lockedBody, not the dial
  // Tipping the flame re-renders the room to composite the lit ring, which can rebuild the modal's
  // surroundings mid-click — so close with a retry rather than a single press.
  await expect(async () => {
    await page.locator("#mback").click();
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 3_000 });
  }).toPass({ timeout: 20_000 });
  // …and neither is the way out
  await expect(mark("temple_gate")).toHaveClass(/locked/);

  // close the ledger: every row set to its verified god, in one press
  await mark("register_gods").dispatchEvent("click");
  await expect(page.locator("#modal .ledgercard")).toBeVisible();
  const answers = await page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    const led = d.rooms.find((r) => r.key === "sun_altar").hotspots.find((h) => h.type === "ledger");
    return led.rows.map((r) => [r.id, r.answer]);
  });
  for (const [rowId, answer] of answers) {
    await page.selectOption(`#modal .verdict[data-row="${rowId}"]`, answer);
  }
  await page.locator("#modal .ledgercard .qsubmit").click();
  // the ledger's own authored correct-feedback (NOT the widgets fixture's "ALL CONFIRMED" stub)
  await expect(page.locator("#modal .ledgercard .qfeedback.ok")).toBeVisible();
  await expect(page.locator("#modal.open")).toBeHidden({ timeout: 15_000 });

  // now the flame answers, and tipping it lights the ring (a full-frame variant → a new image fetch)
  const litArtHits = [];
  page.on("request", (r) => { if (r.url().includes("scene_lit.png")) litArtHits.push(r.url()); });
  await mark("flame_dial").dispatchEvent("click");
  await expect(dialCard).toBeVisible();
  // the authored hint, NOT the engine's world-neutral fallback (and never the old "in the ship" one)
  const dialText = await page.locator("#modal").textContent();
  expect(dialText).toContain("Tip the flame into the channel");
  expect(dialText).not.toMatch(/ship/i);
  await page.locator("#modal button", { hasText: "Tip the flame into the channel" }).click();
  await expect(async () => { expect(litArtHits.length).toBeGreaterThan(0); }).toPass({ timeout: 15_000 });
  // The dial does NOT close itself — it is no longer the terminal gesture, the bridge is. Tipping it
  // re-renders the room to composite the lit ring, which can rebuild the modal's surroundings mid-click,
  // so close with a retry rather than a single press.
  await expect(async () => {
    await page.locator("#mback").click();
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 3_000 });
  }).toPass({ timeout: 20_000 });

  // …and only now does the bridge unlash. Crossing it IS the ending, taken while the fires burn.
  const bridge = mark("temple_gate");
  await expect(bridge).toHaveClass(/open/, { timeout: 15_000 });
  await expect(async () => {
    await bridge.dispatchEvent("click");
    await expect(page.locator("#done.open")).toBeVisible({ timeout: 4_000 });
  }).toPass({ timeout: 20_000 });
  const escapeTitle = await page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    return d.escapeDone.title;
  });
  await expect(page.locator("#doneTitle")).toHaveText(escapeTitle);

  expect(errors).toEqual([]);
});

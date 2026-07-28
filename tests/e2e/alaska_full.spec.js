// e2e full-scenario drive of Alaska ("Signal in the Cold") — the whole two-objective path in a real
// headless browser: solve the four analysis rooms in order — R1/R2 MCQs (pH>8 → Mg-in-NOAT) then R3/boss
// Type 4 pick-the-point rooms (chloride outlier → warmest lake), where you draw the ggiraph chart and
// CLICK the tagged point — confirm the graded Canvas code mints at the boss, pick up Claire's four image
// fragments (the three coloured filtered-glass templates + the tail-number board) and confirm they STACK
// as images in the field notebook, then crack the escape keypad and reach the escape finish.
//
// This exercises the wiring (all four puzzles, door targets/gating, the lock), the Type 4 pick-the-point
// path (ggiraph render + data-id click grading), AND the image-in-notebook engine feature (pickup clues
// logging their `image`). Data-driven off scenario.json (MCQ indices, pick answers, door targets, the
// lock answer) so it survives re-authoring. The two pick rooms boot WebR + install ggiraph, so the test
// is WebR-heavy (see the raised timeout below) — the MCQ + lock grading remain pure JS.
//
// Hotspots are clicked via dispatchEvent('click') (you enter facing the door, so other markers are
// rotated out of Pannellum's arc but their divs + handlers are live). Pannellum renders our hotspots
// with cssClass "hsmark <type> <state>" in array order, so forward/back doors are told apart by their
// rank among the room's door hotspots (read from scenario.json), not by any DOM id (Pannellum sets none).
const { test, expect } = require("@playwright/test");

const ALASKA = "/escape_rooms/rooms/data_vis/alaska/play.html";

test("alaska: full analysis + notebook image-stack + keypad escape", async ({ page }) => {
  test.setTimeout(300_000);   // two pick rooms boot WebR + lazy-install ggiraph (~20-40s boot, ~10s install)
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto(ALASKA);

  // Read the whole scenario's answer key + navigation graph up front, so the drive tracks re-authoring.
  const S = await page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    const rooms = (d.rooms || []).filter((r) => r.panorama);
    const hasEntry = (r) => !!(r.entry && (typeof r.entry === "string" ? r.entry : r.entry.text));
    const byKey = (k) => rooms.find((r) => r.key === k);
    return {
      rooms: rooms.map((r) => {
        const doors = (r.hotspots || []).filter((h) => h.type === "door");
        const fwdRank = doors.findIndex((h) => (h.direction || "forward") === "forward");
        const fwd = doors[fwdRank];
        const puz = (r.hotspots || []).find((h) => h.type === "puzzle");
        const lock = (r.hotspots || []).find((h) => h.type === "lock");
        const q = puz && puz.question, pk = puz && puz.pick;   // a puzzle is EITHER an MCQ or a pick-the-point
        const target = fwd && fwd.to ? byKey(fwd.to) : null;
        return {
          key: r.key,
          title: r.title || "",
          phase: r.phase || "analysis",
          isPick: !!pk,
          correct: q ? q.correct : null,
          nopts: q ? (q.options || []).length : 0,
          pickAnswer: pk ? pk.answer : null,
          lockAnswer: lock ? lock.answer : null,
          fwdRank,                                   // rank of the forward door among this room's doors
          targetTitle: target ? target.title || "" : "",
          targetHasEntry: target ? hasEntry(target) : false,
        };
      }),
    };
  });
  const room = (k) => S.rooms.find((r) => r.key === k);

  // --- helpers ---------------------------------------------------------------
  async function answerMCQ(r) {
    await expect(page.locator(".hsmark.puzzle")).not.toHaveCount(0, { timeout: 30_000 });
    await page.locator(".hsmark.puzzle").first().dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    const opts = page.locator("#modal .qopt input[type=radio]");
    await expect(opts).toHaveCount(r.nopts);
    await opts.nth(r.correct).check();
    await page.locator("#modal .qsubmit").click();
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });
    // A correct MCQ fires the actual solve (close modal + solveRoom) on a ~900ms delay. WAIT for the
    // modal to auto-close before doing anything else — otherwise later clicks race the pending solve.
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 });
  }
  // Type 4 pick-the-point: open the puzzle, wait for the live R session, draw the ggiraph chart, then
  // CLICK the answer point (the SVG geom tagged data-id="<pick.answer>"). Grades like a check (answer=1).
  async function solvePick(r) {
    await expect(page.locator(".hsmark.puzzle")).not.toHaveCount(0, { timeout: 30_000 });
    await page.locator(".hsmark.puzzle").first().dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    // The picker needs the booted WebR session; wait for it (boots eagerly at scenario start).
    await expect(page.locator("#webr-status")).toContainText("ready", { timeout: 90_000 });
    // The picker now renders the STUDENT'S OWN plot (2026-07-28): they build a ggplot and assign it to
    // `p`, and the engine tags it by idColumn. Assign a per-lake plot to `p` (tags all lakes, so the
    // room's answer is clickable in both pick rooms) and print it — its rendered canvas is our signal the
    // run finished (so `p` is assigned) before we draw.
    await page.locator("#code-input").fill("p <- ggplot(dplyr::distinct(alaska_lake_data, lake, water_temp), aes(lake, water_temp)) + geom_col()\np");
    await page.locator("#run-btn").click();
    await expect(page.locator("#webr-output canvas.webr-plot")).not.toHaveCount(0, { timeout: 120_000 });
    // "Draw the clickable chart" → renderStudentPickSvg (first pick room also lazy-installs ggiraph → allow generous time).
    const holder = page.locator("#modal .pickholder");
    await page.locator("#modal .qsubmit").click();
    await expect(holder.locator("[data-id]")).not.toHaveCount(0, { timeout: 120_000 });
    // Click the correct tagged point on the plot (dispatchEvent to bypass SVG actionability checks).
    await holder.locator(`[data-id="${r.pickAnswer}"]`).first().dispatchEvent("click");
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 });
  }
  // Click each clue; if it offers "Add to notebook", take it. Returns how many were picked up.
  async function pickupClues() {
    // Close any modal that's still open first — the puzzle modal mounts the WebR console into #mbody,
    // and opening a clue over it (openModal clears #mbody) would destroy #console-block and wedge
    // closeModal. With it closed, the console sits safely back in #console-holder.
    if (await page.locator("#modal.open").count()) {
      await page.locator("#mback").click();
      await expect(page.locator("#modal.open")).toBeHidden();
    }
    const clues = page.locator(".hsmark.clue");
    const n = await clues.count();
    let picked = 0;
    for (let i = 0; i < n; i++) {
      await clues.nth(i).dispatchEvent("click");
      await expect(page.locator("#modal.open")).toBeVisible();
      const add = page.locator("#modal button", { hasText: "Add to notebook" });
      if (await add.count()) { await add.click(); picked++; }
      await page.locator("#mback").click();
      await expect(page.locator("#modal.open")).toBeHidden();
    }
    return picked;
  }
  async function notebookCount() {
    const t = await page.locator("#notebookCount").textContent();
    const m = /\((\d+)\)/.exec(t || "");
    return m ? parseInt(m[1], 10) : 0;
  }
  async function walkForward(r) {
    // After the room is solved, all its doors are open (forward now, back always) in array order, so the
    // forward door is the fwdRank-th open door. dispatchEvent because the marker may be rotated out of view.
    await page.locator(".hsmark.door.open").nth(r.fwdRank).dispatchEvent("click");
    if (r.targetHasEntry) {
      await expect(page.locator("#loading.open")).toBeVisible({ timeout: 10_000 });
      await page.locator("#loadBtn").click();
    }
    if (r.targetTitle) {
      await expect(page.locator("#hudroom")).toHaveText(r.targetTitle, { timeout: 10_000 });
    }
  }

  // --- enter (x500 is now collected on the submission screen, not here) ------
  await page.locator("#enter").click();
  await expect(page.locator("#hudroom")).toHaveText(room("room1").title, { timeout: 30_000 });

  // --- room 1: solve, pick up the RED template, advance ----------------------
  await answerMCQ(room("room1"));
  await expect(page.locator("#notebookCount")).toHaveText(/\(1\)/, { timeout: 10_000 }); // answer auto-logged
  expect(await pickupClues()).toBe(1);                                                   // Claire's red template
  await expect(page.locator("#notebookCount")).toHaveText(/\(2\)/);
  await walkForward(room("room1"));

  // --- room 2: solve, pick up GREEN, advance ---------------------------------
  await answerMCQ(room("room2"));
  expect(await pickupClues()).toBe(1);
  await walkForward(room("room2"));

  // --- room 3: solve (pick-the-point), pick up BLUE, advance -----------------
  const nbBefore = await notebookCount();
  await solvePick(room("room3"));
  // regression: a solved PICK room auto-logs its feedback.correct to the notebook (puzzleNoteText `pick`
  // fix — without it logToNotebook drops the empty note and the entry is silently lost).
  await expect(page.locator("#notebookCount")).toHaveText(new RegExp(`\\(${nbBefore + 1}\\)`), { timeout: 10_000 });
  expect(await pickupClues()).toBe(1);
  await walkForward(room("room3"));

  // --- boss: solve (pick-the-point) → analysis finishes and mints the graded code
  await solvePick(room("boss"));
  await expect(page.locator("#done.open")).toBeVisible({ timeout: 10_000 });
  // The graded completion code moved OFF the finish card onto the submission-prep screen (submission-prep
  // refactor): a scenario WITH an escape shows an "analysis complete" card with the code hidden + a
  // "skip to submit" route. Peek at the submission screen to confirm the code is minted + non-empty, then
  // back out to the room to do the (ungraded) escape (openSubmitPrep + subBack are non-destructive; the
  // escape stays gated on the already-solved boss).
  await expect(page.locator("#codeWrap")).toBeHidden();
  await page.locator("#doneToSubmit").click();                                          // → submission-prep screen
  await expect(page.locator("#submitPrep.open")).toBeVisible({ timeout: 10_000 });
  // x500 is now entered HERE (not on the landing screen); confirming it mints + reveals the code.
  await page.fill("#subX500", "test0001");
  await page.locator("#subX500Go").click();
  await expect(page.locator("#subCodeVal")).toBeVisible({ timeout: 10_000 });
  expect((await page.locator("#subCodeVal").textContent()).trim().length).toBeGreaterThan(0);
  await page.locator("#subBack").click();                                               // back to the room
  await expect(page.locator("#submitPrep.open")).toBeHidden();
  await expect(page.locator("#done.open")).toBeHidden();
  expect(await pickupClues()).toBe(1);                                                   // Claire's tail-number board

  // the notebook now holds all FOUR image fragments, stacked (the feature under test)
  await page.locator("#notebookChip").click();
  await expect(page.locator("#modal.open")).toBeVisible();
  expect(await page.locator("#modal img").count()).toBeGreaterThanOrEqual(4);
  // Phase-1 engine: the images render as draggable tiles on the collage board, and dragging one snaps it
  // a whole cell over (the shared snap-grid behind the hospital facet-collage + this overlay). Regression
  // home for the drag mechanic.
  const tiles = page.locator("#nbBoard .nbtile");
  expect(await tiles.count()).toBeGreaterThanOrEqual(4);
  const before = await tiles.first().evaluate((el) => el.style.left);
  const bb = await tiles.first().boundingBox();
  await page.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2);
  await page.mouse.down();
  await page.mouse.move(bb.x + bb.width / 2 + 132, bb.y + bb.height / 2, { steps: 6 });
  await page.mouse.up();
  const after = await tiles.first().evaluate((el) => el.style.left);
  expect(after).not.toBe(before);   // the tile snapped to a new cell
  await page.locator("#mback").click();
  await expect(page.locator("#modal.open")).toBeHidden();

  // --- boss → escape phase (the helipad door is gated on the boss puzzle) -----
  await walkForward(room("boss"));   // → escape1 "Out on the helipad"

  // --- escape: the keypad only opens on Claire's tail number (N0KR) ----------
  const answer = room("escape1").lockAnswer;
  expect(answer).toBeTruthy();
  await page.locator(".hsmark.lock").first().dispatchEvent("click");
  await expect(page.locator("#modal.open")).toBeVisible();
  await page.fill("#lockInput", answer);
  await page.locator("#modal .qsubmit").click();
  await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });
  // the lock releases on a ~900ms delay (close modal + solveRoom). WAIT for the modal to auto-close so
  // the solve has actually run — otherwise the hatch is still locked when we click it.
  await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 });
  // the hatch is now open — escape1's two doors (back + hatch) are both open; the forward hatch is last
  await expect(page.locator(".hsmark.door.open")).toHaveCount(2, { timeout: 10_000 });
  await page.locator(".hsmark.door.open").last().dispatchEvent("click");
  await expect(page.locator("#done.open")).toBeVisible({ timeout: 10_000 });
  await expect(page.locator("#doneTitle")).toHaveText((await page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    return (d.escapeDone && d.escapeDone.title) || "You escaped!";
  })));
  await expect(page.locator("#codeWrap")).toBeHidden();   // escape finish carries NO code (ungraded)

  expect(errors, `no uncaught page errors:\n${errors.join("\n")}`).toEqual([]);
});

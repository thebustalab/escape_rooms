// playthrough.js — a reusable, scenario-agnostic FULL-PLAYTHROUGH harness for the escape-room player.
//
// It actually PLAYS a scenario end to end in a real headless browser + WebR: navigate the built rooms,
// solve EVERY graded analysis puzzle by its type (MCQ / console-`check` / pick-the-point / grid), let the
// analysis objective complete and mint the submission code, then run the ESCAPE objective (walk into an
// escape-phase room and/or key the in-room `endsEscape` lock/grid) and assert the escape finish + that a
// submission code is minted. This generalises the hand-written alaska_full.spec.js so a new scenario needs
// only a row in the spec's SCENARIOS list (plus, for any console-`check` room, the R answer to type).
//
// Design, mirroring the engine (see shared/pano-player.js):
//   • The whole answer key + door graph is read LIVE from scenario.json (readScenarioPlan) so the harness
//     tracks re-authoring: MCQ correct index + option count, pick answer + idColumn, console-check
//     `requires`, lock answers, grid answers, per-room forward-door rank + target, phase, escapeDone title.
//   • Hotspots are clicked via dispatchEvent("click") — you enter facing the door, so other markers are
//     rotated out of Pannellum's arc (their divs + handlers are live, but a real mouse click can't reach
//     them). This is the same pattern the existing specs use.
//   • DELAYED-SOLVE gotcha: a correct MCQ / check / pick / lock fires the real solve (closeModal +
//     solveRoom) on a ~900ms setTimeout AFTER showing `.qfeedback.ok`. So we ALWAYS wait for
//     `#modal.open` to be hidden after a correct answer — the auto-close is the signal the solve ran.
//   • Console-`check` rooms boot real R in WebR (~20–40s first boot, reused across the scenario). The R
//     assignment to type is supplied per room by the caller (consoleAnswers[roomKey]) — sourced from the
//     room's intended answer (its `check.expr` / hint), kept beside the spec so it survives re-authoring
//     of prose but is checked against the LIVE grader.
//
// What it covers: the wiring of every graded gate, door nav + gating, the two-phase analysis→escape
// boundary, the analysis-finish code mint, and the escape finish. What it does NOT cover (left to
// alaska_full.spec.js): the notebook image-stack / collage-drag feature, and the submission PDF export.

const { expect } = require("@playwright/test");

// Read a scenario's full answer key + navigation graph from its scenario.json (fetched relative to the
// already-loaded play.html). Returns only what the harness drives, in a browser-serialisable shape.
async function readScenarioPlan(page) {
  return page.evaluate(async () => {
    const d = await (await fetch("scenario.json", { cache: "no-store" })).json();
    const rooms = (d.rooms || []).filter((r) => r.panorama); // BUILT rooms only (the player skips stubs)
    const byKey = (k) => rooms.find((r) => r.key === k);
    const hasEntry = (r) => !!(r && r.entry && (typeof r.entry === "string" ? r.entry : r.entry.text));
    const phaseOf = (r) => r.phase || "analysis";
    return {
      id: d.id,
      scenario: d.scenario,
      escapeDoneTitle: (d.escapeDone && d.escapeDone.title) || "You escaped!",
      rooms: rooms.map((r) => {
        const hs = r.hotspots || [];
        const doors = hs.filter((h) => h.type === "door");
        const puz = hs.find((h) => h.type === "puzzle");
        const q = puz && puz.question, ck = puz && puz.check, pk = puz && puz.pick;
        const fwdRank = doors.findIndex((h) => (h.direction || "forward") === "forward");
        const fwd = fwdRank >= 0 ? doors[fwdRank] : null;
        const target = fwd && fwd.to ? byKey(fwd.to) : null;
        return {
          key: r.key,
          title: r.title || "",
          phase: phaseOf(r),
          puzzle: puz ? {
            id: puz.id,
            type: pk ? "pick" : (ck ? "check" : "mcq"),
            correct: q ? q.correct : null,
            nopts: q ? (q.options || []).length : 0,
            pickAnswer: pk ? pk.answer : null,
            checkRequires: ck ? (ck.requires || []) : null,
          } : null,
          locks: hs.filter((h) => h.type === "lock").map((l) => ({
            id: l.id, answer: l.answer || "", mode: l.mode || null, endsEscape: !!l.endsEscape,
          })),
          grids: hs.filter((h) => h.type === "grid").map((g) => ({
            id: g.id, answer: g.answer || {}, endsEscape: !!g.endsEscape,
          })),
          fwdRank,
          fwdTo: fwd ? (fwd.to || null) : null,
          fwdEndsEscape: fwd ? !!fwd.endsEscape : false,
          targetTitle: target ? (target.title || "") : "",
          targetHasEntry: target ? hasEntry(target) : false,
        };
      }),
    };
  });
}

class Playthrough {
  // page: Playwright page; plan: from readScenarioPlan; consoleAnswers: { <roomKey>: "<R code to type>" }
  constructor(page, plan, consoleAnswers) {
    this.page = page;
    this.plan = plan;
    this.consoleAnswers = consoleAnswers || {};
  }

  room(key) { return this.plan.rooms.find((r) => r.key === key); }
  // the room plan for the room currently shown in the HUD
  async currentRoom() {
    const t = (await this.page.locator("#hudroom").textContent() || "").trim();
    return this.plan.rooms.find((r) => r.title === t) || null;
  }

  // ---- per-type puzzle solvers ------------------------------------------------
  async answerMCQ(rp) {
    const page = this.page;
    await expect(page.locator(".hsmark.puzzle")).not.toHaveCount(0, { timeout: 30_000 });
    await page.locator(".hsmark.puzzle").first().dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    const opts = page.locator("#modal .qopt input[type=radio]");
    await expect(opts).toHaveCount(rp.puzzle.nopts);
    await opts.nth(rp.puzzle.correct).check();
    await page.locator("#modal .qsubmit").click();
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 }); // wait out the ~900ms solve
  }

  // console-`check`: type the caller-supplied solving R assignment, Run it on the live session, then Check.
  async solveCheck(rp) {
    const page = this.page;
    const code = this.consoleAnswers[rp.key];
    if (!code) throw new Error(`No console answer supplied for console-check room "${rp.key}" — add it to consoleAnswers`);
    await expect(page.locator(".hsmark.puzzle")).not.toHaveCount(0, { timeout: 30_000 });
    await page.locator(".hsmark.puzzle").first().dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    // WebR boots eagerly at scenario start; the Run button enables when the session is ready.
    await expect(page.locator("#run-btn")).toBeEnabled({ timeout: 120_000 });
    await page.locator("#code-input").fill(code);
    await page.locator("#webr-output").evaluate((el) => (el.innerHTML = "")); // clear so we can detect the new run
    await page.locator("#run-btn").click();
    // A finished run appends to #webr-output (text, a plot canvas, or a muted "(no output)" for a bare
    // assignment). Waiting for that guarantees the required vars are assigned before we hit Check.
    await expect(page.locator("#webr-output .webr-out, #webr-output canvas.webr-plot")).not.toHaveCount(0, { timeout: 120_000 });
    await page.locator("#modal .qsubmit").click(); // "Check my answer" — grades check.expr on the live session
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 20_000 });
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 });
  }

  // Type 4 pick-the-point: build a per-item plot in the live console, assign it to `p`, render the
  // clickable chart, then click the tagged answer point. (Same shape as alaska_full.spec.js.)
  // consoleAnswers[roomKey] is the R plot code (assigns a ggplot to `p`, tagging every candidate).
  async solvePick(rp) {
    const page = this.page;
    await expect(page.locator(".hsmark.puzzle")).not.toHaveCount(0, { timeout: 30_000 });
    await page.locator(".hsmark.puzzle").first().dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    await expect(page.locator("#run-btn")).toBeEnabled({ timeout: 120_000 });
    const plotCode = this.consoleAnswers[rp.key];
    if (!plotCode) throw new Error(`No pick plot code supplied for pick room "${rp.key}" — add it to consoleAnswers`);
    await page.locator("#code-input").fill(plotCode);
    await page.locator("#run-btn").click();
    await expect(page.locator("#webr-output canvas.webr-plot")).not.toHaveCount(0, { timeout: 120_000 });
    const holder = page.locator("#modal .pickholder");
    await page.locator("#modal .qsubmit").click(); // "Draw the clickable chart"
    await expect(holder.locator("[data-id]")).not.toHaveCount(0, { timeout: 120_000 });
    await holder.locator(`[data-id="${rp.puzzle.pickAnswer}"]`).first().dispatchEvent("click");
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 });
  }

  // Solve a room's PRIMARY graded puzzle, dispatched by type.
  async solvePrimary(rp) {
    if (!rp.puzzle) return;
    if (rp.puzzle.type === "mcq") return this.answerMCQ(rp);
    if (rp.puzzle.type === "check") return this.solveCheck(rp);
    if (rp.puzzle.type === "pick") return this.solvePick(rp);
    throw new Error(`Unknown puzzle type for room "${rp.key}": ${rp.puzzle.type}`);
  }

  // ---- escape gates -----------------------------------------------------------
  async solveLock(lock) {
    const page = this.page;
    await expect(page.locator(".hsmark.lock:not(.done)")).not.toHaveCount(0, { timeout: 10_000 });
    await page.locator(".hsmark.lock:not(.done)").first().dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    if (lock.mode === "stones") {
      // stone keypad: "|" = standing, "_" = fallen; click the keys in order, then submit
      for (const ch of (lock.answer || "").replace(/[^|_]/g, "")) {
        await page.locator(ch === "|" ? "#modal .key.kstand" : "#modal .key.kfall").click();
      }
      await page.locator("#modal .key.ksubmit").click();
    } else {
      await page.fill("#lockInput", lock.answer);
      await page.locator("#modal .qsubmit").click();
    }
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 });
  }

  async solveGrid(grid) {
    const page = this.page;
    await page.locator(".hsmark.grid:not(.done)").first().dispatchEvent("click");
    await expect(page.locator("#modal.open")).toBeVisible();
    for (const [item, bucket] of Object.entries(grid.answer)) {
      await page.locator(`#modal .cell[data-item="${item}"][data-bucket="${bucket}"]`).click();
    }
    await page.locator("#modal .qsubmit").click();
    await expect(page.locator("#modal .qfeedback.ok")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#modal.open")).toBeHidden({ timeout: 10_000 });
  }

  // ---- navigation -------------------------------------------------------------
  // Walk the room's forward door. After a solve, all its doors are open in array order; the forward door is
  // the fwdRank-th open door. Handles the target's optional interstitial "loading" card + HUD assert.
  async walkForward(rp) {
    const page = this.page;
    await expect(page.locator(".hsmark.door.open")).not.toHaveCount(0, { timeout: 10_000 });
    await page.locator(".hsmark.door.open").nth(rp.fwdRank).dispatchEvent("click");
    if (rp.targetHasEntry) {
      await expect(page.locator("#loading.open")).toBeVisible({ timeout: 10_000 });
      await page.locator("#loadBtn").click();
    }
    if (rp.targetTitle) {
      await expect(page.locator("#hudroom")).toHaveText(rp.targetTitle, { timeout: 10_000 });
    }
  }

  async _escapeDoneShown() {
    if (!(await this.page.locator("#done.open").count())) return false;
    const t = (await this.page.locator("#doneTitle").textContent() || "").trim();
    return t === this.plan.escapeDoneTitle;
  }

  // ---- top-level driver -------------------------------------------------------
  async enter() {
    const page = this.page;
    await page.goto(this.plan.path);
    await page.locator("#enter").click();
    const firstAnalysis = this.plan.rooms.find((r) => r.phase === "analysis" && r.puzzle);
    if (firstAnalysis) {
      await expect(page.locator("#hudroom")).toHaveText(firstAnalysis.title, { timeout: 30_000 });
    }
  }

  // Solve every graded analysis room in scenario order, advancing forward. Returns when the LAST analysis
  // puzzle is solved — at which point the engine auto-fires the analysis finish (the #done "analysis
  // complete" card, or #submitPrep directly if there's no escape phase / pending escape).
  async playAnalysis() {
    const page = this.page;
    const analysisRooms = this.plan.rooms.filter((r) => r.phase === "analysis" && r.puzzle);
    for (let i = 0; i < analysisRooms.length; i++) {
      const rp = analysisRooms[i];
      await expect(page.locator("#hudroom")).toHaveText(rp.title, { timeout: 15_000 });
      await this.solvePrimary(rp);
      const isLast = i === analysisRooms.length - 1;
      if (isLast) {
        // Analysis just completed → either the finish card or the submission screen appears (after the
        // engine's ~650ms settle on top of the ~900ms solve).
        await expect(page.locator("#done.open, #submitPrep.open")).toBeVisible({ timeout: 15_000 });
      } else {
        await this.walkForward(rp);
      }
    }
  }

  // From the analysis-finish state, run the escape objective to its finish. General loop: solve any
  // available unsolved lock/grid in the current room; else walk an open forward door; repeat until the
  // escapeDone card appears. Handles BOTH shapes: a separate phase:"escape" room reached by a door
  // (alaska), and an in-room `endsEscape` lock that becomes available once analysis is done (hawaii).
  async playEscape() {
    const page = this.page;
    // Close the "analysis complete" card (X) to get back into the room; the code was minted independently.
    await expect(page.locator("#done.open")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#codeWrap")).toBeHidden(); // the code lives on the submission screen, not here
    await page.locator("#doneClose").click();
    await expect(page.locator("#done.open")).toBeHidden({ timeout: 10_000 });

    for (let step = 0; step < 10; step++) {
      if (await this._escapeDoneShown()) return;
      const rp = await this.currentRoom();
      // 1) an available, unsolved escape lock in this room
      if (await page.locator(".hsmark.lock:not(.done)").count()) {
        const lock = (rp && rp.locks[0]) || { answer: "", mode: null, endsEscape: false };
        await this.solveLock(lock);
        if (lock.endsEscape) { await this._awaitEscapeDone(); return; }
        continue;
      }
      // 2) an available, unsolved escape grid in this room
      if (await page.locator(".hsmark.grid:not(.done)").count()) {
        const grid = (rp && rp.grids[0]) || { answer: {}, endsEscape: false };
        await this.solveGrid(grid);
        if (grid.endsEscape) { await this._awaitEscapeDone(); return; }
        continue;
      }
      // 3) walk an open forward door (into the next escape room, or through the terminal hatch)
      if (rp && rp.fwdRank >= 0 && await page.locator(".hsmark.door.open").count() > rp.fwdRank) {
        await page.locator(".hsmark.door.open").nth(rp.fwdRank).dispatchEvent("click");
        // that click either ends the escape (terminal forward door / endsEscape door) or navigates
        if (rp.targetHasEntry && await page.locator("#loading.open").count()) {
          await page.locator("#loadBtn").click();
        }
        await page.waitForTimeout(500);
        if (await this._escapeDoneShown()) return;
        continue;
      }
      throw new Error("playEscape stuck: no unsolved lock/grid and no open forward door in the current room");
    }
    throw new Error("playEscape did not reach the escape finish within the step budget");
  }

  async _awaitEscapeDone() {
    await expect(this.page.locator("#done.open")).toBeVisible({ timeout: 10_000 });
    await expect(this.page.locator("#doneTitle")).toHaveText(this.plan.escapeDoneTitle, { timeout: 10_000 });
  }

  // From the escape finish (or the no-escape analysis finish, where #submitPrep is already open), open the
  // submission screen, enter an x500, and assert a submission code is minted. The post-2026-07-28
  // submission-prep screen does NOT print the code on screen — it's minted, logged to the field notebook,
  // and baked into the PDF. So we assert: (a) the per-room submission work renders (renderSubmitWork), and
  // (b) the minted code lands in the field notebook (the +1 notebook entry that mintCode logs).
  async submitAndAssertCode() {
    const page = this.page;
    if (!(await page.locator("#submitPrep.open").count())) {
      // came from the escape finish card → step through to the submission screen
      await expect(page.locator("#doneToSubmit")).toBeVisible({ timeout: 10_000 });
      await page.locator("#doneToSubmit").click();
    }
    await expect(page.locator("#submitPrep.open")).toBeVisible({ timeout: 10_000 });
    const nbBefore = await this._notebookCount();
    await page.fill("#subX500", "test0001");
    await page.locator("#subX500Go").click();
    // the per-room refine blocks render for each graded analysis room
    await expect(page.locator("#subWork .swroom")).not.toHaveCount(0, { timeout: 20_000 });
    // and the code was minted + logged to the notebook (mintCode only logs it when mintedCode is truthy)
    await expect(async () => {
      expect(await this._notebookCount()).toBe(nbBefore + 1);
    }).toPass({ timeout: 10_000 });
  }

  async _notebookCount() {
    const t = await this.page.locator("#notebookCount").textContent();
    const m = /\((\d+)\)/.exec(t || "");
    return m ? parseInt(m[1], 10) : 0;
  }

  // The whole thing.
  async play() {
    await this.enter();
    await this.playAnalysis();
    const hasEscape =
      this.plan.rooms.some((r) => r.phase === "escape") ||
      this.plan.rooms.some((r) => r.locks.some((l) => l.endsEscape) || r.grids.some((g) => g.endsEscape));
    if (hasEscape) {
      await this.playEscape();
    }
    await this.submitAndAssertCode();
  }
}

module.exports = { Playthrough, readScenarioPlan };

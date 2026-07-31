# Full-playthrough e2e — how it works, how to extend, what it (doesn't) cover

`e2e/full_playthrough.spec.js` + `e2e/lib/playthrough.js` are the per-scenario **full solve-through** e2e:
they actually PLAY a scenario end to end in a real headless browser + WebR — navigate the built rooms,
solve every graded analysis puzzle by its type, complete the analysis objective (minting the submission
code), run the escape objective, and assert the escape finish + that a code is minted. This closes audit
gap #3: before it, only alaska had a hand-written solve-through; everything else got a static audit + a
generic smoke test, so a mis-grading `check.expr`, a `starterCode` that won't run in WebR, or an escape
that never fires would pass the whole audit.

## Design

- **`readScenarioPlan(page)`** fetches the scenario's own `scenario.json` (relative to the loaded
  `play.html`) and returns the whole answer key + door graph in a serialisable shape: per built room —
  puzzle `{type: mcq|check|pick, correct, nopts, pickAnswer, checkRequires}`, `locks[]`
  (`answer, mode, endsEscape`), `grids[]` (`answer, endsEscape`), the forward-door rank/target/entry, and
  phase. So the spec **tracks re-authoring** (answer keys, wording, door targets can change without
  touching the test).
- **`class Playthrough`** drives it:
  - `enter()` → `playAnalysis()` (solve each analysis room's primary puzzle in scenario order, advancing
    through forward doors; the last solve auto-fires the analysis finish) → `playEscape()` (a general
    loop: solve any available unsolved lock/grid in the current room, else walk an open forward door,
    until the escape-done card shows — handles BOTH a separate `phase:"escape"` room reached by a door
    *and* an in-room `endsEscape` lock/grid) → `submitAndAssertCode()`.
  - Hotspots are clicked via `dispatchEvent("click")` (you enter facing the door, so other markers are
    rotated out of Pannellum's arc). After any correct answer it waits for `#modal.open` to be hidden —
    the ~900ms delayed-solve gotcha (see `../AGENTS.md`).
- **Submission assertion (current engine, post-2026-07-28):** the code is NOT shown on-screen anymore
  (no `#subCodeVal`). It's minted, **logged to the field notebook**, and baked into the PDF. So the
  harness asserts (a) `#subWork .swroom` renders (the per-room refine blocks = `renderSubmitWork`) and
  (b) the notebook count ticks up by one when `mintCode` logs the code (only happens if `mintedCode` is
  truthy). That's a real proof the code minted.

## Console-check answer sourcing (the hard part)

Console-`check` rooms boot real R in WebR (~20–40s first boot, reused per scenario) and grade
`check.expr` on the **live** session. The harness supplies the correct R assignment per room from
`CONSOLE_ANSWERS[scenario][roomKey]` in the spec, **derived from the room's intended answer** (its
`check.expr`/`hint`), and types it into the live console → Run → Check — so it's graded by the real WebR
grader, never faked. Example: hawaii room3's expr is
`toupper(trimws(as.character(answer))) == "KEEI_B"`, so the answer is `answer <- "KEEI_B"`.

Pick-the-point rooms get an R plot (also in `CONSOLE_ANSWERS`) that assigns a **per-candidate** ggplot
to `p` (one mark per id-column value) so every candidate — including the answer — is a clickable,
id-tagged mark; the harness then clicks the mark whose `data-id` is the room's `pick.answer`.

Chosen approach: **a small per-scenario answer map beside the spec**, not auto-derivation from
`check.expr`. Auto-parsing the R logical is brittle (arbitrary expressions); an explicit map is one line
per console room, is obvious to a reader, and — crucially — is still validated against the live grader,
so a wrong map entry fails the test.

## Extending to a new scenario

1. Add a row to `SCENARIOS` in `full_playthrough.spec.js`:
   `{ name: "<scenario>", path: "/escape_rooms/rooms/<chapter>/<scenario>/play.html" }`.
2. For each **console-`check`** room, add `CONSOLE_ANSWERS[<scenario>][<roomKey>] = "<R assignment>"` —
   the code that satisfies that room's `check.requires` + `check.expr` (read them from `scenario.json`).
3. For each **pick-the-point** room, add `CONSOLE_ANSWERS[<scenario>][<roomKey>]` = R plot code that
   assigns a candidate-tagged ggplot to `p` (see the alaska entries for the pattern).
4. MCQ, lock (text + `mode:"stones"`), and grid rooms need **nothing** — their answers are read straight
   from `scenario.json`.
5. Run: `cd escape_rooms/tests && npx playwright test e2e/full_playthrough.spec.js -g <scenario>`.

Also add the scenario to `smoke.spec.js`'s `SCENARIOS` list (the load/enter/render check).

## Covered / not covered

Covered: every graded gate's wiring (MCQ index, console-`check` running real R + grading `expr`,
pick-the-point ggiraph render + data-id click, plus lock/grid support for future scenarios), door nav +
gating, the two-phase analysis→escape boundary, the analysis-finish **code mint**, and the escape finish.

Not covered (deliberately): the field-notebook **image-stack + collage-drag** feature and the submission
**PDF export** — those stay in `alaska_full.spec.js`, the one bespoke spec that exercises them. The
harness also assumes rooms are solved in **scenario order** along forward doors (true for the current
linear data_vis scenarios); a non-linear/open-world maze scenario (e.g. hierarchical_clustering/canyon)
would need the driver taught to follow `unlockedWhen`/`availableWhen` gating rather than array order.

## Assumptions worth knowing

- Analysis rooms are played in `scenario.json` order and the last one solved is the analysis-finish
  trigger (matches the engine's "all analysis puzzles solved" auto-finish).
- One escape lock/grid per room in the escape loop (`locks[0]`/`grids[0]`); scenarios with multiple
  independent escape gates in one room would need indexing added.
- `availableWhen`-gated escape locks are assumed available by the time the loop reaches them (they are,
  since the loop runs only after analysis completes).

// e2e FULL PLAYTHROUGH — actually PLAY each ready scenario end to end in a real browser + WebR, one test
// per scenario, driven by the reusable harness in ./lib/playthrough.js.
//
// For each scenario the harness: enters, solves EVERY graded analysis puzzle by its type (MCQ /
// console-`check` / pick-the-point), lets the analysis objective complete + mint the submission code, runs
// the ESCAPE objective (walk into an escape room and/or key the in-room endsEscape lock), asserts the
// escape finish, then opens the submission screen and asserts a submission code is minted.
//
// This is the gap #3 fix: before this, only alaska had a hand-written full solve-through; every other
// scenario got a static audit + a generic smoke test, so a mis-grading console-check `expr`, a
// non-running starterCode, or an escape that never fires would pass the whole audit. Add a scenario by
// adding a row below (and, for a console-`check` room, the R answer to type — see CONSOLE_ANSWERS).
//
// Console-check answer sourcing (the hard part): the harness supplies the correct R assignment per
// console room from CONSOLE_ANSWERS, derived from the room's intended answer (its `check.expr` — e.g.
// hawaii room3's expr `toupper(trimws(as.character(answer))) == "KEEI_B"` → type `answer <- "KEEI_B"`).
// It's typed into the LIVE console, Run, then Check — so it's graded by the real WebR grader, not faked.
// Pick rooms are supplied a plot that assigns a per-item ggplot to `p` so every candidate is a clickable,
// id-tagged mark; the harness then clicks the point whose data-id is the room's pick.answer.
const { test, expect } = require("@playwright/test");
const { Playthrough, readScenarioPlan } = require("./lib/playthrough");

// Per-scenario console answers, keyed by room key.
//   • console-`check` room → the R code to type + Run (an assignment that satisfies check.requires + expr)
//   • pick-the-point room  → the R plot code that assigns a candidate-tagged ggplot to `p`
const CONSOLE_ANSWERS = {
  alaska: {
    // Both pick rooms grade on the `lake` id column; one bar per lake makes every candidate clickable.
    room3: "p <- ggplot(dplyr::distinct(alaska_lake_data, lake, water_temp), aes(lake, water_temp)) + geom_col()\np",
    boss: "p <- ggplot(dplyr::distinct(alaska_lake_data, lake, water_temp), aes(lake, water_temp)) + geom_col()\np",
  },
  hawaii: {
    // room3 is a console-check: expr is toupper(trimws(as.character(answer))) == "KEEI_B" → assign it.
    room3: 'answer <- "KEEI_B"',
  },
};

const SCENARIOS = [
  { name: "alaska", path: "/escape_rooms/rooms/data_vis/alaska/play.html" },
  { name: "hawaii", path: "/escape_rooms/rooms/data_vis/hawaii/play.html" },
];

for (const sc of SCENARIOS) {
  test(`${sc.name}: full playthrough — solve every puzzle, escape, mint the code`, async ({ page }) => {
    test.setTimeout(300_000); // console-check / pick rooms boot real R in WebR (~20–40s), reused per scenario
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));

    await page.goto(sc.path);
    const plan = await readScenarioPlan(page);
    plan.path = sc.path;

    const pt = new Playthrough(page, plan, CONSOLE_ANSWERS[sc.name] || {});
    await pt.play();

    expect(errors, `no uncaught page errors:\n${errors.join("\n")}`).toEqual([]);
  });
}

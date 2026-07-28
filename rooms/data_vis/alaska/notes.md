---
authority: intent
---

# Alaska scenario — design record

Durable facts (room ladder, verified answers, decoder key) live in `AGENTS.md`; this is the design log.

## Ladder REDESIGN — filtering variety + forced-plot picks (SPEC, 2026-07-22, Lucas)

Supersedes the four-MCQ ladder currently in `AGENTS.md` (pH / nitrogen / chloride / warmest, key
`c(3,2,4,1)`) — **not yet built**; `AGENTS.md` canon updates only when the build lands. Two problems in
the built version drove this: (1) rooms 2 & 3 were the *same* move (filter one element, rank the max) —
a difficulty **plateau** the puzzle skill forbids; (2) nothing ever forced a **plot**, though the whole
`data_vis` chapter is about seeing structure you can't tabulate. Fix: escalate the *filtering* every rung
AND make the two dense rooms genuine plot-picks via the new **Type 4 Pick-the-Point** puzzle
(`notes/puzzle_types_design_notes.md`; ggiraph `data-id` SVG, feasibility-verified same day).

Decisions locked with Lucas: R2 stays **MCQ** (let students settle into the interface before the
puzzle-type switch); boss margin **accepted as-is** (real data, +10.3%); codec rework done via the
**phased plan** below. All four answers re-verified against `alaska_lake_data.csv` (20 lakes, long
format) on 2026-07-22.

| Room | Type | Filtering increment | Analysis | Answer / margin |
|------|------|---------------------|----------|-----------------|
| **R1** dispatch cabin | MCQ (unchanged) | single **threshold** filter + `distinct`/count | pH > 8, how many & which | **North_Killeak_Lake** (8.04; next 7.82) |
| **R2** kitchen | MCQ (**new question**) | **compound** filter, two conditions that *bite* | `park=="NOAT" & element=="Mg"`, most | **Feniak_Lake** (7.66 vs 3.03 = **2.5×**) |
| **R3** radio room | **Type 4 pick-the-point** | filter one element, **plot all 20 lakes**, click the outlier | highest chloride | **North_Killeak_Lake** (337 vs 105 = **3.2× outlier**) — *plants the decoy* |
| **Boss** helipad | **Type 4 pick-the-point** + misdirection | ignore the primed variable; read the hint, **re-plot a new variable**, pick the max | warmest water (beacon hint) | **Lava_Lake** (20.18 vs 18.30 = **+10.3%**); North_Killeak decoy sits at 11.34 |

Design rationale:
- **Monotonic on two axes** — filtering: threshold → biting-compound → outlier-across-the-full-set →
  variable-switch-under-misdirection; and puzzle type: MCQ → MCQ → plot-pick → plot-pick-with-trap.
- **R2's compound filter genuinely bites** — global Mg max is North_Killeak (37.7, BELA), so dropping the
  NOAT condition gives the wrong lake; that makes North_Killeak the sharpest distractor. (Avoided the
  hollow "most nitrogen in GAAR", where Walker is both the GAAR and global max so the park filter does
  nothing.) Six data-derived options: Feniak / North_Killeak (forgot the filter) / Wild_Lake (GAAR max,
  wrong park) / Desperation_Lake / Lake_Kangilipak / Okoklik_Lake.
- **The two pick-the-points are a deliberate setup→subvert pair.** R3 teaches "plot the extreme, click
  it"; the boss re-poses the identical surface, but the extreme on the *primed* variable (chloride →
  North_Killeak, where the search party flew) is wrong — read the beacon hint, re-plot on temperature,
  pick Lava. Same gesture, ground shifts. The repeated surface is what makes the trap land.
- **North_Killeak recurs on purpose** — R1 answer, R2 trap distractor, R3 answer/decoy, boss decoy. It is
  the scenario's "obvious extreme" lake, and the boss's whole lesson is that the obvious extreme is the
  wrong place. (Flagged as a deliberate choice, not an accident.)
- **Escape unchanged** — Claire's three-mask AND-filter overlay (`N0KR`) already echoes the chapter's
  filter idea and is built/wired.

### Phased build plan (codec + engine + wiring)

Biggest-win-first, confirm each phase before the next (repo AGENTS.md convention). Site is git-on-Mac-only
— no commits here; Syncthing carries edits.

- **Phase 1 — Type 4 engine (the enabler). DONE 2026-07-22.** Added to `shared/pano-player.js`:
  `openPuzzle` dispatches `h.pick` → `openPickPuzzle`; `renderPickSvg` runs `pick.plotCode` through
  ggiraph's `dsvg` device and returns the tagged SVG; `buildPickCard` injects it + wires `[data-id]`
  clicks with the standard attempts/feedback ladder; on the correct pick reports `{ answer:1, attempts }`
  → graded in-codec like a `check` (decision (a)). `ensureGgiraph` lazy-installs ggiraph on first pick
  room only. `node --check` clean; validated end-to-end in a real browser by `tests/pick_point_smoke.mjs`
  (real alaska data + the R3 chloride plot → 20 unique data-id bars, click on North_Killeak resolves,
  ~16.6s). No engine codec change was needed — a pick is `type:"puzzle"` and rides the existing
  `solveRoom → roomResults` path.
- **Phase 2 — codec/decoder rework. Tooling DONE 2026-07-22; key-vector flip DEFERRED to Phase 3 (coupled).**
  `validate_keys.py` is now **pick-aware** (a `pick` puzzle → expected `1`, like a `check`), docstring
  updated, with a new regression test `decoder/test_validate_keys.py` (6 cases, incl. the redesigned
  ladder → `c(3,2,1,1)` and pick→1) — all green, all 5 scenarios still PASS, `decode_codes.R` parses.
  `DATA_VIS_ALASKA_KEY` carries a documented PENDING comment for the target key `c(3,<R2 idx>,1,1)`.
  **Why the vector didn't change yet:** `validate_keys` enforces key↔scenario.json lockstep, so the key
  can only flip once the rooms actually become pick rooms — that edit lands *with* Phase 3, not before,
  to keep the build green. The existing `score_step` already handles pick rooms (answer 1 vs correct 1 →
  attempts-based score); no scoring change needed. Escape stays out of the codec (unchanged).
- **Phase 3 — wire the four rooms. DONE 2026-07-22.** Rewired via `_scratch/wire_ladder_redesign.py`
  (idempotent; scenes/clues/doors/sfx untouched — diff was the three puzzle bodies only): R1 unchanged;
  R2 new compound-Mg-in-NOAT MCQ → Feniak_Lake (correct index 2, 6 data-derived options); R3 chloride
  pick-the-point (answer `North_Killeak_Lake`); boss warmest pick-the-point (answer `Lava_Lake`), the
  existing beacon-manual clue already carries the "warmest water" hint. Decoder key flipped to
  `c(3, 2, 1, 1)`; `validate_keys.py` PASS. Both shipped `plotCode`s verified end-to-end in a real
  browser by `tests/pick_point_smoke.mjs` (now reads picks straight from scenario.json): each renders 20
  uniquely-tagged bars and its answer point clicks through. JS units (23) + decoder regression (6) green.
- **Phase 4 — tests. DONE 2026-07-22.** `tests/e2e/alaska_full.spec.js` now drives R1/R2 via `answerMCQ`
  and R3/boss via a new `solvePick(r)` helper (open → wait for "R is ready" → "Draw the chart" → wait for
  the ggiraph `[data-id]` points → click `[data-id="<pick.answer>"]` → assert solve+advance). Data-driven
  off scenario.json (`isPick`/`pickAnswer`), test timeout raised to 300s (WebR + ggiraph). **PASSES**
  (~25s) — full path: 2 MCQs + 2 pick rooms → graded code mints → 4 image fragments stack → keypad escape.
  Bug found + fixed along the way: `puzzleNoteText` didn't read `pick.feedback.correct`, so a solved pick
  room logged an **empty** note and `logToNotebook` silently dropped it (no field-notebook entry). Fixed
  in `pano-player.js`; **failure mode** = solved pick room adds nothing to the notebook; **regression** =
  the new spec asserts `#notebookCount` increments by 1 after R3's pick solve.
  Suite state: JS units 23/23; decoder regression 6/6; e2e **5/6** — the one failure,
  `harness_pick.spec.js`, is a **pre-existing, unrelated** harness-authoring-UI test (candidate image not
  visible on `:8751`); `/api/scenes` globs `scene/*.png` only, so the two non-image files this redesign
  added to `_scratch/` can't affect it, and no harness code was touched. Flagged for Lucas separately.

**Open decision blocking Phase 1:** how does a graded pick-the-point encode in the codec? Two options —
(a) treat it like a `check`: `answer = solved ? 1 : 0` + attempts, so it stays in the submission code
alongside the MCQs (my lean — keeps the boss graded/auditable); or (b) keep it escape-style ungraded and
drop R3/boss from the codec (simpler, but loses the graded boss). Needs Lucas's call before I touch the
engine.

## Escape rework — "Claire's filtered glass" overlay (DECIDED, 2026-07-20, Lucas)

Supersedes both the built **initials** escape (`NWNL` = first initial of each room's answer lake — pure
name-matching, doesn't exercise the chapter idea) **and** the never-built "Cynthia's mineral-water tea"
concept (kept as history at the foot of this file). This is the direction to build.

**Premise.** The helicopter you must borrow to reach the downed pilot belongs to **Claire**, a station
pilot who is *obsessed with filters and with documenting everything*. She has fitted a **coloured filtered
glass pane** in each of the three puzzle rooms, so each room's light is tinted a different colour, and she
leaves a **note in every room** (she over-documents). Her notes read as ordinary station clues — but each
one carries, at the bottom, a **4×4 grid (16 positions)** with several cells **blacked out**. It's the
*Secret of the Unicorn* mechanic from Tintin: superimpose the three puzzle-room grids and **exactly one
position stays clear through all three**. The **beacon room (the boss)** holds a final note — the same 4×4
grid, but every cell filled with a candidate **code**. The code sitting in the one surviving position is
Claire's **helicopter keypad code** (the `escape1` lock).

**Why it's the right escape — it *is* `filter()`, on the world instead of the data (Lucas's framing).**
The point of the escape is to exercise the *same part of the brain* as the chapter technique — **filtering
down to the one thing that satisfies every condition** — but without any code or data. Each coloured mask
is a **condition**; stacking all three is a **logical AND**; the single surviving cell is the one
"position" that passes every filter — exactly what `filter()` across three conditions returns as the one
surviving row. So it's not a name-matching trick and it's not "one more `filter()` in R" either: it's the
*idea* of filtering, transferred into the physical logic of the room. (Clarified here at Lucas's request —
if the pedagogy ever reads as "just a logic puzzle", this is the line to defend: it's deliberate transfer
of the filtering move into the escape-room world.)

### Mechanic — concrete

- **Three mask notes**, one each in **room1 / room2 / room3** — `clue` hotspots, **`pickup: true`** so
  each lands in the **field notebook** (the notebook becomes the stacking surface: all three masks sit
  together for the student to overlay by eye, so it's genuine inference, not a memory test across rooms —
  back-nav is the backup). Each note = Claire's in-world text **+ a 4×4 mask** (some cells blocked). The
  mask is **exact-content, load-bearing** → render it **deterministically** (a small script → PNG), *not*
  gpt-image-2 (per the clue-image caveat). Tint each mask in its room's glass colour — **red / green /
  blue** reads beautifully as three stacked transparencies and doubles as the "filtered glass" motif.
- **The three masks must intersect in exactly ONE cell.** Author them so no single mask (and no *pair*)
  gives it away — each leaves ~5–7 cells open, the triple-intersection is one. **Verify with a one-line
  script** before building (same non-negotiable "compute it, don't eyeball it" rule as the analysis
  answers). Illustrative construction (target cell = row 3, col 2):
  - A(red) open: (3,2)(1,1)(1,4)(2,3)(4,4)(3,4)
  - B(green) open: (3,2)(1,1)(2,1)(4,2)(3,3)(1,3)  → A∩B = {(3,2),(1,1)}
  - C(blue) open: (3,2)(4,1)(2,2)(1,2)(3,4)(4,4)   → excludes (1,1) → A∩B∩C = {(3,2)} ✓
- **The code grid** — a `clue` in the **boss (beacon) room**, `pickup: true`. A 4×4 grid, **every** cell a
  plausible same-format code; the surviving position holds the real one. Also exact-content → deterministic
  render. All 16 codes same shape so you can't guess the special one without the overlay.
- **The keypad** — `escape1` `obj_2` (`type:"lock"`): change `answer` from `"NWNL"` to the surviving
  cell's code; keep `length: 4` (so the grid codes are 4 characters). Door/gating unchanged.
- **Stays out of the codec.** Escape-phase, ungraded — decoder key `c(3,2,4,1)` untouched, `validate_keys.py`
  still passes (it skips `phase:"escape"`). Analysis rooms (pH>8 / nitrogen / chloride / warmest) unchanged.

### Cleanup this rework requires (don't leave clues pointing at the dead code)

- **Retire the initials-prank clues** that seeded `NWNL`: room2 `a_recipe` ("Matthew … L.S./O.F." soup
  gag) and room3 `a_piece_of_paper` ("Matthew changed the locker code to the first initials of the lakes
  …"). These actively mislead toward the retired mechanic → replace them with Claire's mask-notes. Room1's
  `obj_2` pinned note is a *science* clue (pH context) — **keep** it; add Claire's mask-note alongside.
- **Rewrite the escape text** that references the old mechanic: `escape1.entry` and `escapeDone.body`
  ("You worked the code from the four lakes") — reword to Claire's notes / the overlay.
- **Narrative:** Claire is the pilot whose helicopter we borrow (she replaces the never-built "Cynthia").
  The **missing** pilot is still the one stranded at **Lava_Lake** — unchanged.

### plannedHotspots to add (design-time manifest for the harness box-marking)

- room1: `{type:"clue", label:"Claire's red-glass note", pickup:true, note:"4×4 mask A (red); part 1 of 3"}`
- room2: `{type:"clue", label:"Claire's green-glass note", pickup:true, note:"4×4 mask B (green); part 2 of 3"}`
- room3: `{type:"clue", label:"Claire's blue-glass note", pickup:true, note:"4×4 mask C (blue); part 3 of 3"}`
- boss:  `{type:"clue", label:"Claire's code sheet", pickup:true, note:"4×4 grid of codes; surviving cell = keypad code"}`
- escape1: existing `obj_2` lock — just repoint `answer`.

### Decisions — all RESOLVED 2026-07-20 (Lucas)

1. **Coloured glass = full scene regen.** Lucas is regenerating room1/2/3 on the `:8751` harness so the
   light is genuinely tinted (red / green / blue). New `scenePrompt`/`doorPrompt` already written into
   `scenario.json` (each adds a coloured filtered-glass pane + a visible hand-written card; house style,
   no text/people). Regen changes the art ⇒ **all** of room1/2/3's hotspot boxes get re-marked in-harness.
2. **The 16 codes = helicopter tail numbers** (`N` + 3 alphanumerics), same shape so the winner doesn't
   stand out. Generated + rendered.
3. **Matthew retired.** The two initials-prank pickup clues (`a_recipe` room2, `a_piece_of_paper` room3)
   are **removed** from `scenario.json`; the boss survival card's `pickup` dropped (only escape fragments
   collect now). Claire is the note-leaver.
4. **Keypad stays 4 characters.**

### Built this session (deterministic assets + spec)

- **Renderer:** `escape_grids/make_grids.py` (Pillow). Self-verifying — asserts each *pair* of masks
  shares ≥2 open cells (no pair leaks it) and the *triple* intersection is exactly one. Outputs, in
  `escape_grids/`: `mask_room1.png` (red), `mask_room2.png` (green), `mask_room3.png` (blue),
  `code_grid.png`, and `grids.json` (the answer key). Re-run `python3 make_grids.py` after any change.
- **Answer:** triple-intersection cell = **row 3, col 2** → winning tail number **`N0KR`**. The
  `escape1` lock `answer` is now `N0KR` (length 4). Mask open-cells + full 16-code layout: `grids.json`.
- **`plannedHotspots`** added to room1/2/3/boss/escape1 so the harness box-marking checklist is complete.
- **Escape text** (`escape1.entry`, `escapeDone.body`) rewritten off the old initials mechanic onto
  Claire's templates/board.

### Notebook stores images (engine change, 2026-07-20) — the overlay lives in the notebook

The field notebook now carries **images**, not just text (`pano-player.js`: notebook entries are
`{source,text,image}`; a `pickup` clue logs its `image` alongside its caption; `v=35`). So the three
coloured masks **actually stack in the notebook** — the student picks up each template, opens the
notebook, and overlays the three tinted grids by eye (true *Secret of the Unicorn*). The grids keep their
row/col **labels** so the surviving cell is easy to name and look up on the board. This is Lucas's
preferred path (2026-07-20) and a deliberate investment for future image-fragment puzzles — it replaces
the earlier coordinate-string workaround (which existed only because the notebook was text-only).
*Playtest lever:* the board's diegetic method line is the scaffold if the overlay reads as too obscure.

**Draggable + translucent now (engine change, 2026-07-21).** The notebook's image section became a
**draggable snap-grid collage board** (shared engine — see `../../AGENTS.md` → "Collage board"), and the
three masks are flagged **`overlay:true`** in `scenario.json`, so they render **semi-transparent** and can
be **physically dragged onto one cell** and stacked — the overlay is done by hand now, not just "by eye."
The tail-number board stays opaque (you read the masks over it). Covered by `tests/e2e/alaska_full.spec.js`.
No content/answer change (still `N0KR`).

### Ready-to-wire clue content (Phase 2 — drop in after the harness marks the boxes)

For each, set the clue's **`image`** to the PNG and **`pickup`** to the short caption string (the caption
is logged as the entry's text; the image is logged automatically alongside). Bodies are Claire's voice,
instruction-free except the board (the one deliberate diegetic nudge).

- **room1 clue** — `image: "escape_grids/mask_room1.png"`, `pickup: "Claire's RED template — I of III"`,
  body: *“Red pane — dispatch cabin. Best light in the station, if you ask me. I keep a cut-out template
  of each coloured pane; this is the red one. They only mean anything as a set — template **I of III**.
  — Claire (pilot)”*
- **room2 clue** — `image: "escape_grids/mask_room2.png"`, `pickup: "Claire's GREEN template — II of III"`,
  body: *“Green pane — the mess kitchen. Template **II of III**. Keep it with the other two. — Claire”*
- **room3 clue** — `image: "escape_grids/mask_room3.png"`, `pickup: "Claire's BLUE template — III of III"`,
  body: *“Blue pane — radio room. Template **III of III**. That's the set complete. — Claire”*
- **boss clue (the tail-number board)** — `image: "escape_grids/code_grid.png"`,
  `pickup: "Claire's fleet board — read the tail clear through all three templates"`,
  body: *“My dispatch board — the station fleet's tail numbers. Only one of these birds is mine. Lay my
  three window templates over the board and read the tail number that shows clear through all three —
  that's the one on the pad, and that's its keypad code. — Claire”*

### Remaining handoff

(a) Lucas regenerates room1/2/3 scenes (coloured glass) + re-marks their boxes, and marks the new Claire
clue box in each of room1/2/3/boss, via `:8751`. (b) Claire-content wiring (above) drops into those
clues. (c) `escape1` lock is already `N0KR`. Escape stays out of the codec — decoder untouched
(`validate_keys.py`: Alaska PASS, key `c(3,2,4,1)`).

### WIRED — Step 4 done (2026-07-21)

Art + boxes + sfx landed (all rooms `builtFrom` a `gpt_*`); the puzzle/clue/door/lock content is now
filled in `scenario.json`, re-verified against the CSV at wiring time. State:

- **4 MCQ puzzles** wired (pH>8 / nitrogen / chloride / warmest), correct indices **3,2,4,1** =
  `DATA_VIS_ALASKA_KEY` (guard PASS). Starters are dataset-name-only (no pipeline); ≥6 data-derived
  options; escalating value-based hints; no `reveal`; `feedback.correct` names the answer (notebook line).
- **Clues:** room1 park-codes note (`str()` + why-pH, KEPT); the three Claire mask templates
  (body + `image` mask PNG + `pickup` caption → the notebook stores the images and stacks them);
  boss beacon manual (warmest-water hint) + Claire's tail-number board (`image` `code_grid.png`, pickup).
- **Doors/gates completed** (the harness left `to`/`requires` unset): forward/back `to` on every door;
  boss→escape1 gated on the boss puzzle (`requires: the_workbench_laptop`); escape1 hatch gated on the
  lock (`requires: the_keypad_panel`, no `to` ⇒ fires `escapeDone`). Lock `answer: N0KR`, length 4.
- **Judgement call (foregrounded):** the old room2 puzzle used a deliberately-broken starter
  `filter(element = Nitrogen) %>% ggplot()` ("fix my code"). That violates the Phase-2 convention "no
  solving pipeline in the starter — the student writes the analysis", so I **replaced it with the
  dataset-only starter and reworded the prompt** off "your coworker started on their code" to "your
  coworker wants to know…". If Lucas prefers the repair-the-code beat, it should become a **console-check
  (`check`)** puzzle, not an MCQ with the pipeline pre-given. Flagged for his call.
- **e2e-covered (2026-07-21):** the wiring is verified end-to-end in a headless browser by
  `tests/e2e/alaska_full.spec.js` (Playwright) — drives all four MCQs → code mint → picks up the four
  Claire fragments and asserts they **stack as images** in the notebook → keypad `N0KR` → escape finish.
  `npm run test:e2e` (+ `npm test` unit) both green. The wiring was correct first time; the only bugs
  found were in the test itself (racing the engine's ~900ms delayed solve — see `tests/AGENTS.md`).

---

## History — superseded escape concepts (kept per design-log convention)

- **"Cynthia's mineral-water tea" (2026-07-20, never built).** A data-grounded escape where the keypad
  code fell out of filtering a tea-obsessed pilot's lake-water tins. Three options were sketched — "her
  morning cup" (one filter for an extreme), "the remedy run" (effect→element→filter, Lucas-leaning), "the
  tasting ladder" (plot+rank → 4-digit code). Superseded by Claire's overlay, which Lucas preferred for
  its *Secret of the Unicorn* elegance; the filtering pedagogy is preserved in transferred form (see
  above). Kept here in case a future data-grounded escape variant is wanted.
- **Initials code `NWNL` (built 2026-07-17, being replaced).** Helicopter code = first initial of each
  room's answer lake (North_Killeak / Walker / North_Killeak / Lava). Pure name-matching; retired because
  it didn't exercise the chapter idea. Build details in `../../notes/two_phase_escape_design_notes.md`
  (Slice 2).

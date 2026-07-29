---
authority: intent
---

# Hawai‘i Aquifers — room sequence design notes

Escape-room case for the **Data Visualization** chapter (first data-vis
assignment). Three practice rooms then a boss room. Each room adds one new move
on the same dataset so it's familiar by the boss.

> **STATE 2026-07-28 — GitHub Pages 404 (folder case) fix in progress.** Hawaii 404'd online
> while Alaska worked. Root cause: the `escape_rooms` repo (its own standalone git repo,
> `github.com/thebustalab/escape_rooms.git`) tracked the folder as **`rooms/data_vis/Hawaii/`**
> (capital H, on `origin/main` HEAD `55d0e0c`), but the book links + on-disk folder are lowercase
> `hawaii`. GitHub Pages is case-sensitive → lowercase link 404s. **Fix (Lucas, on the Mac):**
> `git rm -r --cached rooms/data_vis/Hawaii` → `git add rooms/data_vis/hawaii` → verify `git status`
> shows the capital→lowercase rename → commit + push. Pages rebuilds in ~1 min. Separately, ALL
> internal capital-`Hawaii` path/identifier references were lowercased on 2026-07-28 (scenario.json
> `"scenario":"hawaii"`, generated `scenario_inventory.json`, `tests/e2e/smoke.spec.js`, decoder
> comments, notes/AGENTS path refs) — leaving only correct English ("Hawaiian" adjective in art
> prompts, "Hawai'i" place name, and two geographic place-name mentions in `notes/candidate_locations.md`).

> **STATE 2026-07-28 — door wiring fix (beach door mis-routed to the start).** room3 (the Ke‘ei
> coast/"beach" wellhead) had **both** its doors authored with `to: null` — the back door ("The path
> back") and the forward hatch ("The access hatch"). With no explicit target the engine falls back to a
> positional guess (`resolveDoorTarget`: a back door with no `to` walks to the nearest **built** room
> below the current index; a forward with no `to` runs `goThrough`). Fixed by setting explicit targets to
> match the sibling Alaska scenario: **room3 back → room2, room3 forward → boss.** The full graph is now
> linear + backtrackable: room1→room2→room3→boss, each with a back door to the previous (boss "ladder up"
> → room3). scenario.json is fetched `no-store`, so no cache bump — but it needs the Mac push to reach
> GitHub Pages.
> **On the exact cause (not fully confirmed):** `to:null` *alone* does NOT send a back door to the start —
> for a strictly-linear, all-built chain the back fallback lands on the previous room. The "→ start"
> symptom most likely arose because the fallback loop **skips non-`built` rooms** — during the art re-gen
> a room between was transiently not-built, so room3's targetless back door fell through to room1. Either
> way the lesson holds: **author every door's `to` explicitly** so routing never depends on build-state or
> room order. Now guarded by `tests/door_graph.test.js` (which also prompted converting the
> `comparing_means/spa` scenario from the all-`to:null` fallback to explicit targets). See the root
> `AGENTS.md` retain-wiring note for how the hotspot-redraw drop is now prevented.

## REDESIGN 2026-07-16 (Lucas) — a continuous field-rounds story

The generic filter-and-facet ladder (below, kept for history) was replaced by a
narrative walk-through. You're a **field hydrologist on your rounds**; each room
is a real stop with a real, data-derived answer, and the answers were **verified
against the CSV**. The live design is now in `scenario.json` (`authoring` scene
prompts + per-room `designNote` MCQ specs). Summary:

- **Room 1 — the field lab (scene UNCHANGED).** No filter: plot `abundance` ×
  `analyte`, which analyte runs highest overall? → **dissolved_solids** (660).
- **Room 2 — the Moanalua jungle wellhead (scene NEW: inland rainforest).** You've
  sampled sulfate across aquifer_1; `filter(aquifer_code=="aquifer_1", analyte=="SO4")`,
  highest well, is it over 20? → **Moanalua_Wells_Pump_3 = 19, NOT over 20.** Door
  opens onto a jungle trail down toward the coast.
- **Room 3 — the Ke‘ei coast wellhead (scene = the OLD Room-2 seaside prompt,
  moved here).** A colleague hands you aquifer_6 chloride data;
  `filter(aquifer_code=="aquifer_6", analyte=="Cl")`, does any well cross 250? →
  **KEEI_B = 280, the only one over 250.** Its door is a **floor hatch + ladder DOWN**
  to the boss.
- **Boss — down inside the Ke‘ei well (scene NEW: underground wellroom, eerie but
  cool).** Cl is already > 250; `filter(well_name=="KEEI_B", analyte=="Na")`, is Na
  over 150? → **Na = 180, yes → seawater intrusion confirmed at KEEI_B.**

This **resolves the old region-key question** (see the OPEN section further down,
now marked RESOLVED): KEEI_B/aquifer_6 is the **Kona** aquifer, matching the CSV
key. The scene re-assignment: Room 1 keeps its prompt; the old seaside Room-2 prompt
becomes Room 3 (portal changed to a ladder-down hatch); Room 2 and the boss get new
prompts (jungle wellhead; underground wellroom). The old Room-3 "back at the bench"
and old boss "big-island map room" prompts are retired.

---

## Original ladder (HISTORY — superseded by the redesign above)

The boss was the existing CHEM 5725 exercise (`teaching/CHEM5725/exercises.csv`,
Data Visualization Q3 — Kiana & Dr Kamaka, saltwater intrusion), with three
lead-up rooms scaffolding **filtering rows and building plots**.

## The dataset (`hawaii_aquifers`)

`https://thebustalab.github.io/phylochemistry/sample_data/hawaii_aquifers.csv`

- **Long format**, one row per well per analyte. Columns: `aquifer_code`,
  `well_name`, `longitude`, `latitude`, `analyte`, `abundance`.
  (longitude/latitude are mostly `NA`.)
- 106 wells across **10 aquifer codes** (`aquifer_1` … `aquifer_10`).
- **9 analytes:** Ca, Cl, HCO3, K, Mg, Na, SiO2, SO4, `dissolved_solids`.
- `dissolved_solids` reaches the hundreds; every other analyte sits under ~100.
  Cl max = 99, Na max = 90.

## Why reverse-engineer from the boss

The boss requires a student to stack several moves:
`filter(analyte %in% c("Na","Cl"))` → `filter(abundance > 50)` →
`facet_grid(analyte ~ .)` → colour/label by `well_name` → spot the joint
outliers → map wells to a region. That's 4–5 ideas at once. So each practice
room introduces **one** of those moves, on the same data.

## The ladder (no filter → one filter → multi-value filter + facet → full combo)

### Room 1 — first plot, no filtering
- **Skill:** plot grammar only — pick data, map x/y, choose a geom.
- **Code shape:** `ggplot(hawaii_aquifers) + geom_point(aes(x = abundance, y = analyte))`
- **Question:** which analyte reaches by far the highest values?
- **Answer:** `dissolved_solids` (hundreds vs everything else < ~100).
  Un-eyeballable without plotting; needs no filter. An easy first win that
  familiarises them with the columns.

### Room 2 — one filter
- **Skill:** `filter()` with a single `==` condition, then read an outlier.
- **Code shape:** `filter(analyte == "Cl")` → plot Cl across wells.
- **Question:** which well has the most chloride?
- **Answer:** `LALAMILO_D` (aquifer_7, Cl = 99). The core boss move in miniature.

### Room 3 — two-value filter + facet
- **Skill:** `%in%` for multiple values, and `facet_grid` small multiples.
- **Code shape:** `filter(analyte %in% c("Na","Cl"))` + `facet_grid(analyte ~ .)`
- **Question:** which aquifer stands out as high in **both** sodium and chloride?
- **Answer:** aquifer_7 (Lalamilo wells top both; aquifer_2 / Kamaile is the
  runner-up). This is the boss minus the threshold, the colour-by-well, and the
  geography step.

### Boss — the CSV question as-is
- Add `abundance > 50`, colour/label by `well_name`, identify the specific
  wells, google them to a region.
- Reference code (from exercises.csv):
  ```r
  hawaii_aquifers %>% filter(analyte %in% c("Cl","Na")) %>%
    ggplot() + geom_point(aes(x = abundance, y = aquifer_code)) +
    facet_grid(analyte ~ .)
  hawaii_aquifers %>% filter(analyte %in% c("Cl","Na"), abundance > 50) %>%
    ggplot() + geom_point(aes(x = abundance, y = aquifer_code, color = well_name)) +
    facet_grid(analyte ~ .)
  ```

## Room look & feel (decided)

**Format: pseudo-360 panorama** (the `alaska_pano/` direction), not the flat
two-screen style. Each room is a gpt-image-2 scene you look around, with
clickable hotspots that pop the puzzle and a door/scene swap on solve.
**The flat rooms (`alaska/`, `datavis1/`, `demo_hub/`) are to be deleted** —
superseded by the pano approach. (Deletion not yet done; awaiting the go-ahead.)

**Narrative:** one continuous case following Kiana and Dr Kamaka (from the
exercises.csv story), same two characters throughout, a distinct backdrop per
room that tracks the fieldwork:

- **Room 1 — the Honolulu lab bench.** All the water samples spread out for a
  first look. Pairs with the overview plot (no filter).
- **Room 2 — a coastal wellhead site.** Out in the field, zeroing in on
  chloride. Pairs with the one-filter step.
- **Room 3 — back at the bench.** Sodium and chloride compared side by side.
  Pairs with the two-analyte + facet step.
- **Boss — the big-island map room.** Deciding which community to warn. Pairs
  with the full analysis + geography step.

Visual continuity across all four: same field-station world, dusk/night,
teal-and-amber palette, painterly cinematic, no people, no text. Each scene
carries natural hotspot candidates (a laptop showing the plot, the island map,
shelves of labelled sample bottles).

## Format & mechanic decisions

- **Puzzle mechanic — phased.** Phase 1: build all four rooms **multiple-choice**
  (what the engine does today) so the whole chain is playable end-to-end and the
  ladder is proven. Phase 2: upgrade to the **console-check** mechanic from
  `../../notes/puzzle_types_design_notes.md` (student writes the pipeline, assigns to a
  named variable, hits Check, engine grades on the live R session) — clearly the
  better pedagogy for a filter-and-plot sequence, but needs the one engine change
  built first. Biggest wins first; validate the sequence before the polish.
- **Engine mode:** the chain is a `flow: "journey"` scenario (rooms worked in
  order, solving each unlocks the next), already supported by `escape-engine.js`.

## Scene prompts (authoring)

Draft gpt-image-2 prompts for the four scenes live as the **default column
prompts in `alaska_pano/harness_gpt.html`** (`ROOM_PROMPTS`, one per column,
tags `room1`…`room4`). Generate/tune them there; copy the winners back here or
into the scenario when the room is built.

**Each scene includes a CLOSED DOOR** — the swap portal that opens on solve — and
each has a matching **open-door modifier** (`DOOR_PROMPTS`, same index in the
harness), so the columns pair scene↔open all the way down. The closed doors:
Room 1 a heavy wooden door on a side wall; Room 2 a weathered plank supply door
in the shelter's solid wall; Room 3 a wooden door beside the island map; Boss a
tall door beneath the wall map. The door hotspot's masked `/api/dooropen` edit
repaints only that door's box, so opening one door leaves the rest of the scene
untouched.

## Authoring tooling — four-column harness (BUILT 2026-07-15)

The gpt-image-2 harness (`authoring/harness_server.py` + `alaska_pano/harness_gpt.html`,
`harness_ui` tmux on :8751) now generates **the whole room series in one pass**:
four side-by-side generate+pick columns, one per room, each with its own tag,
prompt and candidate grid, running gpt-image-2 concurrently (per-slot job state,
tag-namespaced filenames `gpt_<tag>_NNN.png`, atomic index reservation). A single
shared wrap + hotspot editor below acts on whichever base was last clicked. Full
detail in `../../AGENTS.md` → "Four-column generation".

**Still open on the pano side** (from `../../AGENTS.md`): wiring a hotspot click
to a real WebR MC puzzle (the viewer currently pops a placeholder modal) is the
next integration step before a pano room is actually playable.

## RESOLVED — the region answer key (was: affects Room 3 + boss)

Superseded by the 2026-07-16 redesign. The boss no longer keys on the whole-dataset
Na+Cl joint outlier (which was the Lalamilo/Kamaile ambiguity). It keys on **KEEI_B
in aquifer_6**, whose wells (Ke‘ei, Holualoa, Kahalu‘u, Keahuolu, Honokohau) are all
in the **Kona** district of Hawai‘i Island. Ke‘ei is South Kona, so the CSV **"Kona"**
key is now correct by construction. No open ambiguity remains.

## TODO next time — wire the submission code + boss figure into the pano player

The pano rooms are now genuinely playable: the shared **`shared/pano-player.js`**
(+ `pano-player.css`) drives any chapter's `window.CHAPTER` — pseudo-360 rooms with a
WebR-editor puzzle + multiple-choice gate, door swap on solve, ‹ › nav. (This supersedes
the "wiring a hotspot click to a real WebR MC puzzle is the next step" note above — that
part is done.) Two pieces are still **not** wired, and they're what the real Canvas
assignment needs:

1. **Submission code — ✅ DONE (Phase 5, 2026-07-16).** `pano-player.js` now calls
   `shared/codec.js` at the finish screen: one step per room ({answer, attempts}; console-check
   rooms encode `answer=1`), keyed on the scenario `id` + `SECRET` (moved into `pano-player.js`),
   shown with a copy button. This scenario is **id 7**; decoder key `DATA_VIS_HAWAII_KEY` added to
   `decoder/decode_codes.R` (grow its `correct` vector as rooms 2–3 + boss are built). A boss byte
   will be appended once the boss room exists (see item 2).
2. **Boss figure deliverable.** The boss room ends in a **figure** the student builds in the
   WebR console (the plot + `buildCaption()`), then **downloads as a PNG watermarked with
   their x500 + the code** and uploads to Canvas (Lucas grades it by hand). `pano-player.js`
   already captures the x500 (`window.__x500`); add a "Download your figure" button that
   exports the WebR plot canvas to PNG with the watermark baked in. Verify `buildCaption()`
   actually runs in WebR first (bustalab function — may pull heavy deps).

---

## RGB-cipher escape rework (2026-07-20, Lucas) — in progress

Adds the two-phase escape (Objective 2) Hawai‘i never had, as a **learned-cipher lock**.

**Mechanic.** Each room holds an abstract **artwork** (a clue hotspot → a generated RGB cipher image in
the modal): mixed red/green/blue dots up top, a central divider stamped with a 3-digit code, and only the
"passed" colour(s) at the bottom. Room 1 = `010`→green, room 2 = `100`→red, room 3 = `001`→blue (three
worked examples teaching position = R,G,B). The **well/boss** artwork shows green+blue at the bottom with a
**blank** divider, so the player deduces `011` and enters it on the **valve keypad**. Dot sizes are decorative.

**Boss valve mechanic.** Solving the boss data puzzle opens the **valve control panel** (the `scene_open`
swap = the panel cover slides open, revealing the keypad). The keypad is a `lock` hotspot, answer `011`,
no-instructions. Entering it = the escape (turn the valve on/off). The **ladder up is always open** (not
boss-gated) and backtracking is enabled so players can revisit the earlier artworks.

**Scene layout (prompts updated 2026-07-20).** Art placeholder per scene — room1 framed painting on a wall,
room2 a standing outdoor installation, room3 a panel on the wellhead building, boss a framed piece beside the
valve panel. The readable cipher is the **clue-image modal**, NOT painted into the scene (gpt can't hold exact
codes at scene scale). **Backtracking doors:** room1 = single forward door; room2/room3 = forward (closed) +
an always-open back path to the previous room; boss = the always-open ladder up + the valve panel.

**The existing science clues stay** (why-sulfate / why-chloride / two-markers) — they serve the data puzzles
and are separate from the art.

**Build state / next.** Scene+door prompts updated. TODO in the harness: regenerate all 4 scenes, then mark
the new hotspots — an **artwork clue** box per room + the **valve keypad (lock)** box in the boss + **back-door**
boxes in room2/room3. Then Claude wires: generate the 4 cipher clue images (prompts drafted in chat), the `011`
lock + feedback, door directions/targets (back doors always-open, `to` set), the boss valve-panel swap on solve,
and the escape finish (`escape`/`escapeDone`). id stays 7; escape rooms are out of the codec so the decoder key
is unaffected.

### RGB cipher — the four clue-image prompts (2026-07-20; island re-theme 2026-07-21)

Written as a consistent set; only the code + the colours that fall through change. Risky bits for gpt: the
exact digits and (on the well one) the blank divider — check those, fall back to a deterministic render if
gpt can't hold them. **Re-themed 2026-07-21 (Lucas): the divider is now a weathered pale bamboo beam (not
brushed metal), on a teal-and-amber tropical-dusk background** — the digits are *branded* into the bamboo.
The live prompts are the `clue.imagePrompt` fields in `scenario.json`; the sketch below tracks them.

- **Room 1 (010 → green passes):** Abstract vertical panel with a tropical Hawaiian island feel, painterly
  but flat and clean, high contrast, square. Deep teal-and-amber dusk background (turquoise-lagoon +
  volcanic-black, warm amber glow). TOP third: a loose scattered row of small glowing dots in red, green and
  blue in mixed sizes, like luminous tropical blossoms. MIDDLE: a horizontal length of weathered pale bamboo
  runs across like a beam, three bold digits branded dark into it: 010. BOTTOM third below the bamboo: only
  GREEN dots have fallen through — no red, no blue. Soft film grain, warm island light. No other text/
  numbers/symbols except the 010 branded on the bamboo.
- **Room 2 (100 → red):** …same, digits **100**, only RED below the bamboo (no green/blue).
- **Room 3 (001 → blue):** …same, digits **001**, only BLUE below the bamboo (no red/green).
- **Well / boss (blank → green+blue → deduce 011):** …same, but the bamboo beam is completely BARE and
  unbranded (no digits, no carving), and BOTH GREEN and BLUE dots have fallen through together at the bottom —
  no red. No text/numbers/symbols anywhere; the bamboo is entirely bare.

---

## Wiring pass (2026-07-21, Claude) — puzzles + clues + escape filled

After Lucas placed the art + hotspots, the puzzle/clue/lock/door content was wired into
`scenario.json` (Phase 2 of the design skill). All answers re-verified against the CSV.

- **Puzzles = MCQ** (matching the sibling Alaska + the decoder, not the empty `check` scaffolds the
  harness had seeded). ≥6 data-derived options each, correct index varied per room. **Correct-index
  vector `c(3, 5, 0, 2)`** for room1/room2/room3/boss — set in `decoder/decode_codes.R`
  (`DATA_VIS_HAWAII_KEY`) + its self-test (Rscript green, id-7 grades 40/40). Answers: room1
  dissolved_solids; room2 Moanalua_Wells_Pump_3 = 19 (under 20); room3 KEEI_B = 280 (only well >250);
  boss KEEI_B Na = 180 (>150 → intrusion). Distractors are real near-misses (runner-up wells, wrong
  analyte at KEEI_B — Mg 95 / SO4 46 / Ca 14 — near-name KEEI_C_WELL, threshold-verdict flips).
- **Science clues** (`A pinned note` / `Staring off…` / `field notes` / `checklist`): why-it-matters +
  long-format shape + a real `str()` block. No pipeline syntax, no answer given away.
- **RGB-cipher artwork clues**: `imagePrompt` set on each (`The framed painting` 010→green, `standing
  installation` 100→red, `wellhead panel` 001→blue, `framed piece by the valve` blank→011). **Lucas
  generates these in the harness** (Generate ×2). ⚠️ gpt-image-2 is unreliable at exact digits / clean
  colour separation — eyeball each; if it won't hold 010/100/001 or the blank bar, fall back to a
  deterministic render (a PIL script → PNG). Claude offered to build that renderer.
- **Escape**: boss `The valve keypad` lock = `011`, length 3 (ungraded, not in codec). Door targets set
  (forward: room1→2→3→boss; back doors always-open room2→1, room3→2, boss ladder→room3).
- **Room2 puzzle — DONE (2026-07-21).** Lucas placed the "field laptop" box; the SO4 MCQ is now wired
  (correct index **5**, `c(3,5,0,2)` in lockstep, `validate_keys` green). All four analysis rooms are
  now filled and the scenario is completable.
- **Puzzle-authoring rules tightened (2026-07-21, Lucas → skill).** Two new conventions in the design
  skill, applied across ALL scenarios (alaska/hawaii/airship/hospital): (3) `starterCode` is the **bare
  data-object name only** — no commented instruction lines (exception: repair-the-pipeline puzzles like
  hawaii **room3**, which keeps its intentionally-broken `filter(...)` code); (4) the `question.prompt`
  is the **raw question only** — the method (filter/plot/reshape) moves to `feedback.wrong[0]`. hawaii's
  starters/prompts were swept to match.

---

## Audit + ladder reshape (2026-07-22, Claude ← Lucas)

Audited against the `escape_room_puzzles` skill. Two outcomes: a grading bug fixed, and the ladder
reshaped so each rung adds a real increment (the old room1/room2 and room2/room3 pairs were near-plateaus).

- **Room 2 grading bug — FIXED.** The correct index was `5`, but option 5 was a **duplicate**
  `Moanalua_Wells_Pump_2` (the real answer `Moanalua_Wells_Pump_3` sat at index 4, marked wrong). A
  student who analysed correctly was graded WRONG. `validate_keys.py` couldn't catch it — it only checks
  scenario.json's index vs the decoder key (both said 5), not that the option *text* at that slot is the
  right answer. Fix (no codec change): option 5 → `Moanalua_Wells_Pump_3`, freed index 4 → a fresh real
  distractor `Beretania_High_Service`. `correct = 5` and the decoder key `c(3,5,0,2)` untouched; six
  distinct real aquifer_1 wells again. A **duplicate-option guard was added to `validate_keys.py`** so
  this class of bug can't recur.

- **Ladder reshape — strictly monotonic filter progression (decoder UNCHANGED).** Verified against the
  local CSV.
  - **Room 1** — was a *no-filter* whole-survey read ("which analyte highest"). Now a **single-condition
    filter**: `filter(aquifer_code == "aquifer_1")` → which analyte is highest → **dissolved_solids**
    (~340 in aquifer_1, vs Cl 136 — a clean 60% winner, and deliberately **not KEEI_B**, so it doesn't
    telegraph the boss). Answer stays `dissolved_solids` (index 3) → decoder unchanged. The pinned-note
    clue was reworded from "plot it all before filtering" to "narrow to your working slice first."
  - **Room 2** — a **two-condition filter**, `filter(aquifer_1, SO4)` → highest well =
    **Moanalua_Wells_Pump_3** (19). Prompt reworded to just "which well carries the most sulfate?" —
    the **threshold-decision was handed down to room 3** so room 2 is a clean "read the extreme" rung,
    not a second threshold room. Answer/index unchanged (5).
  - **Room 3** — unchanged; it already **owns** the escalation: correct the colleague's **broken
    two-condition filter** *and* apply the **alarm threshold** (any aquifer_6 well over 250? → KEEI_B,
    280). Index 0.
  - **Boss** — still the sodium verdict (index 2) for now. **Planned: convert to a map-pick** joint
    Cl×Na read (click the well high on both), whose companion console plot seeds the submission-package
    figure. **Coupled to the submission-package feature** (see `../../AGENTS.md` → "REQUIRED before Fall
    2026") — do the boss map-pick *with* that build, not ahead of it, because that screen is where the
    figure deliverable now lives.

  Resulting rungs: 1 filter → 2 filters → 2 filters + debug + threshold → (planned) 2-variable visual
  recognition. Puzzle types today: 3× MCQ + escape lock; the boss map-pick will add a second type.

- **Escape confirmed DONE.** The RGB-cipher escape is fully wired (valve keypad `lock` = `011`, four
  cipher artwork clues, `escapeDone`). `scenario_inventory.json` said `has_escape: false` — stale/generator
  gap; regenerated 2026-07-22.

- **Traps considered, not forced.** No Simpson-style trap — wrong chapter (that's a `group_by` move). The
  genuinely-relevant, genuinely-present traps here are **NA/`na.rm`** (KEEI_B's HCO3 is literally `NA`) and
  **filter-first-vs-global-max**; left as candidates for the boss map-pick's companion console if wanted.
  At assignment-1 level the existing boundary nudge (19 feels over 20) + the boss's read-the-right-analyte
  distractors were judged proportionate.

---

## Room 3 console-check wired + decoder fixed (2026-07-28, Claude ← Lucas)

Room 3 had been switched to console-check mode in the harness but left as an **empty skeleton**
(`expr:""`, no prompt/requires/feedback), so hitting "Check my answer" evaluated an empty R
expression → error → it could never grade correct. This is the Phase-2 upgrade the format notes
above planned (student repairs the pipeline instead of picking an MCQ option). Wired it up:

- **Room 3 check.** `starterCode` = the colleague's intentionally-**broken** chloride filter
  (`filter(aquifer_code = "aquifer_6", analyte = Cl)` — `=` for `==`, unquoted `Cl`). Student fixes
  it, keeps `abundance > 250`, and assigns the flagged `well_name` to `answer`. `requires:["answer"]`,
  `expr: toupper(trimws(as.character(answer))) == "KEEI_B"`. Answer re-verified against the CSV:
  **KEEI_B (280) is the only aquifer_6 Cl well over 250** (next is HOLUALOA at 210). Prompt is the raw
  question + assign mechanic; filtering method sits in `feedback.wrong[0]`; no `reveal`.
- **Decoder fixed — the real second bug.** A console-check room encodes `answer=1` on solve, but
  `DATA_VIS_HAWAII_KEY` still had room 3 as MCQ index **0** (`c(3,5,0,2)`), so a correctly-solved
  room 3 would have graded WRONG. Key → **`c(3,5,1,2)`**; comments + the decoder self-test's `psteps`
  updated (Q3 answer 0→1). `validate_keys.py`: hawaii **PASS**. Rscript self-test: hawaii **40/40**.
- **Added `test_hawaii.py`** (there was none) — pins all four answers to the CSV, asserts room 3 stays a
  console-check targeting KEEI_B (not a reverted MCQ), MCQ correct-index↔option-text lockstep, and the
  decoder key `c(3,5,1,2)`. All pass.
- **Still MCQ:** room 1, room 2, boss. Only room 3 is a console-check for now.

## Escape flow fixed — in-room escape lock now recognised (2026-07-28, Claude ← Lucas)

Completing the analysis jumped **straight to the submission window**, skipping the valve-keypad escape.
Cause: the player detected an escape objective only via a separate `phase:"escape"` room, but Hawaii's
escape is a `lock` (the valve keypad, `011`) **inside the boss (analysis) room**. Solving the boss puzzle
completes the analysis → `finishAnalysis` saw no escape phase → `openSubmitPrep()`.

Fixed generally (option B — future-proofs any boss-room escape), in `shared/pano-player.js`:
- New `hasPendingEscape()` — an unsolved `lock` flagged `endsEscape` counts as a pending escape, so
  `finishAnalysis` shows the *analysis-complete* card (finish message + ✕ only — no skip/play-again) instead of jumping
  to submission; the exit-debrief spoiler guard also honours it.
- Solving an `endsEscape` lock now fires `showEscapeDone()` (the in-room analogue of an `endsEscape` door).
- Hawaii's valve keypad got **`endsEscape:true`** + **`availableWhen:{solved:"boss"}`** (so it can't be
  keyed before the boss puzzle reveals the panel — closes the enter-011-early exploit).

Flow now: solve boss puzzle → analysis-complete card (message + ✕ only) → close → wellroom with the valve
panel open → key `011` → escapeDone ("you disconnected the well"). Submission reachable from both the
analysis-complete card and the escape-done screen. Player-script cache bumped (js v58 / css v55).

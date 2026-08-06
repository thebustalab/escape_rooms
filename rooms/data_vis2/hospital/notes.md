---
authority: intent
---

# Hospital scenario — design record

Design conversation with Lucas, 2026-07-18 (walked through with the harness). Durable facts (verified
answers, ladder) live in `AGENTS.md`; this is the narrative/design log and the open decisions.

## Metabolomics re-theme (2026-07-30)

**Why.** The scenario shared `alaska_lake_data` with `data_vis/alaska`, and the two puzzles collided:
room 2's heatmap already revealed which lake the pilot fell into, which the boss then asked for again
(a room2→boss redundancy Lucas flagged). Fix: re-theme the **analysis rooms** onto a hospital
**metabolomics panel** for a patient, **Elias** (woven in from the opening line), and restructure so no
room hands the next its answer. The **engine, codec, escape (facet-collage keypad 729), doors and art**
are unchanged — only the analysis-room **data + wording** changed.

**Data.** New LONG-format teaching set built + verified by `build_metabolomics.py` (deterministic;
reproduces the two committed CSVs byte-for-byte): `metabolomics_hospital.csv` (20 patients × 10
metabolites) + `metabolomics_hospital_unknown.csv` (Elias). Eight metabolites are real values from
`metabolomics_data`; two are engineered — the **indoxyl/p-cresyl Simpson pair** and **Elias** (patient
54's near-twin + a creatinine spike). See `phylochemistry/sample_data/AGENTS.md`.

**The four rungs (no leaks; verified in `test_hospital.py`).**
- **R1** pivot_wider + scatter+smooth: is **choline** a proxy for **2-aminoisobutyric acid**? → strong
  positive, r ≈ 0.985, holds within group (idx 3).
- **R2** scaled `geom_tile` heatmap: Elias's closest patient → **Patient 54** (margin 0.89). **Creatinine
  is excluded** ("renal assay pending") — this both kills the boss leak *and* gives the clean match; the
  exclusion is then the boss's dramatic reveal (idx 1).
- **R3** facet_wrap(~patient_status): the indoxyl/p-cresyl link is **Simpson's paradox** — pooled 0.95,
  within-group ≈ 0 (idx 4).
- **Boss** compare Elias's panel to the cohort, most-elevated of five markers → **creatinine → Nephrocidin**
  (z +6 vs healthy, cohort max; idx 0). Clue = *the worksheet on the gurney* (marker→syndrome→treatment).

Decoder key `DATA_VIS2_HOSPITAL_KEY` boss index **2 → 0** → `c(3,1,4,0)` (+ self-test). Status left
`in_development` pending a playtest of the new data/puzzles.

**Playtest fix (2026-07-30).** First playtest hit `bind_rows(): Can't combine ..$patient_number <double>
and ..$patient_number <character>` in room 2 + boss. Cause: Elias's `patient_number` is the string
`"Elias"` (so his column reads "Elias" on the heatmap) while the cohort's are bare numbers → readr types
the two CSVs' `patient_number` differently. Fix: both binding starters now
`mutate(patient_number = as.character(patient_number))` before the bind — keeps Elias's label, changes no
answers/options/decoder/data. Guarded in `test_hospital.py` (any unknown-binding starter must coerce).
(Separately, R also can't start until the two new CSVs + `datasets.R` are pushed live from the Mac — the
github.io URLs 404 otherwise; that's a publish step, not a code bug.)

**Full audit (2026-07-30, `escape_room_audit`).** Puzzles/data/decoder/wiring all clean — every answer
re-derived from the CSVs (R1 choline~2-AIB pooled 0.99 / within 0.95–0.98; R2 nearest 54 d=0.10 vs 2nd 58
d=1.00; R3 Simpson pooled 0.95 / within −0.22 & 0.21; boss creatinine z+6.0, cohort max, every other
candidate marker ≤0z), single-winner margins, ≥6 data-derived distractors (R2 options 54/58/56/57/52/60 =
the genuine six nearest), decoder lockstep `c(3,1,4,0)`, `validate_assets` clean bar in-dev `solveSfx`.
The audit caught a cluster of **stale-Alaska/v1 residues in player-facing text** (survived the re-theme):
fixed — `escapeDone.body` ("the pilot's stable, the infection's named" → Elias), `escape1.debrief` +
`.technique` (still described the retired geom_text map puzzle → facet-collage keypad), `subtitle`
("filter, count" → "pivot, heatmap, facet"), and the boss `scenePrompt` prop ("mud-caked flight-data
recorder" → clipboard of lab results). Added a stale-theme guard to `test_hospital.py` (scans player-facing
narrative for Alaska/v1 tokens; scene/design/plannedHotspots excluded).

**Solve sounds wired + normalized (2026-07-31, Lucas's ask).** All 5 gates now have `solveSfx` (CC0
freesound, trimmed to the door event + loudnorm'd to −18 LUFS, wired at `volume 0.65` ≈ −22 LUFS effective
vs the −34 LUFS-effective music bed). `validate_assets` now PASSes hospital. Full record + sources +
reproducible method: `escape_rooms/notes/solve_sounds.md` → "Hospital (2026-07-31)". **Still blocking
`ready`:** the boss scene art still shows the flight-recorder (prompt fixed; needs a :8751 regen), plus the
decorative lake-print (room2) / parks-map (room3) residues — all art-harness work. Left `in_development`
pending those + Lucas's playtest.

**Removed the vitals-pulse HUD (2026-07-31, Lucas — "too game-like").** Dropped the top-level
`hud: {kind:"vitals", healAt:"analysis"}` (green pulsing heartbeat emblem) from `scenario.json`. The `fx:
["flicker"]` fluorescent overlay is kept. Engine unchanged — `vitals` stays available as a `hud.kind` for
other scenarios; hospital just no longer opts in.

**Black zenith cap in room3 + break room (2026-07-31, Lucas playtest).** The player showed a black disc at
the top of the corridor (room3) and break room (escape1). Cause: the panoramas cover only `vaov:90`
vertically, so the sphere's top is uncovered (near-black background); it's invisible unless the ceiling is
bright AND the view is level — room3 (top luma 226) and escape1 (161) at pitch −5.6/−5.9 hit both, while
room1/boss look down more (−8.1/−9.2, cap out of frame) and room2's top is dark (luma 62, cap blends). The
harness wrap tester didn't reveal it because free-drag tuning looks away from the cap. **Durable fix
shipped:** a **"Preview as player"** toggle in `authoring/ui/reproject_test.html` (locks drag off + pinned
pitch + faces the door = exactly the player) — see `escape_rooms/AGENTS.md` `wrap` bullet. **STILL TO DO
(Lucas, harness):** re-tune room3 + break-room `wrap` with that toggle on — raise `vaov` toward ~110–120
until the cap is painted out — and Save. The two rooms' committed `wrap` is unchanged so far (fix enables
the tuning; it doesn't guess the values).

**Open / follow-ups.** (a) The boss was the chapter's assessed `exercises.csv` item (on the lake data);
the re-theme **decouples it** — add a metabolomics entry there if the boss must stay the graded item.
(b) `solveSfx` is still unset on all five gates (pre-existing; harmless while in-dev). (c) Two art
residues left un-regenerated: room 2's *framed print of a sunny lake*, room 3's *wall map of parks*.

## Premise & voice

The player is the **hospital's instrument-repair technician**, night shift, in a medium-sized Alaskan
town. Second person, same register as the Alaska/Hawai'i data-vis scenarios. They start finishing a
repair in the ground-floor pharmacy and get pulled up through the building — pharmacy → elevator →
corridor → lab — each floor a data question, ending at a bush pilot who needs the right antibiotic.
Continuous story, one dataset (`alaska_lake_data`), North Killeak Lake recurring as the through-line.

## Story beats (for the between-room `entry` cards, authored at wiring)

- **Room 1 (pharmacy) — scenario `story`.** Pharmacist stops you leaving: a canoe carrying a
  pH-sensitive shipment tipped; is the medicine spoiled (acidic water)?
- **Room 2 (elevator) — `entry`.** Recap: the shipment verdict. Then the phone rings — a bush pilot
  pulled from **North Killeak Lake**, get to the lab; lake data texted to your phone. Task: highest
  sodium.
- **Room 3 (corridor) — `entry`.** Recap: North Killeak had the highest sodium. You run into your
  **crush**, who wants to canoe this weekend at the park with the most lakes — name it to get past.
  You say yes to the weekend but you've got to get to the lab. Task: park with the most lakes.
- **Boss (lab) — `entry`.** Recap: GAAR has the most lakes. Now the pilot, **Elias Kane**, has an
  infection narrowed to five bacteria; you need the most abundant element in North Killeak Lake to pick
  the antibiotic. (Full text is exercises.csv Data Vis II Q1.)

## Scene prompts (all NEW art — none reused)

Pharmacy / elevator interior / corridor / lab, all in the house style (dusk-night, deep teal + one
amber light, painterly, no people, no text), centre-and-around 360 framing. Each carries a CLOSED
forward door (the swap portal): elevator door (room1) → elevator doors (room2) → LAB door (room3) →
placeholder door to the escape phase (boss). Rooms 2/3/boss also show an OPEN back passage to the
previous room. Prompts live in `scenario.json` `authoring.scenePrompt`/`doorPrompt` (pre-filled into
the harness Step-2 columns). The elevator "back door" is a mild narrative stretch (you rode up) — kept
for back-nav convenience; retune in the harness if it reads oddly.

## Open decisions / judgement calls to confirm with Lucas

1. **Working title "Vital Signs"** + folder names `data_vis2` / `hospital` (lowercase, matching
   `data_vis`) — rename freely in harness Step 1.
2. **Room 1 lake = Desperation_Lake (pH 6.34 → spoiled)?** Any lake < 7 works; Desperation is the
   lowest pH and a fitting name. Confirm, or pick another.
3. **Room 1 is intrinsically yes/no** — reframed to pH-value + verdict options for ≥6 choices. OK?
4. **Room 2's answer (North_Killeak, highest sodium) = the pilot's lake = the boss's lake.** Nice
   recurring motif, but confirm the coincidence reads as intentional rather than a bug.
5. **Boss ships 5 options** (the canonical exercise antibiotics); skill prefers ≥6 — keep 5 as
   assessed, or add a 6th plausible-antibiotic distractor? Decide at wiring.
6. **Escape-phase mechanic still undecided** — no escape room/lock yet.

## Chapter-alignment revision (2026-07-18) — force multi-variable-mapping plots

Agreed the puzzles must force the Data Vis II *plot-craft* (multi-variable mappings), not chapter-3
filtering. Verified data facts driving this:
- **pH vs water_temp is NOT correlated (r = 0.16)** — a `geom_smooth` there is a flat line; unusable.
- **Salt ions co-vary almost perfectly:** Na~Cl r = 0.999, Br~Cl r = 1.00 (holds without North_Killeak);
  pH tracks salinity only moderately (pH~Cl/Na/F/K r ≈ 0.60–0.66).
- **Chemical similarity to North_Killeak across all 11 elements → White_Fish_Lake** (Euclid 257 vs 363;
  profile r = 0.993; the two saline lakes).

State (updated 2026-07-19): **Room 1 LOCKED** — salt-sensitive reframe: pivot_wider + geom_point/geom_smooth,
"is chloride a good proxy for sodium?" → yes (Na~Cl r=0.999). **Room 2 LOCKED** — geom_tile heatmap →
White_Fish. **Room 3 LOCKED** — the crush *challenges* room 1 ("is that true in every park?"): same Na~Cl,
`facet_wrap(~park)` → NOT uniform (pooled 0.999 is driven by BELA's outlier; NOAT 0.42). **Boss unchanged**.
**Escape LOCKED** (see below). Full per-room state lives in each room's `designNote`.

## Escape finalised (2026-07-19) — the crush's lake, a clickable data map

`escape1` = the break room. Finale = **MAP puzzle** (new engine `map` type): a wall-chart hotspot opens a
modal with the **unlabelled pH×Ca scatter of all 20 lakes** (`escape1/map.png` + `map_points.json`, rendered
from the CSV via matplotlib; 20 fraction-coord click-boxes). Click your deduced lake → **Imuruk**.
Deduction: the crush drops a friend's group-trip NOTE in the corridor ("volcanic-coast park, the lake with
the SOFTEST water"); a **BELA** postcard decodes volcanic-coast→BELA, a **soft-water** postcard decodes
softest→lowest-pH, a **NOAT decoy** postcard forces real matching; data → lowest-pH BELA lake = Imuruk
(6.44). Unlabelled chart ⇒ engineered path is `geom_text(aes(label=lake))` to find Imuruk's point.
Crush gender-neutral (they/them), group invite, non-creepy. Axes pH×Ca: best separation of all 20 (min
norm-dist 0.054) + decoupled from the constraint so the label-reveal is forced. Postcards are opt-in
pickups: **pharmacy = soft-water, corridor = BELA + the note, break-room fridge = NOAT decoy** (dropped
the awkward elevator postcard). Final postcard/​note copy is in each pickup room's `designNote`.
**Map is deliberately BLANK — no instructions, no hints, neutral "Nothing happens." on a wrong click**
(Lucas 2026-07-19, like the combination lock; some students won't get it, and that's accepted for now).
**WebR/chapter checks (2026-07-19):** `tidyr` **has a WebR build** (verified by raw-grepping the r-wasm
PACKAGES index — pivot rooms are safe). `geom_text`/`geom_label` were **not** in ch.4 (first appeared in
ch.5) — so a `geom_text`/`geom_text_repel` paragraph was **added to ch.4's "more geoms" section** (the
`solvents` example), making the escape's label-reveal a taught technique. (Escape is also solvable with
ch.3/4 skills alone: `filter()` to your lake, plot the single point, read its position.) Book edit is on
this box only — Syncs to the Mac, where Lucas renders/commits (site repo is Mac-only).
**Open:** a possible **hidden hint system** for stuck students (Lucas mulling); a 4th postcard (2nd decoy)
if we want harder park-matching.

## Palette (2026-07-18): fully cool / clinical

Applied to all four scene prompts + the cover — cold blue-white fluorescent + faint cyan-green glow,
stainless/glass/mint/linoleum, hard geometric, **no warm light** (amber dropped for now). This makes the
hospital read as clearly distinct from Alaska's warm rustic cabin. NOTE: dropping amber entirely breaks
the series' shared single-amber-glow signature — reintroduce a tiny amber pinprick (exit sign / one
window) if the set should still read as one family.

## Wiring DONE (2026-07-19, harness step 4 "Check with Claude")

All four analysis rooms + the escape were wired from the marked hotspots; every value recomputed live
against `alaska_lake_data.csv` (r/distances/pH all confirmed against the designNotes). Decoder key
`DATA_VIS2_HOSPITAL_KEY` (id 8, `correct = c(3, 1, 4, 2)`) + self-test added; `validate_keys.py` +
`Rscript decode_codes.R` + `test_hospital.py` all green.

- **MCQ answers (0-based correct):** room1 = idx 3 (yes, Na~Cl r≈0.999 — chloride is a safe proxy);
  room2 = idx 1 (**White_Fish_Lake**, nearest to North_Killeak at Euclid 257 vs next 363); room3 = idx 4
  (**NOAT** weakest per-park, BELA 1.00 / GAAR 0.68 / NOAT 0.42 — pooled 0.999 misleads); boss = idx 2
  (**Chlorocidin** — Cl 337.23 is max among the five candidate elements). Boss got a **6th distractor**
  ("Magnistatin", magnesium — Mg is 2nd-most-abundant overall, tempting if you don't restrict to the five
  bacteria), so all four rooms carry ≥6 options and no same-slot tell.
- **Escape — two judgement calls made from Lucas's actual markup** (differs from the design notes above;
  flagged to him): (1) the central hotspot Lucas marked as a **`lock`** was wired as the **MAP puzzle**
  (`map.answer = "Imuruk_Lake"`, 20 points from `escape1/map_points.json`, no instructions, wrong-click
  "Nothing happens.") — a bare lock has no derivable code from "Imuruk", and the map assets were already
  built. (2) The postcards were **relocated to match where the hotspots actually landed**: the crush's
  **note** = the corridor clue (room3), and the **soft-water** + **Bering Land Bridge** postcards = the
  two break-room clues — so the deduction (volcanic-coast park = BELA + softest water = lowest pH →
  lowest-pH BELA lake = Imuruk) closes from the marked pickups. The **NOAT decoy was dropped** (no hotspot
  for it; the pharmacy/elevator postcard pickups were never marked). Reconsider if Lucas wants the
  original distribution + decoy back (needs more clue hotspots drawn in rooms 1–2).
- **Doors:** forward+back wired with explicit `to` (room1→…→boss→escape1; back doors to the previous
  room). Entry cards / landing / `done` / `escapeDone` were already drafted at design and left as-is
  (they recap the verified answers correctly).

## Still TODO (book surfacing — not part of harness step 4)

- Surface the scenario on the book's Data Vis II exercises page (cover card, like `3_datavis_1.Rmd`).
- Add the scenario to the book chapter `4_datavis_2.Rmd` exercises section.
- Confirm `ggrepel`/`tidyr` render live in WebR on a real playtest (tidyr build already verified present).

---

## Escape + narrative redesign v2 (2026-07-20, Lucas) — the postcard/correlation lock (SUPERSEDES the map puzzle)

The `map`-puzzle escape (click Imuruk on the pH×Ca chart) is **retired**: it was click-guessable and didn't
touch the chapter technique (correlation). Replaced by a **world-based, Myst-style** escape that keys on
correlation-by-observation. The four analysis rooms (salt-proxy / heatmap / facet / antibiotic) are UNCHANGED.

### Premise (crush throughline, from the start)
The player (instrument technician) is clocking off for a long-awaited **dinner date with their crush**, who is
waiting in the **break room** at the end. Every room's puzzle is another delay — and along the way they help
save the pilot. **Summer Alaska reskin:** regenerate all art bright, sunny, warm, colourful — a *happy* hospital,
postcards pinned everywhere — NOT the cold/clinical winter look (infection is if anything more plausible in
summer). Drops the amber-vs-cool clinical palette entirely.

### The escape (break room)
The crush looks up: "Sorry it took so long!" / "Don't worry — I've been finishing a piece for the local tourism
magazine, trying to work out **why people love or hate certain lakes**. Tell me the two reasons and we can go to
dinner." The **way out is a door with a 4-digit keypad**. On the back of the door, a **poster** (the crush's
reference chart) keys each water measure to a 2-digit figure. The crush's **laptop sits open on the table — a
WebR console with NO prompt** (available to verify/corroborate; deliberately non-prescriptive). Enter the code → dinner.

### The puzzle (world-based; data-backed)
**8 postcards** scattered 2-per-room across rooms 1–4 (pickup → field notebook), from hospital coworkers on lake
trips. Loved/hated is **inferred from tone, never stated**; the salient reason is experiential, never named as an
analyte. Reading all eight, the pattern emerges: the raves are all about **warm water**, the complaints all about a
**rotten-egg / sulphur smell**. → the two reasons are **temperature** (like) and **sulfur (S)** (dislike). The poster
gives each its figure; code = **temperature-figure then sulfur-figure**.

**Verified lakes (alaska_lake_data):**
- LOVED / warm (17–20°C, and *uniquely* separated by temperature — no confound): **Lava_Lake, Lake_Narvakrak,
  Nutavukti_Lake, Imuruk_Lake**.
- HATED / sulfur (high S; also high Ca/Mg — hard water — so DATA alone is ambiguous on the dislike side, the
  postcards' *smell* cue pins it to S): **Wild_Lake, Lake_Matcharak, Kurupa_Lake, Iniakuk_Lake**.

**Poster key (analyte → 2-digit figure; diegetic, adjustable):**
water_temp 63 · pH 29 · Ca 82 · Mg 26 · Na 90 · K 71 · Cl 55 · S 07 · Br 44 · F 38 · N 49 · C 17 · P 13
**→ Lock code = 63 07 = `6307`** (temperature-figure then sulfur-figure; like-reason first, per Lucas).

### The 8 postcards (inferred sentiment; warmth vs sulfur cue; names match the data exactly)
LOVED (warm):
1. **Lava_Lake** — "Two whole days here and I've barely been out of the water — you can wade in at dawn and it's
   already like stepping into a bath. Swam out past the point under the stars. Bringing the whole ward next summer. —Reyes"
2. **Lake_Narvakrak** — "Finally a lake up here you can get into without your teeth chattering — warm right through,
   even the shallows off the far shore. Floated on my back for an hour reading. Don't tell the day shift. —Okoye"
3. **Nutavukti_Lake** — "Day 3 and the kids will not get out of the water. Warm as the tub at home and clear to the
   bottom. I've given up trying to make them leave. Wish you were here — you'd never leave either. —Sam"
4. **Imuruk_Lake** — "Hauled the canoe up expecting to freeze, and instead we've swum every afternoon — bath-warm by
   noon. Best week off I've had in years. —Delgado"
HATED (sulfur smell):
5. **Wild_Lake** — "Well. Drove six hours for this and the whole shore smells like a carton of eggs left in the sun.
   Couldn't even eat lunch. Packing up early — write when you find somewhere that doesn't reek. —Petrov"
6. **Lake_Matcharak** — "That stink got into the tent, the clothes, my hair — like sleeping next to a struck match all
   weekend. Never again. Tell the others to strike this one off the list. —Blum"
7. **Kurupa_Lake** — "The moment we got out of the truck it hit us — this eggy, matchstick smell rolling off the water.
   Lasted about an hour before we gave up. How is anywhere allowed to smell like this. —Ng"
8. **Iniakuk_Lake** — "Beautiful spot, ruined — a rotten-egg reek off the shallows you can't get away from. The dog
   wouldn't even drink. Relocating to literally anywhere else. —Marsh"

### Engine wiring (after the summer art + hotspot boxes exist)
- **Retire** the `map` puzzle + `escape1/map.png`/`map_points.json` + the test guard for it.
- Break-room hotspots to mark: a **`lock`** on the keypad (answer `6307`, no instructions, feedback: correct →
  the date, wrong → "The lock doesn't budge."), a **`clue`** = the poster (the analyte→figure key; NOT pickup), a
  **puzzle/console** affordance = the crush's laptop opening a WebR console with an empty/near-empty starter (dataset
  named only), and the **8 postcard `clue` pickups** (2 per room, `pickup` = a one-line notebook summary).
- Rewrite `story` (crush + dinner-date opening) and the entry cards to carry the crush throughline; `escapeDone` =
  they finally go to dinner.
- Rooms 1–4 analysis puzzles UNCHANGED. `id` 7→ unaffected; escape stays out of the codec, decoder key untouched.
- Summer scene prompts: to be rewritten next (all 5 scenes: bright/sunny/colourful + postcards; break room adds the
  keypad door + poster + crush's open laptop).

---

## Escape redesign v3 (2026-07-21, Lucas) — the facet-collage inventory puzzle (SUPERSEDES v2 AND the still-wired v1 map)

**Status of the two earlier escapes.** v1 (click-Imuruk on the pH×Ca map) is the one **currently wired in
`scenario.json`** (`escape1` `obj_3`). v2 (the 8-postcard warm/sulfur correlation lock, code `6307`) was
**designed in these notes but never wired**. Both key off `alaska_lake_data`. v3 replaces both: it is
**decoupled from the lake data, non-computational, and puzzle-like** — Lucas's three hard constraints
(2026-07-21), on the grounds that the four analysis rooms + the boss already make the student *compute*
(filter / correlate / facet-in-code / read plots), so the escape should be the **recognition echo** of
faceting, done by hand, with no console. This is exactly the skill's Step-0 ideal (the escape as the
"computation already performed, only RECOGNISE it" move — like `wrangling/trees`).

### The one-line premise

The crush is waiting in the **break room** for a long-delayed dinner date and is laying out a **collage
for the local tourism magazine**. "Help me lay out this spread and we can go." The **way out is a
3-digit keypad lock** on the door. The player has been collecting **9 postcards** through rooms 1–4; the
escape is arranging them into the crush's collage grid and reading the code off it. **Zero R. No dataset.**

### The mechanic (faceting by hand)

Faceting is nothing but *"arrange these panels into a grid by two variables."* So the escape **is**
faceting, performed physically:

1. **9 postcards**, collected as `pickup` clues across rooms 1–4 (and/or the break room). Each carries a
   **single prominent code digit 1–9** (its identity) plus **three ordered attribute tags** along one
   edge (the faceting variables' values). Optional tiny "#n of 9" catalogue mark so the player knows the
   set is complete. **One face only — no flip** (digit centred, tags along the bottom edge).
2. The player drags the 9 postcards into a **3×3 grid** in their **inventory/notebook canvas** (new
   engine mechanic — see below), faceting them: **one attribute becomes the rows (down the page), a
   second the columns (across)**. The third attribute is an honest **decoy dimension**.
3. When the grid is faceted the intended way, the **middle row's three digits, read left→right, are the
   keypad code.** Enter them → door opens → dinner. The lock is the **existing `lock` hotspot**, so the
   canvas needs **no correctness detection** — the player reads the row and types it; a wrong code just
   "doesn't budge," like every keypad.

### The door is the format key

On the back of the door, the crush's **already-started collage**: a **3×3 frame with the middle row
highlighted** and a line in the crush's voice — *"I've started it on the back of the door; the three
across the middle are what I need."* That is the only scaffold telling the player it's 3×3 and that the
**middle row = the code**. (Non-pickup `clue` with an `image`.)

### The combinatorics that make it work (design constraint, not a burden)

- **Latin-square construction.** The 9 postcards' three attributes must be arranged as a **Latin square**
  — every (level, level) combination of any two variables appears **exactly once**. Then **any** pair of
  variables tiles the 3×3 cleanly (no gaps, no collisions), so whichever facets the player tries they get
  a plausible grid and a plausible code. That's the point: **no arrangement visibly "fails,"** so the
  puzzle isn't given away by which layouts break.
- **Six candidate codes.** Three variables → 3×2 = **6 ordered (rows, cols) pairings**, each a different
  middle row → up to 6 codes. We must steer the player to the intended one **without brute force.**
- **Ordered variables ⇒ the code is well-defined.** All three faceting variables must be **ordinal**
  (season, trip-length, remoteness, group-size, budget… — *not* a nominal like park name). Only then does
  each variable have a natural **middle level** (which row is the middle) and a natural **left→right
  order** (how the three middle digits read), mirroring how ggplot orders facets by factor level. With a
  nominal variable the middle row and its reading order are undefined and the code goes fuzzy.
- **Two editorial notes disambiguate** (on the break-room table). Each **indirectly names one axis + its
  orientation**, never the word "facet." Worked example:
  - Note A (editor): *"Readers love seeing how a place changes as the summer wears on — run that
    progression **down the page**."* ⇒ rows = **season**, ascending.
  - Note B: *"And set them **across** from the gentlest spots to the wildest."* ⇒ columns =
    **remoteness**, ascending left→right.
  - Together they pin the pair **and** orientation **and** order ⇒ exactly **one** of the six codes. The
    third attribute (say group-size) is the decoy.

### Why this satisfies the constraints

- **Decoupled from the data** — the postcards are coworkers'/crush's summer-trip world, their attributes
  and digits are authored, nothing reads `alaska_lake_data`.
- **Non-computational** — collect, read two notes + the door, drag 9 cards, read a row, type 3 digits. No
  WebR. (The crush's laptop from v2 is dropped, or left closed as flavour.)
- **Teaches the chapter's signature move** — faceting: choosing the right two variables, and that a good
  facet pair is one that tiles cleanly.

---

## Engine change — the inventory becomes a snap-grid canvas (reusable; Lucas 2026-07-21)

Generalises the 2026-07-20 image-notebook work (notebook entries already carry `{source,text,image}`;
Alaska's three masks currently render as a **static vertical list** and are overlaid "by eye").

**New default inventory view = a grid canvas.** Collected **image** entries populate a grid; new pickups
auto-place into the next cell (raster order); each tile is **click-draggable** and **snaps to the nearest
cell**. Text-only clues keep a list section/tab (Clues vs Images/Board).

Two capabilities, both authored per-entry so scenarios opt in:

- **Multiple images per cell (stacking).** A cell may hold several tiles (offset / z-ordered). Needed by
  the **Secret-of-the-Unicorn** overlay (three masks into one cell); the hospital facet grid uses **one
  per cell**.
- **Semi-transparency, overlay-only.** A per-entry flag (e.g. `overlay:true`) renders that image
  **semi-transparent** so stacked masks blend into a true superimposition. **Only overlay-flagged images**
  (the Unicorn masks) are translucent; postcards stay **opaque**. Lucas's call: don't make everything
  translucent — scope it to the images that come from an overlay puzzle.

**Cross-benefit (why the engine work pays off twice):** this upgrades **Alaska's** Secret-of-the-Unicorn
from imagine-it-in-your-head to **physically dragging the three translucent masks onto one cell** and
reading the surviving clear cell — and it powers the **hospital** facet grid. One investment, two
scenarios, and a foundation for future image-fragment puzzles.

Session-only state, same lifecycle as `caseFile` (cleared on Enter). Reduced-motion respected. Ship
behind the existing `?v=` cache-bump on `pano-player.js`/`.css`.

---

## Phased implementation plan (v3)

**Phase 1 — Engine: the draggable snap-grid inventory** (`shared/pano-player.js` + `.css`). The reusable
foundation, scenario-agnostic. Turn `openNotebook`'s image rendering into a grid canvas: auto-place
image entries into cells on collection; drag + snap-to-cell; **multiple tiles per cell** (offset/z);
per-entry **`overlay`** flag → semi-transparent tile. Keep text clues as a list section. Retrofit
**Alaska**: flag its three masks `overlay:true` so they physically stack. No `scenario.json` schema
break (new fields are additive). Bump `?v=`. **Coverage:** unit + extend the Playwright e2e
(`tests/e2e/alaska_full.spec.js`) to drag-stack the masks. *Deliverable: notebook grid works in both
scenarios; Alaska overlay upgraded.*

**Phase 2 — Content/data: the 9 postcards + 2 notes + door** (design artefact, no art yet). Pick the
theme (coworkers' summer trips / the crush's magazine collage — summer reskin already agreed in v2).
Choose **3 ordinal attributes × 3 levels**, lay the 9 cards as a **Latin square** (every pair crosses
cleanly), assign each a unique **digit 1–9**. Write the **two editorial notes** (indirect axis + order)
and the **door's started-collage** line. **Verify the combinatorics** (replaces "verify against CSV"):
enumerate all **6 (rows,cols) orderings → 6 candidate codes**, confirm the two notes select **exactly
one**, and record that code. *Deliverable: a small `postcards` spec (per-card: digit + 3 attribute
levels), the intended facet pair, the 6-code enumeration, and the resulting keypad code.*

**Phase 3 — Art** (harness `:8751`, all NEW, bright summer). Nine **postcard images** (big centred digit
+ 3 attribute tags on the bottom edge + "#n of 9"); the **two editorial notes**; the **door's started
collage** (3×3, middle row highlighted); the **break-room scene** if not reused. No-people / no-lettering
rule bends only for the deliberate on-card digits/tags (they're diegetic postcard print).

**Phase 4 — Wire `scenario.json`.** **Retire v1**: remove the `map` puzzle (`escape1` `obj_3.map`) +
`escape1/map.png` + `map_points.json`. Mark/author: **9 postcard `clue` pickups** spread across rooms 1–4
(+ break room), each `pickup` = short caption, `image` = postcard PNG, opaque; **2 editorial-note
`clue`s** on the break-room table; **door started-collage `clue`** (image, non-pickup); a **`lock`** on
the door (`answer` = the 3-digit code, no instructions, `feedback` correct→dinner / wrong→"doesn't
budge"). Rewrite `story` / `entry` cards / `escapeDone` onto the collage-and-dinner throughline. Escape
stays **out of the codec** — `DATA_VIS2_HOSPITAL_KEY` untouched.

**Phase 5 — Validate + close out.** `json.load` parses; rewrite **`test_hospital.py`** (drop the map/Imuruk
guards; add: the 9 pickups + 2 notes + door lock present; the **6-code enumeration yields a unique code**;
the **keypad `answer` equals the intended middle row**). `validate_keys.py` still green (escape excluded).
Once built, graduate durable facts to **`AGENTS.md`** (hospital: the new escape + code; `escape_rooms/AGENTS.md`:
the **inventory snap-grid + overlay mechanic**). Site is **Mac-only git** — Syncthing carries edits; Lucas
renders/commits there.

**Sequencing note.** Phase 1 (engine) and Phase 2 (content design) are independent and can proceed in
parallel; Phases 3→4→5 are linear and follow both.

### Phase 1 — DONE (2026-07-21)

The draggable snap-grid inventory shipped in the shared engine (`shared/pano-player.js` + `.css`, bumped
to `?v=36` across all four `play.html`). The notebook now renders a **Clues** list + a **Collage board**
(`#nbBoard`) of draggable image tiles that auto-tile, snap to a grid (`NB_CELL=132`, default 3 cols via
`SCENARIO.boardCols`), stack multiple per cell, and persist their `pos` for the session; a per-clue
**`overlay:true`** flag renders a tile semi-transparent. Retrofitted **Alaska** (its three masks flagged
`overlay:true` → now physically draggable + stackable). Durable spec: `../../AGENTS.md` → "Collage board".
Coverage: `tests/e2e/alaska_full.spec.js` (board tiles + a real drag-snaps-a-cell assertion) + unit +
smoke all green. **No `scenario.json` schema break** (all new fields additive). Next: **Phase 2** — design
the nine postcards (Latin square), the three ordinal variables, the two editorial notes, and verify the
six-codes-to-one combinatorics.

### Phase 2 — DONE (2026-07-21): the nine postcards, the variables, the code

Content design only (no art/wiring yet). All combinatorics **verified + reproducible** in
**`escape2_facets.py`** (stdlib; run it after any digit/variable/note change) — it proves the three
pairwise crossings are clean, the six pairings give six **distinct** codes, and the intended pairing →
the keypad code.

**Theme (decoupled from the lake data).** The crush is laying out a spread of readers' **summer-trip
postcards** for the local tourism magazine. Coworkers' cheerful notes from around Alaska — fishing,
berries, hot springs, hikes. Nothing references `alaska_lake_data`; every value is authored on the card.

**Three ORDINAL faceting variables (each 3 levels):**
- **season** — June / July / August (**rows**, down the page; middle level **July**)
- **remoteness** — roadside / short hike / backcountry (**cols**, across; gentle→wild L→R)
- **trip length** — a day / a weekend / a week (**the DECOY**; the editor rules it out)

The 9 cards are a **Graeco-Latin square**: `length = (season + remoteness) mod 3`, so **every** pair of
variables tiles a clean 3×3 (no arrangement visibly fails — the point). Faceting **rows=season ×
cols=remoteness** puts the **July row across the middle**, and its three digits L→R (roadside→backcountry)
are the **keypad code 729**. The other five pairings give 972 / 826 / 682 / 874 / 784 — the codes a player
gets by faceting the *wrong* two variables; the editorial notes steer to the right pair.

**Verified card table (digit · season · remoteness · length):**

| digit | season | remoteness | length | (in the July/middle row?) |
|:---:|---|---|---|---|
| 3 | June | roadside | a day | |
| 8 | June | short hike | a weekend | |
| 1 | June | backcountry | a week | |
| **7** | **July** | **roadside** | a weekend | ← middle row, col 0 |
| **2** | **July** | **short hike** | a week | ← middle row, col 1 |
| **9** | **July** | **backcountry** | a day | ← middle row, col 2 |
| 5 | August | roadside | a week | |
| 6 | August | short hike | a day | |
| 4 | August | backcountry | a weekend | |

**Keypad `lock.answer` = `729`** (3-digit, per Lucas). Escape stays out of the codec.

**Card face spec.** Each postcard shows: a **prominent centred digit** (legible when tiled small on the
board — it's what the player reads across the middle row); a **franked tag block** with all three
attributes, e.g. `July · backcountry · a day` (the *semi-structured* surface Lucas asked for, so the
player facets by tags without re-reading prose each rearrangement — the decoy tag is present, forcing the
choice); a **tiny `#n/9`** catalogue mark (so the player knows the set is complete). Prose is the charm +
the diegetic justification for each tag; the tags are the working surface. One face — no flip.

**The nine postcards (prose; each encodes its three attributes experientially):**

1. **#1 · June · roadside · a day · digit 3** — *"Snow still packed in the ditches but the sun's up half
   the night now. Grabbed a day off and just drove till a pull-off looked good — camera on the dash the
   whole way, home before dark. Or what passes for dark in June. — Priya"*
2. **#2 · June · short hike · a weekend · digit 8** — *"Breakup's finally done — trail was mud to the
   knee, but only an hour in from the lot. Pitched Friday, walked out Sunday. Two nights was just enough
   to dry the boots. — Marco"*
3. **#3 · June · backcountry · a week · digit 1** — *"The floatplane dropped us Monday and doesn't come
   back till Saturday. No road within fifty miles, no bars on the phone, and the light never really
   goes. Seven days of nobody. Bliss. — Nadia"*
4. **#4 · July · roadside · a weekend · digit 7** — *"Peak of summer and every turnout on the highway's
   got a camper in it. Snagged one right off the road Saturday, stayed the night, drove home Sunday. Warm
   enough to sit out in a t-shirt at midnight. — Deb"*
5. **#5 · July · short hike · a week · digit 2** — *"Hiked the hour in from the trailhead and just…
   stayed. Seven days, same little meadow, wildflowers up to here and the sun on the tent by seven every
   morning. Didn't want to walk back out. — Kim"*
6. **#6 · July · backcountry · a day · digit 9** — *"Chartered the little plane just for the day — landed
   on a gravel bar miles from anywhere, fished till the pilot came back at six. High summer, hot enough
   we swam. One perfect day, no road, no nothing. — Theo"*
7. **#7 · August · roadside · a week · digit 5** — *"A whole week in the camper, never more than a stone's
   throw from the highway. First of the fireweed's gone to cotton and there's a real chill by 2am now.
   Aurora one night — faint, but back. — Sol"*
8. **#8 · August · short hike · a day · digit 6** — *"Quick one — hour up the trail and back before
   supper, buckets of blueberries to show for it. Leaves just starting to turn at the tops. Fingers
   stained for days. — Ivy"*
9. **#9 · August · backcountry · a weekend · digit 4** — *"Packrafted three days from the nearest road,
   out over the long weekend. Termination dust already on the high peaks and the nights properly dark
   again — summer's turning. Worth every mile. — Wes"*

**The two editorial notes (break-room table; indirect — never say "facet"):**
- **Note A (fixes rows = season, chronological, July centrepiece):** *"Love the pile of postcards! For
  the spread, take the reader through the season — run them from the first of summer at the top down to
  the tail end at the bottom, so the height of summer sits right across the middle of the page. That July
  band is the heart of the piece."*
- **Note B (fixes cols = remoteness L→R; rules out the length decoy):** *"And read them left to right by
  how far you've got to go to get there: the easy roadside stops on the left, the deep backcountry on the
  right. I don't care how *long* anyone stayed — that's not the story. It's **when**, and **how far
  out**."*

Together they pin rows = season (Jun→Aug, top→bottom), cols = remoteness (roadside→backcountry, L→R),
length = ignored ⇒ the unique pairing → **729**. *(Harder variant if wanted: drop Note B's "I don't care
how long" line so length is only un-hinted, not explicitly excluded — the player must infer it's the
leftover dimension.)*

**Door — the started collage (non-pickup `clue` on the back of the door; the FORMAT key, no axis labels):**
An empty **3×3 frame with the middle row highlighted** (three glowing slots) + the crush's line: *"I've
started the layout here on the back of the door — help me fill it in? The three across the middle are the
ones I need."* Tells the player it's 3×3 and that the **middle row is the code**, without revealing the
faceting variables (those come from the editorial notes). The keypad sits beside it.

**Pickup distribution (INTENDED — adjust at wiring to where hotspot boxes actually land, as the v1 escape
had to):** pharmacy ×2 (#1,#2), elevator ×2 (#3,#4), corridor ×2 (#5,#6), lab ×1 (#7), break room ×2
(#8,#9) = 9 postcards; **two editorial notes on the break-room table**; the started-collage + keypad on
the break-room door. Each postcard is a `pickup` `clue` (opaque tile — **no `overlay`**); the digit + tags
live in the card art, the `pickup` string is a one-line notebook caption (e.g. `"Postcard #4 — July ·
roadside · a weekend (7)"`).

Next: **Phase 3** — art (nine postcards, two notes, the started-collage door, the break-room scene), then
Phase 4 wiring (retire the v1 map puzzle; mark the pickups + notes + door lock `729`).

### Phase 3 (deterministic art) — DONE (2026-07-21); wrap art is Lucas's on the harness

Split agreed with Lucas: **load-bearing art rendered deterministically** (exact digits/tags/prose can't be
trusted to gpt); **wrap/scene art = gpt harness** (Lucas); **editorial notes = plain-text `clue` bodies**
(no art needed). Rendered by **`make_postcards.py`** (matplotlib, deterministic), which **imports all card
data from `escape2_facets.py`** — the same module the verifier checks — so the printed digit on each card
cannot drift from the verified code 729.

- **`postcards/postcard_1.png … postcard_9.png`** — the nine collectable postcards (square 800×800; a
  seasonal band, the prose + sender, a postage-stamp **code digit**, a franked **tag strip**
  `season · remoteness · length`, and a `#n of 9` catalogue mark). Named by catalogue #, not by digit.
- **`postcards/collage_door.png`** — the back-of-door started layout: an empty 3×3 with the **middle row
  highlighted** + caption "the three across the middle are the ones I need". No axis labels (the faceting
  variables come from the editorial notes).

Wire at Phase 4: each postcard = a `pickup` `clue` with `image: "postcards/postcard_N.png"`, opaque (**no
`overlay`**), `pickup` = a one-line caption; the collage = a **non-pickup** `clue` with
`image: "postcards/collage_door.png"` + the crush's body line; the lock `answer: "729"`.

**OPEN — board legibility (flagged to Lucas 2026-07-21, needs his call before Phase 4).** On the collage
board, tiles render ~120 px (`NB_CELL` from Phase 1). The **code digit is legible** at that size, but the
**tag strip is not** — so a player can't facet by reading tags *on the board*; they'd have to identify each
card by its digit from the in-room read (working-memory load the case-file is meant to avoid). Options:
(a) **visually encode the two facet variables** so arranging works at thumbnail — season = a bold tile
colour (the band already hints it), remoteness = a clear icon (car / boot / plane) — keeping the digit for
the code and tags for the full read (a cheap deterministic tweak to `make_postcards.py`; **recommended**,
most robust); (b) **enlarge** the board tiles (bump `NB_CELL`) and the on-card tag text so tags read at
size (simpler, but strains mobile width); (c) accept identify-by-digit + the notebook. Recommend (a).

### Phase 4 — art handoff (2026-07-21): scene prompts + box-marking checklists rewritten for v3

The current scene PNGs are still the **cool/clinical v1** art (the break room even shows the old
survey-chart map on the wall) — the summer prompts were written but **never regenerated**. So all five
scenes need regenerating. Done this pass, in `scenario.json`:

- **`authoring.scenePrompt`/`doorPrompt` rewritten for all 5 rooms** — kept the summer reskin, but:
  (1) postcards are now **staff summer-trip postcards, not "of lakes"** (decoupled from the data);
  (2) the **break room** drops the v2 reference poster + the open WebR laptop + the v1 survey-chart map,
  and instead shows the **keypad door with a part-started 3×3 magazine COLLAGE pinned to its inner face**,
  a **corkboard of trip postcards**, and the **editor's marked-up notes on the table** (laptop now closed,
  pushed aside — the escape is non-computational); (3) the **boss** fridge lost its postcards (crayon
  drawings instead) so no pickup is tempting there.
- **`plannedHotspots` rewritten to the v3 box-marking checklist** so the harness marks boxes drop-in:
  - **Postcard distribution (revised from Phase 2):** pharmacy **#1,#2** · elevator **#3,#4** · corridor
    **#5,#6,#7** · break room **#8,#9** · **boss none** (moved the lab's card to the corridor noticeboard —
    holiday postcards in the pilot-emergency lab read oddly). All 9 collected before the break room. The
    specific #→room mapping is arbitrary (player collects all 9); adjust to where boxes land.
  - **Break room (`escape1`):** a **`lock`** (keypad, answer **729**), the **collage `clue`** (non-pickup,
    `postcards/collage_door.png` — the format key), **two editorial-note `clue` pickups** (A pins rows=season,
    B pins cols=remoteness + rules out length — text bodies, no art), **two postcard pickups (#8,#9)**, and
    the forward (gated on the lock) + back doors. **The v1 `map` puzzle is gone from the checklist.**

**Lucas's next step (harness :8751):** regenerate all 5 scenes from the new prompts, then mark the boxes
off each room's `plannedHotspots`. **Then I wire (final Phase 4):** fill the postcard/note/collage clue
bodies + the `729` lock, set the postcard tiles opaque (no `overlay`), rewrite the escape `entry` +
`escapeDone` onto the crush/dinner throughline, retire `escape1/map.png`+`map_points.json`+`make_map.py`
and the map guard in `test_hospital.py`, and re-run the guards.

### Phase 4 wiring — DONE (2026-07-21, harness step-4 "fill the puzzles")

Lucas did all wraps + hotspot boxes; I filled every puzzle from the notes + designNotes, recomputing
every value against `alaska_lake_data.csv`:

- **Four analysis MCQs** (all ≥6 options, no `reveal`, escalating axis-agnostic `wrong` hints, and a
  short `feedback.correct` that names the answer for the field notebook). Verified answers + wired correct
  indices (= the decoder key `c(3,1,4,2)`): **room1** idx 3 — Na~Cl r = 0.9993 (0.994 w/o North_Killeak),
  chloride is a safe proxy; **room2** idx 1 — **White_Fish_Lake** (Euclidean 257 vs next 363); **room3**
  idx 4 — **NOAT** weakest per-park (BELA 1.0 / GAAR 0.675 / NOAT 0.424, the pooled 0.999 misleads);
  **boss** idx 2 — **Chlorocidin** (Cl 337.23 is the max of the five candidate elements; 6th distractor
  **Magnistatin**/Mg kept). Practice starters give only the dataset name; the **boss** starter keeps the
  assessed exercise's own `ggplot(aes(x=mg_per_L,y=lake))` (it's a read-the-plot assessment — the code
  doesn't reveal which element is highest).
- **Escape v3** wired exactly as specced: `lock` **729**, non-pickup **collage** clue, two pickup
  **editorial-note** clues, nine pickup **postcard** clues (opaque, image + caption), `boardCols:3`,
  way-out door `requires` the keypad + no `to` (fires `escapeDone`). Rewrote `story` (dinner-date hook),
  the `escape1` entry, and `escapeDone` onto the crush/dinner+collage throughline (the old Imuruk map
  ending is gone).
- **Guards green:** `test_hospital.py` rewritten (map guards → keypad/collage/MCQ-vs-CSV guards; imports
  `escape2_facets` for the 729 check), `decoder/validate_keys.py` PASS, `Rscript decode_codes.R` self-test
  grades the id-8 hospital 40/40 with `ans=3,1,4,2`. AGENTS.md updated (map escape → keypad escape).
- **Still open:** board legibility (remoteness icons — decision 1 above); the orphaned v1 map assets
  (`escape1/map.png`,`map_points.json`,`make_map.py`) can be archived; book-page surfacing.

### Open decisions — parked for a later turn (2026-07-21)

Both deferred by Lucas at session close; resolve before/at final wiring:
1. **Board legibility → remoteness icons.** The code digit reads at ~120 px board size and season reads via
   the stamp colour, but the tag strip does not. Recommended fix: add a **remoteness icon** (car / boot /
   plane) to each postcard so the columns are as scannable as the rows — a cheap `make_postcards.py` tweak,
   independent of the wrap art. (Full options in Phase 3's "OPEN — board legibility".)
2. **Analysis-room art: summer regen vs leave cool.** Regenerating rooms 1–3 + boss for the summer look
   means re-marking their boxes, which may clear the four wired MCQs (content is safe in `scenario.json` —
   re-wire if so). Alternative: regenerate **only the break room** now (the one that structurally must
   change for v3) and reskin the analysis rooms later. Lucas to choose which at art time.

---

## Audit against the `escape_room_puzzles` skill (2026-07-22, Claude ← Lucas)

Full scenario-by-scenario audit. **Everything wired verifies clean.** Re-ran every answer against
`alaska_lake_data.csv`, plus `escape2_facets.py`, `test_hospital.py`, `validate_keys.py` — all green.
- Room 1 Na~Cl r = 0.9993 (0.9941 w/o North_Killeak) → idx 3 ✓. Room 2 nearest = White_Fish, dist 257 vs
  next 363 (huge margin), 6 real lake distractors ✓ → idx 1. Room 3 per-park Na~Cl BELA 0.9997 / GAAR
  0.6755 / NOAT 0.4235 → NOAT weakest, idx 4 ✓ (the taught pooled-correlation trap). Boss Cl 337.23 max
  overall and of the 5 candidates → Chlorocidin idx 2 ✓; 6th distractor Magnistatin (Mg 37.68). Escape:
  6 distinct facet codes, intended pairing → 729 ✓. Decoder key `[3,1,4,2]` in lockstep.

**Doc drift FIXED (canon was stale).** `AGENTS.md`'s "room ladder" + "book-chapter alignment note" still
described the *original* (superseded) ladder — room 1 pH-spoilage, room 2 highest-sodium, room 3
most-lakes — none of which are wired; the chapter-alignment revision replaced them with salt-proxy /
heatmap / facet and the canon never caught up. Rewritten to match the wired v3 scenario (only the boss
line was still correct). Also stripped two **stale designNote pickup blocks** in `scenario.json` (room 1
"Dana soft-water" card; room 3 "BELA volcanic-coast" + crush soft-water note) — leftovers from the
retired v1/v2 pH-based escape, superseded by the v3 faceting postcards. Player never saw them (designNote
is ignored), pure hygiene.

**Ladder monotonicity — the boss rung (RESOLVED 2026-07-22).** Rooms rise 1→2→3 (correlate →
profile-match a heatmap → facet *and reinterpret*), but the **boss is the gentlest cognitive rung** — a
single-lake "read the highest element" lookup — so the curve peaks at room 3 and dips at the boss. Already
an accepted deviation (boss = the assessed exercise verbatim), but Lucas wants to **escalate the boss**.
Sketch (2026-07-22): stop *naming* the lake — instead give the **park** the pilot flew over + a
flight-recorder **pH reading**, so the student must `filter(park)` + find the lake at that pH to *derive*
the lake, then find its most-abundant element, and answer via a **plot-picker** (map puzzle type — adds
puzzle-type variety). **Data supports it cleanly:** North_Killeak is in **BELA at pH 8.04**, the highest
pH in BELA and unique (BELA has no duplicate pH), so "BELA + pH 8.04 → North_Killeak" is a single clean
winner. (Caveat: GAAR has a duplicate pH — Nutavukti/Takahula both 6.88 — so the derive-by-pH trick only
works for a park with distinct pH values; BELA/North_Killeak is safe.)

**RESOLVED (Lucas):** keep it a plain **MCQ — no plot-picker, no new engine wiring.** Just reframe the
prompt: stop naming the lake, give the **park (Bering Land Bridge) + the flight-log pH (8.04)**, and let
the student **derive** the lake (`filter` BELA → the pH-8.04 lake = North_Killeak) before finding the
highest of the five candidate elements → antibiotic. Options + answer (**Chlorocidin, idx 2**) + decoder
key **unchanged**; the off-list Na/Mg abundance trap stays. **Wired 2026-07-22:** boss `question.prompt`,
`entry` text and `feedback.wrong[0]` reworded to the park+pH derivation; boss `starterCode` dropped to
bare `alaska_lake_data` (method → the wrong-hint, per the 2026-07-21 convention). `test_hospital.py` +
`validate_keys.py` stay green (answer/index unchanged). Chosen over the plot-picker/map-pick because it
adds a real derive-the-lake step and keeps the analyte traps, with zero new engine work.

---

## Audit + promotion to `ready` (2026-08-05, `escape_room_audit`)

Full four-phase audit, all clean. Every answer independently re-derived from the **served** long-format
CSVs (`phylochemistry/sample_data/metabolomics_hospital*.csv`): R1 choline~2-AIB pooled r 0.985 (within
0.95/0.98) → idx 3; R2 nearest to Elias (creatinine excluded) = Patient 54 d 0.10 vs 2nd 0.97 → idx 1; R3
p-cresyl~indoxyl pooled 0.95 / within −0.22 & 0.21 (Simpson) → idx 4; boss creatinine z +3.5 vs cohort,
cohort max, next candidate −0.83 → Nephrocidin idx 0. Decoder `c(3,1,4,0)` in lockstep; `test_hospital.py`,
`escape2_facets.py`, `validate_keys.py`, `Rscript decode_codes.R`, `validate_assets.py` (ready-strict) all
green.

**One bug found + fixed — the blank Editor's note B.** `escape1`'s `editor_s_note_b` had `body: ""` +
`pickup: true` + no image → it opened a blank modal and logged a contentless notebook entry. Note A had
absorbed both axis instructions at wiring, so B was a dead orphan. Per Lucas: **deleted B**, renamed A to
"Editor's note" (the escape now has a single note; A carries the full rows=season + cols=remoteness + ignore-
length guidance). `test_hospital.py` updated to expect **one** editorial note with a non-empty body.

**Central-validator gap closed (generic class → central check).** `validate_assets.py`'s blank-clue check
treated any truthy `pickup` as content, so a boolean `pickup:true` masked the empty body. Tightened: only a
**non-empty string** pickup is a caption; a boolean `pickup:true` with empty body + no image is now flagged.
New regression test **`authoring/test_validate_assets.py`** pins the string-vs-boolean distinction.

**Promoted `status` → `ready`** and regenerated `scenario_inventory.json`. Publish dependency: the two
metabolomics CSVs must be pushed live from the Mac (github.io URLs 404 otherwise). Non-blocking polish left:
the two decorative Alaska art residues (room2 lake print, room3 parks map) + the boss flight-recorder prop
regen — all art-harness work. Not yet in the JS e2e `SCENARIOS` list (`tests/e2e/{smoke,full_playthrough}.spec.js`)
— add when convenient so the Playwright playthrough covers it (needs the CSVs live first).

---

## Scene-spec backfill for build_world (2026-08-06)

Hospital was built with the OLDER harness (scenePrompt, no sceneSpec). Backfilled a reconstructed
`authoring.sceneSpec` for all 5 built rooms so it's editable/regenerable in the v2 build_world harness.
Verified: `to_hotspots` covers every gameplay hotspot id, `render_prompt` round-trips, validators unchanged
(test 0 fail, validate_assets PASS — status:ready holds, decoder c(3,1,4,0)). Older prompts had no explicit
`seam` clause, so a plausible calm interior seam was supplied per room. Backup:
`_scratch/scenario.json.pre_scenespec_20260806_*.bak`.

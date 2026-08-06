---
authority: intent
---

# Trees scenario (draft) — Data Wrangling

Chapter `wrangling`, scenario `trees`. **Idea captured 2026-07-21 (Lucas).** Draft only — nothing
designed/verified/built yet. First scenario in a new **`wrangling`** chapter folder (sibling of
`data_vis`, `data_vis2`, `hierarchical_clustering`). Codec id: take `next_free_id` from
`rooms/scenario_inventory.json` when scaffolded (10 at capture time; whichever of temple/trees is
scaffolded first takes it — regenerate the inventory after).

Chapter alignment: the CHEM5725 **Data Wrangling** exercise (`teaching/CHEM5725/exercises.csv`) drills
`group_by()` + `summarise()` — grouped means, max/min, ranges (its own rows use `beer_components` and
`wine_quality`, e.g. "which wine type has higher mean sulfate"). This scenario exercises the **same
technique on a different dataset/story** (a modified New York street-tree set), so it can serve as one
half of the chapter's **pre/post pair** (see `../../../notes/puzzle_inventory.md` → chapter design
principles).

## Analog grounding (Step 0 — the real-world act the code performs)

The design starts from the escape-room harness's **zeroth step**: *where, in ordinary life, do people
perform by hand what this code does?* The Data Wrangling verbs are `group_by` + `summarise` —
**sorting things into piles by a shared trait, then reading one number off each pile** (the tallest in
each pile, the average width of a pile, the spread within a pile). That is exactly what a **field
naturalist** does: walk a transect, bin what you see by species / health / location, and tally a
summary per bin.

And — the point Lucas flagged for computation-heavy rooms — the **escape** is built on the case where
*the computation has already been performed and a person only has to recognise it*: each monorail car
has already been "grouped and summarised" for you in its wall imagery; the player's job is to **read
off which grouping variable produced that summary**, not to compute it. That recognition-not-
computation move is the whole escape.

## Theme / world

The player is a **forest ecologist on an alien world**. The entire scenario lives in a **canopy
research network** — a web of **catwalks and a forest monorail/chairlift** strung through the crowns
of impossibly tall trees. The forest is so deep we **never see the ground**: only canopy, drifting
mist, and the occasional **mountain peak** breaking through. In most "rooms" the mist hangs close; in
one or two, it **clears** for a reveal (a valley of canopy, a far ridge of peaks). Earthy and organic
but unmistakably alien — bioluminescence, strange bark, oversized fungal forms — not chrome sci-fi.

Distinct from the field-science interiors (Alaska station, Hawai'i wellroom) and the temple: this is
an **exterior, airy, vertical** world. Teal-and-amber house palette still holds (dusk canopy, amber
lichen-glow, mist).

## Storyline (DECIDED 2026-07-21, session Forest)

The player is **one person** — a forest ecologist on this alien world who is *also* an obsessive
**artifact collector**. The instruments and the tree measurements are the day job; the collecting is
the drive. This single-protagonist framing does real design work:

- **The monorail cars are the collector's own hoard.** The shelves of specimens (fronds, pods, cones,
  cores, vials) aren't just field samples — they're the collector's trove, **catalogued and sorted by
  their own hand**, each line's car sorted by a different variable. That gives an in-world reason the
  cars are "already grouped and summarised": the player is reading *how the collector chose to sort
  their own collection*, which is exactly the recognition the escape depends on.
- **The prize is an alien artifact in a cliff-side vault.** For years the collector has known of an
  **alien gate set into a rocky precipice** at the edge of the canopy — a vault they've never been able
  to open, rumoured to hold a genuine alien artifact. The whole scenario is the attempt to get in and
  add it to the collection.
- **The escape = opening the vault.** The 3×3 grid IS the alien gate's lock: recognise, for each
  monorail line (door shape), which variable that line's car was grouped by, and the gate opens. Inside
  is the artifact — the payoff.
- **The boss = a boulder on the scramble up to the cliff.** The boss is its own spot, *on the way* to
  the vault: a steep, winding scramble to the cliff top with a **boulder blocking the path**. Clearing
  the boulder (the culminating graded wrangling task) opens the final stretch to the vault. This is
  where the **mist clears for the reveal** — the cliff, the precipice, the gate ahead.
- **The daily ritual — why the trek happens at all (DECIDED 2026-07-21).** Every day the collector
  finishes the round of research stations and then, *at the end of the day*, makes the same
  pilgrimage: up the scramble to the cliff to try, once more, to crack the vault. It's an obsessive
  nightly routine — they've done it countless times and never got in. Framing the run as "one more
  end-of-day attempt at the vault" gives the whole station→scramble→cliff journey its motive, and sets
  up the payoff: *today* is the day it finally opens. (The scenario `story` / between-room `entry`
  cards carry this — the opening establishes the routine; the finish is the artifact claimed at last.)

## Structure — three stations, a boss, and the escape (DECIDED 2026-07-21)

Ladder (per the skill's reverse-engineer-from-the-boss rule): **3 graded stations + a graded boss
(its own room) + the ungraded escape**. Layout: `station1 →(line □)→ station2 →(line ○)→ station3
→(line △)→ scramble/boulder (BOSS) → cliff-top vault (ESCAPE)`, so each of the three lines is ridden
once and its car's grouping is seen before the escape asks about it. The boss (the boulder on the
scramble) sits *between* the last station and the vault — clearing it opens the final climb; the
vault gate at the top is the ungraded 3×3 escape.

- **Research stations = the puzzle rooms.** Each station is a platform/hut in the canopy with an
  **instrument** that measures the surrounding trees and dumps a table into the WebR console. At each
  station the player solves **one data-wrangling puzzle** off that instrument's data (a modified
  `ny_trees` set). Deliberately bread-and-butter `group_by`/`summarise`:
  Refined ladder (DECIDED 2026-07-21, session Forest): each station = `group_by |> summarise` +
  **plot** + answer. The three stations are single-grouping warm-ups on the three categorical axes
  (species / vigor / zone — matching the escape's three lines); the boss is the **regroup** capstone,
  built on a deliberate **Simpson's-paradox flip** the last station sets up:
  - **Station 1 — single grouping (species).** `group_by(species) |> summarise(mean(trunk_girth_cm))`
    → widest species. + plot.
  - **Station 2 — single grouping (vigor).** `group_by(vigor) |> summarise(mean(bark_glow))` →
    brightest-glowing vigor class. + plot.
  - **Station 3 — single grouping (zone): THE SHORTCUT.** `group_by(canopy_zone) |>
    summarise(mean(vitality_index))`, phrased *"which zone's trees are healthiest as they stand?"* →
    the count-weighted answer. This deliberately hands the player the *naive grand-mean* answer.
  - **Boss (the boulder on the scramble): THE REGROUP.** Same `vitality_index`, but phrased *"which
    zone is genuinely the best place for a tree to thrive, regardless of which species dominates it?"*
    → forces `group_by(canopy_zone, species) |> summarise(mean)`, **ungroup**, `group_by(canopy_zone)
    |> summarise(mean)` (species-balanced). Because the data has an engineered flip, this lands on a
    **different zone** than S3's shortcut. The player recognises they already computed S3's answer the
    easy way and it's *wrong here* — the whole teaching moment. Mints the Canvas code.
  - **Why this shape (DECIDED):** Lucas wanted the shortcut route to be its own (third) puzzle so that
    at the boss the different wording + different answer is immediately felt. Fairness is handled by
    **precise phrasing + explicit clues** that point at the species-mix confound — it's a taught
    lesson, not a hidden gotcha. This average-of-averages-vs-grand-mean point is **new to Lucas's
    curriculum** (flagged as a highlight).
- **The escape** is the ungraded, no-instructions two-phase finale (the 3×3 grid, below) — a **new
  puzzle type** to build.

- **Between rooms = the monorail rides.** To get from one room to the next the player boards a
  **monorail car** on one of **three lines**. The rides are the connective tissue *and* carry the
  escape's hidden information (below). **The three lines are identified by DOOR SHAPE, not colour**
  (see the accessibility note) — a **square** door, a **circle** door, a **triangle** door.
  - **Ride mechanic (DECIDED):** you step into the car through its shaped door; a **sound plays**; after
    **~5 seconds** the sound ends and the **far door opens**, letting you step out at the next room.
    Navigation is plain **back-and-forth** (the two-door back-nav already in the engine) — **no
    auto-logging of rides**; the player walks back to re-inspect a car if needed. Keep the ride short so
    it's a beat, not dead time; use it for a mist-clears reveal.

## The monorail cars — where the "already-summarised" data hides

> **SUPERSEDED 2026-07-21 (session Forest):** the shelves no longer sort by the tree variables
> (species/health/zone). They hold the collector's *collectibles* sorted by a visual **trait** —
> **beetles by colour (□), cones by size (○), shells by shape (△)** — AI-generated, opt-in pickups.
> See *Scene + hotspot inventory* and *Scenario WIRED + handoff*. The brainstorm below is kept for
> history; read it through that lens.

Three lines (square / circle / triangle door). **Each line's car has SHELVES of specimens, and those
specimens are GROUPED and summarised by a different variable** — legible on the shelf, never a
captioned chart. Shelves chosen over wall-imagery (DECIDED): specimens on shelves are **easier to
inspect** and more flexible than glowing wall-patches. The player rides all three; **no auto-log** —
back-nav lets them revisit a car to re-read its shelves.

- **Shelved specimens (the readable grouping cue).** Trays / racks of collected samples — pressed
  fronds, seed-pods, cones, cores, vials — **sorted into distinct bins**, each bin a group. One line's
  car sorts the shelves **by species** (each bin a different tree kind); another **by health status**
  (vigorous → sickly bins); another **by canopy zone** (bins laid out as a little map). The **grouping
  variable is what changes between lines**, not the underlying trees. The per-bin "summary" is soft —
  "these sort into four kinds by health," not "Norway Maple = 4.2" — so the player reads *which variable
  the car grouped by*, which is all the escape needs.
- **Fungus stays as flavour.** Bioluminescent shelf-fungus / lichen still dresses the cars for the
  alien-earthy mood, but the **specimen shelves carry the actual grouping signal** (fungus was too vague
  to read reliably).

## The escape — a 3×3 grouping grid

At the network's exit/hub: a **3×3 button grid**.
- **Columns = the three monorail lines, keyed by DOOR SHAPE** (square / circle / triangle) — the same
  shaped doors the player boarded. Shape, not colour, is the line's identity.
- **Rows = the three collectible TRAITS** — **colour / size / shape** (REVISED 2026-07-21; was
  species/health/zone). Match each shape-line to the trait its collection was sorted by: □ beetles→
  colour, ○ cones→size, △ shells→shape.
- The player must select, **for each shape column, the row (grouping variable) that that line's car
  was grouped by** — i.e. the correct **one-button-per-column combination** (three presses, order-
  independent, one per column). Getting the mapping right unlocks the escape.

This is a **matrix / matching** variant of the escape-side vocabulary — closest to the **pattern-match
lock (#6)** and the "recognise the group-by" idea, and a lighter cousin of the **inference board
(#11)**. It's the *ungraded, unlabelled echo* of the group-by/summarise the stations taught (per the
chapter principle: the escape re-poses the boss reasoning with the labels stripped — here you recognise
*which grouping made this summary* from imagery alone).

**Engine note (DECIDED — build a new puzzle type):** build a small **grid-select** puzzle type — an
N-column × M-row button grid, one selection per column, that checks the selection vector against a key
and fires `solveRoom` when correct (an escape/ungraded gate, out of the codec — sibling of the
`ledger`/`lock` types). Add it to `../../../notes/puzzle_inventory.md` when specced. (Rejected the
cheaper "encode the mapping as a 3-char lock code" fallback — the grid reads far better.)

**Accessibility — SOLVED by door shape.** The earlier colour-blind worry (columns = line *colours*) is
resolved: the lines are identified by **door SHAPE** (square / circle / triangle), an inherently
non-colour cue, carried consistently on the boarding door, the car, the notebook, and the grid column
headers. Colour can still tint each line for flavour (use a colour-blind-safe trio, e.g. Okabe-Ito),
but **shape carries the identity** — nothing load-bearing rides on hue.

## Resolved 2026-07-21

- **Structure:** 3 graded stations + a **graded boss in its own room** + the ungraded grid escape.
- **Cars carry SHELVES of grouped specimens** (not wall-imagery); fungus is flavour only.
- **Lines identified by DOOR SHAPE** (square / circle / triangle) — resolves the colour-blind issue.
- **Ride mechanic:** board → sound plays ~5s → far door opens; plain **back-and-forth** nav, **no
  auto-log** of rides.
- **Escape = a NEW `grid-select` puzzle type** to build (not a lock fallback).
- **Ambient = spores** (canopy cousin of fireflies).
- **Storyline (session Forest):** ecologist **and** collector = one person; monorail cars = the
  collector's own catalogued hoard; the prize = an alien artifact in a **cliff-side vault**; the
  **escape = opening that vault** (the 3×3 grid is its gate-lock); the **boss = a boulder** on the
  steep scramble up to the cliff (mist-clears reveal here).
- **Refined puzzle ladder (final):** S1 group_by(species)→girth; S2 group_by(vigor)→glow; **S3 =
  group_by(zone)→vitality, the SHORTCUT** (count-weighted); **boss = the REGROUP** (species-balanced),
  landing on a *different* zone via an engineered **Simpson's-paradox flip**. Shortcut→Cragside,
  regroup→Sunspire Heights. Fairness carried by phrasing + explicit clues; new to Lucas's curriculum.
- **Dataset chosen & BUILT (Option 1):** engineered alien re-skin `data/forest_census.csv` with
  multi-axis structure + the flip. All four answers verified. See *Alien re-skin + verified puzzle
  slate* section.
- **Storyline ritual:** the collector's nightly end-of-day pilgrimage up to the vault motivates the
  trek; *today* it finally opens.

## Data reality — signal vs noise (VERIFIED 2026-07-21, session Forest)

Working copy duplicated to `data/ny_trees_raw.csv`; profiled with `_scratch/explore.py` (clip to
height 5–120 ft, diameter 1–60″, drops ~17k dirty rows → ~361k clean). Findings that constrain the
puzzle design:

- **The categorical skeleton is real and clean.** 12 real species (`spc_common`), 4 boroughs
  (`boroname`: Queens 175k ≫ Brooklyn 107k > Bronx 42k > Manhattan 37k), 4 status classes (`status`:
  Good 243k ≫ Excellent 84k > Poor 33k > Dead 1.5k). **Counts group cleanly on every axis** with big
  unambiguous gaps — great puzzle material for `summarise(n = n())` / `count()`.
- **The continuous columns carry signal on ONE axis only: species.** `tree_height` and
  `tree_diameter` are structured *per species* (Callery Pear ~21 ft & 7.5″ … Red Maple ~100 ft, Silver
  Maple ~23″ widest) — clean, botanically plausible, well separated. But grouped by **borough or
  status they're near-identical** (boroughs are just species mixtures): mean height per borough spans
  only 60–72 ft, max height per borough is ~119.99 in all four. So a mean/max/range-of-a-continuous-
  column puzzle is **only defensible grouped by species**, not by borough/status.
- **Consequence for the 2-var / 3-var rungs.** A genuine, *meaningful* two- or three-variable grouping
  on a continuous column needs a second axis that actually moves the number — which the raw data does
  **not** have (only species does). Real clean two-var answers in the raw data are **count-based**
  (commonest species per borough: Brooklyn→London Planetree, Queens→Norway Maple, Bronx/Manhattan→
  Honeylocust). "Tallest" among species is also soft at the top (Red Maple 100.7 vs Oak 99.8 vs Zelkova
  99.7 — within 1%); "shortest" (Callery Pear 21) and "widest" (Silver Maple, +7.4%) are the clean ones.

**THE FORK — RESOLVED 2026-07-21: Lucas chose Option 1.** Engineer the alien re-skin dataset with
real multi-axis structure: keep the real categorical skeleton + counts, regenerate the measured
columns so each axis genuinely moves a number. Built — see next section. (Rejected Option 2:
constrain to raw-data-supported count puzzles.)

## Alien re-skin + verified puzzle slate (BUILT 2026-07-21, session Forest)

Generator: `_scratch/build_forest_census.py` (deterministic, seed 20260721) → **`data/forest_census.csv`**
(6,000 rows, 8 cols). Uses the real ny_trees category set (12 species, 4 zones, 4 vigor classes)
re-skinned to the alien world, but the rows are **generated directly** with *engineered per-zone
species mixes* (a deliberate departure from raw real proportions — required to build the paradox flip,
below) and **measured columns from an additive effect model** so each axis drives a clean winner.
The 55 MB raw working copy was **dropped 2026-07-21** (only `explore.py` used it; repointed to the
canonical `sample_data/ny_trees.csv`). `forest_census.csv` is the shipped artifact and lives in-repo.

**Columns (student-facing):** `specimen_id, species, canopy_zone, vigor, crown_height_m,
trunk_girth_cm, bark_glow, vitality_index`.

**Category re-skin.** Species (12, real→alien by girth rank): widest = **Bloomspire**, tallest =
**Goldfan Ginko**, … smallest = **Palepear** (full list in the generator). Zones (borough→alien):
Queens→**Mistfen Reach**, Brooklyn→**Sunspire Heights**, Bronx→**Hollowdeep**, Manhattan→**Cragside**
(the vault zone). Vigor (status→alien): Excellent→**Radiant**, Good→**Thriving**, Poor→**Waning**,
Dead→**Husk**.

**Effect model (what drives what):**
- `trunk_girth_cm` ← **species** only (base 9–36 cm + noise). → Station 1 winner **Bloomspire**.
- `bark_glow` (alien bioluminescence 0–100) ← **vigor** only (Radiant 80 → Husk 5). → Station 2
  winner **Radiant**.
- `crown_height_m` ← **species + canopy_zone** — kept as a realistic **distractor** column (not
  graded), so the clue `str()` shows more than the puzzle needs and the student must pick the right col.
- `vitality_index` ← **species + zone + vigor**, engineered for the FLIP → Station 3 (shortcut) + Boss
  (regroup).

**The engineered flip (the whole teaching point).** Two forces pull against each other:
- **`zone_vit`** makes **Sunspire Heights** genuinely the best zone *for every species* (zone lift
  Sunspire +12, Cragside +6, Mistfen +3, Hollowdeep 0) → it wins the **species-balanced regroup**.
- **`species_vit`** splits the 12 species into 6 high-vitality (+20) and 6 low (0); the **per-zone
  mix is skewed** — Cragside is packed with high-vitality species (9× weight), Sunspire with low ones
  → Cragside's **raw count-weighted grand mean** is inflated and it wins the **shortcut**.
- Net: **shortcut → Cragside, regroup → Sunspire Heights** — a genuine two-way flip. Cragside only
  *looks* healthiest because of what's planted there; Sunspire is the truly better ground.

**VERIFIED answers (re-run `build_forest_census.py` to reconfirm; deterministic):**
- **Station 1** — `group_by(species) |> summarise(mean(trunk_girth_cm))` → **Bloomspire** (36.0,
  +8.8%). *Widest species.* + plot.
- **Station 2** — `group_by(vigor) |> summarise(mean(bark_glow))` → **Radiant** (79.9, +31%).
  *Brightest-glowing vigor class.* + plot.
- **Station 3 (SHORTCUT)** — `group_by(canopy_zone) |> summarise(mean(vitality_index))` → **Cragside**
  (66.5, +15% over Sunspire). Phrase: *"which zone's trees are healthiest as they stand?"* + plot.
- **Boss (REGROUP)** — `group_by(canopy_zone, species) |> summarise(m = mean(vitality_index))`,
  **ungroup**, `group_by(canopy_zone) |> summarise(mean(m))` → **Sunspire Heights** (64.2, +8.8% over
  Cragside). Phrase: *"which zone is genuinely the best place for a tree to thrive, whatever's
  planted?"* Mints the Canvas code. **Different zone than S3** — the flip fires.

**Fairness handled by phrasing + clues, not left as a trap (RESOLVED — supersedes the earlier
"regroup doesn't bite" caveat).** The boss wording explicitly asks the equal-weighting question, and
the boss clue calls out the species-mix confound (zones differ wildly in what grows there, so a raw
average misleads). A student who reuses S3's shortcut method gets Cragside and is *meant* to notice it
can't be right here — that recognition is the lesson. Thinnest (zone×species) cell ≈ 6 rows; harmless
because every student reads the identical shipped CSV, so their computation matches the key exactly.

## Ambience & time-of-day arc (DECIDED 2026-07-21, session Forest)

**Cheerful, golden, mysterious — never creepy.** Lucas has upbeat forest music picked out; the whole
run must feel positive and warm even where it's misty. The scenes carry a **time-of-day clock** that
doubles as the story's "one more end-of-day attempt":

- **Station 1** — early morning, soft **mist**, low **golden dawn** light.
- **Stations 2 → 3** — mist thins, light climbs toward **midday**, brighter and clearer.
- **Boss (boulder scramble)** — **golden-hour evening**.
- **Vault (cliff top / escape)** — **sunset**; the **mist lifts and the vista resolves** (valley of
  canopy + far peaks revealed) as the gate opens.
- **Throughout:** warm golden light even in mist (glowing/soft, not cold); `ambient: "spores"` drifting
  in the gold; `fx` a soft drifting-mist overlay early, clearing late. No horror cues anywhere.

**Elevation / location arc (DECIDED 2026-07-21) — a second progression, running with the weather.** The
monorail climbs the whole way: each platform is **higher up the trees** than the last, the mist sinks
below, and the **mountain peaks are progressively revealed**, ending on the cliff-top with the full
panorama. Baked into every scene prompt:
- **Station 1** — *lowest*, deep in the misty crown; ground hidden; one far peak barely showing.
- **Car □ → Station 2** — climbing out of the depths; near the treetop; a ridge of peaks emerging.
- **Car ○ → Station 3** — higher still; above most of the canopy; mountains clear across the horizon.
- **Car △ → Boss** — leaves the trees; a ledge high on the mountain; peaks close, canopy far below.
- **Vault** — *highest point*; windswept cliff-top; full canopy-and-peaks vista at sunset.
The two arcs reinforce each other: the day advances *and* you ascend, so the finish feels earned.

## Monorail mechanic — RESOLVED 2026-07-21 (two doors, car = its own scene)

> **SUPERSEDED 2026-08-04 (art-pipeline session):** reverted to a **single-door, world-state-switch** car.
> One door per car; a **lever (world-state switch)** inside picks direction; the SAME door shows a different
> station per state — a **multi-view door** (`door.opensOnto:[{state,reveal}]` in the scene spec → one
> state-tagged door-open variant per station, all art generated in the art step; runtime pick-by-state is
> **deferred wiring**). Chosen because later stations carry TWO monorail lines, and two-doors-per-car would
> fill the panorama with doors. This replaces BOTH the two-door model here AND the shared-"down"-node back-nav
> referenced throughout — the single door + switch is now the back-nav. See `notes/art_pipeline.md` → session
> 2026-08-04. The two-door reasoning below is kept for history.

Confirmed the **two-door car-as-scene** model (rejected a single-door bidirectional portal). Reason:
engine doors point at a **fixed** destination; a single door that delivers you to the *opposite*
platform from wherever you boarded would need custom "remember where I got on" state — more to build,
more to break, to save one door. Two doors give it all for free: walk in, the **collection shelf is on
the wall opposite the two doors**, one door goes back, one goes onward, and re-inspecting a car later is
just walking back into that scene. The square/circle/triangle shape lives on the **boarding door at the
platform**, and repeats on the car + the escape grid columns. Custom bit is small: the **ride beat** —
step in, ~5 s hum, then the onward door becomes usable (a light scene behaviour, not new door logic).

## Plots per station (RESOLVED — open item 1)

Each station = group-and-summarise → a **bar chart**, read the winning bar:
- **S1** — mean `trunk_girth_cm` per `species` → tallest bar **Bloomspire**.
- **S2** — mean `bark_glow` per `vigor` → brightest **Radiant**.
- **S3 (shortcut)** — mean `vitality_index` per `canopy_zone` → tallest **Cragside**.
- **Boss (regroup)** — **species-balanced** vitality per zone (two-stage) → **Sunspire Heights**. This
  is the codec-watermarked deliverable figure.

## Question phrasings + boss clue (RESOLVED — open item 2)

Prompts state *which question*, never the method (method → `feedback.wrong`):
- **S3 prompt (draft):** *"Your instruments have logged a vitality reading for every tree in the
  canopy. Across the four groves, which grove's trees are the most vigorous **as they stand today**?"*
  → Cragside.
- **Boss prompt (draft):** *"The vault won't answer to a careless count. It asks not where the strong
  trees happen to stand, but which **ground truly grows a tree best** — giving every kind of tree an
  equal say. Which grove is the finest ground to grow in?"* → Sunspire Heights.
- **Boss clue (draft, in-world field note):** *"Rank the groves by the vigour of the trees standing in
  them and Cragside always wins. But Cragside is thick with Bloomspire and Ironcrown — hardy stock that
  reads strong wherever it roots. That tells me the grove is full of strong trees, not that it grows
  them strong. To judge the ground itself I must give every kind of tree an equal say — take each
  species' vigour grove by grove first, then compare the groves."*

## Scene + hotspot inventory (DRAFT for sign-off — get this right BEFORE art)

Eight scenes. Door graph is linear with a shaped boarding door at each platform; cars sit *between*
platforms and carry a shelf. **Shelves = AI art (gpt-image), Lucas trying it first** (fall back to a
deterministic render only if a tray reads ambiguously). **Collections decoupled from the tree
variables (REVISED 2026-07-21):** the shelves hold the collector's *collectibles* sorted by an obvious
visual trait, not tree data — **beetles by COLOUR (□), cones/pods by SIZE (○), shells by SHAPE (△)** —
which is far more legible for both the AI and the player. The vault grid then matches each shape-line
to its trait. **Collections are NOT pickups (REVISED 2026-07-21 — Lucas wants to force backtracking):**
the clickable clue on each car is a **framed collector's note** beside the cabinet, whose verbiage
describes that collection and cues the player it matters. Re-inspection is by **riding back through the
cars** — so the single-door **back-nav (shared down-nodes) is now load-bearing**, not optional.

> **SUPERSEDED 2026-08-04 (Lucas): the framed collector's note is CUT — no written clue in the cars.** The
> grouping reads from the **tray art alone**, with the car's **shape motif on the display case** carrying the
> shape→trait link (□ on the beetle cabinet, etc.). It holds because re-inspection is by riding back down (now
> the single-door two-view door, not shared down-nodes) — the note was never load-bearing once backtracking
> exists. **Station** clues (field cards, science context for the WebR puzzles) stay. So each car now has **no
> `clue` hotspot** — just the grouped-specimen centrepiece (+ its shape motif), the drive-lever `switch`, and
> the single multi-view door. The `clue` cells for the three cars in the table below are therefore void.

| # | Scene | Time/light | Hotspots |
|---|-------|-----------|----------|
| 1 | **Station 1** (platform) | dawn, mist | `puzzle` (the instrument/console) · `door □` forward (closed, → Car □). *First room: no entry card.* |
| 2 | **Car □** | — | **beetles by COLOUR** (scene art) · `clue` framed collector's note (non-pickup) · `door` forward (→ S2) [+ build-time down-node → S1] |
| 3 | **Station 2** (platform) | late morning | `puzzle` (species→height) · `door` back (→ Car □) · `door ○` forward (→ Car ○) |
| 4 | **Car ○** | — | **cones by SIZE** (scene art) · `clue` framed collector's note · `door` forward (→ S3) [+ down-node → S2] |
| 5 | **Station 3** (platform) | midday | `puzzle` (SHORTCUT, zone→vitality) · `door` back (→ Car ○) · `door △` forward (→ Car △) |
| 6 | **Car △** | — | **shells by SHAPE** (scene art) · `clue` framed collector's note · `door` forward (→ Boss) [+ down-node → S3] |
| 7 | **Boss** (boulder scramble) | golden hour | `puzzle` (REGROUP) · `clue` boss field-note (species-mix confound) · `door` back (→ Car △) · `door` forward (boulder, **gated on solve** → Vault) |
| 8 | **Vault** (cliff top) | sunset, mist lifts | `grid-select` escape (3×3: shape columns × **trait** rows colour/size/shape) · artifact reveal on solve · `door` back (→ Boss) |

- **Three shaped boarding doors:** □ at S1, ○ at S2, △ at S3 — each is the platform's forward door into
  its car; the shape repeats on the car and on the escape grid's column headers.
- **Each car's shelf is sorted by a different visual TRAIT** — colour (beetles □) / size (cones ○) /
  shape (shells △). Keep the grouping unmistakable: **vary the *other* two traits within each tray**
  (a colour tray has big & small beetles → clearly colour, not size).
- **New engine work still needed:** the `grid-select` puzzle type (scene 8), the monorail **ride-beat**
  (single door opens after ~5 s), the **single-door bidirectional** shared-art down-nodes (back-nav),
  and the **spores** particle + **mist** fx (ambience below). None of these block art generation.

## Scenario WIRED + handoff (BUILT 2026-07-21, session Forest)

`scenario.json` written (via `_scratch/make_scenario.py`, re-runnable; validates). **8 stub nodes**
(`station1, car_sq, station2, car_ci, station3, car_tr, boss, vault`), each carrying `authoring.
scenePrompt` + `doorPrompt` (golden-daylight arc baked in), `plannedHotspots` (harness box checklist),
and a full `designNote` (puzzle spec + verified answers + draft prompts/clue/options). `id: 10`,
`chapter: wrangling`, `title: "The Collector's Vault"`. Dataset `forest_census` referenced at a
scenario-local URL (`…/escape_rooms/rooms/wrangling/trees/data/forest_census.csv`) — live once the site
is pushed from the Mac (alt: move to `sample_data/`).

**Ready for Lucas now:** run the authoring harness (`:8751`) to generate the 8 scene images
(+ cover) and draw hotspot boxes off `plannedHotspots`.

**Handoff TODO (not blocking art):**
- **Music:** Lucas has cheerful forest music picked — give the URL and I'll fire the `youtube_audio`
  observer row (clip + fade) and set `music`/`musicVolume`/`musicCredit`.
- **Ambience engine:** add the **spores** particle + **mist** fx (currently `ambient: "fireflies"` as a
  working stand-in); wire the **ride-beat** and the **grid-select** puzzle type.
- **Decoder:** on build (Phase 2), add `WRANGLING_TREES_KEY` (scenario_id 10, `correct = c(...)` for
  station1/station2/station3/boss) to `decoder/decode_codes.R` + its self-test; run
  `decoder/validate_keys.py`. Vary the correct index across the 4 rooms.
- **Inventory:** trees now claims id 10 — regenerate `authoring/scenario_inventory.py` (temple must
  take the next free id).
- **Phase-2 wiring:** fill real `hotspots` from each `designNote`; recompute distractor values; add the
  car **down-nodes** (shared art) for back-nav; write the boss clue + `feedback.correct` (names Sunspire).

## Open design questions

- ~~**The boss puzzle.**~~ RESOLVED 2026-07-21: the regroup / Simpson-flip boss (see the puzzle slate).
- ~~**Dataset tuning.**~~ RESOLVED 2026-07-21: engineered `data/forest_census.csv` built + all answers
  verified (see the puzzle slate). Still TODO before build: decide the exact **plot** each station asks
  for, and write the boss **clue** that flags the species-mix confound.
- **Grid ↔ car legibility.** The escape only works if the player reliably read each car's grouping. With
  no auto-log, back-nav is the safety net — keep the shelf grouping visually unambiguous and consider an
  oblique in-world legend. Playtest the recognition specifically.
- **Only three groupings, three lines — keep them distinct.** The three grouping variables must be
  visually *and* conceptually separable (species vs health vs zone) so a car's grouping is unmistakable.
  Avoid two variables that would produce similar-looking groupings.
- **Pre/post partner.** The `wrangling` chapter wants a **second** scenario asking the same
  group_by/summarise question style on a different dataset/story — trees is one of the pair.

## How it maps to established vocabulary

- **Two-objective structure** (`../../../notes/two_phase_escape_design_notes.md`): stations = graded
  analysis (real `group_by`/`summarise` in the console, codec-minted); the 3×3 grid = the ungraded,
  no-instructions escape.
- **Escape = unlabelled echo of the boss technique** (`puzzle_inventory.md` chapter principle): the
  stations group-and-summarise *with* labels and code; the grid asks the player to recognise *which
  grouping produced a summary* from imagery alone — transfer, not repetition.
- **Mechanic:** new **grid-select / matching** puzzle type to build (relatives: pattern-match lock #6,
  inference board #11, deduction ledger #9). Add it to `puzzle_inventory.md` when specced.
- **Aesthetic layer:** `ambient` mist/spores (a new particle? "spores" akin to fireflies), `fx` a soft
  drifting-mist overlay, per-room SFX = wind through canopy + creaking cable + distant alien birdcall;
  a mist-clears reveal as a scene beat. House teal-and-amber holds (dusk canopy + amber lichen-glow).

## ART BUILD — scene-spec pipeline (2026-08-05)

Trees is the **first scenario through the automated scene-spec art pipeline** (see
`notes/art_pipeline.md` for the pipeline itself). State: **all 8 rooms spec'd (`authoring.sceneSpec`) +
`scenePrompt`s rendered; a `worldPlate` prompt authored; art generation IN PROGRESS** (Lucas rendering rooms
via build-world step 2's level-1 pano stage on `:8752`). Trees-specific decisions this session:

- **World plate** — scenario-level `worldPlatePrompt` (top of `scenario.json`, also the `worldPlate` entry in
  the stage-1 spec bundle): a time-neutral "world bible" (canopy world, cars with the 3 door motifs, peaks,
  teal-amber palette). Generated first; referenced by every room. gpt-image-2 refs it high-fidelity (no
  loosen); Lucas tested and it "didn't pull station1 too hard", so keeping the single plate for now.
- **Strong dark→bright gradient.** `station1` + `car_sq` rebuilt to be the **deep, dark, enclosed bottom** —
  immense trunks vanishing into mist above AND below, a few god-rays, lichen/spore glow only, negatives ban
  mountains/open-sky/sun — to maximise contrast with the sunlit boss/vault. car_sq's two door-reveals carry
  the gradient (dark station1 back ↔ brightening station2 forward).
- **Seam + vehicle-door conventions applied to all 3 stations** (now canon in `SCENE_SPEC_GUIDE.md`): the wrap
  seam is continuous trunk/canopy backdrop with structural objects in the FRONT and cables running UP (not off
  the edge); and each station door **is the docked gondola's own sliding door**, not a separate boarding door
  with a car behind (stations 2/3 therefore show two gondolas — the line you rode + the line you board).
- **Cars** (`car_sq`/`car_ci`/`car_tr`): single multi-view switch door (`opensOnto` back/forward) + a
  drive-lever `switch` + the grouped-specimen cabinet carrying its **shape motif** (□ colour / ○ size /
  △ shape) — **NO written clue** (the clue-drop; the art carries the grouping). Vault gate is a `lock`
  (`grid-select`, new engine type still to build).
- **STILL DEFERRED to the WIRING pass** (`escape_room_wiring`, not blocking art): the world-state switch
  runtime (lever → state → door view/target + freeze/hum sfx), the `grid-select` puzzle type, the ride-beat,
  `WRANGLING_TREES_KEY` decoder lockstep + `test_trees.py`, ambience/sfx, and `design_notes.md` (step-0 record).

## WIRED — content + engine (2026-08-05, session "ideas")

The WIRING pass is essentially done; only the sound pass + the state-view door ART remain.

- **World-state SWITCH-DOOR mechanic BUILT (engine, reusable).** The deferred "lever → state → door
  view/target" is now a real engine feature, not a trees hack: a `door` carries
  `variants:[{state,when,to,direction?,panorama?}]` and a `dial` (the drive-lever) flips which is live, so one
  door routes back OR forward by state. Nav needs only `to`+`when` (the state-specific door ART can arrive
  later — the door shows its closed base until then and still routes correctly). `activeDoorVariant` in
  `shared/variant_resolve.js`; `doorNav`/`rerenderCurrentRoom` + the door-nav rewrite in `shared/pano-player.js`;
  schema in the hub AGENTS.md door bullet; unit tests in `tests/variant_resolve.test.mjs`. Cache tokens bumped
  (pano-player.js v=69 / test_play v=64). Each car dial also carries an `sfx` (lever-throw clunk) via a new
  openDial hook. **Door state-view ART is now TURNKEY** — the car doors' sceneSpecs already declare
  `opensOnto` (states `to_station1/2/3`, `to_boss` with reveal prompts), and the nav variants are aligned to
  those exact state names + a `when` gating on the lever, so the harness art MERGES onto the nav wiring. Two
  harness fixes made this compose (2026-08-05): `_add_variant` now MERGES (art fields overlay, nav
  to/direction/when survive — regression `test_add_variant_merges_onto_switch_door_nav`), and the door-view
  queue skips only states that already have a `panorama` (a nav-only state still generates). **Lucas's step:**
  in build-world, per car, **Place all hotspots** (queues the 2 door-open views) → **Generate all
  cinemagraphs** (runs them); each reveal paints into the door box and attaches as that state's `panorama`.
- **Puzzles = console `check` (not MCQ).** Only 4 categories on the vigour/zone axes → too few for a fair
  ≥6-option MCQ, and `check` is truer to a real `group_by`/`summarise` (proven through the codec by henges).
  Each assigns the winning group NAME to `answer`; graded by a case/space/underscore-normalised string compare.
  Re-verified vs `data/forest_census.csv` at wiring time: S1 girth→**Bloomspire**, S2 glow→**Radiant**,
  S3 shortcut→**Cragside**, boss regroup→**Sunspire Heights** — and the Simpson's **flip fires** (S3≠boss).
- **Cars = ungraded dial + switch-door junctions** (default lever = onward; throw it to go back). The vault
  `lock` became a **`phase:"escape"` 3×3 `grid`** (`endsEscape`), mapping □→colour / ○→size / △→shape.
- **Entry cards DROPPED** (Lucas 2026-08-05): every per-room `entry` deleted; only the opening scenario
  `story` survives, and the engine now logs it to the field notebook at start ("Your assignment") so it stays
  re-readable. This is a **general** simplification Lucas wants across scenarios, not trees-only.
- **Station clues = pure collector's-notes flavour** on the three hoards (beetles/cones/shells), one per
  station, naming no sorting trait and pointing nowhere — the player must notice the notes draw the eye; the
  car tray ART carries the actual grouping. Boss clue flags the species-mix confound *conceptually* (no method,
  no answer).
- **Decoder + tests GREEN.** `WRANGLING_TREES_KEY` (id 15, `correct=c(1,1,1,1)`) + a self-test added to
  `decoder/decode_codes.R` (Rscript self-test passes, trees grades 40); `validate_keys.py` extended to treat a
  dial-only junction room as intentionally ungraded (and passes trees); `test_trees.py` added (pins the four
  answers + the flip + switch-door graph + grid mapping + decoder lockstep — ALL PASS); trees added to the e2e
  smoke list. The wiring regenerator is `_scratch/wire_puzzles.py` (re-runnable) with `_scratch/scenario.prewire.json` as the pre-wire backup.
- **REMAINING (open threads, 2026-08-06):** sfx are wired + balanced and the station/car/boss door art is
  generated; what's left is (1) **regenerate the two black-hole car doors** — `car_ci`/`car_tr`, whose boxes
  were pulled off the seam and whose reveals were rewritten bright (`_scratch/fix_door_art.py`); regenerate
  them (Variants tab, per-tile Regenerate, on the restarted :8752 server) and eyeball; if still black, the car
  panoramas themselves need re-gen so the door sits off the seam; (2) a **browser playtest** of the full
  run + point/copy `tests/e2e/alaska_full.spec.js` to a `trees_full.spec.js` (trees is already in the e2e
  `smoke` list). Restart :8752 first so it carries this session's server changes (switch-door merge,
  cinemagraph pool, reloop, uncommit-fold).

---
authority: intent
---

# Escape-room puzzle inventory

A living catalogue of **puzzle mechanics** for the CHEM 5725 escape rooms — what each is, what
Myst/Riven idea it borrows, what data technique it can teach, and whether the engine supports it yet.
Grows as we design. Started 2026-07-18.

Companion docs: `puzzle_design_resources_notes.md` (the Myst/Riven design philosophy + references),
`two_phase_escape_design_notes.md` (the two-objective structure + the lock/per-gate engine work),
`puzzle_types_design_notes.md` (the graded ANALYSIS-side puzzle *types* — Compute-the-Key,
Classify-the-Unknown, Repair-the-Pipeline).

**Two families.** *Analysis-side* puzzles are graded and teach the technique directly (they live in
`puzzle_types_design_notes.md`). *Escape-side* mechanics (this file's focus) are the ungraded,
no-instructions Myst/Riven layer beyond the boss — but the best of them still *teach*, by making the
student apply what the analysis rooms taught.

## Chapter design principles (bake into every scenario)

- **Paired scenarios are a pre/post test — match the question STYLE across the pair (2026-07-18).**
  A book chapter maps to **two** scenarios built on **different datasets/stories** but asking the **same
  kind of question / exercising the same technique**, so Lucas can use one as a pre-test and the other
  as a post-test. Current pairings — chapter **`data_vis2`** (Data Visualization II): **`hospital`**
  ("Vital Signs", `alaska_lake_data`, Q1) ↔ **`airship`** ("The Alembic", `solvents`, Q3). Both must
  drill the Data-Vis-II *plot-craft* — **multi-variable aesthetic mappings**, `geom_tile`, regression /
  `geom_smooth` — **not** chapter-3-style single-column filtering. When designing either scenario's
  rooms, mirror the other's question types so the two stay comparable. (Hospital's `notes.md` already
  commits to this; keep them in step.) Chapter **`wrangling`** (Data Wrangling): **`trees`** ("The
  Collector's Vault", `forest_census`) ↔ **`egypt`** (Alexandria cargo, `wine_cargo`) — both drill
  `group_by`/`summarise` with a **Simpson's-paradox regroup boss**; mirror the question style across the
  pair. (Both drafted 2026-07, `rooms_built: 0`.)
- **The escape is a DATA-FREE meta-echo of the boss technique (transfer, not repetition) — UPDATED
  2026-07-22.** The default (Lucas, "unconnected to the data, as usual"): the escape re-poses the boss's
  *cognitive move* as a **meta version enacted in the world, decoupled from the scenario's dataset
  entirely** — no CSV, no console, none of the data's values/categories; the player performs the move on
  **in-world props**. This keeps the escape from feeling repetitive (it tests transfer/abstraction) and is
  pure Riven. Design it from the world + the technique's shape, **never from the data**. Canon in the
  skills (`escape_room_puzzles` step 4, `escape_room_story` beat 4). Exemplars: **trees** — the grid
  matches each monorail line to the collectible trait its car was sorted by (beetles/cones/shells,
  decoupled from the tree variables); **egypt** — collect image-cards, then group-and-summarise them by
  visual traits (a symbol-queue → 3×3 grid-select), untouched by the wine data.
  - **Earlier lighter variant (precedent, not the default):** `hospital` (unlabelled pH×Ca scatter +
    pick-a-point) and `airship` (sigil-dial + unlabelled mapping charts) used a *same-data, labels-stripped*
    echo — the boss problem with the labels removed. Kept as built precedent; new scenarios take the fully
    data-free form above unless one deliberately wants the lighter one.

## Scenario inventory & id collisions

Every scenario carries a unique codec **`id`** (a collision makes two scenarios' submission codes decode
into each other — this bit us with two id-8 scenarios on 2026-07-18). **Before creating a scenario, read
`rooms/scenario_inventory.json` and take its `next_free_id`.** Regenerate it with
`authoring/scenario_inventory.py` (stdlib; scans every `scenario.json` + the decoder's reserved ids,
flags duplicates). Keep chapter folder names consistent (`data_vis`, `data_vis2`, …).

## Mechanic catalogue

| # | Mechanic | Myst/Riven root | Teaches / data-technique hook | Engine status |
|---|----------|-----------------|-------------------------------|---------------|
| 1 | **Learned-cipher lock** — the code is written in the world's own notation; decode the notation (from a chart/clue) before you can read the answer | Riven D'ni numbers (base-25) learned from the schoolhouse game | Reading a dataset's *own* coding as a language (element symbols, park/aquifer codes, sample IDs); decode-then-apply | **Have** (lock + clue hotspots; author the "language") |
| 2 | **Scattered-fragment lock** — each digit lives in a different room; only someone who saw them all can assemble it | Myst Selenitic sound-maze; Riven "see the whole" | Meta-puzzle / synthesis across rooms; rewards observing every result | **Have** (per-gate solve + back-door nav) |
| 3 | **Sequence-in-order lock** — enter/press things in the right ORDER; the order itself is the puzzle | Riven 25 animal slabs / fire-marbles (which + when) | A data-derived *ranking* (lakes by temp, wells by chloride, solvents by polarity) | **Partial** — ordered *string* works in today's lock; click-in-sequence gate = to build |
| 4 | **Alignment / dial lock** — turn a mechanism to a value read elsewhere; locks when aligned | Riven rotating dome (stop it with the lens clue) | Match a control to a measured/derived value; continuous vs threshold reading | **To build** (rotational-dial UI) |
| 5 | **Set-the-mechanism lock** — configure a multi-part device to a value from a clue | Myst clock tower (set 2:40) | Combination from a synthesised clue | **Have** (combination lock) |
| 6 | **Pattern-match lock** — recognise a shape/cluster from a figure and reproduce its signature | Myst Stoneship constellations | Reading a scatter/PCA/cluster plot; identify the outlier/group | **Have** (clue-with-plot + lock) |
| 7 | **World-state dial** — a dial sets a persistent STATE; a *downstream* room behaves differently per state; you learn the mapping by experimenting and revisiting | Riven rotating dome + lever/valve state changes; Myst age-wide power routing (Channelwood) | Multi-condition filtering / faceting: the same data under different mappings reveals different subsets; the answer is the **intersection** across states | **Built (engine) 2026-07-18** — `dial` + `mapview` hotspot types in `pano-player.js`; wired in the `data_vis2/airship` scaffold |
| 8 | **State-conditioned rooms (`showWhen`)** — any hotspot/panorama appears or changes based on `gameState`; the world reacts to what you did (drain a tank → a hotspot appears; throw a breaker → a room powers on) | Myst/Riven core — rotating dome, draining fountains, Channelwood power routing | Cause→effect reasoning; a lever/filter in one place changes another | **Partial → generalise.** The airship dial→mapview (#7) is the **proto**; a general `showWhen` reading `gameState` is the deferred world-state gate. **Top build rec.** |
| 9 | **Deduction ledger** — assign a verdict to MANY entities in a grid; it locks a group in when that whole group is right (no per-cell reveal) | Return of the Obra Dinn (the book) | Classification / clustering — label every sample (poisonous/safe, which cluster, guilty/innocent) | **To build** (new puzzle type). Best fit for Classify / clustering chapters |
| 10 | **Sonification** — a data series played as tones; find the outlier by ear | Riven Selenitic sound-maze | Data has shape beyond a plot | **Partial** (per-room SFX exists); needs a visual fallback for accessibility — a "sometimes" mechanic |
| 11 | **Inference board** — draw connections between collected notebook clues to reach a conclusion | Outer Wilds rumour board | How analysts reason from scattered evidence; makes the meta-puzzle a *visible* act | **To build** (extends the field notebook) |
| 12 | **Assembled overview map** — a scenario map that fills in as you explore | Myst island map; Obduction | Navigation + the Riven "reward for seeing the whole" | **To build** (cosmetic / nav; pairs with back-nav) |
| 13 | **Idle interactables** — flavour-only clickable objects that reward curiosity | Myst everywhere (valves, portholes, music boxes) | — (immersion; trains the click-to-explore habit the real puzzles need) | **Have** (flavour `clue` hotspots) — near-free polish |
| 14 | **Knowledge-gated re-reading** — a clue that's illegible until you've learned something later; revisiting pays off | Outer Wilds / Riven (the world reveals itself as you understand it) | Transfer; rewards revisiting with new understanding | **Have** (back-nav + writing) — a writing move, not engine |
| 15 | **Grid-select (matrix selector)** — an N-col × M-row button grid; select one cell per column; the selection vector checks against a key → `solveRoom` (ungraded escape gate; sibling of `lock`/`ledger`, out of the codec) | Myst/Riven combination panels | Recognise/produce a **mapping**: which grouping made a display (trees), or which trait per queued verb (egypt). **Egypt active variant:** collect image-cards → **group-and-summarise** them by visual traits via a symbol-queue, entering results on the grid — a *data-free* active echo of `group_by \|> summarise` | **BUILT 2026-07-26** (`grid` hotspot in `shared/pano-player.js` — items×buckets matrix, one bucket per item, checks against `answer`; ungraded like `lock`; **logic-tested, browser-test pending**). **First consumer: `comparing_means/squirrel` roost** — 4 kinds × 3 height-tiers, the data-free height compact-letter display. Still specced for `trees` + `egypt`. |
| 16 | **Bell-pull / summoning cord** — pull a cord or rope on a wall and a bell rings in a **distant** room, tripping an effect there (a door opens, a hotspot appears, a mechanism advances). A tactile remote trigger: work out **which cord rings which bell / opens which door** and the ordering, and that mapping is the puzzle. Themed on the Victorian servant-bell (pull-cord → bell in the servants' hall) | Myst Channelwood lever/power routing; the physical remote-trigger | Cause→effect across rooms; **same world-state family as #7/#8** — a control here writes `gameState`, a distant room reads it. Could physicalise any "set a switch, a far room reacts" lesson (conditional filtering, faceting) | **To build** — sibling of #8 `showWhen`: a `pull`/lever control writing `gameState` + a distant `showWhen`-gated door/hotspot. Reuses the deferred world-state gate evaluator; near-free once #8 lands. **First consumer: `comparing_means/spa` escape (cords set the 5 hot-spring candles), 2026-07-24** |
| 17 | **Projection gallery / walk-the-PCs** — the same set of objects is displayed in several rooms, each room a **different projection/rotation** of the identical points (told apart by a per-room visual tag — stone colour, moss). The puzzle is to **find the projection of maximum spread** (= PC1), or **order the projections by spread** (= a walkable scree plot), or find the projection where a sub-group stands apart. Spatialises PCA: walking through a doorway rotates your view onto another principal component | Myst/Riven "see the same space from a new vantage"; the rotating-dome reveal (#4/#7 kin) | **PCA / dimensionality reduction** — max-variance axis (PC1), scree/variance-explained ordering, and "which axis separates this group". The scenario's signature spatial layer | **To build** (scenario `dimensionality_reduction/henges`, PUZZLE phase done 2026-07-23; ladder + engineered `druid_ingredients` dataset verified in its `notes.md`). Design/engine work is `escape_room_design`'s job; the graded rooms still run real PCA in WebR |
| 18 | **Elevation-transition beat (learn-the-heights-by-travelling)** — a short interstitial screen shown **before each between-room jump** that makes the jump's direction unmistakable — **up / down / same level**. Across the scenario these beats cumulatively teach the player the **relative heights of the populations they're visiting** (each population sampled ~3× as they move), so that by the finale they can group the populations by height **from memory, by eye** — with no dataset. The signature travel layer that *is* the escape's data source | Myst/Riven vertical traversal (Channelwood ladders, Mechanical Age lifts) where elevation is felt, not told | **Comparing means, done data-free** — repeated sampling of distinct populations builds a felt sense of each group's central tendency + spread; the escape is a by-eye ANOVA/compact-letter grouping. A travel beat that doubles as the recognition-escape's teacher | **To build** — an interstitial `entry`-card variant carrying an up/down/level glyph + cumulative height cue; feeds a **#15 grid-select** escape (colours × letters). **First consumer: `comparing_means/squirrel` (heights → CLD escape), 2026-07-25** |
| 19 | **Cut-the-tree floodgate panel + draggable elevation-map** — a data-free escape for hierarchical clustering: roaming logs each confluence's elevation onto a **draggable-node inventory map** (drag each node along a scaled elevation axis = plotting the dendrogram by hand); a **calibration-matrix panel** (rows = flood-gate cut heights, columns = clusters, cells = tributaries-per-cluster) is completed one bracketed row at a time — reading the map at a cut height and counting = a **dendrogram cut + per-cluster count summary**, done on the world, not the CSV | Myst Channelwood water routing / the engineer's control panel | **Hierarchical clustering, data-free** — read a dendrogram cut and summarise each cluster; pairs with the #18-style travel that teaches the node elevations | **To build** — draggable-node map UI + matrix-cut panel + a "next-in-queue" puzzle dispenser at any puzzle node (open-world progression, replaces per-node `availableWhen`). First consumer: `hierarchical_clustering/canyon` ("The Confluence"), 2026-07-25 |

**Candidate borrowings (brainstormed 2026-07-18) — rows 8–14 are ideas, not yet built.** Top build
rec: **#8 `showWhen`** — the airship's dial→mapview (#7) is *already* the proto (a control in one room
changing a distant display), so generalising it into a `gameState`-reading `showWhen` on any
hotspot/panorama is the natural next primitive and unlocks the whole Myst "world reacts to you" class.
Strongest new puzzle **types**: **#9 deduction ledger** (Classify/clustering chapters) and **#11
inference board** (makes the meta-puzzle visible) — **full build-ready specs** (worked example,
confirmation rule, JSON schema, engine work) in `ledger_and_inference_board_specs.md`. **#13 idle
interactables** is a near-free polish pass for any scenario.

Built engine pieces these draw on (see `two_phase_escape_design_notes.md`): the `lock` hotspot
(no-instructions keypad, fixed derivable code, not in the codec); the **per-gate solve model**
(`door.requires`, room-namespaced gate keys); two-door back-nav (revisit any room).

## #7 — the world-state dial (design target, 2026-07-18)

**Lucas's idea:** a dial with several states; turning it one way makes a *future* room do one thing,
another state makes that room do something else — and *discovering that mapping by experiment* is the
puzzle. Connect it to learning a data technique.

**Why it fits the `solvents` / Data-Vis-II scenario.** That exercise's whole skill is selecting a
solvent that satisfies **three conditions at once** — immiscible with water, relative polarity ≈ 0.6,
density < water — i.e. filter the reference table by one property at a time and take the **intersection**.
A dial makes that physical:

- The dial has three states — **density · polarity · miscibility** (the three columns of `solvents`).
- A downstream room (a rack of labelled solvent bottles, or a wall plot) **re-renders per state**: set
  it to *density* and only the light (< water) bottles glow; set it to *polarity* and only those near
  0.6 glow; set it to *miscibility* and only the water-immiscible ones glow.
- The escape opens for the **one bottle that glows under all three states** — the intersection. To find
  it you must cycle the dial, revisit the room each time (back-nav), and mentally AND the three subsets.
- That IS the Data-Vis-II lesson (map multiple variables / facet by condition / read a coloured scatter)
  turned into a manipulable object — and it's pure Myst: no instructions, you learn what each dial state
  means by seeing its effect.

**Engine work it needs (new — extends the deferred world-state gate evaluator):**
1. A **`dial` control hotspot** — N labelled states; selecting one writes a `gameState` variable
   (e.g. `gameState.filter = "density"`). Reuses the existing `onSolve` `set` effect + the `gameState`
   bag; no codec involvement.
2. **Conditional room content** — hotspots (and optionally the panorama) shown only when a `gameState`
   condition holds, via a `showWhen` field evaluated like `unlockedWhen` (this is the deferred
   counter/state-gate evaluator, now with a concrete use). So the "glowing bottles" are clue/lock
   hotspots gated on the dial state.
3. **Re-render on state change / revisit** — changing the dial (or re-entering the room) re-evaluates
   `showWhen`. Back-nav already lets the player return to see each state's effect.
4. Optional: a **per-state panorama** so the room visibly changes, not just its hotspots.

**Open questions:** does the dial live in the room it affects, or an earlier room (spookier, more
Riven)? Is the final gate a lock (type the intersection solvent) or does the correct bottle's hotspot
become clickable only when all three states have been "witnessed"? How much to signpost that three
states must each be tried (fairness vs. discovery)?

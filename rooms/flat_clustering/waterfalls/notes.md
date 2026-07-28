---
authority: intent
---

# Waterfalls — flat-clustering escape room (design notes)

Scenario slot: **chapter `flat_clustering`, scenario `waterfalls`** (new chapter folder;
this is the first flat-clustering room). Status: **design / prototyping** — puzzle ladder,
dataset, story, scenario.json all still TO DO. This file is the running record of the
design conversation; it is the authoritative log until the scenario.json exists.

## Premise / theme (working)

Treasure-hunter descent into a lost culture's **sorting temple** — a circular, open-topped
shaft-cistern whose ancient waterworks channelled sacred offerings (gems / ore / pigment /
votive tokens) into `k` sacred pools **by kind**. The mechanism is jammed and the shaft is
flooded; the explorer must re-run the sort correctly to descend and leave with the prize.
Tie to the technique is literal: **flat clustering = sorting things into k groups**, and the
temple's whole purpose is that sort. Indiana-Jones *vibe*, not pastiche. Avoid the
geochemistry/water-chem/ecology framing used elsewhere.

## Two independent puzzle systems (keep them decoupled in the student's head)

1. **Data puzzles (graded, WebR).** The tangible flat-clustering analysis on a real,
   reskinned dataset (tequila-style chemistry → dressed as artefact/mineral/pigment assays,
   with understandable labels + categories). TO DO — not yet designed. In-world, solving a
   ledge's analysis is what **unlocks that ledge's diverter**.
2. **The escape (ungraded, client-side).** The dynamic descent maze below. Data-free,
   outside the decoder/codec (harness treats `phase:"escape"` rooms + `lock/grid/dial`
   hotspots as non-graded). See the escape-room skill canon.

## The escape mechanic — DYNAMIC DESCENT MAZE (locked direction)

- **One descent = the entire scenario.** Not a finale bolted onto a normal room sequence;
  the whole scenario is a series of 360 viewpoints down a catwalk/ladder/bridge descent.
- Circular shaft. Player **starts at the TOP** on a catwalk and descends level by level via
  ladders + rope bridges to the basins at the bottom.
- Water pours in from the rim as **streams**; a **diverter** (a binary lever, throwable only
  while standing on its lever ledge — i.e. after you've reached/earned it) steers a stream
  left/right. A ledge a stream currently pours onto is **flooded** → impassable.
- **Escape = reach a bottom ledge with every stream resting in its correct basin** — i.e. the
  final diverter configuration that produces the correct k-means-style **assignment** (each
  item/stream → its correct one of k basins). The 2-D nature (both floor axes matter) is the
  flat-vs-hierarchical lesson, made physical; boundary "trap" streams need both axes.
- **The good part:** the diverter setting that clears the bridge you need *now* is often not
  the setting the final sort needs, so you throw a lever, cross, then come back and throw it
  **back** — a genuine self-reconfiguring backtracker. The generator rejects instances that
  are statically solvable (can't just set the answer and stroll down).

### Difficulty decision (locked)
Go for the **harder** maze (≈14-action, with a re-toggle) but **give better tools** to carry
the load — a full-information planning **viewport**, so the challenge is route-planning, not
blind memory. Full info from the start (a "fills in as you go" reveal is a future dial).

### The viewport (planning instrument)
Deterministic, **not 3-D**: a **concentric-ring top-down map** of the shaft.
- rings = levels (outermost = top catwalk, inner = basins);
- angular position around a ring = column;
- **gray lattice = the walkway/bridge skeleton** (where you *could* step: to the ledge below
  or one column either side) — drawn independent of water;
- **blue-filled node = flooded ledge** (a stream is on it → can't stand);
- **coloured spiral = a stream's current route** (offset per stream so co-located paths stay
  distinct); numbered at its basin end;
- **triangles = diverter levers** (green = should end ON for the sort, red = should end OFF);
  **gold star = start**.
Harness realisation = a `mapview` image swapped by dial state → **pre-render one PNG per
switch combination** (D diverters → 2^D images) with the engine.

## Engine (`cave_engine/`)

- `generate_cave.py` — **Option-A static layout** (the assignment/watershed instance: k
  basins on a 2-D floor, N streams, tunable boundary "traps", unique-by-margin). Emits the
  `grid` answer `{stream: basin}` + an ASCII floor map. Kept as the assignment core.
- `cave_descent.py` — **the dynamic descent maze (v4, clean-lever rebuild 2026-07-26)**.
  Implements the two agreed rules: **one diverter per stream** (independent, reversible
  levers) and **one fused goal** (win = every stream in its basin; visible on the map, no
  separate "reach the bottom" condition). Meandering streams (baseline col per level → no
  free chute), full ladders + sparse bridges. **FOUR levers** (= 4 data puzzles), each at a
  different depth, all starting WRONG so all must be thrown → no dead levers; the solver
  requires **exactly four throws, one per lever, in a forced order** (rejects re-throws), so
  it's a clean order-and-navigation puzzle. Reports **k** (distinct basins) for the guess-k
  lock. BFS-solves; renders BOTH diagram styles per water-state.
  - run: `python3 cave_descent.py --seed 23 --png`
  - knobs: `--cols --levels --streams --k --pbridge --seed`
  - stdlib for logic; matplotlib only for PNGs.
- Reference instance: **seed 23** (C5×L4, 4 levers, k=3) → 19 actions, forced order
  g0→g3→g1→g2, 15 navigation moves; g2's lever platform is flooded until g1 reroutes its
  stream (a real dependency). Default C=5×L=4, streams=4, k=3.

### v3 review findings — fixed in v4 (2026-07-26)
- Multiple levers steered one stream → unpredictable/irreversible + dead levers (g4 unused,
  g0 gated nothing). Fixed by **one lever per stream** + **all levers must be thrown**.
- "Reach the bottom" and "sort correct" were decoupled → looked solved when it wasn't. Fixed
  by the **single visible goal** (all streams home).

### v2 review findings — all fixed in v3 (2026-07-26)
1. **Diagram lied about connectivity** — it drew diagonal bridges the movement model never
   allowed, so it looked over-connected / straight-to-the-bottom. Fixed: diagrams draw only
   the real edges (ladders + sparse bridges).
2. **Descent wasn't gated** — v2 streams sat in one column at every level, so a clear chute
   always existed at the start. Fixed by meandering baselines + a "bottom unreachable at
   start" acceptance test.
3. **Dead levers** — clamping + cancellation produced throws with no visible effect. Fixed by
   the feedback-clean rule (reject any solution with an invisible throw).

### Diagram style — DECISION PENDING
Both rendered for comparison. **Grid (side-on) is the clear winner for a planning tool**;
rings are prettier as "looking down the shaft" but harder to trace. Likely: grid as the
in-game planning viewport, rings as cover/flavour art. Awaiting Lucas's call.

## Harness realisation — OPEN QUESTIONS / next steps

- **State-gated bridges need a spike.** Player engine (`shared/pano-player.js`) gained an
  **open-world maze** mechanic + world-state-counter gates (`{gte:[...]}`) and `dial`+
  `mapview` on 2026-07-26, which covers diverters + the state-conditioned viewport. But
  doors currently open on *solved gates / counter thresholds*, not "dial == X" — so
  "bridge passable iff switch in position X" likely needs a **small gate-evaluator
  extension**. PROVE with a throwaway test before committing the scenario. (Possibly the
  same maze work is coming from another session — worth reconciling.)
- **Widen the shaft for the real build** — 3 columns renders cramped; 4–5 cols + maybe one
  more level reads more like a map. Difficulty tunes independently of size.
- **Design the tangible dataset + flat-clustering puzzle ladder** (reskinned, treasure-hunter
  labels) — the normal `escape_room_puzzles` phase, still to do.
- Then story → design → (art) → wiring, per the escape-room skill pipeline.

## Decisions locked so far
- Topic = flat clustering (fills a real gap; k-means assignment ↔ watershed basins).
- Mechanic = dynamic descent maze; one descent = whole scenario.
- Hard maze + full-information planning viewport (concentric rings).
- Theme = treasure-hunter sorting-temple.
- Data puzzles unlock diverters (the two systems meet at the levers, but the escape stays
  ungraded/data-free).
- **Four levers = four puzzles** (3 + boss); solve a puzzle → unlock its lever. One lever per
  stream; each thrown once in a forced order.
- Win = every stream in its correct basin (visible); no separate reach-the-bottom gate.
- **Guess-k lock** at the very bottom: recognising the whole thing as k-means and entering k
  is the final recognition beat (single digit for now — obfuscate later).

### PIVOT 2026-07-26 — author by hand, not auto-generate
Auto-generation hit a wall: with the platform-flooding model, a solvable AND shortcut-free
instance is ~1 in 20,000 random shafts (the bottleneck is *solvability* — random lever
placement deadlocks, only ~20 in 7,000 shafts let you throw all four levers). Constructive
generation was the proposed fix, but Lucas has worked the puzzle out on paper instead, with a
**revised model**: **rivers cut the BRIDGES (edges), not the platforms** — platforms are always
standable; a bridge a river crosses is impassable. Grid is **3 cols × 4 rows**.

- **`puzzle_editor.html`** (scenario root) — a self-contained visual editor so Lucas can lay
  out his paper design: a platform grid, tap a bridge to mark a river cutting it, drop
  switches/diverters, define **multiple states** (each = one switch configuration + its
  river/bridge picture + optional traced river polylines + notes), then export JSON to hand
  back. JS syntax-checked; no external deps; touch-friendly. Exported JSON schema:
  `{grid:{rows,cols}, absentBridges:[...], markers:[{id,kind,x,y,label}],
  states:[{name,switches,cutBridges,rivers,notes}]}` (bridge ids `H-r-c` horizontal, `V-r-c`
  vertical). An edge has three states: **absent** (`absentBridges`, structural/global — no
  bridge, platforms unconnected), **present-open**, **present-cut** (`cutBridges`, per state,
  a river across it). Passable ⟺ present AND not cut.
- The `cave_descent.py` auto-generator is **paused** (kept for reference); the exhaustive
  no-shortcut verifier it contains (`reach_states`) is still the right tool to *validate*
  whatever Lucas authors, once his design is in.

**Lucas authored `puzzle.json` (2026-07-26) — VERIFIED SOUND.** 4×3 grid, 5 states, 4 switches
(S1@1,0 → S2@2,0 → S3@1,1 → S4@1,2 boss), 4 diverters. Sequence: each switch's diverter opens
the way to the next; S3 seals the way back (forward-committed to the boss); after the boss,
**re-throwing S3** (a deliberate backtracker) uncovers the 2,0→3,0 bridge and opens the descent
to the EXIT at (3,0). `cave_engine/read_authored.py` parses it, plays it back per state, and
**confirmed the no-shortcut property**: the bottom row is unreachable in states 1–4, reachable
only in state 5. Note for WIRING: state 5's bridge config depends on **S4 AND S3 together**
(the boss causes "no visible change" alone) — a bridge's cut-state is a function of the whole
switch vector, not one switch each. Housekeeping: marker ids/labels drifted from erase/redraw
(ids S1,S2,S4,S5 = labels S1–S4); per-state switch on/off flags left false (states defined by
`cutBridges`, which is authoritative).

**`player_map.html`** (scenario root) — the LIVE player-facing map. Shows ONLY the current
world (no 5-state stepper — that would give the puzzle away). Live game state is built in:
tracks the 4 diverter positions, drawn as glyphs — `|` neutral, `/` or `\` diverted, current
solid + **alternate greyed** (D1 starts `/`→`|`, D2 `|`→`\`, D3 `|`→`/`, D4 `/`→`|`; switch Si
flips Di). Tap a reachable platform to move; a **Throw Sx** button appears when you're on a
switch and flips its diverter; the map recomputes cut bridges + rivers + reachability.
Loads `puzzle.json` via fetch with file-picker fallback.

**ROUTER WIRED INTO THE LIVE MAP (2026-07-26).** `player_map.html` no longer uses the 5-state
lookup — it ports `router.py` into JS (`route()`), computing cut bridges + river polylines live
from the diverter positions for ANY combination. Validated: the JS port reproduces all 5
authored states exactly (after state 1 got its `V-2-0`). Throw switches in any order and the map
shows the true picture, live rivers, and reachability. (Third stream still a decorative one
pending Lucas's chosen source lane.)

**KEY MODEL FINDING (2026-07-26): the bridge picture depends on the diverter COMBINATION, not
each diverter independently.** Verified: bridge `H-2-0` is cut when D1 & D2 are both neutral
(state 2) but NOT when D2 flips (state 3) even though D1 is unchanged — so a river's path is a
function of several diverters together. Consequence: the map is driven by a
combination→picture lookup (`CONFIG2STATE`) seeded from Lucas's 5 authored states (the intended
path). It faithfully renders every configuration on that path, but a config Lucas hasn't
authored has no picture (the map flags it). To make it bulletproof, EITHER (a) capture what
each diverter does to the rivers so any combination is *routed/computed* (also makes authoring
one-per-diverter instead of enumerating states), OR (b) gate switches so only intended combos
are reachable. **Open decision — awaiting Lucas.**

### River ROUTER (option a) — built + validated 2026-07-26
`cave_engine/router.py` implements the flow model and computes cut bridges for ANY diverter
combination:
- 3 streams fall from top sources in **lanes = gaps between columns**; a stream running
  straight down cuts the **horizontal** bridge in its gap; diverted sideways it cuts the
  **vertical** ladders it crosses (perpendicular either way).
- Diverter shift by position: `/`=left 1, `|`=none, `\`=right 1; **D4 = 2 columns** (2-storey
  drop). Streams fall through diverters in **height order** (D2 sits a hair above D3 — that
  ordering is load-bearing; it's why state 4 funnels everything left).
- **Validated: reproduces 4 of Lucas's 5 authored states exactly from first principles.** The
  lone miss is **state 1 missing `V-2-0`** — the router (and state 2) say a 2-column D4
  diversion cuts BOTH ladders it crosses; state 1 only has one. Near-certain erase/redraw slip
  → **state 1 should add `V-2-0`.**
- Mechanically the cuts come from streams in the two gaps (gap0 = col0|1, gap1 = col1|2); the
  search's third source lane is inert, so the "3rd stream" is a visual/redundant one (confirm
  its intended source with Lucas).
- **ART BUDGET:** the 16 diverter combinations collapse to **8 distinct map pictures** (many
  switch flips are invisible — no stream reaches that diverter in that combo). The reachable-
  in-play subset is likely fewer; needs a play-reachability pass over the 16 combos.
- **Next:** wire this router into `player_map.html` (replace the 5-state lookup → compute any
  config = the bulletproof option-a map); optionally fold sources+routing into the editor so
  authoring is "place sources, set diverters" and states derive automatically.

### PUZZLE PHASE — verified ladder + dataset (2026-07-26)

**Analog grounding.** Flat clustering / k-means = sorting a mixed heap of specimens into "these
belong together" piles by their measured traits — a curator laying out a reliquary of phials and
grouping them by kind. The recognition move (for the escape, built later, data-free): seeing the
heap has settled into k natural groups and reading how many / how big.

**Chapter technique sequence** (`9_flat_clustering.Rmd`): k-means (choose k via the elbow) →
summarise-by-cluster (dbscan is also in the chapter but skipped here). Ladder tracks that order.

**Dataset — `reliquary_phials` (ENGINEERED, verified).** 24 phials × `clarity, mineral, resin,
ash` (4 profile measures, comparable ~0-100 → three true families sized **6/8/10**) + `weight`
(grains, ~500-9000; huge-variance, family-INDEPENDENT = the scaling trap). Raw candidates
(`chemical_blooms`, `tequila_chemistry`) don't give a clean scaling flip, so it was engineered
(cf. `trees`). Deterministic build: `_scratch/build_phials.py` (Python/sklearn); verified in the
STUDENT's tool, base R `kmeans()`, seed-robust: `_scratch/verify_phials.R`. CSV:
`data/reliquary_phials.csv`. **Public URL:**
`https://thebustalab.github.io/escape_rooms/rooms/flat_clustering/waterfalls/data/reliquary_phials.csv`.

**Verified ladder (strictly monotonic; trap = scaling at the boss):**
- **S1 — run k-means, read a family.** `kmeans(phials[,c("clarity","mineral","resin","ash")],
  centers=3, nstart=25); table($cluster)`. Q: how many phials in the **largest** family? →
  **10** (families 10/8/6; ARI 1.0). Distractors: 8, 6, 12, 9, 3, 24.
- **S2 — choose k (elbow). [TYPE 4 pick-the-point — "click the elbow".]** Plot WSS vs k
  (`ggiraph::geom_point_interactive`); the student CLICKS the elbow → **k=3** (WSS
  37689→11667→**966**→810→661→543; the drop collapses after 3). Pick-the-point (not MCQ) also
  sidesteps the fact that k∈1..6 gives only 5 possible wrong MCQ options.
- **S3 — summarise by cluster. [TYPE 3 console-check.]** Student writes the pipeline (cluster,
  then mean resin per family) and assigns `answer` = the SIZE of the highest-mean-resin family;
  check `answer == 6` (mean resin 68.1 vs 28.3 vs 21.8; the size-6 family wins by 39.7).
- **BOSS — the scaling trap.** Cluster on **all five** measures. `kmeans(scale(phials[,2:6]),3)`
  (correct) vs `kmeans(phials[,2:6],3)` (naive — weight drowns everything, ARI 0.07). Q: which
  phial shares **Jasper**'s family? → **Selenite** (scaled; Jasper's true family A =
  Amber/Cinnabar/Onyx/Selenite/Verdigris; seed-robust). **DECOY = Antimony** (Jasper's unscaled
  weight-band mate — what you get without scaling). Filler distractors: Bloodstone, Galena,
  Chrysolite, Ochre (B/C). **Do NOT offer Onyx** (in family A *and* Jasper's weight band —
  ambiguous). CLUE: weight is in grains (thousands) vs tens for the rest → scale first.
  Deliverable = the scaled cluster plot (figure + submitCodec).

**Boss cognitive move (seed for the STORY-phase escape):** assign each sample to its true family
once the measures are on equal footing, and watch the many resolve into k groups. The basin
escape re-poses this data-free (recognise k pools, read their sizes) — and stays INDEPENDENT of
this dataset (basin 3/2/4 need NOT match the data's 6/8/10).

**Judgement calls:** (1) engineered dataset — documented; (2) escape kept data-free/independent
per Lucas; (3) **puzzle-type variety in place** — S1 MCQ (Type 1), S2 pick-the-point (Type 4,
click-the-elbow), S3 console-check (Type 3), boss MCQ + figure deliverable (Type 2); all four
types are engine-built; (4) scenario id 10 must be added to `decoder/decode_codes.R` when wired.

## Narrative (STORY phase, 2026-07-26)

**Logline.** You breach the failing, flooding vault-engine of *the Assay* — a ruthless order of
alchemists who reduced the world to "base" and "worthy" — to reclaim the **Wellheart**, a living
stone they tore from a valley of ordinary folk (whose springs ran bitter without it), and carry it
home; the engine opens only to one who can sort as they did, and the flood is rising.

**Framing guardrail (Lucas, load-bearing).** NOT a relic-hunter looting an indigenous temple/tomb.
The **builders are the villains** (the Assay); the setting is **fantastical alchemy** (invented
order, distilled essences), deliberately removed from any real culture; the protagonist reclaims a
dead villain-order's ill-gotten hoard, not a living people's heritage. Keep this framing in all copy.

**World (from the analog: sorting a mixed heap into "these belong together").** The Assay believed
all things could be *assayed* — reduced to their true kinds and sorted. Their engine is a great
drowned waterworks that parts distilled essences into sacred pools; behind it they sealed everything
they judged worthy. The technique has a dark edge in their hands (sorting to decide worth) — the
player turns the same skill against them. Cast: **zero living characters** (the Assay speak only
through carved fonts, inscriptions, a taunting warning-stone); the goal is front-loaded in the
opening. **Landmark = the drowned floor / the vault**, where the escape is sited (earned by the
descent). **Signature travel = the diverter-maze descent** (the built router/viewing-port mechanic).
**Environmental arc = DEPTH** (spatial, backtrack-safe); the flood is ambient rising tension (the
**clock**), not baked per-room.

**ROOM TOPOLOGY — NOT a linear chain (fixed 2026-07-26; scene prompts now match `puzzle.json`).**
Derived from the map: `catwalk`(row0) → down → `station1`(row1, a **3-way JUNCTION**); from station1,
**down** → `station2`(row2) and **across** → `station3`(row1). `station3` → **across** → `boss`(row1,
a dead-end, ONLY reachable/exitable via station3). `station2` → **down** → `basin`(row3, the bottom).
So **station1/station3/boss are all the SAME level** (row 1, a horizontal gallery — station3 and boss
are *across*, NOT "deeper"); the **basin is reached by dropping through station2's column, NOT from the
boss**; the deepest room is the basin (the escape), which is correct. **Gate model:** inter-room
passages are **OPEN rope bridges/ladders veiled by waterfalls** — the *water* is the gate (a diverter
clears it), NOT closed stone doors; the ONE closed door is the basin's **vault**. (Earlier scene
prompts wrongly encoded a straight vertical chain with closed doors — corrected.)

**Per-room beats** (why the analysis is needed *now*, what it unlocks):
- **catwalk** — orientation. Stand on the rim; the viewing port shows the whole engine and the rising
  water. Goal front-loaded: the hoard is at the bottom, the engine opens only to a sorter, go down
  before it drowns.
- **station1** (largest family=10) — the engine's first font: prove you can read a tray of phials
  (count the largest kind). Answer releases D1 → throw it, drop lower.
- **station2** (elbow k=3) — a subtler font: not how big a kind is, but *how many kinds there are*.
  Read the elbow → releases D2.
- **station3** (console-check, family-of-6) — the measuring font: sort *and weigh* — read a property
  off each kind. Releases D3. (Backtracker: throwing S3 seals the way back; you return after the boss.)
- **boss** (scaling trap) — the engine-hall, the Assay's final safeguard. It hands you every measure
  incl. the phials' weight (in grains, thousands). **Misdirection:** the obvious reading (cluster
  as-is) is the snare — weight drowns the truth and mis-sorts Jasper (→ Antimony). The warning-stone
  taunts the confound; scale, and Jasper falls with his true kin (Selenite). Releases D4.
- **basin** — ESCAPE (data-free recognition). The Assay's completed sort lies revealed: the essences
  gathered into their pools. Read the sort as its makers would — how many pools, how each fills — and
  set that reckoning into the vault. It opens; take the hoard, climb the rising passage to daylight.
  (Provisional code from the ART's pools, currently 3-2-4; independent of the dataset.)

**Escape payoff.** The boss's cognitive move (assign to true kinds once measures are on equal
footing; see the many resolve into k groups) re-posed data-free on in-world props (the pools) — pure
recognition, the thematic climax, the Assay's own sort turned into the key that robs them.

**Voice.** Earnest, concrete, sensory; ominous-grand mood (a drowned alchemical engine, amber-on-teal,
rising water); the Assay's inscriptions cold and gloating. Cards kept short.

**Story-map text** is written into `scenario.json`: `story`, `enterLabel`, per-room `entry` cards,
`done`, `escapeDone`, `debrief.intro`. Title **"Where the Waters Divide."**

**Judgement calls / settled:** (1) villain-alchemist framing per Lucas (guardrail above); (2) order
named **"the Assay"**; the relic is the **Wellheart**, stolen from the vale-folk and being
**returned** (Lucas 2026-07-26 — a righteous return motive, not looting); (3) no living cast (the
Assay speak via inscriptions); (4) escape counts (3-2-4) pinned to the basin ART, not the data;
(5) basin finale is deliberately GRAND + knee-deep-flooded to sell the rising-water clock.

### scenario.json DRAFTED 2026-07-26 (design phase, narrative + art prompts)
`scenario.json` filled out as far as it can go without the puzzles. **Title "Where the Waters
Divide", id 10** (free; must be added to `decoder/decode_codes.R` when graded puzzles are wired).
Theme = the treasure-hunter **Sorting Engine** temple; six rooms down one shaft:

| room | key | role | diverter |
|---|---|---|---|
| catwalk | `catwalk` | orientation, holds the **viewing port** (= the live player_map) | — |
| stations 1–3 | `station1/2/3` | flat-clustering puzzle (TBD) → unlock a diverter | D1 / D2 / D3 |
| boss | `boss` | boss puzzle (TBD) → final diverter | D4 |
| basin | `basin` | **escape** — the k-means recognition finale | — |
| spillway | `spillway` | **flavour side room** (2,1), off station2 — the Assay's cast-off gallery (discard stream); one `clue` | — |
| sump | `sump` | **flavour dead-end** (3,1), below spillway — drowned discard sump, ruined vale-folk marker; one `clue` | — |

(Added 2026-07-28 — open-decision #1. Scenario is now **8 rooms = all 8 reachable platforms**, 1:1.)

- **Environmental arc = DEPTH only** (spatial, backtrack-safe — the S3 re-throw means the player
  doubles back, so no time-of-day arc). Dusk sky at the top → amber temple-light + teal water
  deep down.
- **Diverter levers = `dial` hotspots; the viewing port = a `mapview`.** Puzzle consoles are
  `puzzle` hotspots. The maze movement itself is the router/engine (already built).
- **Basin finale (the PRIORITY art):** k pools each fed by a *cluster* of falling threads =
  k-means made physical; the escape act is reading the **cluster sizes** into a keypad lock.
  PROVISIONAL code `324` (basins fed by 3,2,4). Data-free, ungraded, `endsEscape`.
- **All rooms `built:false`** (stubs with `authoring.scenePrompt`+`doorPrompt` + `designNote` +
  `plannedHotspots`). Every room needs NEW ART; the basin is the one Lucas wants first.
- **TODO before build:** the whole `escape_room_puzzles` phase — pick the dataset + k-means
  ladder + verified answers; THEN set the basin's true pool/feed counts + lock code, and give the
  threads the samples' colours so the finale reads as "my clustering". Then `escape_room_story`
  polish, then wiring.

### OPEN DECISIONS (awaiting Lucas, as of handoff 2026-07-26)
1. ~~**Rooms `(2,1)` & `(3,1)` are reachable but roomless**~~ **RESOLVED 2026-07-28 (Lucas): ADD both
   as visitable dead-end rooms.** Built as FLAVOUR side rooms (no graded puzzle, no diverter) — the
   Assay's **discard/waste stream**, reinforcing the villain framing: `spillway` at (2,1) = the cast-off
   gallery where the Assay sluiced away everything they judged "base" (across from station2); `sump` at
   (3,1) = the drowned dead-end below it, a grim mirror of the sacred basins, holding a ruined vale-folk
   marker. Each has one `clue` lore hotspot, no interactive machinery. **Latent map fix caught in the
   same pass:** the map gives station2 an ACROSS bridge to (2,1) (`H-2-0`) that station2's prompt/hotspots
   didn't depict — now added (station2 is a 3-way: up / across-to-spillway / down). Topology: station2
   —ACROSS→ spillway —DOWN(`V-2-1`)→ sump (dead-end; `H-3-0` absent, so walled off from the basin).
   `H-2-1` leads only to the unreachable/roomless (2,2), depicted as a **collapsed bridge** (no phantom
   passage). Scenario now **8 rooms = all 8 reachable platforms** (1:1; no roomless spot, no dead art).
2. **Harness pano-swap capability** — does :8751 swap a whole panorama by world-state, or must the
   state variants ship as `mapview`-style state-indexed images? Blocks authoring the state variants.
3. **State-variant authoring for the 3 switch-floors** (base + 1 delta each on the *floor-visible*
   bridge) — pending #2; re-point the current single `doorPrompt`s to the correct floor-visible bridge.

### `escape_room_scene_validator` pass — run 2026-07-26 (skill bootstrapped here)
The new **`escape_room_scene_validator`** (a general pre-art art-prompt validator: room accounting +
bidirectional hotspot accounting + map consistency + state variants + consistency sweep) was run over
this scenario. Results:
- **Check 1 ROOM ACCOUNTING — ~~GAP~~ RESOLVED 2026-07-28.** `reach_art` → **8 standable platforms**;
  the scenario now has **8 rooms**, 1:1 with the reachable platforms. Lucas chose to **add** `(2,1)` and
  `(3,1)` as visitable flavour dead-ends (`spillway` + `sump`; see OPEN DECISIONS #1). Unreachable
  `(2,2)`/`(3,2)` have no room = correct (no dead art). No roomless standable spot remains.
- **Check 2 REVERSE — orphan fixed.** The `catwalk` prompt drew a diverter **lever** but that room has
  no diverter → **removed** (replaced with scenic stone-post + rope). No other orphans.
- **Check 2 FORWARD — passes.** All 24 planned hotspots have their object in the prompt.
- **Check 3 MAP CONSISTENCY — passes** (the connectivity fix earlier this session).
- **Check 4 STATE VARIANTS — TO DO.** Carrier = **immersive art** (Lucas: build multiple art per room);
  33 raw → **11** floor-visible views; the three switch-floors each need a base + one delta on the
  *floor-visible* bridge (e.g. station1's varying span is the ACROSS bridge to station3, not the
  down-ladder — the current single `doorPrompt` needs re-pointing). **BLOCKER:** does the :8751 harness
  swap a *panorama* by state, or must variants ship as `mapview`-style state-indexed images? Output
  format depends on it.

### `escape_room_scene_validator` RE-RUN — 2026-07-28 (after adding spillway + sump)
Full 5-check pass over the updated `scenario.json` (now 8 rooms):
- **Check 1 room accounting — PASS.** 8 rooms = all 8 reachable platforms (1:1); no roomless spot, no
  dead room (unreachable (2,2)/(3,2) correctly have none).
- **Check 2 hotspot accounting (bidirectional) — PASS.** Forward: every new hotspot object is named in
  its prompt (discard-tally stone; vale-folk marker; the new station2 across-bridge; both ladders/bridges).
  Reverse: no orphans — the flavour rooms deliberately contain **no** lever/console/font/keypad/dial, only
  a `clue` object + door passages; the (2,2)-ward `H-2-1` is drawn as a **collapsed** bridge (no hotspot,
  no phantom way on).
- **Check 3 map consistency + bidirectional passages — PASS.** New passage pairs agree in type + inverse
  direction: station2 ⇄ spillway (level rope bridge, both ends); spillway ⇄ sump (ladder down ↔ ladder up).
  basin ⇄ sump correctly absent (`H-3-0` absent → walled off, neither prompt depicts a bridge). **Fix
  folded in:** station2 now depicts its ACROSS bridge to spillway (was missing; station2 is a 3-way).
- **Check 4 state variants — deferred (unchanged).** sump = single view (no variant ever). spillway =
  single-view strict; its down-ladder water-gating folds into the existing deferred state-variant work
  (open-decisions #2/#3, gated on the harness pano-swap question). No new variant authoring needed here.
- **Check 5 consistency sweep — PASS.** Environmental arc holds: spillway matches station2's depth (small
  dusk-sky disc far up, heavy spray), sump matches the basin's bottom (flooded/no-sky/rising water) but
  ruined & stagnant vs the grand sacred basins. Controls co-located (clue with its object); no controls to
  misplace. coverPrompt unchanged. World-backdrop continuity intact (deep interior shaft; no off-world
  features in art or in entry/debrief/designNote text). **JUDGEMENT CALL (recorded):** `H-2-1` is a present
  bridge in `puzzle.json` but (2,2) is unreachable/roomless, so it is depicted as collapsed rather than a
  live water-gated span — player-honest (it's never traversable in play) at a slight loosening vs the raw
  structural graph; `puzzle.json` itself was NOT changed.

### Next layer (deferred, agreed)
- **Passive streams for the k-visual + scaling**: many streams that flow straight to their
  basins with no lever, so the shaft *looks* like many streams sorting into k pools while the
  puzzle stays at 4 levers. Mostly a rendering/placement concern; watch that passive streams
  don't block the only routes.
- **Guess-k lock** hotspot (separate from the maze generator).
- Optional: reintroduce a literal throw-it-back **backtracker** via a dedicated transit lever
  if the pure order-puzzle feels too light.

---
authority: intent
---

# Henges scenario (PUZZLE phase) — Dimensionality Reduction / PCA

Chapter `dimensionality_reduction`, scenario `henges`. **Idea captured 2026-07-23 (Lucas, "ideas"
session).** First scenario in a new **`dimensionality_reduction`** chapter folder (sibling of `data_vis`,
`data_vis2`, `wrangling`, `hierarchical_clustering`, `embeddings`). Codec id: take `next_free_id` from
`rooms/scenario_inventory.json` when the scenario is scaffolded (**11** at capture time; regenerate the
inventory after `scenario.json` exists).

This file is the **PUZZLE-phase** output (ladder + engineered dataset, both verified). It is the input to
`escape_room_story` (narrative) → `escape_room_design` (scenes + `scenario.json`) → *[art]* →
`escape_room_wiring` (final MCQ text). **Nothing is built yet** — no `scenario.json`, no scenes, no art.

The scenario's origin theme lives in `notes/scenario_theme_ideas.md` → *England / henges → PCA*.

## Analog grounding (Step 0 — the real-world act the code performs)

**PCA = finding the vantage point that spreads a cloud of things out the most, then reading which trait
that spread lines up with.** Where people do this by hand: you photograph a group and *walk around them
until no one is hidden behind anyone else* — the angle of **maximum visible spread**. Or you tip and turn
a cluttered shelf of objects until their differences are most legible. Or you sort a mixed pile by the
**single trait that best separates it**. That "turn it until it spreads out, then name what the spread is
about" is exactly what PCA does: it rotates the data to the axis of greatest variance (PC1) and the
loadings tell you which measured trait that axis is made of.

The **recognition-not-computation** version (the seed for the data-free escape, built later in
`escape_room_story`, NOT here): *recognising which view spreads a set out most*, or *which view makes one
sub-group stand apart* — no computation, just picking the right vantage. The henge mechanic literally is
this: each arch is a different projection of the same stones, and you walk to the one that spreads them.

## Theme seed (for `escape_room_story` — do not over-build here)

England, a ring of **standing-stone henges** (Stonehenge-like). A central hub; **each arch is a doorway
into a different henge**, told apart by **stone colour / the moss growing on them**. Each henge holds an
**altar** with the **same items rearranged** — each henge is a different *projection* of the same points;
walking through an arch **rotates your view onto another principal component**. "Maximise the spread" =
look along PC1; "order the henges by spread" = the scree plot, walkable. **Puzzle data is deliberately
decoupled from this stone/druid furniture** (Lucas, 2026-07-23): the analyses are about **druid
ingredients** (herbs, mushrooms, beetles, roots), keeping the escape's world at arm's length from the
graded puzzles. Full world/stakes/beats/escape are `escape_room_story`'s job.

## Chapter alignment — the book's technique sequence

Chapter `integrated_bioanalytics/chapters/8_dimensional_reduction.Rmd` (PCA via `runMatrixAnalyses`)
teaches, **in this order**:
1. **Scores plot** (`analysis = "pca"`) — project samples to 2-D; read which samples separate, and along
   which dimension (the Alaska example: some lakes split on Dim.1, others on Dim.2).
2. **Ordination / loadings** (`analysis = "pca_ord"`) — which *analyte* drives each axis, i.e. which
   analyte is the **marker** for a group that separates there.
3. **Scree / variance explained** (`analysis = "pca_dim"`) — how much each PC captures.
Its own exercises: "which compound is the **biomarker** for group X" and "top markers for red vs white."
`scale_variance` **defaults TRUE** for PCA (verified in `phylochemistry.R` ~L14073) — the data is
standardised; our answers are verified against that default (and hold unscaled too — see below).

The ladder tracks this sequence, re-ordered only where difficulty must stay monotonic (scree before
ordination), and maps each rung onto the henge mechanic.

## The verified ladder (reverse-engineered from the boss)

Dataset: engineered **`data/druid_ingredients.csv`** (225 ingredients × 9 numeric properties + `kind`;
build + verification below). Every answer re-verified by `_scratch/build_druid_ingredients.py` on each run.

| Room | Technique (book step) | The analysis | Verified answer | Margin | New move (escalation) |
|------|----------------------|--------------|-----------------|--------|-----------------------|
| **1 — scores** | scores plot | run PCA; on the scores plot, which single ingredient sits farthest out along the axis of greatest spread (PC1)? | **Deathwatch Scarab** (\|PC1\|=4.50) | +19% vs Glasswing Beetle II (3.64) | read a scores plot; find the PC1 extreme |
| **2 — scree** | variance explained (`pca_dim`) | from the scree, how much of the total variation does **PC1** capture? (or PC1+PC2) | **PC1 = 25.0%** (PC1+PC2 = 42.7%) | vs PC2 17.8%, PC3 12.7% | quantify & compare spread *across* components |
| **3 — ordination** | loadings (`pca_ord`) | which measured property contributes most to PC1 (the max-spread axis)? | **potency** (loading 0.58) | +18% vs bitterness (0.48) | new object: from samples to *variables* |
| **Boss — marker + trap** | scores + ordination | which property best distinguishes the **mushrooms** from every other ingredient? | **luminance** (PC2 loading 0.62) | +15% vs resin_content (0.53) | find *which axis* separates a group, then read *that* axis |

**Strictly monotonic:** each rung adds exactly one move (one point on one axis → quantify across axes →
read loadings on the main axis → find the right axis for a group, then read its loadings). No plateau.

### The taught trap (the boss) — PC1-fixation

Three rooms train the student on **PC1** (max spread, its driver = potency). The boss asks for the marker
of the **mushrooms** — but mushrooms **do not separate on PC1** (mushroom PC1 mean = **0.03**, dead
mid-pack; beetles own PC1). They separate on **PC2** (mushroom PC2 mean = **1.46**, clearly extreme),
whose driver is **luminance**. So the tempting shortcut — reuse potency, the axis everyone's been reading
— is a **decoy**, and it's a *fair* decoy: potency genuinely fails to distinguish mushrooms (group means
herb 33 / root 52 / **mushroom 58** / beetle 85 — mushrooms are middling), whereas luminance sets them
starkly apart (others ~25, **mushroom 60**). This is the real PCA misconception (students fixate on PC1
and miss that a group can live on a later axis — the chapter's own Alaska example makes exactly this
point). **Fairness carried by wording + a clue**, per the trees precedent (draft wording below; method is
never stated in the prompt — it goes to the wrong-answer feedback in wiring):
- **Boss prompt (draft):** *"The glowing henge answers only to what sets its stones apart. Of all the
  ingredients gathered here, the mushrooms cluster together, unlike anything else — but not along the
  great axis of spread you have followed until now. Which single property is it that marks the mushrooms
  out from every other ingredient?"* → **luminance**.
- **Boss clue (draft, in-world):** *"I have walked the wide henge again and again, and the mushrooms will
  not lie at either end of it — on that first axis they sit with the common rabble. It is only when I turn
  to the **second** view that they draw together, apart from all the rest. Read what that second view is
  built from, and you will have their mark."* (Points the player off PC1 and onto PC2 — the anti-fixation
  cue — without naming luminance.)
- **Wrong-method feedback seed (for wiring):** a student who answers **potency** (the PC1 driver from
  Room 3) is reusing the max-spread axis; the feedback should say the mushrooms are middling on that axis
  (they neither top nor bottom it) and nudge to *which* axis actually gathers them.

### The escape (boss cognitive move — SEED ONLY; designed in `escape_room_story`, not here)

Boss's core move: **identify which axis of variation sets a particular group apart, then name what drives
that axis.** The data-free escape re-poses that on in-world props (henge/stone furniture), decoupled from
the druid-ingredient data entirely — e.g. recognising which henge-view makes one set of stones stand
apart, and which carved trait that view is "about." Do **not** pin props / answer / verification here.

**→ Now designed in the STORY phase (2026-07-23) — see `## Narrative` → *The escape* below, which supersedes
this seed. Note: the escape as built echoes the SCREE (order the henges by spread), with the boss's
anti-fixation lesson threaded through the read direction, per Lucas's call.**

### Puzzle types & variety (proper type assignment)

The rooms use the FOUR graded interaction types (`../../../notes/puzzle_types_design_notes.md`), **all
with built engines** — Type 1 **Compute-the-Key** (write a pipeline, assign a var, graded on the live R
session via the `check` primitive), Type 2 **Classify-the-Unknown**, Type 3 **Repair-the-Pipeline** (fix
broken code), Type 4 **Pick-the-Point** (make a live ggiraph plot, *click* the answer — built + shipped in
alaska 2026-07-22). **MCQ is a fallback, not the default.** Assignment, chosen for variety + a rising
interaction difficulty:

- **R1 (scores outlier) → Type 4 Pick-the-Point.** Plot the PCA scores; click the ingredient flung
  farthest along PC1 (**Deathwatch Scarab**). Exactly the alaska chloride-outlier pattern; engine built.
  The other 224 points are the "distractors" — no MCQ options required.
- **R2 (scree) → Type 1 Compute-the-Key.** Run `pca_dim`; assign the PC1 variance % (or #components to
  pass half the spread) to `answer`; console-checked.
- **R3 (PC1 driver) → Type 1 Compute-the-Key.** `which.max(abs(loadings[,"PC1"]))` → assign the property
  name (**potency**). The skill's own canonical PCA compute example.
- **Boss (mushroom marker + trap) → Type 3 Repair-the-Pipeline (DECIDED 2026-07-23, Lucas).** Hand the
  student code that reads **PC1's** top loading (returns potency — the naive, *wrong* answer for the
  mushroom question); they must fix it to identify what separates the mushrooms → read **PC2** →
  **luminance**. The canonical PCA mistake (reading the wrong component) *is* the taught trap; debugging the
  code embodies the anti-fixation lesson. (Rejected the lighter Type 4 Pick-the-Point-on-the-biplot
  alternative — the code-fix is the stronger capstone.)

**Variety: types 4, 1, 1, 3** — three distinct interaction types, no four-identical-cards plateau, and a
rising ramp (click → compute → compute → debug) that also firms up the R1→R2 escalation. **No unbuilt
engine dependency** — all four graded engines exist; the **walk-the-PCs** spatial layer (#17) is
scene/navigation work for `escape_room_design`, not a graded puzzle type.

**On MCQ / the "≥6 distractors" bar:** because R1 (pick) and R3 (compute) grade on a click / the R session,
and the boss (repair) on corrected output, the ≥6-distractor rule mainly bites for any MCQ *fallback*; the
verified data supplies them regardless (9 properties for a loading MCQ; 225 named points for a scores MCQ).

- **New signature mechanic** — the **projection gallery / walk-the-PCs** (each arch = a projection; find
  or order the projections by spread). Registered as **#17** in `../../../notes/puzzle_inventory.md`.

## Data reality — why the dataset is ENGINEERED (profiled 2026-07-23)

Every candidate real teaching dataset was profiled with real PCA runs
(`_scratch/`-style, sklearn) — **none gives a clean single-winner "which property drives the axis" boss**,
because real correlated data spreads PC1's loadings across a *blend* of variables:

| Dataset | Problem for this ladder |
|---------|-------------------------|
| `chemical_blooms` (druid-herbs candidate) | **Flat scree** — PC1≈PC2≈15% (ratio 1.02); kills the "PC1 is the max-spread axis" conceit. No group structure (78 species). |
| `wine_quality` | Red/white split clean on PC1, but top-two loadings (total vs free SO₂) within **11%** — no single-winner marker. |
| `metabolomics_data` | Clean 2-group split, but 125 metabolites spread the loadings; top marker beats #2 by **2%**. Unanswerable MCQ. |
| `per_table` (stones/minerals) | Nice scree, period separates, but PC1 loadings tied to within **1%**; scattered NAs. |

**Decision (Lucas, 2026-07-23): engineer a fit-for-purpose dataset** (a first-class move per the
`escape_room_puzzles` skill; same call as `trees`). Theme = **druid ingredients**, deliberately decoupled
from the henge/stone escape furniture.

## The engineered dataset (BUILT + VERIFIED 2026-07-23)

Generator: **`_scratch/build_druid_ingredients.py`** (deterministic, seed 20260723) →
**`data/druid_ingredients.csv`** (225 rows × 12 cols). Re-run to reconfirm — it prints a full
verification and **asserts** every design property (fails loudly if a tweak breaks a rung).

**Path & public URL.** Local: `rooms/dimensionality_reduction/henges/data/druid_ingredients.csv`. Public
(scenario-local, live once the site is pushed from the Mac):
`https://thebustalab.github.io/escape_rooms/rooms/dimensionality_reduction/henges/data/druid_ingredients.csv`
(alt if a shorter URL is wanted: move to `phylochemistry/sample_data/`, as the other scenarios' sets are).

**Columns (student-facing):** `specimen_id, ingredient, kind, potency, bitterness, aroma_intensity,
volatility, luminance, pigment, resin_content, moisture, ash_weight`.

- **Samples** = 225 named druid ingredients (evocative unique names), grouped by **`kind`**: herb 70,
  mushroom 58, beetle 51, root 46.
- **9 numeric properties** measured on every ingredient, in plausible units/ranges.

**How it's built (low-rank latent model + noise).** Three orthogonal latent factors drive the properties;
each property loads on **exactly one** factor (single-block — cross-loadings tilt the PCA axes into a flat
blend, the failure mode we hit and fixed), plus idiosyncratic per-property noise and per-cell jitter so
the columns look real, not sterile:
- **f1 → PC1 (the max-spread axis):** driver **potency** (weight 1.0) + a believable descending tail
  (bitterness 0.32, aroma 0.26, volatility 0.20). Separates **beetles (high) ↔ herbs (low)**.
- **f2 → PC2:** driver **luminance** (1.0) + tail (pigment 0.30, resin 0.24). Separates **mushrooms** only
  (the boss group) — orthogonalised against f1 so mushrooms sit *mid-pack on PC1*.
- **f3 → PC3 (nuisance):** moisture + ash_weight — honest distractor columns that drive no group split.
- **One engineered outlier** ("Deathwatch Scarab", a beetle pushed far along f1) = the clean **Room-1**
  answer.
- Drivers get the **largest raw spread in their block**, so the top loading is the same **scaled or
  unscaled** (course default is scaled; robust either way).

**Verified (standardised PCA — the course default):**
- **Scree:** PC1 25.0% > PC2 17.8% > PC3 12.7% (PC1/PC2 = 1.40 — PC1 unambiguously the max-spread axis).
- **R1 outlier:** Deathwatch Scarab \|PC1\|=4.50 vs Glasswing Beetle II 3.64 (**+19%**). Distractor pool:
  Witchhazel II (3.37), Bloodhorn (3.09), Bittercress II (3.03), Tombscarab (3.01)… — a mix of beetles
  (positive extreme) and herbs (negative extreme); ≥6 easily.
- **R3 PC1 driver:** potency 0.582 > bitterness 0.477 > aroma 0.468 > volatility 0.423 (**+18%**). 8
  property distractors.
- **Boss PC2 driver / mushroom marker:** luminance 0.625 > resin 0.533 > pigment 0.489 (**+15%**); mushroom
  PC1 mean 0.03 (mid) vs PC2 mean 1.46 (extreme) — the trap holds; potency (the decoy) group-means confirm
  it fails to separate mushrooms.
- Holds **unscaled** too (potency +58%, luminance +71%).

**Departure from raw data documented:** the entire measured matrix is synthetic (no real ingredient
chemistry) — the category names are invented and the numbers come from the latent model, engineered so
each PCA rung has a single clean winner and the PC1/PC2 misdirection exists. This is the deliberate,
skill-sanctioned engineering, not a claim about real herbs/mushrooms/beetles.

## Judgement calls flagged for Lucas

1. **Engineered, not real, data** — approved in principle 2026-07-23; noting it explicitly (the numbers
   are synthetic, per the trap requirement).
2. **Room 2 (scree) exact question** — I've verified two clean framings: "% variance in PC1" (**25%**) or
   "% in PC1+PC2" (**43%**) / "components to exceed half the spread" (**3**). Pick one in wiring; all are
   single-winner. Leaning "% captured by PC1" as the tightest henge-mechanic fit (the single most-spread
   henge).
3. **Boss group = mushrooms** — chosen because mushrooms are the group I engineered onto PC2. If you'd
   rather the trap group be beetles/herbs, that's a data re-tune, not hard — say the word.
4. **Noise level** — tuned so PC1 is only ~25% (realistic, believable spread; not a razor-clean toy). If
   you want the scores plot to *read* more obviously clustered for players, I can dial the group
   separation up (cleaner plot, less "real"). Current setting favours believability, as you asked.

## Housekeeping / handoff

- **Codec id 11** reserved for `henges` (claim on scaffold; regenerate `authoring/scenario_inventory.py`).
- **Pre/post pair:** the `dimensionality_reduction` chapter should get a **second** PCA scenario (different
  dataset/story, same technique) as the pair — henges is one half.
- **New mechanic** #17 (projection gallery / walk-the-PCs) added to `../../../notes/puzzle_inventory.md`.
- **No git on this box** (site is a Mac-only repo; Syncthing carries edits).
- **Phase status:** PUZZLE ✅ · STORY ✅ (2026-07-23) · **DESIGN ✅ (2026-07-24)** · art (harness) next · WIRING.
- **Next step:** Lucas opens `scenario.json` in the `:8751` harness to generate the art (art is the **last**
  harness step); then `escape_room_wiring` finalises content. Design record: `## Narrative` (below) +
  `## Design phase` (at the foot).

---

## Narrative (STORY phase — authored 2026-07-23, "ideas" session with Lucas)

**Status: STORY phase COMPLETE.** Input to `escape_room_design`. The **ladder, answers, and dataset are
UNCHANGED** from the puzzle phase — this section adds only world, stakes, beats, the escape, and draft
story-map text. Locations are assigned to rungs here (a story call); the graded content is not touched.

### Logline / stakes / clock
- **Logline:** wrecked and star-sick, a traveller must brew the old star-potion from the henge-country's
  ingredients to cure themselves, then **read the stones** to open the portal home — before dawn silences
  the henges.
- **World, in a phrase:** a chain of wondrous, **teleport-linked standing-stone henges** under a dying
  starlit night.
- **Player / stakes — two payoffs, decoupled:** you wash up sick (a wasting *star-sickness* from the
  drowning). **Brewing the potion = completing the four graded puzzles = the cure.** The **escape is
  separate** — reading the henges to open the way home. Fail before dawn and you're stranded a full turn
  of the year.
- **Clock:** the henges only wake while the stars are out. The night **brightens toward dawn** across the
  rooms; when the sun clears the horizon the arches go dark. (Rides the environmental arc.)

### The one principle it serves
**The world IS PCA, and the arches enact it every room.** Each arch is a *projection* of the same field of
stones; stepping through **rotates your view onto another principal component**. Most arches show only
**blackness** (noise); solving the analysis makes the one true arch **resolve into stars** — a portal.
That is PCA finding the single view where structure emerges from the dark, enacted on every solve.

### World (fantastical, built from real henge "bones")
Not a real place, but drawn from real standing stones for variety and believability:
- **Callanish** (Lewis) — radiating stone avenues → the hub-of-arches geometry.
- **Men-an-Tol** (Cornwall) — a holed stone you pass through → the **teleport gates**.
- **Long Meg** (Cumbria) — carved spirals / cup-and-ring marks → the **celestial symbols** read off stones.
- **Avebury** — the West Kennet stone avenue → a processional approach out of the water.
- **Ring of Brodgar / Stenness** (Orkney, on the lochs) → the drowned, **star-mirrored water** of the beach.
- **Signature travel = teleport through the holed arches** (walk-the-PCs, mechanic #17). The wash-up is the
  "adrift" beat; teleport carries all the rest. **No second travel mechanic** (the earlier drowned-mere /
  drift-by-water idea is retired now that the destinations are distinct wonders).
- **No cast** (house no-people rule). The world **instructs by repetition**, not NPCs or left-behind notes —
  this is why the keypad is taught by using one every room (see below).
- **Monolith motif (load-bearing for the escape):** every henge holds a **rock monolith bearing the same
  3–4 small stones**, thrown at a **different spread in each henge** (each henge = a different projection).
  Reading those spreads by eye is how the escape's scree order is found. Abstract stones — **not** the
  druid ingredients; the world stays decoupled from the data.

### Environmental arc (hand to `escape_room_design`)
Room 0 **beach** — deep black night, low moon, stars mirrored on still water → Room 1 **mountaintop** —
thinner, colder, a shade less black → Room 2 **fireflies plain** — first grey of dawn at the horizon →
Room 3 **salt flat / mirror playa** — the stars fading, the east silvering → **Boss / great henge** — first **gold of true dawn**.
Elevation and light rise together. The **great henge dominates the horizon from the beach** (foreshadow /
throughline — the thing you move toward all night).

### Rooms, beats, and the letter/keypad chain
Five locations: an **atmospheric intro (room 0)** + **four graded henges**. Celestial **letters** are
collected by **walking through four lettered portals BEFORE the boss keypad** — so the **boss contributes
the *ordering clue*, not a letter** (it can't give a walk-through letter: you never pass a boss portal
before you need the code). The fourth letter therefore comes from the **pre-opened beach portal**.

| # | Location | Graded rung (UNCHANGED) | Flow | Portal letter |
|---|----------|-------------------------|------|---------------|
| 0 | **Beach** — atmospheric, *no graded puzzle* | — (wash up; learn the star-sickness + the potion goal; the how-the-arches-work on-ramp) | portal **pre-opened from the start** | **A** |
| 1 | **Mountaintop** | R1 scores → **Type 4 Pick-the-Point** (Deathwatch Scarab) | solve → a **code** is revealed (corroborated by an in-room celestial clue) → type at the **monolith keypad** → the **B** arch wakes → walk through | **B** |
| 2 | **Fireflies plain** | R2 scree → **Type 1 Compute** (PC1 = 25%) | solve → code → keypad → **C** arch | **C** |
| 3 | **Salt flat (mirror playa)** — expansive/uniform, so a single teleport-in room | R3 ordination → **Type 1 Compute** (potency) | solve → code → keypad → **D** arch | **D** |
| Boss | **Great henge** (dawn) | Boss → **Type 3 Repair** (mushroom marker = luminance; **PC1-fixation trap**) | solve boss → **no code given**; the great keypad wants A/B/C/D in the right **order** | — (gives the *order* clue) |

**Each puzzle room teaches TWO things by repetition** (no notes/tech in this world):
1. there is a **keypad** and you must enter a code (the code is the reward for solving the WebR puzzle);
2. that code is **tied to another feature of the room** (a celestial artifact/clue that corroborates it).

So by the boss room the player understands (a) how keypads work and (b) that **a room feature reveals the
answer** — so they arrive holding the four letters *and knowing to look for the ordering clue*.

### The escape (data-free; decoupled from the potion + the dataset)
Separate from the potion (the potion = the cure = the graded finish). The escape opens the way home:
- The player holds **A, B, C, D** (in walk-through order) and, in the **field notebook**, an **image of
  each henge's monolith**.
- **Ordering rule = the SCREE.** Rank the four monoliths by the **spread of their stones**, greatest→least
  (worked example: **B, A, D, C**). The scree plot enacted on stone. A blind guesser faces 4! = **24**
  orders; **reading the spreads collapses it to one ranking** (± direction) — which is why guessing can't
  crack it and reading must.
- **Direction from an in-world artifact.** A **rising / moon-rise motif** in the great henge — echoed by the
  celestial symbols themselves (e.g. `o → O → °`, little circles ascending) — indicates **smallest→largest**,
  so they **reverse** the ranking → **C, D, A, B** and enter that at the great keypad → the **portal home**
  opens.
- **Anti-fixation nod (kept cheaply):** the tempting move is to *lead* with the widest-spread monolith (the
  "PC1" of the four); the rising direction puts it **last**. The boss's don't-fixate-on-the-biggest lesson
  threads the escape at no extra cost.
- **Fully data-free & recognition-first:** letters, stones, and artifacts are **world props** — no CSV
  values, no ingredient names, no console. Recognition (read the spreads) + a **combinatoric keypad entry**
  (the Alaska assembled-code precedent). Engine fit: analysis-finish mints the potion/cure; the escape is
  the separate optional `lock` finale.

### Draft story-map text (tighten in the harness story-map)
- **title (draft):** *The Drowned Henges*
- **subtitle (draft):** *Star-sick and adrift — brew the potion, read the stones, and be gone before dawn.*
- **story / opening (landing screen):**
  > The sea gives you back at the dark of the night — coughing brine, colder than you have ever been. A ring
  > of standing arches leans against a sky thick with stars, and the same stars lie unbroken on the flooded
  > shore, so you cannot say where the water ends and the heavens begin. Something is wrong in your blood: a
  > cold light under the skin, a star-sickness taken from the drowning. There is a cure — the old potion the
  > henge-builders brewed from the creatures and roots this country hoards. Gather what it needs, brew it
  > true, and you will live to see the dawn. But the arches only wake while the stars are out. Read them
  > rightly before the sun clears the water and they will carry you home. Fail, and the henges sleep another
  > year — with you inside them.
- **entry — mountaintop (R1):**
  > The arch takes you and lets you go a world away: a knife of black rock high above the drowned country,
  > the air thin and needled with cold. Here too a ring of stones, and on its altar the same handful of
  > pebbles — thrown wider than before. The sky is not so black now.
- **entry — fireflies plain (R2):**
  > Through, and down onto a plain without end, a slow green snow of fireflies rising against a horizon that
  > has begun, faintly, to grey. The stones on this altar sit close, huddled together. Far ahead the great
  > henge burns cold on the skyline, waiting for you.
- **entry — salt flat (R3):**
  > Through, and out onto a floor of white salt without edge or end — so flat, so still, that the fading
  > stars lie mirrored beneath your boots and you seem to walk upon the sky itself. The henge stands alone
  > in all that emptiness, its long shadows thrown pale across the mirror. On the altar, the stones again;
  > and low in the east the dark has begun to silver.
- **entry — great henge (boss):**
  > The last arch sets you down before the great henge, its stones like cliffs against a sky going gold at
  > the rim of the world. No pebbles lie scattered here — only a keypad of living stone, and the marks you
  > have carried all night, waiting for their order.
- **done (potion brewed / cured):**
  > The potion takes with a sound like a held breath let go. The cold light drains from your hands and the
  > shaking stops. You are cured — you will live. But you are not yet home, and low in the east the first
  > true gold is on the water. The great henge is close now. Read its stones, and go.
- **escapeDone (portal home):**
  > You set the marks into the stone in the order the henges gave you — least-spread first, rising to the
  > widest, as the moon-signs rise — and the great arch fills with a light that is not starlight but
  > morning. Beyond it: your own shore, your own year, unbroken. You step through as the sun clears the sea,
  > and the henges go dark behind you, one by one.

### Judgement calls flagged for Lucas
1. **Beach = atmospheric room 0** (no graded puzzle); **R1 (scores) moves to the mountaintop.** Location
   change only — the ladder, answers, and dataset are untouched.
2. **Escape echoes the SCREE** (Lucas's call) rather than the boss's anti-fixation move directly; the
   **rising-direction** twist keeps a thread of the boss lesson. Within the skill's "data-free meta-echo of
   the technique."
3. **Wiring nuance for `escape_room_design`:** the beach's **pre-opened forward portal** needs handling — a
   forward door normally gates on a *solved* room, and the beach is gateless. Options: a pre-solved lock, a
   trivial tap-the-stone gate, or a `back`-style always-live door. Resolve in design/wiring.
4. **Third henge (room 3) = salt flat / mirror playa** (DECIDED 2026-07-24, Lucas) — chosen for its
   ethereal, otherworldly, druid-magic feel. Expansive and uniform, so it's a **single teleport-in room**,
   not a room-chain. Unchosen alternatives are parked in `../../../notes/candidate_locations.md`.
5. **Symbols / celestial alphabet, the exact per-room codes, the ordering artifact, and the per-room
   corroborating clues** are **wiring-time** detail (`escape_room_wiring`); the *pattern* (code tied to a
   room feature; order tied to a boss-room feature) is fixed here.

---

## Design phase (scenes + scenario.json — 2026-07-24)

**Status: DESIGN phase COMPLETE.** `scenario.json` written (parses), **codec id 11 claimed**, inventory
regenerated (`next_free_id` now 12). All six rooms are **stubs** (`built:false`) with scene prompts,
`designNote`s (full puzzle specs), and `plannedHotspots`. Ready for the `:8751` art harness.

**Rooms (keys) → beats.** `beach` (orientation, **ungraded** — teaches the mark-stone keypad at difficulty
zero) → `mountain` (R1 scores, **Type 4 pick** → Deathwatch Scarab) → `plains` (R2 scree, **Type 1 check**
→ 25.0%) → `saltflat` (R3 loadings, **Type 1 check** → potency) → `boss` (**Type 3 repair**, PC1→PC2 →
luminance; PC1-fixation trap) → `escape1` (heart of the great henge — the scree lock). Environmental arc
runs deep-night beach → higher/greyer mountain → firefly plain (first grey) → silvering salt-flat → gold-
dawn great henge → full-dawn heart. Both light and elevation rise together.

**Scree spread ranks (the art carries these).** Each lettered monolith shows the same four stones at a
different spread: **mountain widest (1) > beach (2) > saltflat (3) > plains tightest (4)**. Descending =
B,A,D,C; the rising moonrise frieze ⇒ **ascending answer C,D,A,B** (plains, salt-flat, beach, mountain).
Consistent with the story entry cards (mountain "thrown wider", plains "close, huddled").

**Flagged wiring / build items (carry to the harness + `escape_room_wiring`):**
1. **Per-room mark-stone keypad.** Each forward arch is gated on a `lock` (the monolith keypad) whose code
   is *revealed by that room's graded puzzle* — a **novel two-gate pattern** (puzzle records the codec; lock
   opens the door via `door.requires`). Confirm the harness/engine supports puzzle-then-lock cleanly.
2. **Beach is gateless** — its pre-opened arch gates on a *trivial* lock (key the sigil the open arch already
   shows). Confirm `mountain.unlockedWhen:{solved:beach}` fires off that lock; else make the beach arch a
   `back`-style always-live door (but then `mountain` loses its entry card). *(This is judgement-call #3.)*
3. **Escape heart-stone lock** — the four sigils need a **glyph-entry mode or a glyph→key mapping** (the
   `lock` keypad is alphanumeric today). Decide at wiring, then set the literal `answer` string (order
   C,D,A,B).
4. **Decoder** — id 11 + a **4-entry** key (`mountain, plains, saltflat, boss`, in built-room order) must be
   added to `decoder/decode_codes.R` once the rooms are built; run `decoder/validate_keys.py`.
5. **Dataset URL** is scenario-local (`…/henges/data/druid_ingredients.csv`) — **live only once Lucas pushes
   from the Mac**.
6. **Room-2 scree framing** — used **"% of variance in PC1" = 25.0** (of the three verified framings).
7. **Music** — undecided (optional); not set. `ambient` set to `"mist"` (tunable in harness step 4).

**Deviation noted (per skill checklist):** durable ladder/answers are kept in **this `notes.md`**, not a
separate scenario `AGENTS.md` — none exists yet and every room is a stub, so a second durable file would
only duplicate. Create a lean `henges/AGENTS.md` once the scenario stabilises (rooms built).

---

## Art + mechanics revision — STONE CIPHER & TWO-GATE PORTALS (2026-07-25, live harness/art session)

**⚠️ This section SUPERSEDES the letter/keypad-code design above** (the "letter/keypad chain" table, the
`## The escape` A/B/C/D + moonrise section, and the "sigil A" language in the current `scenario.json`
`designNote`s). Captured live during the art pass; the `scenario.json` `designNote`s/`plannedHotspots`
still carry the OLD scheme and must be re-synced (see *To re-sync* below) once Lucas is out of the harness.

### 1. Art template (settled + working)
Every henge is authored as **ONE 360° stone circle from the exact centre**, with every feature described in
a **single left-to-right sweep** — this composes the pano *and* fixes the reading order of the fallen
stones. Two-image pair per room: closed (`scene.png`) + open (`scene_open.png`). Style: painterly,
cinematic, film grain, **cold starlit blue + one warm amber glow at the portal's heart, NO moon**, no
people, no lettering/text. Per-henge stone colour differentiates: beach barnacle-pale, mountain frost-rimed
dark basalt, plains lichen-grey, saltflat TBD. Mid-rooms show **two arches** (back = starry/arrival on the
left, forward = the way onward on the right); the beach (first room) has **one** arch, pre-awakened.

### 2. The mark is a STONE CIPHER, not a letter (letters RETIRED)
Carved letters (T/H/P/A and the "PATH" easter egg) are **dropped** — image models render letters
unreliably and it fought the no-text rule. Each henge's mark is a **fallen-arch stone pattern**: a row of
**three** stones, each **standing (`|`)** or **fallen (`_`)**, read left-to-right. The generator renders
these faithfully **when the prompt names the count and each stone's state explicitly L-to-R** (verified in
two trials, 2026-07-25).
- **Alphabet (two symbols):** `|` upright stone, `_` fallen stone.
- **Assigned patterns:** beach = `| _ |` · mountain = `| | _` · plains = `_ _ |` · **saltflat = TBD**
  (assign when that room is authored).

### 3. Escape code = the four patterns concatenated in SCREE order
Read the four monoliths by **pebble-spread** (the scree), **tightest → widest = plains, saltflat, beach,
mountain**; concatenate their stone patterns in that order → the full escape code (~12-symbol `|`/`_`
string). Spread ranks the art carries: **mountain widest (1) > beach (2) > saltflat (3) > plains tightest
(4)**. So code = `_ _ |` (plains) + `[saltflat]` + `| _ |` (beach) + `| | _` (mountain), read **ascending**
(tightest → widest). A **direction indicator IS still needed** (asc vs desc is a 2-way ambiguity a reader
would otherwise 50/50) — keep a small **rising motif** in the great henge; it doubles as the anti-fixation
nod (the widest / PC1 pattern lands **last**). Un-guessable: reading the stones gives the one order; blind ~ 2^12.

### 4. TWO-GATE PORTALS (settled 2026-07-25) — awaken, then unlock
Each forward arch has **three visual states** and needs **both** gates to pass:
1. **Asleep** = flat depthless black.
2. **Awakened** = a **dim starry sky** inside the arch — reached by solving the room's **WebR/PCA
   analysis** (the graded gate; this is what keeps the analysis *mandatory* — the keypad is inert until
   awakened).
3. **Unlocked** = a **bright swirling galaxy**, walkable — reached by keying that henge's **stone pattern**
   on the keypad.
- Order: **analysis (awaken) → keypad (unlock) → step through.** Tapping the keypad before the analysis
  shows **"this portal must be awakened first."**
- The analysis is the real intellectual gate; the keypad is *read-the-stones* — it teaches the device and
  **banks that henge's pattern** into the notebook for the escape.
- **Art impact:** do the middle "awakened dim-starry" state as an **engine overlay** (a dim starfield
  dropped into the forward-arch box), NOT a third generated image — keeps the two-image pairs as they are.
  Unlock swaps to `scene_open` (galaxy). *(Approach to confirm at wiring; Lucas favours the overlay.)*

### 5. The stone keypad UI (new engine render-mode for the `lock` type)
A **bespoke keypad**, not alphanumeric. Four controls: **`|`** (append standing), **`_`** (append fallen),
**`X`** (clear), **spiral** (submit → check vs `answer`). Above them a **display of N slots** filling L-to-R.
- Buttons are little **carved-stone icons** (upright / toppled), not ASCII, so the alphabet is unmistakable.
- **Configurable display length:** **3** in a puzzle room (one henge's pattern); the **escape** keypad is
  the *same device* with a **long** display (~12) for the whole concatenated code.
- **`answer`** = the `|`/`_` string (e.g. beach `"|_|"`). Keypad **gated on the room's analysis** (awaken);
  shows the "awaken first" message otherwise.
- The **great henge has no fallen stones of its own** — its escape code comes only from the four banked
  patterns.

### 6. The beach teaches all of it (difficulty zero)
Beach (orientation, ungraded, forward portal **pre-awakened**): read its own fallen stones (`| _ |`), key
them on the two-button keypad → portal unlocks → step through. Teaches the alphabet + "patterns are codes"
+ the device, at no stakes. Add a one-line clue ("the old ones wrote in stones raised and fallen").

### 7. Deterministic clue images (the exactness safeguard)
The **scene art** shows fallen stones as *atmosphere only* — do **not** trust the generator for the exact
code. The precise pattern the player reads/banks is a **clean deterministic graphic** (a small script, like
Alaska's escape grids), logged to the field notebook per henge. Keeps the code exact regardless of art
variance.

### 8. Build / wiring items (for `escape_room_wiring` + engine)

**ENGINE BUILT 2026-07-25 (untested — needs a browser playtest; no JS runtime on this box).** In
`shared/pano-player.js` + `pano-player.css`, gated behind a scenario flag **`stonePortals: true`** (set on
henges only, so every other scenario is byte-for-byte unchanged — verified Hawai‘i's puzzle+lock boss is
unaffected): (a) **three-phase portal** — a forward arch is asleep (black) → **awakened** (analysis/primary
puzzle solved: a dim starfield `.portalglow` overlay kindles in the arch + the door marker goes starry-blue)
→ **unlocked** (its keypad lock keyed: swaps to `panoramaOpen`, door walkable); the open image now keys on
`portalUnlocked` (forward door open) not "primary solved". (b) **stone keypad** — `lock` `mode:"stones"`
renders a slot display + four keys (`|`, `_`, X-clear, spiral-submit); answer is a raw `|`/`_` string
(bypasses `normalizeCode`). (c) the keypad is **inert until awakened** ("This portal must be awakened
first"). Cache tokens bumped to **v=46**. Wired in `scenario.json`: `stonePortals:true`, beach's placed lock
= stone mode answer `|_|`, and stone `mode`/`answer`/`length` banked on every planned lock (mountain `||_`,
plains `__|`, saltflat `_|_`, escape `__|_|_|_|||_`). **Still TODO at build:** each two-gate room's forward
door must be set to `requires` its lock in the harness (the door↔gate link needs the placed lock's id).
**Testable now:** the stone keypad + unlock→galaxy on the **beach**; the full awaken→overlay→unlock needs a
two-gate room (mountain) built with its art + `door.requires` set.

### 9. Final wiring (2026-07-25, session 2) — escape merged into the great henge; spreads locked
- **Inner sanctum removed.** `escape1` deleted; the escape now lives IN the great henge (`boss`): the boss
  analysis AWAKENS the way-home arch, then the massive **heart-stone** stone-keypad (long display) UNLOCKS it
  with the full code. Way-home door `requires` the heart-stone lock + **`endsEscape:true`** — a new engine
  hook in `handleDoor` → `showEscapeDone`, so the great henge stays analysis-phase (potion/cure still mints on
  the boss solve) yet the way-home door ends the escape. Great henge has NO fallen stones and NO pebble-monolith.
- **Pebble spreads LOCKED** (art will attempt the measurements; the deterministic notebook graphic is the
  fallback): **beach ~5 ft (WIDEST, rank 1) > plains ~3 ft (2) > mountain ~1 ft (3) > saltflat touching
  (TIGHTEST, 4)**. Prompts carry the measurements. Caveat: independently-generated scenes won't be
  proportionally comparable, so the exact ranking still comes from the graphic if the art isn't clean enough.
- **Escape code recomputed** (ascending, tightest→widest = saltflat, mountain, plains, beach) =
  **`_|_||___||_|`** (`_|_`+`||_`+`__|`+`|_|`), set as the heart-stone `answer`. Per-room lock patterns
  unchanged (beach `|_|`, mountain `||_`, plains `__|`, saltflat `_|_`).
- Cache tokens now **v=47**; `scenario_inventory.json` regenerated (henges id 11, verified unique).

### 10. WIRING COMPLETE (2026-07-26) — all five rooms playable, every validator green
All puzzles filled + **re-verified against the CSV** (mountain **pick** → Deathwatch Scarab; plains
**check** → 25.0%; saltflat **check** → potency; boss **repair** check, broken code reads PC1 → fix to
PC2 → luminance). Two-gate doors wired: every forward arch `requires` its `the_mark_stone` lock (so the
keypad isn't bypassed), back arches have explicit `to`, and the boss **way-home** door `requires
the_heart_stone` + `endsEscape:true`. Escape code (heart-stone) = **`_|_||___||_|`** (saltflat+mountain+
plains+beach, scree ascending). Engine: **`mintCode` now skips ungraded rooms** (`roomResults.has`) so the
pre-awakened beach takes no codec slot; `validate_keys.py` skips a built lock-only/pre-awakened orientation
room to match. Decoder: **`DATA_VIS_HENGES_KEY` id 11, correct = c(1,1,1,1)** + self-test (grades 40).
`rooms/.../henges/play.html` created; `test_henges.py` added (pins all four answers + the trap + doors +
escape code + decoder lockstep — **ALL PASS**). Cache tokens **v=49** (js; css v=48). Validators green:
`test_henges.py`, `validate_keys.py` (henges PASS; the WARN "all index 1" is expected for an all-check/pick
scenario; the 2 FAILs are the separate in-progress `spa` scenario, not henges), `Rscript decode_codes.R`
(id-11 round-trip TRUE, 40 pts), `node --check`.

**Test prerequisites / still-to-do (non-blocking for a first playtest):**
- **Data must be live:** the WebR console loads `druid_ingredients` from the absolute github.io URL, so the
  `data/` CSV must be **pushed from the Mac** or the console can't fetch it.
- **Per-room sfx** not sourced yet (the "Sounds" step); **deterministic scree clue-image** not built (the
  art carries the spreads for now); **JS suite** (`tests/` npm + Playwright e2e) is Lucas's browser run —
  add henges to `e2e/smoke.spec.js` and re-point `alaska_full.spec.js` when ready.
- **Music** file lands via the fire-and-forget download; `music` field already points at it (degrades
  gracefully until present).
- **New `lock` render-mode:** stone keypad (`|`/`_`/`X`/spiral + N-slot display), gated on the room's
  analysis, "awaken first" message, `answer` as a `|`/`_` string, configurable length. Cache-bump + test.
- **Three-state portal:** black → (engine overlay) dim-starry on analysis-solve → `scene_open` galaxy on
  keypad-unlock. The forward door becomes walkable only after unlock.
- **Deterministic clue-image script:** per-henge pattern graphic → notebook.
- **Escape long-code keypad** (~12 slots); no in-scene stones in the great henge.
- **Decoder:** id 11 + key (`mountain, plains, saltflat, boss`) once built; `validate_keys.py`.
- **Assign saltflat's pattern + confirm its spread** (rank 3/4) when authoring that room.

### 9. Prompt / art status (2026-07-25)
- **beach:** rebuilt to single-circle + `| _ |` stones, no letter, no moon — Lucas iterating art (`built:true`,
  `gpt_beach_9` at last sight; may re-gen).
- **mountain:** prompt rebuilt (`| | _`, no moon, single-circle). **plains:** prompt rebuilt (`_ _ |`, moor,
  fallen-stone row verified rendering). **saltflat:** next.
- **Music:** `youtube_audio` observer row fired 2026-07-25 (`https://youtu.be/dRjoEDeqvyE` →
  `audio/drowned_henges_theme.mp3`, 0:00-6:00, 128K, crossfade-loop 20). Set `music`/`musicVolume` (0.1)/
  `musicCredit` once it lands (grab the track title for the credit).

### To re-sync into `scenario.json` (when Lucas is out of the harness)
The live `scenario.json` `designNote`s + `plannedHotspots` still describe the **letter** scheme. Update each
room's `designNote` to the stone-cipher + two-gate mechanic, set each `lock`'s `answer` to the `|`/`_`
pattern, and add the keypad-length + awaken-gating fields once the engine mode exists. Do NOT overwrite
Lucas's `scenePrompt`s / `built` flags / placed `hotspots` — targeted field edits only, harness closed.

### 10. Sound effects wired (2026-07-30) — VERIFICATION + BALANCE PENDING
All 5 rooms now carry ambience `sfx` arrays and all 9 graded gates (each puzzle + each lock) carry
`solveSfx`, wired directly into `scenario.json` (Lucas confirmed out of the harness). Design: a shared
`stone_drone.mp3` (sacred hum) under every room + per-room beds (beach waves+wind, mountain wind, plains
meadow+shimmer, saltflat vast-wind+shimmer, boss dawn-birds+wind). Solve stings (Lucas-chosen, CC0):
`solve_portal_awaken.mp3` (magical bell flourish, on scrying-basin puzzles), `solve_portal_open.mp3`
(warp-in, on mark-stone locks), `solve_way_home.mp3` (teleport, on boss heart-stone). All CC0 from
freesound; provenance in `audio/CREDITS.md`. Pulled via the `sound_pull` observer (2 rows fired; the 2nd
re-pulled the 3 Lucas-picked solve stings after deleting the old picks so idempotency didn't skip them).
- **STATUS:** 8 of 10 mp3s on disk; **`beach_waves_night.mp3` + `plains_meadow.mp3` NOT YET landed** (pull
  still in flight or those 2 URLs failed). `validate_assets.py dimensionality_reduction/henges` will FAIL
  on those two missing files until they arrive (all other lines are green — every room has sfx, every gate
  has solveSfx). A pre-existing unrelated MISS: `cover.png` absent (henges cover not set; flagged to Lucas).
- **NEXT:** once both files land, run `python3 authoring/auto_balance.py dimensionality_reduction/henges`
  (LUFS reduce-only so nothing beats the 0.1 music bed), then it's done. If the 2 files never appear,
  re-pull just those (spec at `_scratch/sfx_pull_spec.json`; sources = el_boss/587164, ali.g/855326).

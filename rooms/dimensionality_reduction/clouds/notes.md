---
authority: intent
---

# Clouds scenario — Dimensionality Reduction / PCA (pair to `henges`)

Chapter `dimensionality_reduction`, scenario `clouds`. **Idea captured 2026-08-04 (Lucas, "clouds"
session).** Second scenario in the `dimensionality_reduction` chapter — the **pre/post pair to
`henges`** (same PCA technique + same question style, different dataset + world; see the paired-scenario
principle in `escape_rooms/AGENTS.md`). Codec id: **16** (`next_free_id` at capture time; regenerate the
inventory with `authoring/scenario_inventory.py` once `scenario.json` exists).

**Status.** This file currently holds the **analog grounding + world/premise + escape mechanic** — the
STORY-phase conceptual work, done first in conversation. **Still to do:** the formal **puzzle ladder +
engineered dataset** (`escape_room_puzzles`), mirroring henges's ladder shape on the clouds dataset;
then scenes/`scenario.json` (`escape_room_design`); then art; then wiring. **Nothing is built yet.**

---

## Analog grounding (Step 0 — the real-world act the code performs)

**PCA = finding the direction (vantage) along which a cloud of things spreads out the most, then reading
which measured traits that spread is made of.** In `clouds` this is made literal:

- The **alien city below is the data cloud.** Each **district** is a data point. Each district is
  measured on several visible architectural attributes (**height, colour, brightness, + a 4th** — TBD;
  see dataset).
- **Flying the plane = choosing a projection.** Your **heading (compass bearing) is the projection
  direction.** A principal component *is* a direction and a heading *is* a direction, so "PC1 lies along
  bearing X°" is literally true. From most bearings the city collapses into an overlapping muddle (low
  spread); from a couple of special bearings it stretches out longest — those are the principal axes.
- **PC2 ⊥ PC1 = a 90° difference in heading**, so orthogonality is felt physically (the two principal
  bearings are a quarter-turn apart). The compass readout can be shown to reinforce this (Lucas unsure if
  distracting — keep it visible but subtle, not a required input).
- **High-dimensional via the cloud-lens conceit (Lucas: keep it high-D, 3D is too simple).** Each cloud
  aperture is an alien lens that maps the districts' *many* attributes down onto the 2-D tableau you see
  below — i.e. each view is a linear combination of attributes (a real projection in feature space), not
  just "a 3-D object seen from an angle."
- **Loadings are visible in the world.** Along a principal-component view the districts sort by the
  feature(s) that drive that axis — e.g. tall buildings toward the back, glowing buildings toward the
  front. "What is this axis made of?" = reading a loading, straight off the art.

The escape's recognition move (data-free, below) is **reconstructing the correlation structure of the
attributes by reading the two principal-component views = reading a biplot** (variables pointing the same
way are positively correlated, opposite = anti-correlated, at right angles = uncorrelated). This is a
real, taught PCA skill, not a metaphor for one.

---

## World / premise (STORY phase — settled with Lucas 2026-08-04)

- **Setting.** A small **open-cockpit aeroplane** flying above a **permanent cloud-sea**, in golden light
  with shafts / rays of sun. The alien city is **on the ground — NOT floating**: its towers rise through
  the cloud so that only upper floors and spires break the surface, an archipelago of skyscraper-tops
  peeking through gold cloud. (Nothing floats but the cloud itself.)
- **Why the player is up there — concrete (revised 2026-08-04).** From the ground you are *inside* the
  cloud: at street level you can only ever see the nearest tower or two, so the city's overall grain — the
  directions along which it's organised — is **invisible below the cloud and only resolves from above it**.
  The pattern exists; you just can't see it until you're over the cloud-sea, sighting along the right
  headings. (Replaces the earlier vague "no one has ever read it from the ground".)
- **Why the override dial sleeps — concrete (Lucas, 2026-08-04).** These are **alien planes — the only
  craft that fly here** — and their builders keyed them to the city. The **ring-current holds every plane
  until its pilot has read the city's grain**; only then does the craft *wake* and permit departure. The
  sleeping override is an **intentional lock, not a malfunction** — and it's why the derelict planes still
  circle: their pilots never read the city, so their planes never woke.
- **The cloud microbial gardens (Lucas's touch — keep it).** Each district's patch of the cloud-sea is a
  living **cloud-garden**, and its microbial/chemical makeup is a **readout of the district beneath**. The
  player **samples the cloud-gardens** (the graded WebR data); PCA of those samples recovers the same axes
  the city's tower-tops visibly spread along — the R analysis and the cockpit view, two faces of one
  structure.
- **Layout — a big ring, travel DECOUPLED from solving (Lucas, 2026-08-04).** The player flies a **large
  circle** of cloud-aperture view-rooms, each sighting the city down a different heading (same city,
  different projection). **The graded puzzles are NOT room-bound:** a single **console hotspot in the
  cockpit serves the four analyses in series, up the ladder, on each click** — so the player can solve the
  whole survey from one position, then still has to **explore the ring to escape**. Traversal enforces
  nothing; the ladder order is enforced by the console's series. Matches the open-world model (roam freely,
  order the puzzles not the doors). **Engine note:** console-serves-puzzles-in-series is the parked
  "dynamic puzzle queue" idea (`escape_rooms/AGENTS.md`) — **needs a small new engine feature**, and a
  **codec rethink** (four graded puzzles at one location vs the current one-slot-per-built-room model).
  Flagged for the DESIGN/engine phase.

### Environmental arc — SPATIAL, not temporal (resolves the ring/backtracking problem)

The ring allows constant backtracking/looping, so a **temporal** day→night arc breaks (loop the other
way and time runs backwards — Lucas flagged this; it's also the project's canon lesson: arcs should be
**place-constant, not per-room temporal**). Decision:

- **Tier 1 (start here, zero engine).** Give each *place* a **constant** character — one district under a
  low shaft of sun, one in cloud-shadow, one lit from below by its glowing cloud-garden, etc. Fixed per
  place, so circling never contradicts itself; still delivers varied rays-of-sun vibes.
- **Tier 2 (only if needed).** A genuine sunset clock would have to be a **global tint overlay driven by
  progress** (puzzles solved), not by position — so a revisited room always shows the *current* hour.
  Defer unless the spatial variety doesn't carry the mood.

---

## The escape (data-free meta-echo of the boss — settled 2026-08-04)

**The action — reconstruct the correlation structure (Lucas's mechanic; it's the best one available).**
A **correlation panel** on the plane: the **lower triangle** of a matrix of the **4 building attributes —
height, glow, hue, spires** (6 tiles). Each tile cycles through **three states — flat line / up-slope /
down-slope** (uncorrelated / positively correlated / anti-correlated); **all start flat**. The player
flies the ring, studies how each attribute stretches across the **two principal-component views**, and
fills the triangle in accordingly. This is *reading the biplot* — reconstructing the covariance structure
PCA is built from. **Engineering note:** the existing engine `grid` hotspot is one-choice-per-row, NOT a
triangular matrix of 3-state cells — so this panel is a **small new widget**, buildable but not free.
**The escape is NOT numerically connected to the puzzle dataset (Lucas, 2026-08-04).** The four
architecture attributes and their correlations are **authored world-furniture** — the city views are drawn
to embody a chosen correlation structure, which the player reads off the *art*, not off any column in the
puzzle CSV. Data/puzzles and art/escape are **echoes of each other, not linked numbers.** (So there is no
"PC3 must be negligible in the data" constraint — that only mattered under an earlier, discarded idea of
tying the panel to real properties; the constraint is on the ART showing a consistent two-axis reading,
not on the data.)

**Why it's decoupled from the puzzles (Lucas's key correction).** "Read the city" IS the puzzle content;
the escape's *reward* must cash out elsewhere. So the correlation panel is only the **key** — what it
**unlocks** is pure story (below), unrelated to whether you understand the city.

**The reward — break the alien ring trap, then up and out (settled: Lucas "Alien ring trap then up and
out! Love it").** You're not flying a circle by choice — you're **trapped** in it by a **standing
ring-current** the city's builders raised over their sky; bank whichever way you like and it curls you
back. (That's *why* the level is a ring, and the player literally feels it by looping.) The plane's
**flight-override panel has been DORMANT the whole flight** — it can't be keyed until the survey is done
and the Eye opens (see the finale flow in the **## Narrative → Escape** section, which is authoritative).
Keying the correlation structure there **wakes the plane properly**, the current lets go, and the player
**climbs up and out through the Eye into the open sunset** — *away from* the city, not down into it.

- **Thin diegetic thread (so the panel isn't arbitrary).** The alien plane's override is **keyed to the
  city's own hidden signature — its correlation structure** (its builders locked their sky this way). So
  reproducing that signature wakes your craft. This is why the escape *looks* like PCA (the aliens key
  their locks to the same structure you've been reading) without the reward being comprehension.
- **Trap flavour — RESOLVED: a standing ring-current** (an alien airspace lock manifested as a perpetual
  updraft ring). No storm, no floating city.
- **Motivation** is the plainest kind: you're stuck; everyone wants to get unstuck. No comprehension
  required to feel the pull. And it turns the ring topology's weakness (looping/backtracking) into the
  point (the loop is the trap; the escape is release from it).

---

## Dataset decision (2026-08-04, Lucas)

**ENGINEER a bespoke dataset** (not a real one; not `wine_grape_data`). Reviewed the `exercises.csv` PCA
options first: `metabolomics_data` (kidney, marker on Dim.1) and `wine_grape_data` (Cabernet, marker on
Dim.2 — a natural PC1-trap). Chose to engineer for control over the trap, single-winner margins, and the
cloud-garden theme — same rationale as henges. **Hard constraint: must NOT read as henges's
`druid_ingredients` reskinned.** Deliberately vary from henges: different **property count** (henges = 9),
different **group structure / number of kinds** (henges = beetles/mushrooms/herbs/roots, 225 rows),
different **trap group** (henges = mushrooms hide on PC2), different **variance profile & margins**, and a
cloud-garden-native variable vocabulary. Same *ladder shape* is fine (that's the pairing); the numbers,
groups, and feel must be its own.

## PUZZLE-PHASE OUTPUT — verified ladder + dataset (2026-08-04) ✅

### Dataset (finalized)
- **File:** `rooms/dimensionality_reduction/clouds/data/cloud_gardens.csv` — **212 blooms × 7 properties**,
  5 districts (foundry 44, spire 38, archive 41, market 47, cistern 42).
- **Columns:** `bloom` (unique name), `district` (group), + 7 numeric properties: `spore_density`,
  `moisture_uptake`, `nectar_sugar`, `acidity`, `filament_length`, `pigment_load`, `drift_speed`.
- **Generator (deterministic, seed 20260804):** `_scratch/build_cloud_gardens.py` — runs from any CWD,
  rewrites the CSV, prints full verification, and **asserts** every rung's single-winner + margin and the
  trap. Re-run to re-verify.
- **Public URL (after Mac push):**
  `https://thebustalab.github.io/escape_rooms/rooms/dimensionality_reduction/clouds/data/cloud_gardens.csv`
- **How it's built:** two decoupled latent factors → PC1 = an "energy" cluster (`filament_length` strong,
  + `spore_density`/`drift_speed`/`nectar_sugar`); PC2 = a "chemistry" cluster (`acidity` strong,
  + `pigment_load`/`moisture_uptake`). Foundry districts max the energy factor (own PC1); **archive
  districts sit mid-pack on PC1 but max the chemistry factor (separate on PC2)** — the taught trap.
- **PCA verified FactoMineR-style with variance SCALED** (matches phylochemistry `scale_variance=TRUE`
  default for PCA): scores = `X_std @ V`; loadings = corr(property, PC) ∈ [−1,1]; variance = eigenvalue/p.

### The verified ladder (reverse-engineered from the boss; tracks the book's scores → scree → loadings → marker)

| Room | Book step | Analysis (`runMatrixAnalysis`) | Verified answer | Margin | New move |
|------|-----------|-------------------------------|-----------------|--------|----------|
| **1 — scores** | scores plot (`pca`) | on the scores plot, which single **bloom** sits farthest out along the greatest-spread axis (PC1)? | **Emberbloom-01** (foundry), \|PC1\|=4.71 | +14.4% vs Emberbloom-05 (4.12) | read a scores plot; find the PC1 extreme |
| **2 — scree** | variance explained (`pca_dim`) | how much of the total variation does **PC1** capture? | **PC1 = 44.2%** (PC2 = 30.4%, PC1+PC2 = 74.5%) | vs PC2 30.4%, PC3 8.3% | quantify & compare spread *across* components |
| **3 — loadings** | ordination (`pca_ord`) | which measured **property** contributes most to PC1? | **filament_length** (\|PC1 loading\|=0.945) | +8.0% vs spore_density (0.875) | from samples to *variables* — read a loading |
| **Boss — marker + trap** | scores + ordination | which property best distinguishes the **archive** districts from every other district? | **acidity** (PC2 loading 0.904; archive-vs-rest gap 1.90) | +10.7% (loading) / +39.2% (gap) vs pigment_load | find *which axis* separates a group (PC2, not PC1), then read *that* axis's driver |

**Strictly monotonic**, each rung adds exactly one move. **≥6 distractors:** rooms 3 + boss are MCQs over
the 7 properties (6 wrong each); room 1 has 211 non-winner blooms; room 2 gets wrong-% distractors.

### The taught trap (boss) — PC1-fixation
Rooms 1–3 all drill **PC1** (extreme bloom, its % , its driver = filament_length). The boss asks for the
**archive** marker — but archive is **dead mid-pack on PC1** (archive mean PC1 = 0.27; foundry owns PC1 at
−2.16). Archive separates only on **PC2** (archive mean PC2 = 2.08), whose driver is **acidity**. The
tempting-wrong answer is `filament_length` (the PC1 star) — whose **archive-vs-rest gap is just 0.08**,
i.e. useless for spotting archive. Taught via wording ("distinguishes archive from all others") + a clue
about looking beyond the first axis, never hidden.

### Boss's core cognitive move (SEED for the escape — do NOT design the escape here)
*"A group can be invisible on the biggest axis and only show up on a smaller one — find the right axis for
the group, then read what that axis is made of."* The already-sketched escape (ring-trap + correlation
panel, in the escape section above) is the **story-phase** payoff and stays data-free/decoupled.

### Puzzle types (variety)
Room 1 = **pick** (plot-and-click on the scores plot: build it, click the extreme bloom) · Room 2 = **MCQ**
(scree %) · Room 3 = **MCQ** (loadings) · Boss = **MCQ** (loadings on PC2) · Escape = **grid** correlation
panel (the new 3-state lower-triangle widget — flagged as unbuilt).

### Judgement calls / engineered departures (flagged for Lucas)
- **Fully synthetic dataset** — no real-world source; engineered for a clean, escalating, single-winner
  ladder + the PC1-trap (same rationale as henges, structurally distinct data).
- **Planted "beacon" bloom** (`Emberbloom-01`): its noise on the three PC1 properties is zeroed so it's an
  unambiguous Room-1 winner rather than relying on a lucky random draw.
- **Verified via a Python re-implementation** of FactoMineR-style scaled PCA, not R. Orderings/margins are
  robust to scaling constants, but **reconfirm the exact values in WebR** (`runMatrixAnalysis`) during
  wiring — standard practice.

## Narrative (STORY phase — 2026-08-04)

### Logline · stakes · clock
- **Logline.** A pilot in a borrowed alien plane, caught in the ring-current that seals the sky over a
  vast, cloud-drowned city, must read the city's two hidden axes — visible only from above the cloud — to
  wake the plane's override and climb out into open sky before the light fails.
- **Stakes (concrete, not "you're trapped").** You are held in a **standing ring-current** — an alien
  airspace lock raised as a perpetual updraft ring; bank whichever way you like and it carries you back
  round. The one control that could release you, the cockpit **override dial**, is dark: it is keyed to
  the city's own hidden structure, and until you've charted that structure it stays dead. You are **not
  the first** — other planes drift the ring too, silent, long empty. Read the city, or join them.
- **Clock.** The low sun. You can only read the city while the light rakes across it; as it sinks the
  grain of the streets flattens into shadow. **(Realised SPATIALLY, not temporally — see arc below.)**

### World, from the analog
PCA = *find the heading from which a cloud of things spreads out the most, then read which trait that
spread is made of.* The world makes it literal: a **pilot charting a city whose grain resolves only from
above the cloud**, along the right headings. The city stands **on the ground**, its towers rising through
a permanent cloud-sea so only the upper floors and spires break the surface; each district's patch of that
cloud-sea is a living **cloud-garden** whose makeup reads out the district beneath — so the pilot
**samples the cloud-gardens** (the graded WebR data) to chart the city. **You fly an alien plane (the only
craft that flies here); its override is keyed to the city and won't wake until the survey is read** — the
in-world reason the dial sleeps and the derelicts still circle.

- **Cast — ZERO named living characters.** The goal is front-loaded in the opening (chart the axes → wake
  the override → break the ring), so no character need explain the mechanic. The only "characters" are
  **traces**: the dead override on your own dash, and the silent derelict planes circling with you (a
  motif, not people — honours the house "no people in the art" rule; they're objects/stakes).
- **Landmarks (real-feeling + fantastical).** The five districts read as distinct places far below —
  **the foundry quarter** (lit from within by furnace-glow), **the spires**, **the still archive**, **the
  teeming market**, **the mirrored cisterns**. The ring you're trapped on has a calm centre: **the Eye** —
  a column of gold light punching straight up through the cloud, over the city's true centre.
- **Escape sited at a landmark (earned visit).** The **Eye is the finale.** It is literally the city's
  **centroid** — a quiet PCA nod: PCA centres the data before it finds axes, so the way out sits at the
  mean. The Eye only opens once the survey is charted; you fly in off the ring, wake the override there,
  and climb the gold column out.
- **Signature travel mechanic.** You don't power between rooms — you **ride the ring-current itself**,
  slipping from one cloud-aperture to the next on the very wind that traps you (the thing carrying you is
  the thing holding you). Each aperture is a chamber in the cloud that frames the city down a different
  **heading** (the compass reads it; the two principal headings sit 90° apart — a subtle, non-required
  orthogonality cue, kept visible).
- **Environmental arc — SPATIAL, place-constant (deliberate deviation, flagged).** A temporal day→night
  arc breaks on a ring (loop back and time runs backward). So each place gets a **constant** light
  character under one steady low gold sun: foundry lit from below, archive in cool cloud-shadow, spires
  catching the high rake, market warm and hazy, cisterns pale and misted. The **clock rides in the text**
  (Tier 1, zero engine). *Optional Tier 2 (design's call): a global tint driven by PROGRESS — the gold
  deepens toward ember as rooms are solved — backtrack-safe because it keys on state, not position.*

### Beats (one per graded rung — why the pilot runs THIS analysis now)
*Delivery (Lucas, 2026-08-04): the four graded analyses are served **from the cockpit console in series**,
up the ladder, on each click — NOT one-per-room. The player can chart the whole survey from a single
position; the ring rooms are ungraded **view-rooms** (atmosphere + the principal-heading views the escape
reads). So the beats below are the console's series, and the "rooms" they name are narrative framing, not
where the puzzle lives.*
- **Step 1 — scores (first fix on the grain).** Newly aware you're trapped and the override's dead, you
  take your first cloud-garden reading and run the scores plot to find the city's strongest direction of
  variation — the single most **extreme bloom** (Emberbloom-01) marks it. Your first bearing on the grain.
- **Room 2 — scree (how much that grain is worth).** Is one heading enough? Read the scree: PC1 carries
  **44%** of the city's order — nearly half, but not all. There is a second axis worth finding; the
  override will need both.
- **Room 3 — loadings (what the grain is made of).** You read the loadings to name the main axis:
  **filament_length** drives PC1. Now you can read the first axis straight off the architecture — and
  you're tempted to think the whole city yields to it.
- **Boss — the archive marker (misdirection = the taught trap).** The override needs the districts pinned,
  and the **archive** quarter resists. The tempting move is to read it off the main grain you just
  mastered (filament) — but **archive is dead mid-pack on PC1, invisible there**. Only the *second* axis
  reveals it: its marker is **acidity** (PC2). Finding the axis a group hides on, then reading it — the
  survey's last and hardest fix. With it, the city's grain lies fully charted.

### Escape (the payoff — data-free meta-echo, designed HERE)
**The finale flow (Lucas, 2026-08-04):**
1. **Charting the survey (all four console analyses solved) opens the Eye** — a column of gold light at the
   ring's calm centre (the city's centroid). **Every ring view-room gains a secret door onto it**, so the
   player can enter the pillar from wherever they are.
2. **Click into the pillar of light** → this is what **activates the override panel** that has slept in the
   cockpit the entire flight. (Until the Eye opens, tapping the panel does nothing — it's dormant by
   design, the alien-plane lock.)
3. **The panel = the correlation puzzle.** The **lower triangle of the city's four visible building
   attributes — height, glow, hue, spires** (6 tiles). Each tile cycles **flat / up-slope / down-slope**
   (uncorrelated / positively / anti-correlated), all starting flat. Flying the ring you *saw* how these
   stretched across the two principal-heading views — tall towers ran with bright ones, hue ran against
   height, spires held independent — and now you **reconstruct that correlation structure from memory of
   the views**. This is the boss's cognitive move (*something can hide on the big axis and only show on
   another; find the right axis and read what it's made of*) re-posed on **in-world architecture, wholly
   decoupled from the cloud-garden data** — recognition, no dataset values. **The authored attribute
   correlations are world-furniture, chosen in design/wiring; they are NOT the puzzle numbers.**
4. **Keying it correctly WAKES THE PLANE properly** — the alien craft finally comes fully alive.
5. **Player-performed release (ceremonial gesture).** The pilot then **pulls the woken override dial /
   opens the throttle** — one control, one motion — and the plane breaks the ring-current and **climbs the
   gold column up and out**, over the cloud-tops into the open sunset. Their own hand on the release.

**Engine note:** the panel is the new 3-state lower-triangle `grid` widget (unbuilt); its **`availableWhen`
gates on the Eye being entered** (survey complete + pillar clicked), and it carries `endsEscape`. Flag for
design/wiring.

### Draft story-map text (paste into harness story-map; tighten there)
- **title:** *Where the City Opens*
- **subtitle:** *A cloud-drowned city, and a borrowed plane that won't leave until you've read it.*
- **story (landing):** *The ring-current has you. However you bank, the wind curls you back over the same
  vast city — towers and terraces half-drowned in gold cloud, only their upper floors breaking the surface.
  Down in the streets you'd see nothing but the nearest tower; the shape of the whole place shows only from
  up here, along the right headings — if you can find them. Others drift the ring with you, silent, their
  cockpits long empty; their planes never read the city either, so they never woke. The one dial that might
  free yours sits dark on the dash. You have the light of one low sun. Sample the cloud-gardens, chart the
  two axes, wake the plane, and climb out.*
- **room 1 entry:** *The current slips you into a gap in the cloud. Below, the city runs off toward one
  far horizon more than any other — a grain to it. Take a reading and find its farthest edge.*
- **room 2 entry:** *One heading, and already half the city falls into line. But only half. Read how much
  this grain is worth — and whether a second axis waits.*
- **room 3 entry:** *A direction is not enough; you need to know what it's made of. Read the grain: which
  trait of the gardens the great axis truly follows.*
- **boss entry:** *The override wants every quarter pinned, and the still archive will not sit on the grain
  you've mastered — look for it there and it vanishes into the crowd. Find the other axis. Read what sets
  the archive apart.*
- **done (analysis complete):** *Both axes charted; the city's grain lies open beneath you. On the dash,
  the dead dial stirs — and dead ahead, the cloud parts on a column of gold: the Eye of the ring.*
- **escapeDone (escaped):** *The current lets go. You pull up into the gold column and the ring falls away
  beneath you — the city, the silent drifting planes, all of it sinking into cloud as you climb out at
  last into open, endless sun.*

### Voice notes
Earnest, cinematic, spare. Sensory anchors: raking gold light, the pull of the current, the silent
derelicts, the dead dial. No jokes, no winks. Cards short (2–3 sentences). Mood: lonely wonder, held
tension, release — matched to the golden above-the-cloud palette.

### Judgement calls flagged (STORY phase)
- **Concrete premise (Lucas, 2026-08-04):** the city is **on the ground under a permanent cloud-sea**
  (towers peek through — NOT floating); its grain is invisible at street level and resolves only from
  above. You fly an **alien plane** (only craft that flies here); its override is an **intentional lock**
  keyed to the city, so it stays dormant until the survey is read — this is why the dial sleeps and the
  derelicts still circle. (Replaces the earlier vague "no one has read it from the ground".)
- **Puzzle delivery: a cockpit CONSOLE serves the 4 graded analyses in series (Lucas, 2026-08-04)** —
  not one-per-room. Travel is fully **decoupled** from solving: the player can chart the whole survey from
  one seat, then must **explore the ring to escape**. Ring rooms become ungraded **view-rooms**. ⚠️ Needs
  the engine's parked **"dynamic puzzle queue"** feature AND a **codec rethink** (4 graded puzzles at one
  location vs one-slot-per-room). **Flagged for DESIGN/engine.**
- **Finale flow (Lucas, 2026-08-04):** survey complete → **the Eye opens** (gold column at the ring's
  centre = the data **centroid**); **every ring room gets a secret door onto it**; **clicking into the
  pillar activates the override panel** that slept all flight; solving the correlation panel **wakes the
  plane**, then the player pulls the dial to climb out. Flag the **topology** (secret doors from each ring
  room onto one central node) for `escape_room_design`.
- **Environmental arc made SPATIAL, not temporal** — deliberate, to survive ring backtracking; clock
  carried in text (Tier 1). Tier 2 progress-driven global tint offered to design as optional.
- **Escape resolved to 4 attributes / 6-tile lower triangle** (height, glow, hue, spires); **compass/
  heading readout kept visible but non-required** (orthogonality cue); **trap flavour = a standing
  ring-current**.
- **Derelict-planes motif** used for stakes — objects, not people (house rule safe). Confirm the tone
  sits right with Lucas.

## DESIGN REVISION (2026-08-04, Lucas) — commit engine work + bigger ring + exploration energy

Lucas's calls after the first design pass:
- **Commit the new engine work** (console-serial + grid + Eye/pillar) — do NOT take the buildable-now
  open-world fork. Rationale (his): the fork's room-to-room energy is just "next puzzle behind next door",
  a corridor in open-world costume. The console frees movement to mean something better.
- **The exploration energy = discovering the headings themselves.** You solve the 4 analyses from your
  seat, but the city **only opens along ~2 of many headings** — so you must fly the whole ring to discover
  which, and read the grain off them. Finding the principal components by hunting the compass IS the game.
- **Bigger ring (else too easy).** With 3 views there's nothing to discover; with a big circle most
  headings give a **muddle**, a couple **half-resolve**, and only **two truly open** the city (90° apart).
  The hunt gains teeth, and the escape gets richer.
- **The Eye is reachable ONLY via the two OPENER apertures' pillars (Lucas, 2026-08-04 refinement).**
  You reach the city's centre (the centroid) only by flying IN along a heading that opened the city — a
  principal axis through the centroid, geometrically true to PCA. This makes identifying the two axes an
  **enacted recognition** (fly an opener in) rather than a menu pick — so the separate "pick-two" escape
  beat is **DROPPED**. The muddle/half-light pillars never open (the half-light is the hard near-miss).
  Escape at the Eye is now **one beat**: the correlation panel (which needs readings from BOTH openers, so
  both must have been visited) → release gesture. Net: one fewer new widget.

### Revised room set — 8 rooms (7 in the circle + the Eye)
Ring (open doors between neighbours): **`cockpit`** (the solve seat: 4-in-series console + dead dial +
compass) + **6 view-apertures** around the compass:
- `ap_grainrun` — **OPENER (PC1)**: city runs long, foundry blazing at the far end. compass ~034°.
- `ap_stillstand` — **OPENER (PC2)**: archive quarter stands apart. compass ~124° (90° from grainrun).
- `ap_pileup` — **muddle** (towers piled, no grain). ~070°.
- `ap_smear` — **muddle**. ~160°.
- `ap_halflight` — **half-resolves** (partial grain — teaches it's a spectrum, max at the openers). ~205°.
- `ap_backwind` — **near-muddle**; the **derelict planes** drift here (stakes motif). ~285°.
Then **`eye`** (the two-beat escape), reached by a pillar door from every ring room once the 4 console
puzzles are solved. Art cost: **8 new scenes** — tunable (muddles could be trimmed); Lucas can dial.

## DESIGN-PHASE OUTPUT — scenes + scenario.json (2026-08-04; REVISED to 8 rooms)

`scenario.json` written (id 16, all rooms `built:false` stubs with scene prompts, designNotes,
plannedHotspots). It parses. **Not for the art harness yet** — engine work below comes first. **Console
model CHOSEN (no fork).** Ring expanded to 6 apertures + cockpit + Eye (see revision above).

### Rooms (8) + topology
Room list is in **DESIGN REVISION** above (cockpit + 6 apertures + eye). In brief:
- **`cockpit`** (start) — the solve seat: **survey CONSOLE = all 4 graded puzzles in series**, the **dead
  override dial** (foreshadow), the **compass** (orthogonality cue). `deliverable.submitCodec`. Open gaps
  to `ap_grainrun` + `ap_backwind`.
- **6 view-apertures** — ungraded; each a heading round the compass: `ap_grainrun` (OPENER PC1),
  `ap_stillstand` (OPENER PC2, archive apart), `ap_pileup`/`ap_smear`/`ap_backwind` (muddles;
  backwind carries the derelicts), `ap_halflight` (half-resolve near-miss). The openers carry the
  escape-reading clues.
- **`eye`** — the **one-beat ESCAPE**: the correlation panel → `endsEscape` → throttle **release gesture**
  → climb out. Reached by a pillar door **ONLY from the two openers** (`ap_grainrun`, `ap_stillstand`),
  `availableWhen` the 4 console puzzles solved — flying an opener in IS the axis-recognition.
- **Topology:** open ring circle `cockpit–ap_grainrun–ap_pileup–ap_stillstand–ap_halflight–ap_smear–
  ap_backwind–cockpit` (all doors `open`, `unlockedWhen:true`); a **pillar `forward` door to `eye` ONLY in
  the two openers** `ap_grainrun` (~034°) + `ap_stillstand` (~124°, non-adjacent + 90° apart),
  `availableWhen` the 4 console puzzles solved. Travel fully decoupled from solving.

### Environmental arc (per-room, SPATIAL / place-constant — no temporal drift)
One steady low **gold sun** throughout; each place its own constant light, and the **sun angle shifts by
heading** (spatial, not time — backtrack-safe): cockpit warm dash-glow; grain-run furnace-amber at the far
end; still-stand cooler cross-light on the pale archive; pileup/smear thicker gold haze; backwind mournful
gold with the drifting derelicts; half-light an in-between; eye a radiant vertical column of gold.

### Palette divergence (flagged)
House default is dusk/night teal-amber; **clouds is golden DAYLIGHT above the cloud** (like the bright
hospital scenario, not Alaska's dusk). Kept the **single warm-amber glow** signature + icy-blue
cloud-shadow so it still reads as one series. Deliberate; confirm with Lucas.

### ⚠️ ENGINE WORK REQUIRED — before art/wiring (clouds outruns the current engine; CONFIRMED to build)
Fork REJECTED (Lucas): build these, don't fall back to open-world puzzle-per-room.
1. **Console-serves-4-puzzles-in-series.** The parked **"dynamic puzzle queue"** idea
   (`escape_rooms/AGENTS.md`). Realisation encoded here = **4 `availableWhen`-chained puzzle hotspots in
   the cockpit** + `lockedBody`. BUT the **codec mints one slot per built ROOM**, so 4 graded puzzles in
   one room aren't scored per-puzzle. **Decision needed:** (a) extend the codec to per-gate (`gateKey`)
   scoring, or (b) accept cockpit = 1 codec slot and lean on the **submission PDF** (captures each graded
   puzzle's code + figure regardless). Also `isBoss`/`deliverable` are room-level — the "boss" is the 4th
   console puzzle, not a room; `deliverable` parked on the cockpit room.
2. **ONE new escape widget: the 3-state lower-triangle correlation GRID** — 6 tiles each cycling
   flat/up/down vs an answer map; ungraded; fires `endsEscape`. (Engine `grid` is one-choice-per-row →
   genuinely new.) *(The pick-two widget was dropped — see item 3: axis-recognition is enacted by
   traversal.)*
3. **Eye / pillar activation, opener-only.** A `forward` pillar door to the central `eye` node exists
   **ONLY in the two opener apertures** (`ap_grainrun`, `ap_stillstand`), `availableWhen:{allSolved:[the 4
   console gates]}`; the muddle/half-light rooms have NO pillar (their cloud never parts). Entering `eye`
   activates the dormant panel. Doable with existing `availableWhen`+state, but the **two-nodes→one-node**
   topology + dormant-until-entered panel should be confirmed against the engine.

### Escape — one data-free beat (authored world-furniture — NOT dataset numbers)
Axis-recognition is ENACTED by traversal (the Eye is reachable only via an opener pillar), so there is no
pick-two beat. At the Eye:
- **Correlation panel (6 tiles, height/glow/hue/spires):** height~glow **UP**, height~hue **DOWN**,
  height~spires **FLAT**, glow~hue **DOWN**, glow~spires **FLAT**, hue~spires **FLAT**. (A 2-factor
  structure — height/glow/hue on one axis, spires independent — the opener-aperture art must depict
  consistently; **split the readings across `ap_grainrun` + `ap_stillstand` so BOTH must be visited**.
  Final art-correlation lock in wiring.) → `endsEscape` → throttle release gesture.

### Judgement calls flagged (DESIGN phase)
- **Console-in-cockpit vision CHOSEN (fork rejected, Lucas 2026-08-04)** — commit the new engine work.
  Rationale: the buildable-now open-world fork's room-to-room energy is a corridor; the console frees
  movement to be *exploration* (hunt the opening headings). See DESIGN REVISION.
- **Ring enlarged to 6 apertures** (was 3) so the axis-hunt has teeth (Lucas: "otherwise too easy").
- **Eye reachable ONLY via the two opener pillars (Lucas, 2026-08-04)** — reaching the centroid along a
  principal axis; axis-recognition is enacted by traversal, so the pick-two beat was dropped (one fewer
  widget, stronger recognition). The half-light's non-opening pillar is a deliberate hard near-miss.
- **Cover prompt** drafted (biplane over a gold cloud-sea). **Music** not yet chosen.
- **Debrief** authored (top-level + per-room, all 8).

## Open decisions / next steps

- [x] **Puzzle ladder + engineered dataset** — DONE (above), all answers verified single-winner + trap.
- [x] **DESIGN phase** — DONE: `scenario.json` stubs + scenes + escape; engine-work + palette + the
      console-vs-open-world fork flagged above for Lucas.
- [x] **STORY phase** — DONE (Narrative above): world, stakes, clock, landmarks, travel, arc, beats,
      data-free escape + ceremonial release, and draft story-map text. Earlier open decisions (compass,
      trap flavour, panel attribute count, env-arc tier) resolved in the Narrative's judgement-calls.
- [ ] **NEXT: ENGINE WORK** (before art) — resolve the three items in *DESIGN-PHASE OUTPUT → Engine work
      required*: (1) console-serves-4-in-series + codec-per-gate vs submission-PDF decision (or take the
      buildable-now fork); (2) the 3-state lower-triangle correlation `grid` widget; (3) Eye/pillar
      activation of the dormant panel. **Lucas to weigh the console-vs-open-world fork first.**
- [ ] Add scenario **id 16** to `decoder/decode_codes.R` when scaffolded.
- [ ] **ART** (`:8751` harness, Lucas) — all 5 rooms need NEW art (none reuse a prompt).
- [ ] **WIRING phase** (`escape_room_wiring`, post-art) — MCQ/clue text, sfx, the authored building-
      attribute correlations for the panel, decoder lockstep, `test_clouds.py`.

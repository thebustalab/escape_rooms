---
authority: intent
---

# Escape-room puzzle design — resources, mechanics, and worked examples

**Status:** intent / design notes. Started 2026-07-17 (explorations session). Not yet built —
this is a menu of directions, grounded in the two live `data_vis` scenarios (Alaska, Hawai‘i),
for making the puzzles feel more like *Myst/Riven* investigations than one-shot MCQs. Sits
alongside `puzzle_types_design_notes.md` (the three console puzzle *types*: Compute-the-Key,
Classify-the-Unknown, Repair-the-Pipeline) — that file is the engine-primitive spec; this file
is the design philosophy + mechanics + concrete examples.

**Learning goal is fixed:** every puzzle must still teach real data analysis (filter / group /
plot / threshold / reason). The mechanics below are wrappers that change how the analysis *feels*,
not substitutes for it. The standing warning from the education literature (Room2Educ8): narrative
should motivate, never overshadow the objective — it's easy to over-egg the atmosphere and lose the
data.

---

## The one idea worth stealing from Myst/Riven

Their puzzles aren't brain-teasers bolted onto a world — the puzzle **is** interacting with the
world's own logic, and the clues are deliberately **incomplete**: the better you understand the
place, the more it reveals. Riven teaches you a base-5 number system just by living in it.

For us, **the dataset is the world.** Right now our puzzles go: here's a question → run code →
pick the conclusion. The dataset is a means to an answer. The Myst move flips it: make the dataset
the environment the student *interrogates*, where the answer only emerges because they actually
explored it, and where the scene + story tell them *which* analysis to run but never hand them the
method. Same objective, completely different feel.

---

## Resources (full references — look these up later)

**Puzzle design craft**
- Ron Gilbert — *Puzzle Dependency Charts* (Grumpy Gamer). The practical design tool: map every
  puzzle as a graph; keep it "bushy" (solving one thing opens two or three, which then converge).
  It's how you'd move from our strict room-chain to real branching, and it doubles as a planning
  artefact for the `scenario.json` room graph.
  https://grumpygamer.com/puzzle_dependency_charts/
- *Puzzle Dependency Graph Primer* — Game Developer.
  https://www.gamedeveloper.com/design/puzzle-dependency-graph-primer
- *Analysis: Puzzle Design in the Myst Series* — Game Developer.
  https://www.gamedeveloper.com/design/analysis-puzzle-design-in-the-i-myst-i-series
- *Riven — Immersion through Integrated Puzzle Design*.
  https://experiencedmachine.wordpress.com/2023/03/04/riven-immersion-through-puzzles/
- Falstein et al. — *The Key to Adventure Game Design* (MIT open access PDF). Puzzles should push
  the player to explore and connect, not stare at one static screen.
  https://dspace.mit.edu/bitstream/handle/1721.1/100238/The%20key%20to%20adventure.pdf?sequence=1

**Escape-room mechanics + education research**
- *Puzzles Unpuzzled: Towards a Unified Taxonomy for Analog and Digital Escape Room Games* —
  ACM CHI PLAY (2021). An atomic taxonomy of puzzle mechanics from analysing 39 real rooms; use it
  as a menu to shop from rather than inventing mechanics cold. https://dl.acm.org/doi/10.1145/3474696
- *Design, implementation, and student feedback on a numerical-themed escape room for a data
  analytics subject* — Emerald, *Interactive Technology and Smart Education* (2025). Near-exact
  precedent: a data-analytics escape room for a stats course, with what worked + student feedback.
  https://doi.org/10.1108/ITSE-01-2025-0024
- *Room2Educ8: A Framework for Creating Educational Escape Rooms Based on Design Thinking
  Principles* — MDPI *Education Sciences* (2022, open access). Learner-centred design heuristics;
  source of the "narrative motivates, never overshadows" rule.
  https://www.mdpi.com/2227-7102/12/11/768
- *Escape rooms for learning programming: a systematic literature review* — Ugo, *Review of
  Education*, Wiley (2025). https://bera-journals.onlinelibrary.wiley.com/doi/full/10.1002/rev3.70123
- *A learning analytics perspective on educational escape rooms* — Taylor & Francis (2022).
  https://www.tandfonline.com/doi/full/10.1080/10494820.2022.2041045

**Walkable "world-model" scenes (separate exploration, same session)** — full write-up is in
`AGENTS.md` → Known follow-ups ("Walkable world-model scenes"). Short version: to move from
look-around-from-one-spot to *walking through* a continuous space, real Google Street View is the
wrong tool (real places only, API cost) and stitched AI panoramas hit a continuity problem
(similar-but-disjoint bubbles). The real answer is the current world-model generators that build
ONE continuous explorable 3D volume as **Gaussian splats**, browser-rendered via Three.js —
**World Labs' Marble**, Spline's **Spell**, Echo-2/Spaitial. Room-sized sweet spot fits an escape
*room*. Cost: swap Pannellum → Three.js/Spark, rework hotspots as 3D markers, softer splat look.
Sources: Marble https://www.worldlabs.ai/blog/marble-world-model · Spark 2.0
https://www.worldlabs.ai/blog/spark-2.0 · Spell https://blog.spline.design/introducing-spell ·
Echo-2 https://spaitial.ai/blog/echo-2-release · Skybox AI https://www.blockadelabs.com/

---

## The five mechanics, with worked examples

Each mechanic below is grounded in the two live scenarios:

- **Alaska** (`alaska_lake_data`, long format: `lake, park, water_temp, pH, element, mg_per_L,
  element_type`; 220 rows). Story: trainee analyst at a field station; a pilot goes missing; you
  read the water chemistry to find them. Boss twist: everyone chased the high-*chloride* lake, but
  the beacon still pulses, so the pilot's alive — go to the *warmest* lake (Lava Lake, ~20 °C).
- **Hawai‘i** (`hawaii_aquifers`, long format: `aquifer_code, well_name, longitude, latitude,
  analyte, abundance`; 954 rows, 106 wells, 10 aquifers, 9 analytes). Story: field hydrologist;
  sulfate rounds; inherit colleagues' half-done analyses; end on a seawater-intrusion confirmation
  at KEEI_B (chloride 280 > 250 **and** sodium 180 > 150).

> Values below that aren't already in the scenarios are illustrative — **resolve every answer key
> against the real CSV at build time** (the `escape_room_design` skill's verify step). The point
> here is the *mechanic*, not the final number.

---

### 1. Meta-puzzle (feeder → combination lock)

**What it is:** each room yields a *fragment* — a value, digit, or label — that's meaningless
alone. The boss room combines them. This is the single highest-leverage change and we're already
half-way there (the boss gates on `allSolved:[room1,room2,room3]`), but today the fragments don't
actually *combine* — each room is independent. Make them combine.

**Myst/Riven root:** Riven's whole island is one meta-puzzle; scattered observations converge on
the final domes/number lock.

**Alaska example — the beacon frequency.** The boss beacon rack has a 3-digit frequency dial.
Each feeder room contributes one digit as a small count, not a lake name:
- room1 → *how many* lakes have pH > 8 (= 1)
- room2 → *how many* of the top-nitrogen lakes sit in GAAR (e.g. 4 — resolve against data)
- room3 → *how many* lakes have chloride > 100 (e.g. 2 — resolve against data)

Set 1-4-2 on the dial and the pilot's beacon resolves. Alone each digit is trivia; together they're
the lock. Teaches counting distinct groups under a threshold three ways, then a synthesis step.

**Hawai‘i example — the intrusion report code.** The wellroom laptop needs a 3-part confirmation
code before it will file the intrusion report:
- room1 → the number of analytes that ever exceed 300 abundance (= 1, dissolved_solids)
- room2 → the aquifer number you cleared on the sulfate round (= 1)
- room3 → the last two digits of the alarm well's chloride (280 → 80)

Enter `1 · 1 · 80`. Each is a genuine read of the data from a different room; the boss is the only
place they mean anything together.

---

### 2. Cipher-as-data (decode opaque labels by analysis)

**What it is:** things are labelled only by opaque codes; you *decode* which is which by running
the analysis. The decoding **is** the data work — no lookup table handed over.

**Myst/Riven root:** Riven's symbol-numbers — a symbol means nothing until you work out the system
behind it.

**Alaska example — the mislabelled vials.** A note: the vanished coworker mislabelled five vials
(Sample A–E) before they left; only their chemistry can say which lake each came from. The student
matches each mystery sample's (pH, water_temp, chloride) signature against the known lake table to
recover the lake names. The decoded names then point to the room's answer (e.g. only one decoded
sample is a lake you haven't already flagged). Teaches multi-variable matching / filtering as
*identification*, not just ranking.

**Hawai‘i example — which aquifer is which.** Aquifers are labelled only `aquifer_1 … aquifer_10`.
A field note describes three of them in plain language — "the one whose wells are saltiest on
average," "the one with exactly N wells," "the one nearest the coast." The student runs group-wise
summaries (`group_by(aquifer_code) |> summarise(...)`) to decode which numbered aquifer each
description is, and reads off the code. Direct Riven parallel: `aquifer_6` is meaningless until you
analyse it and discover it's the salty Kona-coast one.

---

### 3. Diegetic, incomplete clue (story → translate to a filter)

**What it is:** a scene note that's a *pointer*, not an answer; the student must translate flavourful
narrative language into a concrete data operation. Contrast today's room3 clues, which literally say
"Filter to `element == 'Cl'`."

**Myst/Riven root:** clues are always in the open, but you have to understand the world to see what
they point at.

**Alaska example.** A note pinned in the radio room, in-story: *"The pilot radioed they were on the
lake that runs warm and sweet — warmer than it has any right to be, and hardly any bite of salt."*
The student must decode: "warm" → high `water_temp`; "sweet / no bite of salt" → low chloride. They
infer `filter(water_temp` high `& chloride` low`)` themselves — the note never names a column or a
threshold. Teaches the same filter as the current room but forces the analytic *reading* of the
problem.

**Hawai‘i example.** A colleague's scrawled note: *"Don't waste time on the deep inland wells — the
trouble's always shallow and coastal, where the sea gets close. Check the one drawing hardest and
tasting of salt."* Decode: "coastal" → the Kona-coast aquifer (aquifer_6); "tasting of salt / drawing
hardest" → highest chloride. Nothing says "chloride > 250"; the student derives the analyte and the
operation from the narrative.

---

### 4. Repair-the-Pipeline (fix broken R, verified by rerun)

**What it is:** the room hands the student pre-loaded **broken** R that's *meant* to answer the
question; they read it, find the bug, fix it, and rerun. Graded on the corrected output via the
engine's `check:{expr}` primitive (see `puzzle_types_design_notes.md`). This is the one mechanic
that tests actual **code-craft** — reading someone else's code, spotting the error — which a
conclusion-MCQ can't. Both stories are *built* for it.

**Myst/Riven root:** Myst is full of broken mechanisms you repair by understanding how they work.

**Alaska example.** Room 3 is "abandoned in a hurry" — diegetically perfect. The still-glowing
laptop holds the vanished operator's half-written script that's supposed to find the highest-chloride
lake but is broken: e.g. it filters `element == "cl"` (wrong case → empty result), or groups by
`park` instead of `lake`, or omits `distinct()` so repeated rows inflate the counts. The student
fixes it so it runs and returns the right lake. The broken script on the dead operator's laptop *is*
the story beat.

**Hawai‘i example.** The Hawai‘i story is literally "inherit a colleague's half-finished work" — a
glove fit. The colleague who "has to head out" leaves their sulfate analysis broken on the field
laptop: an `|` where it should be `&` in the filter (so `filter(analyte == "SO4" | aquifer_code ==
"aquifer_1")` returns almost everything), or abundance mapped to the wrong axis so the plot is
unreadable. The student repairs it to recover the real answer. Diegetically it's exactly what the
entry text already sets up.

---

### 5. Cross-room observation (a pattern only visible across rooms)

**What it is:** a payoff that only resolves when the student compares something from an *earlier*
room with a later one. Rewards memory and exploration; discourages brute-forcing one screen.

**Myst/Riven root:** "the clues were always in the open" — the late reveal recolours what you saw
early.

**Alaska example — the red-herring lake.** North_Killeak is flagged for high pH in room 1 *and*
highest chloride in room 3. The boss reveals why everyone chased it (it looks extreme on every
salt/pH metric) — and why they were wrong (the pilot needs the *warm* lake, Lava Lake). A boss beat:
*"Which lake has been the false alarm all along — flagged twice, but never where the pilot actually
is?"* Answerable only by recalling rooms 1 and 3. Ties the whole narrative together.

**Hawai‘i example — it was there in the first plot.** In room 1 the student plots the *whole*
dataset (every analyte, every well). KEEI_B / aquifer_6 is already sitting high on dissolved_solids
in that first plot — the intrusion signal was visible from the very start. The boss can ask them to
look back: *"Return to your room-1 plot — was the warning there before you ever went to the coast?"*
The pure Riven move: the clue was in the open all along.

---

## Suggested build order (if pursued)

1. **Land the engine primitive first** — the `check:{requires,expr,hint}` grade-on-live-R-state
   step is the prerequisite for mechanics 2, 4, and much of 1. It's already specced in
   `puzzle_types_design_notes.md` and piloted on Hawai‘i room1 (Phase 4). Retrofit one existing
   room as the pilot.
2. **Meta-puzzle wiring (mechanic 1)** — highest leverage, reuses the existing boss gate; mostly a
   `gameState` + combination-check job, little new art.
3. **Repair-the-Pipeline (mechanic 4)** — biggest pedagogical gain (tests code-craft), and both
   stories already motivate it. Alaska room3 and Hawai‘i room2/room3 are the natural homes.
4. **Diegetic clues (mechanic 3)** — cheapest of all: it's a *rewrite* of existing clue/prompt text,
   no engine change. Good quick win to trial the feel.
5. **Cipher-as-data (mechanic 2)** and **cross-room observation (mechanic 5)** — richer, need new
   content design; do after the above prove out.

Open question to settle before building: how much to keep an MCQ fallback vs going console-only for
the harder mechanics (also flagged at the foot of `puzzle_types_design_notes.md`).

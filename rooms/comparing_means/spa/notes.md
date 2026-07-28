---
authority: intent
---

# Spa scenario (draft) — Comparing Means

Chapter `comparing_means`, scenario `spa`. **Idea captured 2026-07-24 (Lucas, session "spa").**
Draft only — nothing designed/verified/built yet. This is the **premise capture + first read**, before
the PUZZLE phase (`escape_room_puzzles`) proper. First scenario in a new **`comparing_means`** chapter
folder (sibling of `data_vis`, `data_vis2`, `wrangling`, `hierarchical_clustering`,
`dimensionality_reduction`, `embeddings`).

Codec id: **12** (scaffolded 2026-07-24; was 11 at capture time, but `henges` took 11 first — the
inventory flagged the collision and spa moved to 12; inventory regenerated). **NOT yet in
`decoder/decode_codes.R`** — add `SPA_KEY` (scenario_id 12) at wiring, once the correct MCQ indices are
finalised.

## Chapter alignment — the technique sequence (READ 2026-07-24)

The book chapter is real and already written:
`websites/thebustalab.github.io/integrated_bioanalytics/chapters/10_comparing_means.Rmd`, and the
course has a matching exercise quiz (`teaching/CHEM5725/exercises.csv` → "[exercises] comparing means",
datasets `tequila_chemistry` and `algae_data`, `pairwiseTTest` on `algae_data`). Per the puzzle skill's
"read the chapter, let its ordered technique sequence be the ladder's backbone" rule, here is the
chapter's sequence **in order**:

1. **Test selection — Shapiro + Levene** (§ *test selection*). Shapiro test = normality *within* each
   group (`group_by()` then test); Levene test = equal variance *across* groups (`y ~ x` formula, no
   group_by). Together they decide **parametric vs non-parametric** for everything that follows. This is
   the chapter's gate move and recurs at every rung.
2. **Two means** (§ *two means*). Parametric = **t-test** (`tTest`); non-parametric fallback (fails
   Shapiro/Levene) = **Wilcox** (`wilcoxTest`).
3. **More than two means** (§ *more than two means*). Parametric = **ANOVA** (`anovaTest`) + post-hoc
   **Tukey HSD**; non-parametric = **Kruskal** (`kruskalTest`) + post-hoc **Dunn**. ANOVA/Kruskal tells
   you *some* group differs; the post-hoc tells you *which*.
4. **Pairs of means** (§ *pairs of means*). **Confirmed against the chapter 2026-07-24:** it filters to
   **two analytes (Na, Cl)**, `group_by(aquifer_code)`, then `pairwiseTTest(abundance ~ analyte)` — i.e.
   **one Na-vs-Cl comparison inside each aquifer facet**, ~10 comparisons, **corrected for multiple
   comparisons** across the facets (finds a significant Na/Cl difference in aquifer_2 and aquifer_9). The
   structure is *"the same two things compared within each of several groups, one comparison per group,
   corrected across groups"* — **`pairwiseTTest`** (parametric) / **`pairwise_wilcox_test`**
   (non-parametric), with **multiple-comparison correction** (default Holm). This is exactly the boss
   shape: **5 pairs of tubs = 5 facets**, one two-tub comparison per pair, corrected across the 5.
   *(Lucas's recollection was right in spirit — several non-cross-comparable pairwise tests with
   correction; the tweak is it's 2 analytes across N facets, and we pick 5 facets for the spa.)*

**This ordered sequence IS the ladder backbone.** It maps onto the spa almost one-to-one: two-means
rooms → many-means room → a pairwise-means boss. The boss Lucas described (pairwise t-test across the
hot-spring tub pairs) lands **exactly** on the chapter's final § *pairs of means* — the culminating
technique. That's a strong sign the premise is well-aimed.

### MANOVA / PERMANOVA — JUDGEMENT CALL for Lucas (flagged)

Lucas asked whether to include **MANOVA** or **PERMANOVA**. They are **not in the chapter** (chapter 10
stops at pairwise t/Wilcox). The puzzle skill treats chapter alignment as a *real constraint, not a
checkbox* — each room = one move, in the chapter's order. So:

- **Recommendation (default):** leave MANOVA/PERMANOVA **out** of the graded ladder to keep it aligned
  with the book. The four techniques above already give a clean, strictly-monotonic 3-rooms-plus-boss
  ladder without them.
- **If Lucas wants them in:** they'd need to be added to the book chapter *first* (they're a genuine
  step up — multivariate response, and PERMANOVA is distance-based/permutational, a different animal).
  That's a curriculum decision, not an escape-room one. Could be a future *second* comparing-means
  scenario (the chapter's pre/post twin) that extends into multivariate territory once the book covers
  it.
- **Do NOT** smuggle an untaught technique into a graded room. If we want a multivariate *flavour*
  without teaching it, that belongs in world-dressing, not a graded puzzle.

## Analog grounding (Step 0 — the real-world act the code performs)

Where does a person, by hand, do what a comparing-means test does? **They eyeball two groups and judge
whether the difference is real or just noise.** A barista deciding whether this week's beans really pull
shorter shots than last week's, or a gardener asking whether the south bed genuinely out-yields the
north or it's just this year — you gather a handful of readings from each side, look at the spread, and
decide *is that gap bigger than the wobble within each group?* That "is the between-group gap bigger
than the within-group scatter" is exactly the t/ANOVA intuition.

The spa premise gives this a gorgeous physical form: **candles as the visible verdict.** A candle above
each door is **lit iff the two groups of candles in the room differ significantly** — significance made
literally visible. The world doesn't just host the technique; it *renders the p-value as a flame*.

**Escape seed (the boss's core cognitive move):** the boss is *pairwise* comparison across many pairs —
"for each pair, is the difference real?" The data-free escape re-poses that same recognition on in-world
props (see *The escape* — needs decoupling work, flagged below).

## Theme / world (Lucas's premise, 2026-07-24)

The player is the **owner of an exclusive Nordic spa**. It's a **snow day**; they want to finish the
morning maintenance rounds and get out on the slopes. The whole run is the owner walking their spa,
room by room, checking each bath is set right — and each check *is* a comparing-means test.

- **Relaxing, luxurious, Nordic-spa mood** — warm wood, candlelight, steam, stone, snow outside the
  windows. Earnest and serene, not spooky (matches the house "earnest, mood-matched" rule).
- **Rooms are bath halls:** cold spa / cold plunge, warm baths, saltwater baths, hot tubs, and so on —
  each a themed chamber. Each room has a **colour/material theme**: gold, green, wood-panelling, etc.
- **Candles everywhere.** Baths are ringed by candles; the count/arrangement of candles is the room's
  data. Above each secret-passage door hangs **one candle, lit or unlit = the significance verdict** for
  that room's comparison.

### The signature travel mechanic — secret employee passages

The distinctive way of moving through this world: **secret staircases, spiral stairs, and ladders
behind hidden doors** — the spa's *employee* passages, as opposed to the *client* hallways (the main
corridors). The owner moves through the building the way staff do, backstage.

- In each room, a **secret passageway door** is a hotspot. It doesn't initially read as a door and
  isn't initially open (or: it's a hotspot all along but visibly sealed) — clearly a *secret* passage.
- The passage **opens when the room's WebR puzzle is solved** (control panel on the wall that controls
  the baths). Above the now-open passage: the significance candle.
- There are also **secret hallways** connecting things purely for aesthetic/continuity — they read as
  backstage passage but aren't a travel-choice mechanic. (Engine-wise these are just linear doors; the
  *spiral-stair / ladder* framing is the flavour.)
- **Every secret-passage door across the whole spa is a hotspot** (sealed until its room is solved).

Maps to the engine's linear door graph: control-panel `puzzle` in each room gates the forward
(secret-passage) door. The spiral-stair/ladder art is the interstitial beat.

### The environmental arc — dark → light by LOCATION, not time

Distinctive twist: the light arc runs **dark to light, but NOT because the day passes** — because of
**where the rooms sit in the building**. It **starts in a very dim, relaxing entryway** (deep interior,
low candlelight, spa-hush) and brightens room by room as the player moves toward the **outdoors**,
ending in the **bright, snowy, open-air hot springs**. So the arc is *interior-dim → exterior-bright*,
an architectural progression rather than a clock. (Contrast trees, where elevation + time-of-day ran
together; here it's depth-in-building → daylight.)

## The DATA is water chemistry — candles are NOT data (CLARIFIED 2026-07-24, Lucas)

**Critical clarification that reshapes the earlier draft.** The measured data the player analyses is the
**water chemistry and temperature of the baths** — the spa owner is getting the baths ready for the day,
testing **pH, temperature, salinity/salt content (for the saltwater baths), sanitiser, hardness,
dissolved solids**, etc. **The data has NOTHING to do with candles.** The earlier "size distribution of
candles as the datum" idea is **dropped** — candles are purely an *indicator + escape* layer, not a
measured quantity.

**So there are two separate systems:**
1. **The water-chem DATA** (pH / temperature / salinity / …), measured with several replicate readings
   per bath → this is what every graded comparing-means puzzle runs on. Replication is natural (the owner
   takes several readings per bath). This solves the "need a distribution, not one number" problem
   cleanly and believably.
2. **The candles = the indicator/escape layer.**
   - **Door-candle** above each room's secret passage: lit iff that room's water-chem comparison came
     out **significant**. It's the *visible verdict* — and teaches the player what a lit candle means
     (Lucas: keep this — it's what makes the escape legible later).
   - **Escape candles** (theme-coloured, one per room, toggled by the bell-pulls): lit at the finale to
     reproduce the *remembered pattern of which rooms were significant* (see *The escape* + Q5).
     Recognition of verdicts, decoupled from all data.

**Graded MCQ, not a binary verdict.** A lit/unlit door-candle is only 2 outcomes; the *graded* MCQ at
the control panel asks for the **analysis result** — which bath differs, which is the correct test given
the Shapiro/Levene outcome, the effect direction/size — so we can field ≥6 data-derived distractors. The
door-candle is the *confirmation/clue*, not the graded answer.

### The bell-pull thread (the escape's control mechanism)

In the earlier rooms there are **bell-pulls / cords** (hotspots). Pulling one makes a **distant bell
tinkle** — and that's all the player knows at the time. The cords are the **control mechanism for the
five escape candles in the boss room**: at the finale the player pulls cords to toggle the candles into
the pattern they *see* in the tub-pairs' candle arrangements (see *Escape* — the pattern is a data-free
recognition, not the boss numbers). The cords carry **no verdict of their own**. **Count resolved
2026-07-24 (Lucas):** cords can **double up in a room** (e.g. **two in the first room**), so five
candles are controllable even with fewer than five rooms — no need for one-cord-per-room. The "distant
bell" is the early foreshadow; its purpose only becomes clear at the boss.

## Structure — rooms, boss, escape (Lucas's premise)

Ladder shape (to be reverse-engineered properly in the PUZZLE phase — this is the premise sketch):

- **Practice rooms (bath halls)** — each teaches one rung of the chapter sequence, brightening toward
  the outdoors. Natural (draft) mapping, to verify against data:
  - **Room 1 (dimmest, e.g. cold plunge)** — **two means, t-test** (with the Shapiro/Levene
    test-selection intro). Are these two baths significantly different?
  - **Room 2 (e.g. saltwater baths)** — **two means, non-parametric** — data fails Shapiro/Levene →
    **Wilcox**. Teaches that test selection *changes the tool* (the taught trap candidate — see below).
  - **Room 3 (e.g. warm baths)** — **more than two means** — **ANOVA + Tukey** (or **Kruskal + Dunn** if
    non-normal). *Which* of several baths differs.
  - *(A 4th practice room is possible — the chapter has enough moves. Keep strictly monotonic.)*
- **Boss — the outdoor hot springs.** The springs are laid out as **five PAIRS of tubs** (ten tubs),
  out in the open as the **weather changes** (snow/steam). For **each pair**, the player compares the two
  tubs' temperature (a two-sample test); run together across the five pairs that is the chapter's
  `pairwiseTTest(value ~ tub)` grouped by `pair` — five comparisons, **corrected for multiple
  comparisons** (Holm). Some pairs differ, some don't. This is the culminating § *pairs of means* and
  where the **multiple-comparisons trap** lives (see below).
- **Escape — the final door out (to the slopes) — CLARIFIED 2026-07-24 (Lucas): DATA-FREE recognition.**
  In the hot-springs (boss) area, **each of the 5 pairs of tubs also has candles arranged around it**.
  The **5 escape candles** (one per pair) must each be lit iff **that pair's two tubs differ
  significantly in their candle groups** — judged **by eye** (many vs few candles around each tub), a
  *recognition* of the same "are these two groups different?" move, **not** a re-read of the
  water-chemistry data. So the escape is **fully decoupled from the dataset** (the boss's temperature /
  pairwise numbers play no part). The player pulls the **bell-cords** (the control mechanism, back in the
  earlier rooms) to set the 5 candles to match what they *see* in the tub-pairs' candle arrangements.
  Set all five right → door opens → ski. **Five candles ≠ number of rooms on purpose** → signals it's
  not a memory puzzle; the control cords can double up (e.g. **two cords in the first room**) so all five
  candles are reachable regardless of room count. *(This is the skill's data-free meta-echo escape — an
  in-world, no-data recognition of the boss's pairwise-comparison move. Supersedes both earlier misreads:
  it is NOT a memory of the earlier rooms, and NOT a read-out of the boss's water-chem verdicts.)*

### The taught trap (skill requires one) — candidates

Comparing means is rich with pitfalls to *teach*, not hide:
- **Multiple comparisons** — running many pairwise t-tests without correction inflates false positives.
  This is the natural boss trap: the hot-springs pairs *tempt* a pile of naive t-tests; the correct move
  is `pairwiseTTest`/`pairwise_wilcox_test` **with** correction, which flips some "significant" pairs to
  non-significant. **Strong candidate — sits exactly where the chapter puts it.**
- **Wrong test for the distribution** — using a t-test/ANOVA when Shapiro/Levene say non-normal/unequal
  variance (should be Wilcox/Kruskal). A room where the naive parametric test gives a "significant"
  call that the correct non-parametric test does not (or vice-versa) is a clean taught trap.
- **"Not significant" ≠ "the same"**, and **mean dragged by an outlier** (one bath with a dozen candles
  skews the mean vs the median) are secondary options.

Pick the trap deliberately in the PUZZLE phase; the multiple-comparisons one is the front-runner.

## Open design questions / judgement calls (for the PUZZLE + STORY phases)

1. **MANOVA/PERMANOVA in or out?** (flagged above) — default OUT; needs a book change first if IN.
   Added to root `todo.md` as the "comparing-means II" scenario (2026-07-24).
2. ~~**Candle data model.**~~ **RESOLVED 2026-07-24 (Lucas):** always measure the **size distribution**
   of the cluster of candles at each spot → inherent replication. See *The candle device*.
3. ~~**Graded MCQ vs binary verdict.**~~ **RESOLVED 2026-07-24:** graded MCQ asks the *analysis result*
   (which bath/pair differs, correct test given Shapiro/Levene) with ≥6 distractors; door-candle is the
   clue. See *The candle device*.
4. ~~**Dataset.**~~ **DECIDED + BUILT 2026-07-24:** engineered spa re-skin `data/spa_water_chem.csv`
   (tequila skeleton, water-chem effect model, all four rungs verified, boss flip asserted). See
   *Engineered dataset + verified ladder*.
5. **Escape design — CLARIFIED 2026-07-24 (Lucas): data-free recognition, decoupled from the data.**
   The 5 escape candles are lit by **recognising, by eye, whether each pair of tubs' *candle groups*
   differ** (many vs few candles) — an in-world, no-data echo of the pairwise "are these two groups
   different?" move. It uses the **candles in the hot-springs area, NOT the water-chemistry dataset** and
   NOT the boss's statistical verdicts. This is exactly the escape-skill's **data-free meta-echo** — so
   the earlier "divergence" flag is withdrawn; the design is skill-compliant. The **bell-pulls** are the
   control mechanism only, and can **double up in a room** (e.g. two cords in the first room) so all five
   candles are reachable — resolves the "fewer rooms than candles" worry. Five ≠ room count = signals
   "not a memory puzzle." Still-open (story/design + art): engineer the **candle arrangements** per tub
   pair so the "clearly different / clearly same" reads are unambiguous by eye (recognition must be fair);
   the exact bell-pull placement; and whether the graded boss reads parametric (`pairwiseTTest`, current
   build) or is engineered non-normal to force `pairwise_wilcox_test`.
6. **Room count / which baths** — settle the exact rooms and their order so the light arc and the ladder
   both climb monotonically (dim interior → bright exterior; t → Wilcox → ANOVA → pairwise boss).

## Dataset survey + recommendation (SURVEYED 2026-07-24)

Surveyed the datasets referenced in `teaching/CHEM5725/exercises.csv` (local copies in
`websites/thebustalab.github.io/phylochemistry/sample_data/`). What a comparing-means ladder needs: a
**grouping variable with replicate measurements of one continuous quantity** (→ re-skins to
spot→candle-size). Candidates, best-structured first:

| Dataset | Shape | Groups × replicates | Fit for the ladder |
|---|---|---|---|
| **tequila_chemistry** | 4720×6 | **16 bottles × 5 reps**, per compound; bottles also fall into classes (Blanco/Reposado/Añejo) | **Best raw structure.** 16 groups → plenty of distractors + a natural 2-level (two bottles → t) → many-level (bottle class → ANOVA) → pairwise-across-bottles (boss). Exercises.csv Q1 dataset. |
| **algae_data** | 180×5 | 3 strains × 2 regimes × 3 reps | The exercise's own `pairwiseTTest` set — but only 3 strains / 3 reps: **too thin** for ≥6 distractors and a rich ANOVA/pairwise boss. |
| **hawaii_aquifers** | 954×6 | 10 aquifers × ~ wells, per analyte | The **chapter's own worked example** → risks feeling like the lecture; and **Hawaii is already a scenario** (`data_vis/Hawaii`, id 7). Good structure though. |
| **wine_grape_data** | 1070×5 | 5 cultivars × 2 treatments (dry/well-watered) × 2 chroma, per metabolite | Clean **two-factor** design (treatment → t; cultivar → ANOVA). Replicate depth unclear (may be 1 per cell) — check before use. |
| **wine_quality** | 6497×14 | 2 types (red/white) + 7 quality scores, 11 continuous props | Huge n → a **very strong two-means** (red vs white), but only 2 main groups; quality_score (7) for ANOVA. |
| **beer_components** | 3625×6 | 5 ingredients × 5 reps, per analyte | Decent (5 groups, 5 reps); 5 groups is a bit tight for ≥6 distractors on the many-means rung. |
| **metabolomics_data** | 93×126 | 2 patient statuses (healthy/kidney), 124 metabolites wide | Two-group only → two-means; medical, not spa. |
| **chemical_blooms** | 78×10 | 78 species × compound-class composition | One row per species, **no within-group replication** → not suited. |

**Recommendation (for Lucas's confirmation):** **engineer a spa/candle re-skin** on a **real
categorical skeleton borrowed from `tequila_chemistry`** (16-bottle → bath structure, 5 replicates →
candle-size readings per spot), rather than shipping a raw set. Reasons, matching the puzzle skill's
"engineer when the raw data won't serve the ladder":
- The candle-size framing needs the exact shape *spot → cluster of size readings*; a re-skin gives it
  cleanly and lets each bath-group be a "spot."
- The **boss needs the multiple-comparisons taught trap engineered in**: several tub pairs where a
  naive pile of uncorrected t-tests calls extra pairs "significant," but `pairwiseTTest` **with
  correction** flips at least one back to non-significant — the lesson only lands if the data is built
  to make that flip happen (deterministic, seeded, verified — like `trees`' Simpson flip).
- We also want a **test-selection rung** where the data genuinely fails Shapiro/Levene so Wilcox/Kruskal
  is the *correct* call (and the naive t-test/ANOVA misleads) — again best guaranteed by construction.
- A re-skin keeps the escape trivially **decoupled** (Q5): the escape is memory-of-verdicts, touching no
  numbers at all.

**DECIDED + BUILT 2026-07-24 (Lucas):** engineer the spa re-skin on the tequila skeleton, believable
with real noise, and make it fail normality where needed. Done — see *Engineered dataset + verified
ladder* below. (The raw-dataset alternative — ship `tequila_chemistry` as-is — was declined; it couldn't
guarantee the correction flip or the Shapiro/Levene failure.)

## Engineered dataset + verified ladder (BUILT 2026-07-24, session "spa")

Generator: `_scratch/build_spa_water_chem.py` (deterministic, seed 20260724) →
**`data/spa_water_chem.csv`** (1,536 rows, 75 KB, web-friendly). Provenance copy of the source skeleton
at `_scratch/_tequila_source.csv` (the 16-bottle tequila set; can be dropped later — only the generator
references the 16-entity shape). Public URL once the site is pushed from the Mac:
`https://thebustalab.github.io/escape_rooms/rooms/comparing_means/spa/data/spa_water_chem.csv`.

**Reskin (per the puzzle skill — keep the categorical skeleton, regenerate the measures).** 16 tequila
**bottles → 16 baths**, grouped by type into rooms; long format like tequila (entity × parameter ×
replicate → value). Values regenerated from a believable water-chemistry **effect model** (bath_type
sets each parameter's baseline; per-bath offsets; realistic noise) engineered so each rung falls out
cleanly. Candles are **not** in the data (escape layer only).

**Columns (student-facing):** `bath, bath_type, pair, parameter, replicate, value` (`pair` is the
hot-spring pool id — blank for the practice baths; it's the boss's facet variable, like `aquifer_code`
in the chapter). **18 baths, 1,728 rows:** cold_plunge ×2, saltwater_bath ×2, warm_bath ×4, and the boss's
**hot_spring ×10 = 5 pairs of 2 tubs** (`<pool>_pool` + `<pool>_grotto` for pools ember/aurora/frost/
slate/gale). **8 parameters:** temperature_C, pH, salinity_ppt, free_chlorine_ppm, calcium_hardness_ppm,
total_alkalinity_ppm, total_dissolved_solids_ppm, turbidity_NTU. **12 replicate readings** per bath per
parameter (n=12 — enough for Shapiro power and a stable boss flip; deterministic so every student reads
the identical CSV). *(Mineral baths from the first draft were dropped to keep the shipped set focused;
add them back if we want a 4th Kruskal/Dunn room.)*

**VERIFIED ladder (re-run the generator to reconfirm; deterministic). Strictly monotonic, tracks the
chapter order:**

- **Room 1 — cold plunges × temperature — TWO MEANS, t-test.** `plunge_glacier` (9.41 °C) vs
  `plunge_fjord` (11.29 °C). Shapiro passes both (p 0.82, 0.79), Levene passes (p 0.27) → **t-test**,
  **p = 9e-9, significant** (fjord warmer by 1.9 °C). Teaches: run Shapiro/Levene → pick t-test → read
  the result. Door-candle **LIT**.
- **Room 2 — saltwater baths × salinity — TWO MEANS, non-parametric (test selection bites).**
  `brine_north` (median 32.7) vs `brine_south` (median 38.0). Salinity is **right-skewed** (engineered
  brine spikes) → **Shapiro FAILS** (p 0.009, 0.004) → must use **Wilcox**, **p = 9e-4, significant**.
  Teaches: normality check changes the tool (the taught trap of using a t-test on non-normal data).
  Door-candle **LIT**.
- **Room 3 — warm baths × pH — MORE THAN TWO MEANS, ANOVA + Tukey.** birch 7.42 / cedar 7.43 / pine
  7.41 / **spruce 7.85**. Shapiro/Levene pass → **ANOVA p = 1e-29, significant**; **Tukey** isolates
  **`warm_spruce`** (spruce-vs-each-other p < 1e-14; the other three mutually n.s., p 0.73–0.98) →
  **single clean winner = warm_spruce**. Teaches: ANOVA says *something* differs, post-hoc says *which*.
  Door-candle **LIT**.
- **Boss — outdoor hot springs × temperature — PAIRS OF MEANS, per-pair t + multiple-comparison
  correction (THE TAUGHT TRAP).** **5 PAIRS of tubs** (pool vs grotto), one two-sample comparison per
  pair, run as `pairwiseTTest(value ~ tub)` grouped by `pair` → 5 comparisons, **Holm-corrected** (the
  course default). Realized per-pair Δtemperature and verdicts: ember −2.18 (SIG), aurora −1.22 (SIG),
  frost −1.02 (SIG), **slate −0.32 (raw p 0.027 SIG → Holm p 0.053 n.s. = THE FLIP)**, gale −0.23
  (n.s.). **Corrected verdict: ember/aurora/frost differ; slate/gale do not** (uncorrected trap wrongly
  adds slate → 4). The generator **asserts** slate flips. Teaches: uncorrected pairwise tests
  over-report; correcting is mandatory. **Graded boss** MCQ (draft): *"after correcting for multiple
  comparisons, which pools' tubs genuinely differ in temperature?"* → {ember, aurora, frost} (trap
  includes slate; distractors = other subsets). **NB the escape candles are NOT this verdict** — the
  escape is a separate, data-free recognition of the *candle groups* around each tub pair (see *Escape* /
  Q5); this water-chem result is the graded boss only.

**Documented departures from raw tequila (per skill).** (1) Values fully regenerated (tequila measured
volatile compounds; we model water chemistry) — only the 16-entity long-format skeleton is reused.
(2) Replicates 5 → 12 (test power + stable boss flip). (3) 59 compounds → 8 water-chem parameters.
(4) Bath counts chosen to serve the ladder (cold 2 / salt 2 / warm 4 / hot-spring 5 pairs = 18 baths),
not tequila's 16 / class proportions — the boss's 5-pair structure drove the count.
(5) A `pair` column was added (blank for practice baths) to carry the boss's facet variable, mirroring
the chapter's `aquifer_code`.

**Open (puzzle-phase) items still to settle:** exact MCQ wording (wiring phase); whether to add a 4th
graded room (mineral baths → Kruskal/Dunn) to also teach the non-parametric many-means branch, or keep
it 3-practice-plus-boss; the exact plot each room asks for; whether the boss reads parametric
(`pairwiseTTest`, current build) or is engineered non-normal to force `pairwise_wilcox_test`.

## Puzzle-type assignment, distractors & shape checks (checklist close-out 2026-07-24)

**Puzzle-type per room + variety (skill: not four identical Compute-the-Key cards).** Analysis-side
types from `notes/puzzle_types_design_notes.md` are *Compute-the-Key*, *Classify-the-Unknown*,
*Repair-the-Pipeline*. Assignment, deliberately varied:
- **Room 1 — Compute-the-Key.** Run the t-test, read the result (significant? which plunge warmer?).
- **Room 2 — Classify-the-Unknown (test selection) → then Compute.** The distinctive move is *choosing*
  the test: read Shapiro/Levene, recognise non-normality, pick **Wilcox** (not t) — a classify step
  before the compute. This breaks the Compute-the-Key monotony.
- **Room 3 — Compute-the-Key (ANOVA) + post-hoc read.** ANOVA then Tukey to name *which* bath — a
  two-step compute (omnibus → post-hoc), a notch different from Room 1's single test.
- **Boss — Deduction-ledger flavour (#9) over pairs + correction.** Assign a verdict (differ / not) to
  each of 5 pairs, *after* correction — a small verdict grid, not a single-key compute.
- **Escape — recognition + Bell-pull (#16).** Eyeball each tub-pair's candle groups (data-free
  pattern-match, kin to #6) and set the 5 candles via the bell-pull control (#16). Not graded.
So the ladder spans Compute → Classify → Compute+post-hoc → verdict-grid → recognition — genuine variety,
not four identical cards. *(If we want even more contrast, Room 3 could become a Repair-the-Pipeline —
fix a broken ANOVA call — but the current spread already satisfies the variety rule.)*

**Unbuilt-engine dependency FLAGGED (skill requires it).** The escape needs **mechanic #16
(bell-pull / summoning cord)**, catalogued in `notes/puzzle_inventory.md` as **"To build"** (a `pull`
control writing `gameState` + a distant `showWhen`-gated candle, sibling of #8). **`spa` is the first
real consumer of #16** — its build is a prerequisite for this escape (design/engine phase, not blocking
the PUZZLE handoff). The graded rooms use only the existing analysis-side `lock`/MCQ engine.

**≥6-distractor availability per graded MCQ (skill: exist, or plan wrong-method where <6 levels).**
Confirmed available now (final text is wiring-phase):
- **Room 1 (2 baths → <6 levels):** wrong-method/read distractors — "not significant", wrong direction
  (glacier warmer), used Wilcox when t was correct, misread p-threshold, compared the wrong parameter,
  "variances unequal so can't test". ≥6. ✓
- **Room 2 (2 baths → <6 levels):** picked t-test (ignored failed Shapiro), "normal, so t is fine",
  wrong bath saltier, Kruskal (>2-group tool), "no significant difference", read salinity vs TDS. ≥6. ✓
- **Room 3 (4 warm baths):** the 4 baths (birch/cedar/pine/spruce) + wrong-method options (lowest-pH
  bath, "no difference" from a bad omnibus read, wrong analyte, skipped post-hoc). ≥6. ✓
- **Boss (5 pairs):** the 5 pool names as subsets + the uncorrected 4-set trap + "all differ"/"none
  differ" + a wrong-pair set. ≥6. ✓

**Long-format / table-shape check (skill).** Data is long (`bath × parameter × replicate`). Every
analysis groups by `bath`/`pair` and one `parameter`, summarising `value` — no per-entity column
duplication (unlike the trees long-format ranking trap). Verified in the generator by computing each
answer straight off the shipped CSV. ✓

**Pairing (pre/post twin) status.** The chapter-design principle wants two comparing-means scenarios on
different datasets/stories, same question style, for pre/post testing. **Twin now premised
(2026-07-25):** the **`squirrel`** scenario (`rooms/comparing_means/squirrel/notes.md`, session
"squirrel") — a self-aware squirrel jumping tree-to-tree through a forest, hawaii-aquifers re-skinned to
tree nut-production, same t/Wilcox/ANOVA/pairwise backbone with a compact-letter-display finale.
Premise-captured only; not yet through the PUZZLE phase. *(Supersedes the earlier "spa currently has no
twin planned" note.)* The MANOVA/PERMANOVA scenario in root `todo.md` is a *different technique set*, not
this pre/post twin.

## What's strong about this premise (my read)

- **The world genuinely IS the technique.** Candle-above-the-door = the p-value made visible is a
  first-class embodiment of significance testing — exactly what the STORY skill's "world IS the
  technique" principle wants.
- **The boss maps onto the chapter's actual final technique** (pairwise means) with no forcing.
- **The travel mechanic (secret employee passages) and the by-location light arc are distinctive** and
  hit the skill's "signature travel mechanic" + "clean environmental arc" levers cleanly.
- **The bell-pull → coloured-candle thread is a proper foreshadow** that pays off at the escape.
- Main things to solve: the **candle→replicated-data** wiring, and **decoupling the escape from the
  dataset**. Both are normal PUZZLE/STORY-phase work, not blockers.

## Next steps (pipeline)

`escape_room_puzzles` (ladder + dataset + verified answers; resolve Q1–Q4, Q6) →
`escape_room_story` (world/beats/escape payoff; resolve Q5) → `escape_room_design` (scenes +
`scenario.json`) → *[Lucas: harness art]* → `escape_room_wiring`. **No git commit on this box** (site is
a Mac-only repo; Syncthing carries edits).

## Narrative (STORY phase — drafted 2026-07-24, session "spa")

*All proper nouns below are drafts, flagged for Lucas: the spa name (**Fjellro**), the rival (**Dagny
Vold**), the pool names (ember/aurora/frost/slate/gale), and the title. Swap freely.*

### Logline · stakes · clock (the three lines)
- **Logline:** At **Fjellro**, an exclusive Nordic mountain spa on a bright morning after the storm, the
  owner must certify every bath's chemistry before the day's first guest reaches the door.
- **Stakes (concrete):** that first guest is **Dagny Vold** — a rival keeper the owner has spent years
  out-classing — arriving with her friends. If a single bath reads wrong when they slip in, Dagny will
  find it and delight in it. Every correct certification is a small win; one wrong call is the crack she's
  been waiting for.
- **Clock:** Dagny's party is **already on the mountain**, climbing the funicular through the cleared
  storm. You glimpse them through each room's windows, nearer every time. Certify the last spring before
  they crest the rise — and you can still click into your skis and take first tracks ahead of them.

### World (built from the analog)
Comparing-means analog = **eyeball two groups and judge whether the gap is real or just noise.** A
Nordic spa-keeper does exactly this by hand every morning: is this bath *genuinely* off spec, or just
the normal wobble of water? **Fjellro** is a place where that judgement is the whole craft. The player
moves through it via the **signature travel mechanic** — the **secret staff passages**: spiral stairs
and ladders behind concealed doors, the employee circulation of an exclusive spa, so the owner works
backstage while the pristine client hallways wait spotless for the arriving guests. **Landmark:** the
**outdoor hot springs** under the mountain (boss + escape sited here) — the visit is earned because the
prized springs are the last and hardest to certify, and where you finally see Dagny's funicular close.

**Cast economy:** one on-screen presence — **you**, the owner (people never appear in the art). One
named, offstage antagonist — **Dagny**, always *arriving*, never seen; she lives entirely in the voice
of the prompts (the standard you hold yourself to). Zero other characters.

### Environmental arc (hand to `escape_room_design`)
Light climbs **by location, not time of day**: from the **dim, candlelit inner sanctum** (deep in the
building, the cold plunge) outward, room by room, toward the **snow-bright open-air springs**. Windows
grow larger as you near the outer wall; through them the **storm-cleared alpine morning** brightens and
**Dagny's funicular climbs closer** (the clock rides the arc). Steam everywhere; crisp cold light; warm
candle-glow inside giving way to snow-glare outside. Mood: **serene, exacting, quietly competitive —
hygge indoors, alpine dawn out.** Never jokey.

### Beats — one per rung (why the owner runs *this* test *now*)
- **Room 1 · Cold plunge (t-test).** Theme: pale blue-grey stone, silver; the deepest, dimmest room.
  The storm chilled the plunges overnight and one reads colder. Dagny always tests the cold plunge
  first. Compare the two plunges' temperature — is one *genuinely* off, or just normal wobble? Certify,
  the passage candle lights, move on.
- **Room 2 · Saltwater baths (Wilcox — test selection bites).** Theme: green sea-glass, verdigris
  copper. The brine spiked overnight; salinity readings are jumpy and skewed. A t-test would lie on data
  this lopsided — you *must* read it the non-parametric way. Is one brine bath truly over-salted? Certify.
- **Room 3 · Warm baths (ANOVA + Tukey).** Theme: honey wood, gold — the warm heart of the spa. Four
  baths; one's pH has drifted. ANOVA to catch that *something's* off, Tukey to pin *which* single bath,
  so you fix only that one and don't disturb the three that are fine. Certify.
- **Boss · Outdoor hot springs (pairwise + correction — the misdirection).** The prized springs, in
  **five pairs**. After a storm every pair *wobbles*, and the tempting move is to "fix" every pair that
  looks off — but test enough pairs and one will look different by pure chance. Correct for the many
  comparisons and only the **truly** mismatched pairs remain. The obvious (uncorrected) read flags a
  fourth pair (**slate**) that's really fine; the careful read leaves three. Dagny would pounce on a
  spring you "corrected" that never needed it. Certify the real ones only.

### Escape — the payoff (data-free meta-echo; the thematic climax)
Set into the springs' old stonework are **five ceremonial "balance" candles**, one per pool, each
**coloured to its pool** (ember = amber, aurora = green, frost = white, slate = grey, gale = steel-blue).
The finale is **not** a re-read of the data: around each pair of pools stand clusters of candles, and the
owner — unaided, no console — judges **by eye** which pairs' candle-groups are *clearly* different and
which are *clearly* matched, then pulls the **bell-cords** (scattered in the earlier rooms; two in the
first room so all five are reachable) to light the balance-candles to that pattern. It re-poses the whole
day's skill — *tell a real difference from noise* — one last time, on candlelight instead of numbers.
When the pattern is right, the spa declares itself **in balance**, the door to the piste swings open, and
you step out onto fresh snow **just as Dagny's funicular crests the rise** — certified, flawless, and
already ahead of her. *(Player-performed ceremonial gesture: the final cord-pull is the release —
one motion, its meaning front-loaded, no second puzzle.)*

**Note (candle colours moved from rooms → pools):** Lucas's first sketch coloured the escape candles by
the *practice rooms* (gold/green/wood). Since the escape decoupled onto the **5 hot-spring pools**, the
5 candles are now keyed to the **pools** (5 colours above), which keeps the whole escape self-contained
in the springs area. Practice-room colour themes (blue-grey / sea-glass / honey-wood) remain as room mood
only, not escape identities.

### Voice notes
Earnest, concrete, sensory; a proud, precise owner's-eye. Ground every line in the world (the thermometer
fogging, brine crusting a tile, the funicular's cable humming closer). Hold the hygge-to-alpine mood;
never ironic. Dagny is a presence, not a caricature — the standard, not a villain twirling a moustache.
Cards short.

### Draft story-map text (paste into the harness story-map; tighten there)
- **title:** *First Guest* — **subtitle:** *A snow-day at Fjellro: certify every bath before your rival
  reaches the door.*
- **story (landing):** *The storm has passed and Fjellro is yours alone — for one more hour. Dagny Vold
  is already on the funicular, her friends laughing beside her, the first guests of the day and the last
  people you want to hand a flaw. Every bath must read true before they arrive. You slip into the staff
  stair behind the entry panel, thermometer in hand, and start where the water is coldest and the light
  is lowest.*
- **entry · Room 1 (cold plunge):** *(first room — no card)*
- **entry · Room 2 (saltwater):** *The stair spirals up into green light and the smell of brine. The
  storm churned salt through these baths overnight — the readings jump like a startled pulse. Trust the
  numbers carefully here.*
- **entry · Room 3 (warm baths):** *A ladder brings you into honey-wood warmth, gold candlelight on
  still water. Four baths, the heart of the house — and one of them, you can already tell, is not quite
  keeping its balance with the rest.*
- **entry · Boss (outdoor springs):** *The last door gives onto cold, brilliant air: the outdoor
  springs, steaming under the peak, paired across the snow. Far below, the funicular is climbing. After
  a storm every pool looks a little off — the trick is telling which ones truly are.*
- **done (analysis certified):** *Every bath reads true. The house is honest, top to bottom — nothing
  for Dagny to find.*
- **escapeDone (escaped):** *The balance-candles hold their pattern; the piste gate clicks open. You
  step onto untouched snow as the funicular crests the rise — flawless, and first. Let her follow.*

### Story-phase judgement calls flagged for Lucas
- **Names** (spa **Fjellro**, rival **Dagny Vold**, pools ember/aurora/frost/slate/gale) and the
  **title** (*First Guest*) are all drafts — swap any.
- **Escape candles keyed to the 5 pools, not the 3 rooms** (see note above) — deliberate, follows the
  decoupling; flag if you'd rather they echo the rooms.
- **Clock device** = Dagny's funicular seen through growing windows. It rides the spatial light arc
  rather than fighting it — but confirm you like the "rival visibly approaching" cue over a plainer
  countdown.
- **Ladder unchanged** — no beat fought the verified answers; nothing pushed back to `escape_room_puzzles`.

## Design record — v2 restructure (2026-07-24, after Lucas saw first art)

Lucas revised the room layout and the escape after seeing early art. Rebuilt via
`_scratch/restructure_v2.py` (re-runnable; preserves the authored graded-puzzle payloads). Changes from
v1 (below):
- **6 rooms now:** added a no-puzzle **`entry`** hall (holds 2 escape cords) before the four graded
  rooms; order `entry → cold_plunge → saltwater → warm_baths → springs(boss) → piste(escape)`. Graded
  ladder (t/Wilcox/ANOVA/pairwise) and verified answers UNCHANGED.
- **Escape is now candle-SIZE recognition, distributed across all rooms** (not 5 clusters at the
  springs). 5 colours, each with a candle-pair in one room and its **cord one room earlier** (Lucas
  confirmed the backtracking is intentional). Verdict by size: massive-vs-tiny = DIFFER → light;
  matched = SAME → dark. A door-candle above each puzzle-room exit shows that room's verdict. Full
  colour→room→cord→verdict table in `AGENTS.md` → *The candle escape (v2)*. Correct gate =
  vermillion/yellow/purple lit; blue/green dark.
- **Colour-blind fix:** dropped Lucas's red/white/blue/orange/yellow (red/orange/yellow collapse under
  red-green colour-blindness). Now **Okabe-Ito colours + a distinct shape per colour** (vermillion/
  square, blue/circle, yellow/diamond, green/triangle, purple/star) — hue never load-bearing alone.
- **Boss depth:** the 5 water-chem spring pairs stay for the graded pairwise puzzle; **2 foreground
  pairs carry escape candles (green SAME, purple DIFFER), 3 sit back along paths** (data only) — Lucas's
  idea, and it gives the springs depth. Escape candle verdicts are decoupled from the water-chem result.
- **Art prompts** re-authored: the per-room candle-pairs + cords (colour+shape) + door-candles are now
  in each `scenePrompt`; the light arc Lucas specified is baked in (entry/cold dark → saltwater pre-dawn
  windows+snow → warm pre-sunrise big windows → springs sunrise → piste golden sunrise) — **with**
  windows/snow but still **no funicular in the art** (the rival clock stays in the `entry` cards).
- Inventory regenerated: spa `rooms_total: 6`, id 12, no dupes.

### v1 record (superseded — kept for history)

## Design record (DESIGN phase — `scenario.json` built 2026-07-24, session "spa")

**`scenario.json` written + validated (parses; all hotspot types valid).** Codec **id 12** (11 collided
with `henges`; inventory flagged it, spa moved to 12, `scenario_inventory.json` regenerated → no
duplicates). Durable facts (ladder + answers + engine flags) live in the new **`AGENTS.md`**
(`authority: canon`).

**5 nodes** (all `built: false` stubs; each has `scenePrompt`+`doorPrompt`, `plannedHotspots`, a full
`designNote` with the verified answer + ≥6 options, a `debrief`, and an `entry` card except room 1):
`cold_plunge` (R1 t-test, first, single fwd door) → `saltwater` (R2 Wilcox) → `warm_baths` (R3
ANOVA+Tukey) → `springs` (BOSS, `puzzleType 2`, `isBoss`, deliverable figure+codec) → `piste` (ESCAPE,
`lock`, `escapeDone`). Secret-passage doors connect them (no separate interstitial scenes — the doors'
`doorPrompt`s depict the spiral stair / ladder). Bell-cords live in the practice rooms (2 in cold plunge
per Lucas, 1 saltwater, 2 warm baths) as the escape control.

**Art prompts stripped to puzzle-relevant elements (REVISED 2026-07-24, Lucas).** The scene prompts no
longer carry outdoor views / windows / the rival funicular / storm-clearing / mountain vistas — those
distract the image model. Each prompt now focuses on what must render correctly: the **pools, their
CANDLE CLUSTERS** (varying counts + heights = the escape's recognition signal), the control panel, the
doors, the bell-cords. The **springs prompt foregrounds the FIVE PAIRS of pools with distinct candle
distributions** (some pairs one pool clearly out-candled, some matched) — the load-bearing render for the
escape. The **rival-approach CLOCK moved into the `entry` cards** (funicular climbing → near the top →
all but arrived). Done via `_scratch/strip_art_prompts.py` (re-runnable; asserts no funicular/window/
vista cues remain). Consequence: the old "dark→light by location" arc is softened to a candlelight-led
**pre-dawn → dawn** cue (indoors candlelit; springs blue pre-dawn; piste first dawn light) — kept subtle
so it doesn't reintroduce vista clutter. Palette held: warm candle-amber + cool teal shadows.

**Puzzle content authored PRE-ART (2026-07-24).** Not just designNotes — the full MCQ payloads
(`starterCode` + `question`: prompt, 7 options, correct index, `maxAttempts`, `feedback.correct` +
3 method-hints) are filled onto each puzzle's `plannedHotspots` entry, plus clue `body`s and the escape
lock `answer`, via `_scratch/fill_puzzle_content.py` (re-runnable). The harness `_attach_planned_content`
copies these onto the placed boxes at commit (matched by `(type, slug(label))`). Correct indices varied:
cold_plunge 0, saltwater 2, warm_baths 1, springs 3. Entry cards written for all rooms except room 1.

**All 5 rooms need NEW art.** `coverPrompt` drafted (steaming spring + amber candle under a peak).
Music: none chosen (TBD — no `youtube_audio` row fired). `ambient: "snow"` (may need a new particle or
fallback). Debrief authored (top-level + per-room).

**Flagged for the build/wiring phases** (also in `AGENTS.md`): (1) the escape needs **mechanic #16
bell-pull + #8 state-gate** engine (unbuilt; spa is #16's first consumer); (2) **WebR support** for the
course stats wrappers is untested; (3) **decoder** `SPA_KEY` (id 12) to be added at wiring with varied
correct indices; (4) the **candle-cluster art** must make clearly-different vs clearly-matched pairs
unambiguous (recognition fairness).

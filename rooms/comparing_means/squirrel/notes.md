---
authority: intent
---

# Squirrel / forest scenario (draft) — Comparing Means

Chapter `comparing_means`, scenario `squirrel` (working name — see judgement calls). **Idea captured
2026-07-25 (Lucas, session "squirrel").** Draft only — nothing designed, verified, or built yet. This is
the **premise capture + first read**, before the PUZZLE phase (`escape_room_puzzles`) proper. It is the
**second** scenario in the `comparing_means` chapter folder, sibling of `spa`.

**This is the spa's pre/post TWIN, NOT the todo's MANOVA scenario.** The spa notes' "Pairing" section
explicitly flagged that `spa` had *no twin planned* and wanted "a second comparing-means scenario
mirroring t → Wilcox → ANOVA → pairwise on other data." This squirrel scenario **is** that twin: same
technique ladder, different world + dataset, for pre/post testing. The `comparing-means II` item in root
`todo.md` is a *different* scenario (MANOVA / PERMANOVA — a curriculum extension needing a book change
first); do **not** conflate the two.

No codec id scaffolded yet (assign from `scenario_inventory.json` `next_free_id` at the PUZZLE/design
phase, like spa took 12).

## Lucas's premise (verbatim intent, 2026-07-25)

- The player **is a squirrel** in a **forest**, moving **between trees** and solving puzzles. The squirrel
  is **quite self-aware** (a knowing narrator).
- **Dataset:** a **re-skinned Hawai'i aquifers** set, re-themed to the **nut-production characteristics of
  different types of trees**.
- **Objective:** statistical tests **building from t-tests through to ANOVA** (the chapter ladder).
- **Goal / stakes:** discover **which type of tree, from where, in which location produces the best nuts** —
  because the squirrel wants to **plant them there**. (Multi-axis: tree *type* × *location/where* × the
  nut measure.)
- **Signature travel mechanic — JUMPING tree to tree.** Jumping is emphasised throughout: there is **one
  interstitial "transition" room before each jump**, and that room makes it clear whether the jump is
  **upward, downward, or on the same level**. **These jumps ARE the escape's data source (clarified
  2026-07-25):** by moving up/down/level between trees, the player *learns the trees' heights by eye*.
  Visiting ~3 trees of each leaf-colour, they build a felt sense of each colour-group's height.
- **Leaf colour** is a per-tree visual identity: every tree has one of **four leaf colours — red, gold,
  green, silver** (updated 2026-07-25 from red/green/blue/yellow). Colour is the escape's grouping axis.
- **Escape — a data-free ANOVA compact-letter-display on tree HEIGHTS (clarified 2026-07-25).** The player
  does a **rough, by-eye ANOVA grouping of the leaf-colour populations by the heights they learned through
  jumping** — no console, no dataset, pure recognition. The height groups are engineered **obvious**: all
  gold trees tall, all silver trees short, red and green trees the same medium height →
  **CLD = A, B, B, C** (gold=A tall, red=B & green=B medium, silver=C short). The player fills the 4×4 grid
  (leaf colours × letters a/b/c/d) with that grouping. **This is a genuine data-free meta-echo** of the
  boss's Tukey/compact-letter move, re-posed on in-world heights instead of the nut data — so it fully
  satisfies the escape skill's "recognition, decoupled from the dataset" rule.

## Why this premise is well-aimed (my read)

- **It fills a real gap.** It is exactly the spa's missing pre/post twin — same t → Wilcox → ANOVA →
  pairwise backbone, a genuinely different surface (forest vs Nordic spa, hawaii-skeleton vs
  tequila-skeleton). Pre/post-test convention satisfied.
- **The goal maps straight onto grouping variables.** "Which tree *type*, from *where*, in which
  *location*" is naturally group_by across two categorical axes → the ANOVA / pairwise rungs. Clean fit.
- **The CLD escape is a genuine comparing-means artifact.** A compact letter display *is* the standard way
  to report "which groups differ" after Tukey — a 4-colour × 4-letter grid is an elegant, on-technique
  finale. **Resolved 2026-07-25:** the boss computes a CLD on the *nut data*; the escape re-poses the same
  CLD move by eye on *tree heights* — a matched pair, boss-computed vs escape-recognised. Both live.
- **The jump mechanic embodies the world** the way the skill's "signature travel mechanic" lever wants, and
  the up/down/level transition rooms are a tidy device.

## Judgement calls / open questions — FOREGROUND for Lucas

These are the things worth Lucas's steer before the PUZZLE phase; none is a blocker, all are real.

1. **~~The escape conflicts with the "data-free recognition" rule.~~ RESOLVED 2026-07-25 (Lucas).** The
   escape is **not** computed from the nut dataset. The player learns tree **heights by eye** through the
   jump mechanic (up/down/level), then does a **rough by-eye ANOVA grouping of the leaf-colour populations
   by height** — pure recognition, no console. The heights are engineered obvious (gold tall / silver short
   / red≈green medium → **CLD A,B,B,C**). This is a textbook **data-free meta-echo**: the same
   compact-letter cognitive move as the boss, re-posed on in-world heights, decoupled from the CSV. The
   boss's computed CLD (on nut data) and the escape's by-eye CLD (on heights) are a matched pair — the
   cleanest possible mapping. Nothing to change; the design now *satisfies* the skill rather than fighting
   it. (Full seed captured in *Escape seed* below, per the skill's "note the boss's core move, design the
   escape in the STORY phase" rule.)

2. **Setting overlap with the existing `wrangling/trees` scenario.** `trees` ("The Collector's Vault") is
   *already* an alien forest canopy with a **jump/monorail-between-stations** travel mechanic — and
   `candidate_locations.md` explicitly flags "Ancient misted forest — Overlaps `trees`, avoid unless
   re-themed." A squirrel-jumping-between-trees forest is very close to it. Needs either a **deliberate
   re-theme** so it reads distinct (different forest character, different jump *feel* — canopy-hop vs
   monorail), or a conscious call that a forest can host two scenarios in different chapters. Worth settling
   before art.

3. **Dataset — `hawaii_aquifers` is the chapter's OWN worked example, and likely needs engineering.**
   - The chapter (`10_comparing_means.Rmd`) uses `hawaii_aquifers` for its § *pairs of means* worked
     example (`aquifer_code` facets, Na vs Cl) — so it "risks feeling like the lecture." Re-skinning the
     *surface* to nuts mitigates that, but the underlying numbers being the lecture's is a mild risk. Flag.
   - **Structure (inspected):** `aquifer_code` (10 levels) × `well_name` (101) × `analyte` (9) → `abundance`;
     plus `longitude`/`latitude` (mostly `NA` in the raw). Natural mapping: **aquifer → location/grove (10),
     well → individual tree (replicate), analyte → nut characteristic (9), abundance → the measured value.**
   - **But the premise wants tree *type* AND leaf *colour* as grouping axes**, which the raw set does not
     carry — they'd have to be **overlaid/engineered** onto the well/aquifer skeleton (assign each tree a
     type and a colour, then regenerate measures from an additive effect model so each axis genuinely moves
     the number — exactly the spa/`trees` engineering move). Expect this to be an **engineered re-skin**,
     not a raw ship. Confirmed properly in the PUZZLE phase.
   - The escape's **4-colour CLD needs colour to be a real grouping axis with enough replicates per colour**
     and a **clean, verifiable letter grouping** (e.g. some colours share a letter, one stands alone) —
     that almost certainly must be **engineered**, like spa's Simpson flip and Shapiro/Levene failure.

4. **~~Height mechanic is travel-flavour, not tied to the stats.~~ RESOLVED 2026-07-25 (Lucas):** the
   heights **ARE the escape**. The up/down/level jumps teach each leaf-colour population's height, and the
   escape is the by-eye ANOVA/CLD grouping of those heights. Height now pays off fully — it's the escape's
   entire data source (kept deliberately *out* of the graded nut dataset so the escape stays data-free).

5. **The self-aware protagonist vs the house "earnest, never jokey" voice — and the protagonist itself.**
   Lucas is **open to dropping the squirrel** ("it doesn't quite fit the vibe") — the load-bearing idea is
   *a player moving between locations at different heights, where the heights are repeated samples of
   distinct populations*, not specifically a squirrel. STORY-phase call: keep a knowing squirrel but pitch
   it *dry and warm* (not winking), or swap to a protagonist that carries the earnest forest mood better.
   Flagged for the story phase; the puzzle/data design below is protagonist-agnostic.

6. **Working name / folder.** Scenario folders are usually **place-named** (alaska, spa, henges, temple,
   japan, egypt, trees). This is captured under `squirrel/` (protagonist) because "trees"/"forest" collide
   with the existing `wrangling/trees` scenario and "squirrel" is unambiguous to search. Swap to a
   place-style name at design time if preferred (e.g. a named grove/canopy) — especially if the squirrel
   protagonist is dropped (JC #5).

## Protagonist & setting options (for the STORY phase — captured 2026-07-25, Lucas mulling)

The load-bearing idea (Lucas): *a player moving between locations at different **heights**, where the
heights are repeated samples of distinct **populations** (trees by leaf colour), aiming to find the best
population to propagate.* Not specifically a squirrel. Requirements any pick must satisfy: (a) **vertical
traversal** so the up/down/level jump beats read naturally (this teaches the escape's heights); (b) a
believable reason to **want to plant/propagate the best nuts**; (c) **earnest, mood-matched** tone (house
rule); (d) **distinct from `wrangling/trees`** (alien glowing canopy + monorail + clifftop vault).

**Protagonist candidates**
- **A seed-caching bird — Clark's nutcracker or a jay (RECOMMENDED).** Nutcrackers/jays *literally* cache
  and plant tree seeds — "wants to plant the best nuts where they'll thrive" is their actual ecology, no
  contrivance. Flight gives effortless up/down/level traversal between canopy heights. Earnest, charming
  without the squirrel's cartoon tension, and real-ecology grounds it far from the alien `trees`.
- **An arborist / forester / field botanist (human).** Climbs canopy walkways/ropes between research
  platforms, samples nut yields, picks a cultivar to propagate for an orchard. Fully grounded, earnest,
  professional. Traversal = climbing/walkways. Least whimsical option.
- **A reforestation drone / seed-planting robot.** Surveys the canopy, measures, decides where to drop seed
  pods. Modern conservation tone; flies (vertical traversal natural). Risk: cooler/less warm.
- **A brachiating canopy animal — gibbon / lemur.** Swinging between trees is gorgeous vertical traversal,
  but the "plant nuts" motive fits a *caching* animal (bird/squirrel/agouti) better than a swinger.
- **Keep the squirrel, pitched earnest.** A diligent, quietly-anxious squirrel forester — viable if the
  self-awareness stays dry/warm, not winking.

**Setting candidates** (distinct from `trees`' alien monorail canopy)
- **Montane / boreal / cloud forest** (misty, vertical, epiphytes) — pairs with the bird; real, earthy,
  visually unlike the alien canopy. Strong default.
- **Terraced orchard / arboretum / botanical garden** — cultivars at different heights + a propagation
  glasshouse; fits "plant the best" literally. Pairs with the arborist.
- **Redwood/sequoia grove** — extreme heights, dramatic vertical traversal.
- **Mythic World-Tree / grove of the ancestors** — branch-levels as floors, sacred leaf-varieties, a
  forest-spirit protagonist; more fantastical (watch the earnest-tone + `trees`-distinctness bars).

**Grounding bonus — the four leaf colours map to REAL trees**, if we want to anchor them: **silver**
(silver birch / whitebeam), **gold** (ginkgo / golden aspen), **red** (red maple), **green** (oak). Lets the
populations be recognisably real species while keeping the colour-coded identity.

**My recommendation:** a **seed-caching bird (nutcracker/jay) in a montane/boreal or cloud forest** — best
thematic fit for "plant the best nuts," natural vertical flight for the height mechanic, earnest, and
cleanly distinct from `trees`. Arborist-in-an-arboretum is the strong grounded runner-up. Decide in the
STORY phase; the puzzle/data design above is protagonist- and setting-agnostic.

### DECISION (2026-07-25, Lucas): the BIRD + "the real"

Lucas chose **the seed-caching bird protagonist** and the **real-tree grounding**. Refinement I took:
**a JAY, not a Clark's nutcracker** — nutcrackers cache *pine seeds* (conifer/montane), but a **jay caches
acorns & nuts and famously plants oaks**, which fits both "nut production" and the real deciduous species
below far better. (Flagged for Lucas to override back to a nutcracker if he prefers the montane look.)
- **Protagonist:** a jay — a seed-caching corvid that wants to find the best nut-trees and cache their
  seeds where they'll thrive. Earnest, real-ecology; dry warmth, no cartoon winking.
- **Setting:** a **real temperate mixed-deciduous forest** (leaning autumn, for the colour + earnest mood),
  vertical enough for the up/down/level flight beats; deliberately earthy/real to stay distinct from
  `trees`' alien monorail canopy.
- **The four leaf-colour populations grounded in REAL trees:** **silver** = silver birch, **gold** = ginkgo
  / golden aspen, **red** = red maple, **green** = oak. Keeps the colour-coded identity while making each
  population a recognisable species. (Nut/seed framing: acorns from oak, samaras/"nuts" stylised across the
  others — the dataset's "nut" is a stylised seed-crop measure, not botanically literal per species.)
- Carried into the STORY phase below.

## Chapter alignment (the ladder backbone — same as spa)

Same chapter, same ordered technique sequence as the spa notes lay out (read there for detail):
**test selection (Shapiro + Levene) → two means (t / Wilcox) → more-than-two means (ANOVA + Tukey /
Kruskal + Dunn) → pairs of means (pairwise t/Wilcox + multiple-comparison correction).** The squirrel
premise's "t-tests building to ANOVA" plus a CLD finale lands squarely on this. The exact reverse-
engineered rung-by-rung ladder + the taught trap + every verified single-winner answer are **PUZZLE-phase
work** (`escape_room_puzzles`), not decided here.

## Analog grounding (Step 0 — carried over from spa, same technique)

Comparing means by hand = **eyeball two groups and judge whether the gap is real or just noise.** For a
squirrel: are *these* trees' nuts genuinely fatter than *those*, or is it just this year's wobble? Same
intuition as the spa's barista/gardener — reused because it's the same chapter.

## Engineered dataset + verified ladder (BUILT 2026-07-25, session "squirrel") — PUZZLE PHASE

Codec **id 13** (from `scenario_inventory.json` `next_free_id`; not yet scaffolded — assign at design).
Generator: `_scratch/build_nut_census.py` (deterministic, **seed 20260725**) → **`data/nut_census.csv`**
(1,536 rows, 72 KB, web-friendly; md5 stable across re-runs). Public URL once the site is pushed from the
Mac: `https://thebustalab.github.io/escape_rooms/rooms/comparing_means/squirrel/data/nut_census.csv`.

**Reskin (per the puzzle skill — keep the categorical skeleton in spirit, regenerate the measures).**
Hawai'i aquifers' shape (location × entity × parameter × value, long format) re-skinned to a forest:
**6 groves × 4 leaf-colours × 2 trees/cell = 48 trees**, **4 nut readings** per tree per parameter,
**8 nut parameters**. Columns (student-facing): **`tree, leaf_colour, grove, parameter, replicate, value`**.
Balanced design (every grove holds all 4 colours equally) so the two grouping axes are independent and
clean — no Simpson confound here (unlike `trees`); the taught trap is the boss's multiple-comparison
correction instead.

**Two axes deliberately sit on SEPARATE metrics** so every rung's grouping distribution stays unimodal
(controllable normality) and each axis genuinely moves its own number:
- **GROVE (location)** drives `kernel_mass_g` (R1) and `oil_content_pct` (R2, right-skewed).
- **LEAF COLOUR (type)** drives `kernel_yield_ct` (R3) and `nut_quality_index` (BOSS).
- 4 filler nut params (`protein_pct, moisture_pct, shell_hardness, nut_diameter_mm`) carry no structure —
  realism + a legitimate wrong-parameter/wrong-axis distractor (grouping the wrong metric finds nothing).

**VERIFIED ladder (re-run the generator to reconfirm; deterministic; strictly monotonic; tracks chapter
order t → Wilcox → ANOVA+Tukey → pairwise+correction — the SAME backbone as `spa`, its pre/post twin):**

- **Room 1 — groves × kernel mass — TWO MEANS, t-test.** `Sunhollow` (31.13 g) vs `Downbriar` (28.29 g).
  Shapiro passes both (p 0.97, 0.60), Levene passes (p 0.12) → **t-test p = 7.1e-8, significant**
  (Sunhollow heavier by +2.84 g). Teaches: run Shapiro/Levene → pick t → read it. Single clean winner
  **Sunhollow**.
- **Room 2 — groves × oil content — TWO MEANS, non-parametric — THE t-TEST GIVES THE WRONG GROVE
  (sharpened 2026-07-25).** `Larkspur` vs `Emberfen`. Larkspur is genuinely oilier for a typical tree
  (**median 14.18 %**, tight, normal); Emberfen's typical tree is poorer (**median 10.46 %**) but a couple
  of freak **"gusher" trees** throw extreme outliers. Result: **Emberfen's MEAN (16.92 %) exceeds
  Larkspur's (14.03 %)** — so a naive **t-test names Emberfen (WRONG)** / reads n.s. (t p = 0.18). But
  **Shapiro FAILS hard on Emberfen** (p ≈ 0, bimodal) → the correct tool is **Wilcox**, which ranks
  **Larkspur** significantly oilier (**p = 7.3e-4, RIGHT**). Teaches the fused **mean-vs-median outlier +
  test-selection** trap: on skewed data the mean (and the t-test) is fooled by outliers; check normality,
  use the rank test, trust the median. Correct winner **Larkspur**. *(Naive-method distractor = Emberfen.)*
- **Room 3 — leaf colours × kernel yield — MORE THAN TWO MEANS, ANOVA + Tukey.** green 43.02 /
  red 39.77 / silver 39.67 / gold 39.64. Shapiro/Levene pass → **ANOVA p = 4.2e-14**; **Tukey** isolates
  **green** (green vs each other p < 1e-8; the other three mutually n.s.) → single clean winner **green**,
  margin **+3.25** over the runner-up. Teaches: ANOVA says *something* differs, post-hoc says *which* —
  and introduces the **compact-letter idea** the boss + escape build on.
- **Boss — leaf colours × nut quality — PAIRS OF MEANS, pairwise + multiple-comparison correction → CLD
  (THE TAUGHT TRAP).** green 77.00 / gold 75.52 / red 69.00 / silver 67.52. All 6 pairwise comparisons,
  **Tukey-corrected**. **Naive uncorrected pairwise calls all four colours mutually different (a,b,c,d)**;
  **corrected, two collapse away** — **gold-green** (raw p 0.041 → Tukey 0.124) and **red-silver** (raw
  p 0.019 → Tukey 0.123) are the flips. **Corrected compact letter display: {green, gold} = A (top),
  {red, silver} = B (bottom)**; the two clusters differ robustly (all cross-pairs p ≈ 0). The generator
  **asserts** both flips and the two-cluster CLD. Teaches: uncorrected pairwise over-reports; correcting is
  mandatory. **Boss deliverable:** the corrected CLD of the 4 colours for nut quality (= which tree types
  are genuinely tied vs genuinely different) + the "best nuts" answer (green/gold tier, from Sunhollow per
  R1). This is the **same technique family as spa's Holm-corrected pairwise boss** (correction method
  differs — see JC).

**Documented departures from raw hawaii (per skill).** (1) Values fully regenerated from an additive
effect model (hawaii measured water analytes; we model nut production) — only the long-format
location×entity×parameter *shape* is reused, not hawaii's numbers or its irregular 3–30 wells/aquifer
counts. (2) A **balanced** 6×4×2 design replaces hawaii's ragged well counts, so grove and colour are
independent. (3) **Colour** and **height** axes are *added* (raw hawaii has neither). (4) Each axis put on
its own metric (see above) — a deliberate simplification so every rung is unimodal and single-winner.

### Escape seed (boss's core cognitive move — designed in the STORY phase, NOT here)

Per the skill, the escape is designed later, with the world. Seed for `escape_room_story`: **the boss's
core move is "produce the compact-letter grouping of the 4 tree types."** The escape re-poses that exact
move **data-free, on tree HEIGHTS learned by eye through the jump mechanic** (up/down/level travel beats),
NOT on the nut dataset. Heights are engineered **obvious** and kept **out of `nut_census.csv`** (like spa's
candles): **gold tall (A), red ≈ green medium (B, B), silver short (C) → CLD = A, B, B, C**. Boss CLD
(computed, on nuts: {green,gold}/{red,silver}) and escape CLD (by eye, on heights: gold / red≈green /
silver) are deliberately **different groupings** so the escape isn't a giveaway of the nut analysis —
same cognitive move, independent content. (Do NOT pin the 4×4-grid props/answer here; that's story/design.)

### Puzzle-type assignment, distractors & shape checks (checklist close-out)

**Puzzle-type per room + variety** (analysis-side types from `notes/puzzle_types_design_notes.md`),
mirroring spa's spread: **R1 Compute-the-Key** (run t, read it) → **R2 Classify-the-Unknown → Compute**
(read Shapiro/Levene, *choose* Wilcox, then run) → **R3 Compute-the-Key + post-hoc** (ANOVA then Tukey to
name which) → **Boss verdict/deduction over the CLD** (assign the corrected letter grouping, not a single
key) → **Escape recognition** (by-eye height CLD via the jump mechanic; ungraded). Genuine variety, not
four identical cards. **Engine note (avoids an unbuilt-engine dependency on a GRADED room):** the boss is
**graded on the existing MCQ/`lock` engine** — its options are candidate tierings (correct =
{green,gold}/{red,silver}; the trap = "all four differ"; other subsets) — the "verdict-grid" is
presentation flavour, **not** the unbuilt #9 deduction-ledger. So all four graded rooms (R1-R3 + boss) run
on the **built** MCQ engine; the only unbuilt-engine dependencies are in the **ungraded escape** (#15
grid-select + #18 elevation beat), flagged below.

**≥6-distractor availability** (final text at wiring): **R1/R2** (2 groves → <6 levels) use wrong-method
distractors — wrong direction, "not significant", used the wrong test (t vs Wilcox), wrong parameter,
"variances unequal so can't test", read the wrong grove. ✓ **R3** (4 colours) — the 4 colours + wrong-method
(grouped by grove → no colour effect, wrong metric, skipped post-hoc, lowest instead of highest). ✓
**Boss** — the correct CLD {green,gold}/{red,silver} + the naive "all four differ" trap + other groupings
({green} alone / {green,gold,red} / three-cluster) + "none differ". ✓

**Long-format / table-shape check.** Data is long (`tree × parameter × replicate`); every analysis filters
to one `parameter` and groups by `grove` or `leaf_colour`, summarising `value` — no per-entity column
duplication. Verified by computing each answer straight off the shipped CSV in the generator. ✓

**Each grouping axis moves its number** (skill: no empty rung). grove moves kernel_mass (R1) & oil (R2);
colour moves kernel_yield (R3) & nut_quality (boss) — all verified. By design grove does *not* move the
colour metrics and vice-versa (the separate-metric departure) — this is intentional and supplies
wrong-axis distractors, not an empty rung.

### PUZZLE-phase judgement calls flagged for Lucas

- **Boss correction method: Tukey (built) vs Holm (spa's).** spa's boss corrects with **Holm** (the course
  wrapper default); this boss uses **Tukey HSD**. Both are honest, taught multiple-comparison corrections,
  and Tukey is the natural partner of ANOVA+CLD. I chose Tukey because **Holm's step-down makes a
  CLD-changing flip nearly impossible to engineer robustly** (both within-cluster pairs would have to land
  in the razor-thin (0.025, 0.05) window simultaneously). Tukey (no step-down) gives a robust two-cluster
  flip. **If you want maximal spa-parity, we can switch the wiring to Holm** and accept a single, more
  fragile flip (or re-pitch the boss to spa's faceted-pairwise-across-groves shape). My recommendation:
  **keep Tukey** — it's cleaner, matches the CLD framing, and the *technique* (pairwise means + correction)
  is identical to spa.
- **Separate-metric axes.** grove-metrics and colour-metrics are disjoint (see departures) so "best grove"
  (Sunhollow, by kernel mass) and "best type" (green/gold, by quality) come off different measures. Clean
  and gives good distractors, but if you'd rather one headline metric carry BOTH axes (so "best type from
  best grove" is one analysis), say so — it's a data-model change (re-introduces within-group mixture, needs
  care to keep normality). Default: keep separate.
- **~~Sharper R2 trap (optional).~~ DONE 2026-07-25 (Lucas asked).** R2 now makes the **t-test give the
  wrong grove**: Emberfen's gusher outliers pull its *mean* above Larkspur's while its *median* stays
  below, so naive means/t → Emberfen (wrong), Wilcox → Larkspur (right). The scenario now has **two**
  taught traps (R2 mean-vs-median/test-selection, boss multiple-comparison). Minor engineered artificiality
  noted: Emberfen (a fen) is deliberately the "spiky gusher" grove — narratively a marsh with a few freak
  oil-rich trees. If that reads as too convenient, we can soften the bonus/probability.
- **Escape-vs-boss CLD independence.** Boss nut-CLD ({green,gold}/{red,silver}) ≠ escape height-CLD
  (gold / red≈green / silver) on purpose. Confirm you like them decoupled (recommended) rather than the
  heights echoing the nut grouping.

## Next steps (pipeline)

**PUZZLE + STORY + DESIGN COMPLETE; DESIGN REWORKED twice 2026-07-26 → final = CIRCLE, 13 nodes (see
`## Design record v3`; v2/v1 kept as history). Grid-select engine BUILT.** Next: *[Lucas: harness art on
`:8751`, 13 unique scenes]* → `escape_room_wiring` (apply the canyon authoring recipe, decoder `JAY_KEY`/id
13, sfx, tests, **browser-playtest the grid**). **No git commit on this box** (Mac-only repo).

## Design record v3 — CIRCLE layout + grid engine (`scenario.json`, 2026-07-26b, session "squirrel")

**Reworked again from the 16-node open-maze (v2) to a clean CIRCLE (13 nodes, exactly 2 doors each)**, at
Lucas's direction. Ladder/answers/dataset still UNCHANGED. Built by the rewritten `_scratch/build_scenario.py`;
graph verified (2 doors/node, all bidirectional, all 13 reachable). Four decisions from Lucas this turn:

1. **Each tree its own UNIQUE art** — 8 tree scenes (4 survey-trees with a lantern + 4 empty/atmospheric),
   no reuse. 13 unique scene arts total.
2. **Escape UNGATED on the leaps** — dropped the `heights_read` counter entirely. A clever player can infer
   the height grouping from a handful of leaps, and tracking which leaps are done is annoying. The grid is
   gated only on the **survey being complete** (`availableWhen {allSolved: the 4 survey-trees}` + lockedBody),
   not on leaps.
3. **Grid-select engine BUILT** — the roost cache-frame is now a real `grid` hotspot (mechanic #15),
   implemented in `shared/pano-player.js` (`openGrid`/`buildGridCard`) + `.gridsel` CSS; ungraded like a lock,
   solving it fires `escapeDone`. **Logic-tested (JS `node --check` passes); browser-test pending** — verify
   in `play.html`. First consumer of #15.
4. **CIRCLE layout** (not the all-connected K4, which gave 5 doors/room; not hub-spoke, which gave 8 from the
   Mother Oak). Single ring, 2 doors each:
   `mother_oak – red_a – red_b – t_rg – green_a – green_b – t_gg – gold_a – gold_b – t_gs – silver_a –
   silver_b – roost – (mother_oak)`. **The permutation math:** a 2-door ring is a *cycle*, which has few
   edges, so it **cannot carry all 6 pairwise transitions** (K4 has 6 edges; a 4-zone ring has 4, and with
   the Mother Oak + roost occupying ring slots, only **3** transitions are cleanly flanked). The 3 kept —
   **red-green LEVEL, green-gold UP-one, gold-silver DOWN-two** — teach the full height order directly + by
   transitivity (gold high, red=green mid, silver low; the missing red-gold & green-silver pairs are
   inferable). Since the escape is ungated (decision 2), partial coverage is fine — exactly Lucas's intent.
   The tree→rung mapping shifted to follow ring order for smooth flow: **red_a=R1, green_a=R2, gold_a=R3,
   silver_a=boss** (correct indices 1/2/0/3). The boss sits at the silver birch but analyses all kinds.

**Flagged:** the grid is **4 kinds × 3 height-tiers** (Tallest/Middle/Lowest), not the "4×4" of the early
sketch — the data has 3 height levels (two kinds tie in the middle, which *is* the CLD lesson). Easy to add a
4th empty tier if the 4×4 look is wanted. And the "serve next in queue" behaviour is the canyon
fixed-puzzle-per-tree + availableWhen chain (a *true* any-tree-serves-next dynamic queue would need a further
small engine feature — not built).

## Design record v2 — OPEN-WORLD rebuild (`scenario.json`, 2026-07-26, session "squirrel") — SUPERSEDED by v3

**Reworked from the 5-room linear draft (v1 below, kept as history) to an OPEN-WORLD 16-node forest** on
the **canyon maze model**, at Lucas's direction (this session). Cross-scenario model + engine grounding:
`../../notes/open_world_and_temporal_arc.md`. Built by the rewritten `_scratch/build_scenario.py`
(re-runnable); graph validated (no dangling doors, all bidirectional, all 16 reachable from `mother_oak`).
**Ladder, verified answers, dataset, and the 4 graded MCQ payloads are UNCHANGED** — only the room/graph/
scene design changed.

**Why the rework (Lucas, 2026-07-26):** (1) *open world, ordered puzzles* — the whole wood is roamable from
the start; ordering lives on the survey lanterns (`availableWhen` chain), not on closed doors. (2)
*backtrack-safe environment* — place-constant art + a global `leaves` ambient instead of a baked
morning→snow arc, so revisiting a stand to study heights never ships the player backwards. (3) *the heights
ARE the escape's data* — 8 tree rooms (2 reps × 4 colours) + 6 pairwise transition rooms let the jay learn
every kind's height by flying; the escape unlocks once all 6 pairwise gaps are felt.

**16 nodes** (all `built:false`; 10 unique scene arts). **Hub/START `mother_oak`** (mysterious cache-frame
foreshadow) → **8 tree rooms** (4 colour-zones × 2: survey-trees `red_a`/`silver_a`/`gold_a`/`green_a` carry
R1/R2/R3/boss availableWhen-chained; height-trees `*_b` are pure repeated-sampling) → **6 transitions**
(K4 edges; each demonstrates a pairwise height gap and does `onPickup:{inc:'heights_read'}`) → **`roost`**
(phase:escape, Mother Oak heartwood; the height-CLD `lock`, gated `{gte:['heights_read',6]}`). Puzzle-tree
correct indices unchanged: `red_a` 1, `silver_a` 2, `gold_a` 0, `green_a` 3.

**Art reuse (keeps 16 nodes → 10 arts):** 4 colour-tree arts (each shared by `_a`+`_b`), 4 transition arts
by tier-relationship (high-mid ×2, mid-low ×2, high-low ×1, level ×1), + `mother_oak` + `roost`. Lucas
accepted the ~doubled art bill; the transitions are full 360 rooms (load-bearing — the height difference is
the whole point) and are reused per height-relationship.

**Engine:** relies on the **canyon open-maze engine** (`availableWhen`/`lockedBody`/`direction:"open"`/
`onPickup`/`condOK {gte}`), BUILT 2026-07-26 (browser-test pending). Still-unbuilt: **#15 grid-select** for
the roost cache-frame (authored as a `lock` with the CLD answer meanwhile). Applied per the **canyon
authoring recipe at wiring** (see `AGENTS.md`).

**Judgement calls flagged:** the `heights_read` gate is `gte 6` (all pairwise transitions) — tunable down
if the full K4 traversal reads as tedious in playtest. The "serve next in queue" behaviour is realised as
the canyon **fixed-puzzle-per-tree + availableWhen chain** (a *true* any-tree-serves-next dynamic queue
would need a further small engine feature — flagged, not built). Grove-based rungs (R1/R2) are served at
colour-trees as a two-layer design (world = colour/height; puzzles = the nut-data survey), like spa's
water-chem-vs-candles split.

## Design record v1 — 5-room LINEAR draft (2026-07-25) — SUPERSEDED by v2 above (kept as history)

*(This linear design was replaced by the open-world rebuild on 2026-07-26; retained for the record.)*

## Design record (DESIGN phase — `scenario.json` built 2026-07-25, session "squirrel")

**`scenario.json` written + validated (parses; id 13; 5 nodes).** Built by `_scratch/build_scenario.py`
(re-runnable initial emit; edit `scenario.json`/harness directly after). Inventory regenerated
(`authoring/scenario_inventory.py`) → squirrel registered id 13, `next_free_id` 14, no duplicate ids.
Durable facts (ladder + answers + engine flags) live in the new **`AGENTS.md`** (`authority: canon`).

**5 nodes** (all `built: false` stubs; each has `scenePrompt`+`doorPrompt`, `plannedHotspots` with full
pre-art MCQ payloads, a full `designNote`, a `debrief`, and an `entry` card except room 1):
`hollow` (R1 t-test, first, single fwd door) → `fen` (R2 Wilcox + mean/median trap) → `kinds` (R3
ANOVA+Tukey) → `crown` (BOSS, `puzzleType 2`, `isBoss`, deliverable figure+codec) → `roost` (ESCAPE,
`lock`/grid-select, `escapeDone`). Forward doors = branch-leaps (gated on solve) carrying the #18
up/down/level beat (R1→fen DOWN, fen→kinds UP, kinds→crown UP, crown→roost DOWN); back doors open.

**Puzzle content authored PRE-ART** (like spa): full MCQ payloads (`starterCode` + `question`: prompt, 7
options, correct index, `maxAttempts`, `feedback.correct` + 3 method-hints) on each puzzle's
`plannedHotspots`, plus clue `body`s and the escape lock `answer`. **Correct indices varied: hollow 1, fen
2, kinds 0, crown 3** (feed `JAY_KEY` at wiring). Puzzle interface skin = a brass **surveyor's lantern** on
a stump/bough (amber-glow house signature; a woodland-survey relic, keeps the no-people rule).

**Environmental arc baked into every `scenePrompt`:** crisp gold morning (hollow) → deep amber, leaves
falling (fen) → flat silver afternoon, wind rising (kinds) → first flurries, bare crown (crown) → settling
snow-glow (roost). Light/season arc (NOT elevation — the hops wander up/down to teach heights). The four
species are shown at their heights in every scene so the escape's by-eye grouping is fair.

**All 5 rooms need NEW art.** `coverPrompt` drafted (jay + ancient oak + amber hollow-glow at dusk). Music:
none chosen (TBD). `ambient: "snow"` (a "falling leaves" particle would suit the early autumn rooms — flag).
Debrief authored (top-level + per-room).

**Flagged for build/wiring** (also in `AGENTS.md`): (1) escape needs **#15 grid-select** + **#18 elevation
beat** engines (both unbuilt; squirrel is #18's first consumer) — graded rooms use only the built MCQ
engine; (2) **WebR support** for the course stats wrappers untested; (3) **decoder** `JAY_KEY` (id 13) at
wiring with the varied indices above; (4) the escape art must show the four species at **clearly-distinct
heights** (recognition fairness); (5) folder is `squirrel/` but the protagonist is a **jay** — consider a
folder rename at build.

## Narrative (STORY phase — drafted 2026-07-25, session "squirrel")

*All proper nouns below are drafts, flagged for Lucas: the title (**Seedfall**), the great-oak landmark
(**the Mother Oak**), and the four species pick (silver birch / golden aspen / red maple / green oak). The
grove names come straight from the dataset (Sunhollow, Downbriar, Mistmarsh, Thornevale, Larkspur,
Emberfen) — swap any.*

### Logline · stakes · clock (the three lines)
- **Logline:** A **jay**, in the last bright days before the snow, must work out **which trees in the wood
  grow the truly best nuts** — and cache their seeds in the ground where they'll thrive — one grove, one
  species at a time, as winter closes in.
- **Stakes (concrete):** a jay caches thousands of seeds each autumn, and the few it never comes back for
  become **the next century's forest**. This is **this** jay's one autumn to get it right. Plant the
  reliably-best trees in the best ground and it feeds generations; be fooled by a grove of lucky gushers or
  by splitting hairs that are really just noise, and the cache — and the forest it would have grown —
  fails. A quietly **self-aware** jay who knows the wood around it is one its mothers planted, and that
  what it buries now it will never see full-grown.
- **Clock:** **the first snow.** The survey must be finished and the master-cache made before the weather
  turns — leaves already thinning and falling, light going flat and cold, the first flurries arriving at
  the high boss vantage and settling on the Mother Oak by the finale. *(As the leaves fall the jay can no
  longer read the trees by colour and must rely on the **heights** it learned by flying — which motivates
  the escape.)*

### World (built from the analog)
Comparing-means analog = **eyeball two groups and judge whether the gap is real or just noise.** A jay
does exactly this by wing every autumn: *are these trees' nuts genuinely better than those, or just this
year's luck?* The world is a **real temperate mixed-deciduous wood in late autumn** — leaf-mould and frost
and low gold light — deliberately **earthy and real** to stand clear of `wrangling/trees`' alien glowing
canopy. Four kinds of tree, each a recognisable species carrying its colour identity: **silver birch
(silver), golden aspen (gold), red maple (red), green oak (green)**; the six **groves** are different
corners of the wood (a sunny hollow, a shaded brook-side, a boggy fen, a dry ridge…). **Landmark:** the
**Mother Oak** — the wood's oldest, tallest tree and the jay's winter **roost** — where the boss vantage
and the escape are sited, so the visit is *earned*: it's where a jay makes its master-cache and where it
will sit out the snow.

**Cast economy:** **zero other characters.** Only **you**, the jay (people never appear in the art; here,
neither do other animals as characters). The goal is **front-loaded** in the opening (survey the wood,
then cache the best at the Mother Oak before the snow), so no character need explain anything — every beat
is just the jay and the wood.

### Signature travel mechanic — flitting tree to tree (the #18 elevation beat)
The jay **flies from tree to tree**, and every hop is **up, down, or level** — shown on a short
interstitial before each jump (mechanic **#18**, `puzzle_inventory.md`). This is the world's distinctive
travel *and* the escape's secret teacher: across the whole survey the jay feels, in its wings, **how tall
each kind of tree stands** — gold aspens towering, silver birches low, red maples and green oaks in
between — without ever being told a number. By the finale that felt sense is all it needs.

### Environmental arc (hand to `escape_room_design`)
A **late-autumn day tipping into winter**, by time/season (the vertical hops wander up and down, so the arc
is the *light*, not elevation): **crisp gold morning** at the first groves → **deep amber afternoon, leaves
thinning** → **flat grey light, wind rising, more bare branches** → **first flurries** at the high boss
vantage → **snow settling on the Mother Oak** at the escape. Light cools and dims; the canopy goes bare —
so the colour-identities the jay relied on literally fall away, handing the finale to remembered height.
Mood: **earnest, weighty, sensory — the hush of a wood before snow.** Never jokey.

### Beats — one per rung (why the jay runs *this* test *now*)
- **Room 1 · two groves, kernel mass (t-test).** The jay opens its survey weighing nuts at two neighbouring
  stands — sunlit **Sunhollow** vs shaded, brook-side **Downbriar**. Are Sunhollow's nuts *genuinely*
  heavier, or does the sunny stand just *look* fuller? Weigh a handful from each, judge the gap against the
  scatter → **Sunhollow** is really heavier. The jay learns *where* a tree grows matters, and that the
  survey is worth continuing.
- **Room 2 · two groves, oil content (Wilcox — the tempting wrong grove).** Winter nuts must be **rich and
  oily**. The jay tests a dry ridge, **Larkspur**, against a boggy fen, **Emberfen**. Emberfen holds a few
  **spectacular "gusher" trees**, dripping with oil — and *on average* the fen looks the oilier ground. But
  a cache can't live on two jackpots among a stand of duds; the jay needs the **typical** tree to be rich.
  Looked at honestly — past the outliers, at the ordinary tree — **Larkspur** is the reliable ground.
  *(The story makes the fen's gushers the tempting answer; the careful read on the median/rank wins — the
  verified R2 trap, where the mean and a naïve t-test actually name the wrong grove, Emberfen.)*
- **Room 3 · four species, yield (ANOVA + Tukey).** Having learned that ground matters, the jay now asks
  *which kind of tree* to favour, and starts with sheer **yield** — how many nuts each species bears.
  Across all four kinds, the **green oak** out-bears the rest; the other three are much of a muchness. The
  survey narrows from *where* to *which*.
- **Boss · four species, nut quality (pairwise + correction — the misdirection) at the Mother Oak vantage.**
  The last question, and the hardest: which kinds make the **best nuts** for the cache? Compare all four,
  pair by pair. The tempting move is to rank them 1-2-3-4 and bury only the single "winner" — every kind
  *looks* a little different. But test enough pairs and some gaps are just noise; **correct for having
  compared so many**, and the four honestly collapse into **two tiers — green oak and golden aspen tied at
  the top, red maple and silver birch below.** The jay can't in honesty separate green from gold, and
  shouldn't pretend to. **Cache both top kinds** — that's the wise, humble answer the wood actually
  supports. *(Obvious = pick one "best"; correct = the {green,gold} / {red,silver} tiering — the verified
  boss CLD + multiple-comparison flip.)*

### Escape — the payoff (data-free meta-echo; the thematic climax)
By now the wood is nearly bare and snow is falling; the jay returns to the **Mother Oak** to lay down its
**master-cache** for winter. A jay files its caches by **height** — which level of the canopy a thing
belongs to — and the Mother Oak's old boughs form a natural **tiered roost**: a lattice of levels. To seal
the survey the jay must place each of the four kinds of tree **on the tier matching how tall it grows**,
**from memory of all its flying** — no numbers, no readings, just what its wings learned: **golden aspen on
the high tier (A), red maple and green oak together on the middle tier (B, B), silver birch on the low tier
(C).** Recognising that height-grouping — a **compact letter display built of branches**, tiers × kinds —
is the escape. It re-poses the boss's exact cognitive move (*sort the kinds into honest groups*) on the
**heights the jay felt by flying**, wholly decoupled from the nut data (the height tiers are deliberately a
*different* grouping from the nut-quality tiers — the finale is recognition, not a re-read of the survey).
Set the tiers right and the cache is sealed; the jay tucks its **last seed** into the Mother Oak — one
final motion — and settles into the roost as the snow comes down, the wood already, quietly, the shape of
next century's forest. *(Optional player-performed gesture: the final seed-tuck as a single ceremonial
state-change — one motion, meaning front-loaded, no second puzzle. The 4×4 grid = the roost lattice, four
kinds × four tiers a/b/c/d.)*

**Escape vs boss — deliberately different groupings.** Boss nut-quality tiers = {green,gold}/{red,silver};
escape **height** tiers = gold / red≈green / silver. Same cognitive move (honest grouping), independent
content — so the escape can't be back-solved from the survey. (Per the puzzle-phase decision; recognition,
not computation.)

### Voice notes
Earnest, concrete, sensory; a jay's-eye view with **dry warmth and quiet weight**, never winking. Ground
every line in the wood — the heft of an acorn in the beak, frost on leaf-mould, the cold coming up through
bare branches, wingbeats in still air, the smell of snow. The **self-awareness is about responsibility**
(*what I bury now, I'll never see full-grown; this whole wood, someone like me planted*), not comedy. Hold
the hush-before-snow mood; cards short.

### Draft story-map text (paste into the harness story-map; tighten there)
- **title:** *Seedfall* — **subtitle:** *A jay's last survey before the snow: find the trees whose nuts are
  truly best, and cache their seeds where they'll thrive.*
- **story (landing):** *The wood is going gold and cold, and the first snow is a day off, maybe less. You
  are a jay, and before the white comes you have one task that matters more than all your others: decide
  which trees here grow the best nuts, and bury their seeds in the best ground — because the few you never
  dig up again will be the forest your grandchildren fly through. So you start low, in the sunlit hollow,
  with a nut in your beak and a whole wood to weigh, hopping tree to tree — up, down, and across — the way
  a jay reads a forest.*
- **entry · Room 1 (Sunhollow / Downbriar):** *(first room — no card)*
- **entry · Room 2 (Larkspur / Emberfen):** *A hop down across the brook and the ground turns to bog: this
  is Emberfen, and a few of its trees are dripping with oil, richer than anything you've seen. Tempting. But
  a winter cache lives or dies on the ordinary nut, not the lucky one — look past the show, at the tree in
  the middle.*
- **entry · Room 3 (the four kinds):** *You climb into the thinning canopy where all four kinds of tree
  stand together — silver, gold, red, green. Enough of comparing corners of the wood; now you ask which
  kind to trust, and you begin the plain way: which simply bears the most.*
- **entry · Boss (Mother Oak vantage):** *A long flight up to the crown of the Mother Oak, snow starting to
  needle the air. From here you can see the whole survey at once. One question left — which kinds truly make
  the best nuts — and the easy answer, to crown a single winner, is the one to distrust.*
- **done (survey certified):** *You know it now: the reliable ground, and the two kinds of tree whose nuts
  are honestly the best. The wood has told you the truth, if you were careful enough to hear it.*
- **escapeDone (escaped / cached):** *The tiers hold; the cache is sealed in the Mother Oak's old boughs.
  You tuck the last seed away as the snow settles, and fold your wings into the roost — the wood around you
  already, quietly, the shape of the forest to come.*

### Story-phase judgement calls flagged for Lucas
- **Bird pick: JAY (not Clark's nutcracker).** Jays cache acorns/nuts and plant oaks — fits "nut
  production" + the deciduous species; a nutcracker would pull us to conifers/montane. Flagged if you'd
  rather the montane look. *(Confirmed direction: "the bird + the real," 2026-07-25.)*
- **Names** — title *Seedfall*, landmark *the Mother Oak*, species (silver birch / golden aspen / red maple
  / green oak) — all drafts; grove names are the dataset's. Swap any.
- **Escape framing = a height-tiered roost lattice at the Mother Oak** (4 kinds × 4 tiers, the #15
  grid-select fed by the #18 height beats). Confirm you like "file the cache by canopy height" as the
  in-world reason the jay groups by height — it's what makes the height mechanic pay off data-free.
- **Environmental arc = light/season (autumn→first snow), not elevation** — because the vertical hops wander
  up and down (they must, to teach all the heights), so elevation can't also be the monotonic arc. Confirm
  you're happy the falling leaves double as the reason the finale leans on remembered height.
- **Ladder untouched** — no beat fought the verified answers; nothing pushed back to `escape_room_puzzles`.

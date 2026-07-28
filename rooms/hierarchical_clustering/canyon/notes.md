---
authority: intent
---

# Canyon scenario (draft) — Hierarchical Clustering

Chapter `hierarchical_clustering`, scenario `canyon`. **Designed 2026-07-25 (Lucas, session "Canyon").**
Draft — world, travel spine, escape mechanic, a FIRST-PASS puzzle ladder, and a reskinned dataset whose
**cluster structure is verified** (see below) are here, but the ladder is not yet verified to the full
`escape_room_puzzles` bar (per-rung single-winner margins + ≥6 planned distractors + R-linkage confirmation),
and nothing is built. Codec **id 14** (take `next_free_id` from `rooms/scenario_inventory.json` at scaffold).

**Working title:** *The Confluence* (subtitle idea: "read the canyon before it drowns"). Provisional.

## Role in the chapter — the temple's pre/post partner

Second `hierarchical_clustering` scenario, paired with **`temple`** (`../temple/notes.md`, also a draft).
Same technique + question style, **deliberately different worlds and escape mechanics** (pre/post test):
- **temple** — maze is a **decoy**; cluster the statue data *against* adjacency; escape = **deduction
  ledger** (#9).
- **canyon** — the geometry **is** the tree (dendritic drainage = dendrogram); escape = **operate the
  waterworks** (draggable map + a calibration-matrix panel), not a ledger.

**Chapter expansion (Lucas):** grow the graded puzzles in *both* scenarios from "cut the tree" to "**cut the
tree, then run a summary statistic on each cluster**" (students have `group_by |> summarise` by now).

## World & premise

A **red-rock slot-canyon system** — a dendritic network of narrow sandstone canyons forking and re-merging
(claimed from `candidate_locations.md`). A **dendritic drainage is literally a dendrogram**: fingertip slots
up high = leaves (samples); the mouth where all water has merged = the root; each **confluence** = an
agglomerative merge, its **elevation** = the merge height. Long ago a vanished people engineered these floods
— an **undercroft of tunnels + gate machinery** beneath the system (own culture; avoid Chaco cliché). The
player is caught as the seasonal flood begins.

## Structure & flow (firmed 2026-07-25)

1. **Cold-open underground.** The player starts in the **undercroft** and finds two things: the **calibration
   panel** (a baffling engraved matrix — "what *is* this?"; Chekhov's gun) and a **map of the whole canyon
   system with the elevations blank** (picked up here). A **ladder climbs all the way up** to the top of the
   tributaries.
2. **Climb to the top, then descend.** From the top the player **goes down** through the whole system,
   free to roam (open maze). Descending builds the dendrogram bottom-up = agglomerative clustering.
3. **Roam, solve, and fill the map.** They visit puzzle nodes (graded clustering rooms) and read every
   confluence's elevation, recording it on the inventory map (see mechanic below). The panel's meaning
   **dawns** as they go.
4. **Boss solved → the storm breaks.** Solving the **last puzzle (the boss)** fires the announcement — *a
   rainstorm is coming, the canyon will flood, get out.* This starts **phase 2**.
5. **Back underground → key the panel → escape.** They return to the undercroft, read their now-filled map,
   complete the panel's code, and it **opens an emergency escape tunnel** out of the whole system to safety.

**Two phases solve the lockout** (`open_world_and_temporal_arc.md`). *Phase 1* (climb + descend + survey +
graded puzzles) is **dry** — nothing seals off before it's reached; optionally the water creeps as an ambient
overlay staying **below every benchmark** (dread, no trap). *Phase 2* (post-boss) is the **flood**, commanded
from the undercroft. "Rising water = agglomerative clock" keeps its meaning without ever stranding a player.

**Open-world progression (Lucas's model — replaces per-node `availableWhen`).** Travel is free. Designate
some confluences as **puzzle nodes**; on arriving at *any* puzzle node, serve **whichever puzzle is next in
the sequence** the player hasn't done — a queue, not a location-pinned puzzle. So they can't be locked out of
progression by visiting the "wrong" node, and elevation-reading (map-filling) runs continuously, decoupled
from puzzle order. *Engine: a "next-in-queue" puzzle dispenser at any puzzle node — small, general; flag for
Lucas's `pano-player.js` work.*

## The escape — draggable elevation-map + calibration-matrix panel (data-free)

Data-free (canon: decoupled from the CSV; runs on the **walked elevations**, like squirrel's heights). Two
sub-skills, split so neither needs real arithmetic:

1. **The inventory map (transcription, by dragging).** The map picked up at the start shows the canyon's
   **branching plan** — a dendrogram in canyon's clothing — nodes drawn, **elevations blank**. As they visit
   each confluence they **drag its node along the elevation axis** to its reading. The map is **properly
   scaled**, so this *is* plotting the dendrogram by hand. *Engine: a draggable-node inventory map (nodes
   move along one axis to record elevation) — new UI; flag for Lucas.* *(Orientation choice: elevation on the
   vertical axis → a natural horizontal waterline; or horizontal axis → Lucas's "draw a vertical line". Pick
   at design; horizontal waterline is the more diegetic read.)*
2. **The calibration-matrix panel (cut + summarise = the technique).** A **grid** etched by the engineers —
   **rows = flood-gate heights (cut thresholds), columns = clusters, each cell = the number of tributaries in
   that cluster at that height.** The cells are per-cluster counts → the panel literally **is** "cut the tree,
   then summarise each cluster." **A matrix code (~3×3 / 4×3) is the chosen encoding** (Lucas, over
   keypad/wheels/cairns). **Two bracketing rows pre-filled** (one higher cut, one lower); the player fills the
   middle row by reading their scaled map at that height and counting crossings. Because the map is scaled,
   reading is trivial — the real work is *realising* you must read it and enter it. Keying it opens the
   emergency tunnel.

### The cut maths (verified consistent, 2026-07-25)

Confluence elevation = merge height; water level E = the cut. Leaves share a cluster **iff their lowest common
confluence is ABOVE the water (dry, elevation > E)**; a confluence **below** the water (submerged) is a merge
the cut severed. Rising water ⇒ **more, smaller clusters** — exactly a dendrogram cut, matching the physical
picture (the flood cuts the canyon into ever more separate systems).

### Escape topology — LOCKED & verified (`_scratch/verify_escape_topology.py`, 2026-07-25)

8 leaf-tributaries T1–T8 (springs, ~1500 m). **7 confluences** = the 7 canyon junctions the player must visit
(the maze); each is a room with a benchmark giving its height. Node · elevation · children:

```
c1 1400  T1|T2      c4 1420  T5|T6      (high pair-junctions — never split at any cut)
c2 1380  T3|T4      c5 1390  T7|T8
c3 1050  {T1T2}|{T3T4}   c6 1200  {T5T6}|{T7T8}     (LEFT mid / RIGHT mid)
c7  850  {T1..T4}|{T5..T8}   (trunk — the boss room)
```

Panel — three flood-heights, three DISTINCT groupings (two rows lit, one dark → the code):

| Cut height E | clusters | sizes | notes |
|---|---|---|---|
| **1300** (lit) | 4 | 2, 2, 2, 2 | above both mids → every pair separate |
| **1125** (dark → fill) | 3 | 2, 2, 4 | above c3(1050), below c6(1200): LEFT splits, RIGHT stays whole |
| **950** (lit) | 2 | 4, 4 | below both mids → the two halves |

**Lock answer = `224`** (the dark 1125 row, left-to-right). Cut bands are wide (mids 1050 vs 1200; trunk 850),
so reading which junctions are above/below a line is unambiguous. Rule: two leaves share a cluster iff their
lowest common confluence is **above** the waterline (dry); rising water ⇒ more, smaller clusters — a dendrogram
cut. **Why 8 leaves / a balanced tree (not a main stem):** a main-stem/caterpillar cuts into one big cluster +
singletons (sizes degenerate to `[big,1,1,…]`); only a balanced tree gives clean partitions like 2,2,4 — which
is why the escape needs the branching maze to gather all 7 heights (see Design record).

## Data — `canyon_water_chem.csv` (engineered + verified 2026-07-25)

`data/canyon_water_chem.csv` — compositional shape of the course's flagship hclust set `chemical_blooms`
(each row a sample; columns % of the whole, sum to 100), reskinned to **spring-water geochemistry** (real
hydrochemical facies). **18 springs × 6 dissolved-mineral classes**
(`carbonate, sulfate, chloride, silica, iron_oxide, salts`), each row summing to 100. Fully synthetic
(deliberate departure from raw data — engineered for clean, escalating, single-winner puzzles).

**Four facies clusters, each dominated by one class:**
- **Carbonate** (West_Fork): Dripstone, Palegate, Lime_Hollow, Chalkseep
- **Sulfate** (East_Fork): Brimstone_Font, Sulphur_Step, Cinderpool, Matchhead_Spring
- **Silica** (North_Branch): Glasswater, Flintrun, Obsidian_Weep, Silverglass
- **Chloride/saline** (South_Branch): Brineseep, Saltmouth, Tidewell, Pillar_Brine

**Two planted outliers (Lucas: multiple outliers, 2026-07-25)** — a spring in one fork whose water belongs to
another family (taps a deeper stratum); naive "group by fork" fails, clustering the chemistry reveals them:
- **Bitterwell** — in **West_Fork**, chemically **sulfate** → clusters with East. (bitter = sulfate, a hint.)
- **Saltglass** — in **North_Branch**, chemically **saline** → clusters with South. (salt = its true nature.)

**Verification (`_scratch/verify_canyon_data.py`, run 2026-07-25).** Across **complete, average, AND ward**
linkage, k=4 gives exactly the four facies groups, and **both outliers join their chemical family every time**
(robust to linkage — matters because the course's R `runMatrixAnalysis` linkage isn't pinned here). Cluster
means: sulfate cluster mean sulfate **61.0** vs ~8 elsewhere (rung-3 margin huge); carbonate 65.2, silica
62.5, chloride 44.4. Sizes: carbonate 4, silica 4, sulfate 5 (incl. Bitterwell), saline 5 (incl. Saltglass).

**Data URLs when scaffolded:**
`.../hierarchical_clustering/canyon/data/canyon_water_chem.csv` (the 18 known springs) and
`.../canyon/data/unknown_spring.csv` (**Unmarked_Spring**, the rung-2 Classify-the-Unknown sample — combine
with the main table à la `wood_smoke` + `unknown_smoke`). Base:
`https://thebustalab.github.io/escape_rooms/rooms/`

**Two independent trees (by design, canon-compliant):** the **boss** clusters the *chemistry* (this CSV, in
R); the **escape** clusters the *walked elevations* (topology above). Decoupled. *Open detail:* relate the 18
chemistry springs to the 8 escape tributaries or keep as separate layers.

## Analog grounding & book-chapter sequence (added 2026-07-25)

**Analog grounding (where hclust is done by hand).** Sorting a collection into **nested families by
similarity** — a rock/mineral hound piling specimens into families then sub-families, a family tree, a
librarian's nested shelving. The domain version here is a **hydrogeologist grouping springs into
water-chemistry "facies" families** (a real practice — Piper/Stiff hydrochemical typing), then asking *which
spring is most like this one?* and *which one doesn't fit its neighbours?*

**Book chapter 7 sequence (read 2026-07-25, `integrated_bioanalytics/chapters/7_hierarchical_clustering.Rmd`).**
Chapter opens on *"which of my samples are most closely related?"* → **distance matrix** (`analysis="dist"`)
→ **build the dendrogram** (`analysis="hclust"`, plot with `ggtree`+`geom_tiplab`/`geom_tippoint`) → **read
it** (spot that some samples are "so different from the others" = outliers; re-analyse without them) →
**annotate** with traits + an aligned **heatmap** (which variables characterise which clade). **Cutting into
discrete k clusters + per-cluster summary stats is NOT in ch.7 today — it's ch.9 (flat) territory.** So the
ladder tracks ch.7's order (nearest-relative → read/outliers) *and* Lucas's deliberate **expansion** grafts
the cut+`summarise` step on (rung 3). Flag: the chapter itself may want a short cut+summarise addition to
match.

**Course hclust settings (read from `phylochemistry.R`, matters for exact answers):** `analysis="hclust"`
uses **euclidean distance, NO scaling** (`scale_variance` defaults FALSE for hclust) and **ward.D2** linkage.
The verifier uses these; the first-merge / nearest-neighbour answer is linkage-independent anyway.

## Graded ladder — LOCKED & verified (`_scratch/verify_canyon_data.py`, 2026-07-25)

3 practice + boss, boss-down, strictly monotonic (each rung adds one move), **puzzle-type variety** (a
Read/NN, a Classify-the-Unknown, a Cut+Summarise, then a misdirection boss — not four identical cards). Every
answer verified against the data under the course's settings; margins + planned distractors below.

1. **Read the tree — nearest relative** (the chapter's opening question). *"Which spring is most chemically
   similar to **Dripstone**?"* → **Lime_Hollow** (d=2.45; runner-up Chalkseep 2.83; **15% margin**).
   *Distractors (≥6):* Chalkseep (near runner-up), Palegate (same fork), a silica/sulfate/saline spring (wrong
   family), etc. *Deliberately a named-spring NN, not the global nearest pair* — the global nearest pair is
   Bitterwell+Matchhead (an outlier), which would leak the boss; a named carbonate spring's NN avoids that.
2. **Classify-the-Unknown** (type variety; the `wood_smoke`/`unknown_smoke` style). A mystery sample,
   `data/unknown_spring.csv` (**Unmarked_Spring**), added to the tree — *which family does it join?* →
   the **silica / North_Branch family** (verified: clusters with Glasswater/Flintrun/Obsidian_Weep/Silverglass).
   *Distractors:* the 4 families (carbonate/sulfate/silica/saline) + wrong-method options ("its own new
   group", "closest to Bitterwell") → ≥6.
3. **Cut + summarise (the expansion).** *Cut into 4 groups; which group has the highest **average sulfate**?*
   → the **sulfate family** (East_Fork **+ Bitterwell**), **mean SO₄ 61.0 vs 8.0 / 8.0 / 7.8** (dominant).
   Teaches `cutree(k=4)` → `group_by(cluster) |> summarise(mean)`. *Distractors:* the 4 clusters + wrong-method
   (highest single sample not cluster mean; wrong column) → ≥6.
4. **Boss — the outliers (misdirection).** *Two springs sit in one fork but their water belongs to another
   family (fed from a different stratum) — which two?* → **Bitterwell** (West_Fork → sulfate) **and Saltglass**
   (North_Branch → saline). Verified: both leave their fork under complete/average/ward linkage. Naive = group
   by fork; correct = cluster the chemistry. `isBoss`, `puzzleType 2`. *Distractors:* other cross-fork
   pairings, a single-outlier answer (only Bitterwell), a within-fork "odd one" → ≥6. *(Not leaked by rungs
   1–3: rung 1 carbonate, rung 2 silica, rung 3 names the sulfate cluster but not its members.)*

## Checklist status — `escape_room_puzzles` phase-exit (completed 2026-07-25)

- [x] **Analog grounding** written (above).
- [x] **Book chapter technique sequence** read (ch.7) and the ladder tracks it; the cut+summarise expansion
      flagged as an extension beyond current ch.7.
- [x] **Ladder reverse-engineered from the boss**, 3 practice + boss, strictly monotonic, one move per rung.
- [x] **Technique trap** built in (adjacency-vs-data, two planted outliers) and hinted via names + boss wording.
- [x] **Every answer verified** against the data under the course's exact settings (euclidean, no scale,
      ward.D2), with single-winner margins (rung 1 15%; rung 3 61 vs 8; boss both leave their fork every
      linkage). Verifier asserts all rungs: `_scratch/verify_canyon_data.py`.
- [x] **≥6 data-derived distractors** planned per rung (listed above; <6-level groupings padded with
      wrong-method options).
- [x] **Puzzle-type variety** — a Read/NN, a Classify-the-Unknown, a Cut+Summarise, a misdirection boss.
- [x] **Deterministic + verified dataset.** Hand-authored (deterministic by construction — no RNG/seed);
      `verify_canyon_data.py` is the re-runnable verifier and asserts every rung. Web-friendly (18 + 1 rows).
      Departure documented (fully synthetic, reskinned from `chemical_blooms`'s compositional shape).
- [x] **Handoff artifacts** in this notes.md: verified ladder spec, dataset path + public URL, judgement calls.
- [x] **Housekeeping:** codec id 14, pairing with temple, mechanics added to `puzzle_inventory.md` (#19) +
      `travel_mechanic_inventory.md`. No git commit on this box.
- [~] **One residual:** the verification is in Python (scipy ward on euclidean) matching the R settings; a
      final **confirm-in-R** with `runMatrixAnalyses(analysis="hclust")` on this box needs an R runtime (not
      run here). Structure is linkage-robust and the NN/first-merge is linkage-independent, so risk is low —
      but re-run in R before the rooms go live.

*(The `escape_room_design` checklist — scene prompts, scenario.json, plannedHotspots, debrief, cover — is the
next phase and not due yet. We've front-run the escape design, which formally belongs to `escape_room_story`;
fine as captured ideation, just flagged.)*

## Narrative (STORY phase, 2026-07-25)

**Phase status:** puzzles ✓ (verified) · story ✓ · **design ✓ (`scenario.json` assembled — see Design record below)** · art pending (Lucas, harness).

### Logline · stakes · clock
- **Logline.** A dendritic red slot-canyon that drowns each flood season; beneath it, a vanished people's
  **floodworks** and one **sealed escape tunnel** that opens only to whoever can read the canyon the way its
  makers did — its waters sorted into **families**, its channels into one **branching tree**.
- **Stakes (concrete).** You are caught in the canyon as the flood comes early. The only way out is the
  makers' tunnel, and its gate reads the canyon's *true* structure — learn to read it or drown. The analysis
  isn't assigned; it's the lock on the door you need.
- **Clock.** The **rising flood** — literal, irreversible, and (phase 2) the very thing that cuts the tree.

### World (built from the analog)
The analog is **sorting samples into nested families by similarity** — a hydrogeologist typing springs into
water "facies." So the world is a canyon whose **waters really do sort into families**, and whose **shape is
itself a dendrogram** (dendritic drainage). The vanished **makers** engineered the floods and built the
undercroft; they are the only "cast," present entirely through **what they left** — carved names, a control
panel, a blank map. **Cast economy: zero living characters.** The goal is **front-loaded** in the opening
(learn the waters, then read the land, then open the tunnel), so no character need explain a mechanic and the
house "no people in the art" rule holds effortlessly.

- **Landmarks (worth visiting).** The **high springs** in the narrow top slots (named in the data —
  Dripstone, Brimstone Font, Glasswater…); the makers' **carved wall-map of the waters** (where the boss is
  sited — a landmark that *foreshadows the panel*); the **drowned undercroft hall** with its panel, blank map,
  and the **sealed tunnel** (where the escape is sited — the Chekhov panel from the cold open, returned to and
  understood). Boss + escape both **earned** at landmarks.
- **Signature travel mechanic.** **Descend the drainage as the flood climbs to meet you** — a ladder up to
  the fingertip springs, then a free downward roam through the forking slots and confluences (the
  elevation-transition beats teach the heights; `travel_mechanic_inventory.md` T2 + the "puzzle-node serves
  next" queue). Down is the current of play; the water rises the other way.
- **Environmental arc (to hand design).** *Elevation* runs down-up-down: lamplit undercroft → **climb** to the
  highest slots → **descend** through the confluences → back underground. *Weather/light* runs one way and
  irreversibly: cool, bruised **pre-storm dawn** in the high slots → cloud massing + first drops as you
  descend → **the storm breaks at the boss** (thunder, first surge) → **flood + lamplight** underground for
  the finale. The storm and the descent arrive at the boss together (earned twice).

### Beats (one per rung — why run *this* analysis now)
1. **Read the tree — nearest relative.** *Top of the descent, among the carbonate springs.* You find the
   makers' first instrument — a way to weigh one water against another — and test it on the spring at your
   feet: *which of these waters is its kin?* (→ Lime_Hollow.) You learn the canyon's waters have families; the
   way on opens.
2. **Classify-the-Unknown.** *Lower, walls closing.* A spring the makers **never named** — no family carved
   beside it. The passage stays shut until it's **placed**: whose kin is this orphan water? (→ the silica
   family.) You learn every water has a family, even the unmarked.
3. **Cut + summarise (the foul family).** *Deeper, the air turns bitter, rock weeping yellow.* A family of
   **foul (sulfurous) water** runs somewhere in the canyon and the makers keyed their works to it — **cut the
   canyon into its families and find which runs most sour** (→ the sulfate family). You learn the families as
   groups with a character.
4. **Boss — the map that lies (misdirection).** *At the makers' carved wall-map*, every spring sorted by the
   **fork** it rises in. But **two names sit wrong** — their water swears a different kin than the stone says
   (→ **Bitterwell**, West but sulfate; **Saltglass**, North but saline). **Tempting = trust the carving
   (group by fork); correct = trust the water (cluster the chemistry).** The pivotal lesson: *kinship hides
   beneath the surface.* The storm breaks as you get it right.

### Escape (the payoff — data-free meta-echo + a ceremonial gesture)
Back in the drowned hall, the boss's lesson is **re-posed on the land itself, no data**: during the descent
you dragged each confluence onto your map at its height (a dendrogram plotted by hand). Now you must read the
**canyon's true branching tree** — not the deceptive maze-layout, exactly as the boss taught you not to trust
the deceptive fork-map — and **cut it**. Complete the makers' half-calibrated panel by drawing the waterline
at the missing height and **counting the severed limbs** (recognition, not computation; no CSV, no console).
Then the **player-performed gesture**: throw the **master gate-wheel** (one control, one motion, its meaning
front-loaded) — a sluice grinds, the flood turns aside, and the sealed tunnel opens. You climb out as the hall
drowns behind you. *Thematic climax:* the whole scenario taught you to read true structure beneath a
deceptive surface — first in the water, then in the shape of the land — and reading the land's true tree is
literally what opens the way out.

### Draft story-map text (paste into the harness story-map; tighten there)
- **`title`:** The Confluence
- **`subtitle`:** Read the canyon's hidden kinship before the water climbs.
- **`story` (landing):** *You came down into the red canyon to map its springs, and the flood season came
  early. Sheltering from the first hard sky, you find a stair cut into the rock — and beneath the canyon, a
  drowned hall of gates and channels the old makers left behind: their floodworks, and a single sealed tunnel
  that climbs to safety. Its gate will not open. Beside it: a panel of engraved dials no living hand has set,
  and a map of the whole canyon with every height left blank. A ladder climbs from the hall all the way to the
  high springs. The makers built this place to be run by someone who could read the canyon as they did — its
  waters sorted into families, its channels into one great branching tree. Climb. Read the springs. Learn
  which waters are truly kin. Then come back down and read the shape of the land itself — before the water
  climbs to meet you.*
- **Room entry cards:**
  - *(R1)* **The high springs.** *The ladder lets you out among the highest slots, where pale water beads from
    the limestone and the sky bruises overhead. Here is the makers' first instrument — a way to weigh one
    spring against another. Which of these waters is kin to which? Start where you stand.*
  - *(R2)* **The orphan spring.** *Lower, the walls close in. You come on a spring the makers never named — no
    mark, no family carved beside it. The way on stays shut until it is placed. Whose kin is this orphan
    water?*
  - *(R3)* **The bitter branch.** *Deeper still, the air goes bitter and the rock weeps yellow. Somewhere in
    the canyon runs a family of foul water, and the makers keyed their works to know it. Cut the canyon into
    its families and find which runs most sour.*
  - *(Boss)* **The carved map.** *You reach a wall the makers cut with every spring's name, sorted by the fork
    it rises in — their own map of the waters. But two names sit wrong: their water swears a different kin than
    the stone says. Thunder now, close. Trust the carving, or trust the water — and be right.*
- **`done` (analysis complete):** *The map lied, and you saw it — two springs betrayed by their own water, fed
  from a stratum the makers never marked. Overhead the storm breaks; the canyon fills. You have the one lesson
  the works demand: kinship hides beneath the surface, and only the reading finds it. Back to the hall,
  quickly — the panel is waiting.*
- **`escapeDone` (you got out):** *You draw the waterline across your map and count the canyon's severed limbs
  — and the panel takes it. You throw the great wheel; deep in the rock a sluice grinds, the flood turns
  aside, and the sealed tunnel opens its throat to the dark. You climb as the hall drowns behind you, up the
  makers' last stair, into rain and open sky. The canyon kept its one promise: read me truly, and go free.*

### Voice notes
Earnest, sensory, **second person**, present-tense-ish; never glib. Warm red sandstone + **cool bruised
pre-storm light** up top → storm and rising flood → **lamplit wet stone** underground. The makers are absent,
felt only through carvings, the panel, the blank map. Mood travels **lonely-wonder → tension → peril**. Keep
cards short (2–4 sentences). No living people (art rule + zero-cast choice).

### Judgement calls flagged
- **Zero living cast** (chosen): the makers are present only through their works; the goal is front-loaded, so
  nothing needs a character to explain it. Very much in the skill's "minimum plot, maximal world" spirit —
  flagging in case you'd want a single voice (e.g. a maker's journal) for warmth.
- **The "foul/sulfurous family" framing** for rung 3 is a story hook I added to give the cut+summarise a
  diegetic *why* (know the bad water). It doesn't touch the ladder/answers.
- Pedagogy untouched: ladder, answers, dataset all unchanged.

## Design record (scenes + scenario.json — MAZE rebuild, 2026-07-25)

`scenario.json` rebuilt around the **branching-tree maze** (id 14, parses, in `scenario_inventory.json`).
**9 room nodes, 8 unique panoramas** (`works` reuses `undercroft`). All stubs (`built:false`) with full
`scenePrompt`/`doorPrompt`, `designNote`, `plannedHotspots` — ready for harness art.

**Why the maze (the load-bearing decision).** The escape gathers the confluence heights **by travelling**, so
the player must pass **every** junction. A branching tree can't be covered by one path → the maze. And a
branching tree is *required* anyway: a main-stem/caterpillar cut degenerates to `[big,1,1,…]`; only a balanced
8-leaf tree gives clean partitions (2,2,4 etc.). So maze + balanced tree are locked together.

**Rooms = the 7 confluences + the chamber.** Leaf-tributaries are **views** (slot-ends), not rooms. The 4
graded puzzles sit **at** confluences (a confluence = where waters merge = where you judge kinship): `j_c1`
(R1 NN→Lime_Hollow), `j_c2` (R2 Classify→silica), `j_c4` (R3 cut+summarise→sulfate), boss `j_c7` (outliers,
**at the trunk**). Plain junctions `j_c3`/`j_c5`/`j_c6` = benchmark + fork only. `undercroft` = cold-open
chamber; `works` = escape (reuses undercroft art). Each confluence room has a **benchmark** giving its height;
the player reads all 7 to fill the map.

**Maze nav graph (all passages open):** undercroft↔j_c1 (ladder) & undercroft↔j_c7 (trunk); j_c1↔j_c3,
j_c2↔j_c3, j_c3↔j_c7; j_c4↔j_c6, j_c5↔j_c6, j_c6↔j_c7; j_c7→works (escape). Left & right branches meet only at
the trunk j_c7 (so you pass the boss room while roaming — nice foreshadow; boss puzzle stays `availableWhen`
until R1–R3 done).

**Escape (`works`) — LOCKED.** A `lock`, answer **`224`**: complete the panel's dark **1125** row (above
c3=1050, below c6=1200 → LEFT splits 2,2, RIGHT stays 4). Lit rows 1300→2,2,2,2 and 950→4,4. Data-free
(heights are world props). Topology + 3 cuts verified: `_scratch/verify_escape_topology.py`.

**Key decisions / engine dependencies (judgement calls, flagged):**
- **WebR-safe R, no ggtree** — all puzzle code is base `dist`/`hclust(method="ward.D2")`/`cutree`/`plot` +
  `dplyr`, never `runMatrixAnalysis`+ggtree (no wasm build). Answers verified under those settings.
- **Maze engine — BUILT + browser-tested 2026-07-26** (`shared/pano-player.js`; Playwright headless Chromium,
  synthetic maze 8/8; alaska+henges boot clean). New optional/backward-compatible fields: all passages open
  via door **`direction:"open"`**; puzzles/locks gated by **`availableWhen`** + **`lockedBody`** (the escape
  panel refuses an incomplete map via **`availableWhen:{gte:["heights_read",7]}`**, fed by each benchmark's
  **`onPickup:{inc:"heights_read"}`**); `condOK` gained the `{gte}` counter; `visitedRooms` fixes junction
  entry cards. **Authoring recipe in `AGENTS.md`.** The richer **draggable-node map + live matrix-grid panel**
  (`puzzle_inventory.md` #19) is still a further upgrade — the current `lock` + map-clue is the shipped
  fallback. **Art can be generated independently** (art ⟂ maze engine).
- **Backtrack-safe world (per `open_world_and_temporal_arc.md`):** scene art is **place-constant** (each
  junction's character set by its DEPTH — high/open/bright vs deep/narrow/dark; trunk cavernous; undercroft
  lamplit). The irreversible **storm→flood clock** is NOT baked per-room; it rides a **global overlay driven
  by `rooms_solved`** (Tier-2 engine) + the entry-card text (Tier-1 now). This replaces the earlier per-room
  storm sequence (which fought backtracking).
- **Two layers stay separate** (resolves the reconcile question): 18 chemistry springs = the graded data; 8
  tributaries / 7 confluence heights = the escape topology. Not forced 1:1.

**Ambience.** `ambient:"none"`, `fx:[]` (no canyon fit in the engine set); a rain/dust ambient + rising-water
tint are desired engine additions (non-blocking). `coverPrompt` drafted. **Music:** recommend a low
canyon-wind + distant-water drone — *not yet fired*; offer to submit the `youtube_audio` row on your nod.

**Art status:** 8 NEW panoramas (`works` reuses `undercroft`), each place-constant by depth.

**Handoff / still to do (downstream):**
- Add **scenario id 14** to `decoder/decode_codes.R` (has 1–9) — wiring/decoder lockstep (`validate_keys.py`);
  flagged, not edited (byte-for-byte codec mirror).
- ~~Build the maze engine bits~~ **DONE + browser-tested** (`shared/pano-player.js`, Playwright). The
  further **draggable-map + matrix-grid panel** upgrade remains optional (lock fallback ships).
- Lucas: harness art → then `escape_room_wiring` fills hotspot MCQs/clues/sfx from the `designNote`s.
- Optional: note the base-R ggtree workaround in the parent WebR thread; add canyon's `AGENTS.md` to the
  parent sub-component index.

## Open decisions (for Lucas)

1. ~~Rung 1 nearest pair~~ **RESOLVED** — rung 1 now asks a *named* spring's nearest relative
   (Dripstone → Lime_Hollow), the chapter's own phrasing, so it no longer leaks the outlier boss.
2. **Map orientation** — elevation vertical (horizontal waterline, more diegetic) vs horizontal (Lucas's
   "vertical line").
3. **Summary-stat variety** — canyon uses *count*; give temple a different trivial stat (e.g. highest pool)?
4. ~~Tree size~~ **RESOLVED** — 8 leaf-tributaries / 7 confluences (balanced binary; verified 3-cut panel).
5. ~~Reconcile 18 springs vs 8 tributaries~~ **RESOLVED** — kept as two separate layers (chemistry = graded
   data; elevation tree = escape topology).
6. **Title** — *The Confluence*?
7. **Map fill mechanic** — the current `lock` + map-clue (buildable) vs the richer draggable-node map +
   matrix-grid panel (engine upgrade).

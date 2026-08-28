---
authority: intent
---

# Scenario theme ideas — backlog

**Status:** intent / raw ideas. A holding pen for narrative *theme* concepts for future
escape-room scenarios, before any of them is tied to a data technique / book chapter or
promoted to a built scenario. Each existing scenario wraps a data-analysis technique in a
setting (Alaska, Hawai'i, hospital, airship, temple, trees); these are candidate settings
looking for a technique.

When one of these graduates into a real build, move it under the appropriate
`rooms/<technique>/<name>/` scenario and use the `escape_room_design` skill.

## Ideas

### Aztec-themed (indoor + outdoor)
- Set in the **Aztec mountains**, with both **indoor and outdoor portions** to the scenario
  — a natural fit for the two-objective structure (indoor analysis rooms, then step outside
  for the escape phase; see `two_phase_escape_design_notes.md`).
- **Aztec gold** could feature in the scene.
- A **large lake** — the kind of lake **El Dorado** is based on — as a landscape element.

### Japanese-themed
- **Pagodas** and that whole aesthetic.
- **Rock islands out on water, connected by rope bridges** — a striking layout for moving
  between rooms/areas.

### Subway-themed → **embeddings** (suggested; the `japan` partner)
- Setting: an **underground subway / metro** — platforms, tunnels, trains, the map.
- **Music/vibe: dub techno** (deep, spacious, hypnotic — suits the tunnels-and-neon mood).
- Draw mechanic ideas from **the Iron Tangle** (Lucas's reference — pull specifics from it when this
  graduates; not yet spelled out here).
- **Suggested technique — embeddings (book ch.13/14; Lucas 2026-08-05, leaning not commitment).** A subway
  map is the canonical embedding metaphor: it discards *geography* and preserves *connectivity/topology* —
  exactly what an embedding does (near on the map = near in vector space, not near on the ground). Puzzle
  writes itself as **nearest-neighbour retrieval** with a "false friend" trap (a station geographically
  close but not actually connected / a different kind). Would be the **pre/post partner to
  `embeddings/japan` (Wind Shrine)** on a different dataset — the pairing convention that chapter wants.
  *Alternative home — OBSOLETE, resolved 2026-08-27:* this once read "Data Vis III (ch.5), which has NO
  scenario at all". Networks was **extracted out of ch.5 into its own chapter 7** that day, so the subway
  went there rather than into Data Vis III. **And Data Vis III no longer exists** — it was dissolved the
  same day: its distribution material went to comparing means and its remaining plot types (3D scatter,
  Venn, ternary, maps) to an appendix. So there is no ch.5 at all now, and no empty chapter to fill.
  See `integrated_bioanalytics/notes/networks_chapter_notes.md`.
- No dataset / ladder assigned yet.

### Jewel-thief heist → **flat clustering** (REASSIGNED 2026-08-27; the `waterfalls` partner)
> **Technique changed 2026-08-27 (session "Canal boat", Lucas).** Was penciled for **numerical modeling**
> as the `sailing` partner (2026-08-05). Reassigned to **flat clustering** because the heist turns out to
> be a markedly better *k*-means world than a modeling one, and because modeling's slots were taken by the
> canal (see the entry below). The old modeling reading is preserved at the foot of this entry.

- Setting: a **heist** — a jewel thief and a vault.
- **Music/vibe: James Bond-style** spy score.
- **Premise hook:** *beat the thief to the vault* — a race/clock framing (pairs with a timed or
  against-the-clock structure). **Survives the technique change intact**: knowing *which crew is which* is
  precisely what tells you whose pattern leads to the next target.
- **Technique — flat clustering (book ch.10; `10_flat_clustering.Rmd` = k-means → choose *k* via the
  elbow → summarise-by-cluster).** A run of burglaries across a city, each job carrying its measurements
  (entry method, hour of the night, tools, time inside, what was taken). The investigative question is
  **"is this one crew or three?"** — which is *k*-means asking its own defining question in plain English,
  and gives the corpus its **most diegetic elbow**: the elbow plot's *k* IS the number of thieves. Real
  practice, not a contrivance — linking offences by **modus operandi** to infer how many offenders are at
  work is a genuine forensic technique.
- **The scaling trap transplants better than waterfalls' own.** **Haul value** runs into the thousands
  (pounds) while every MO feature sits on a small scale. Cluster raw and you group the jobs by **how much
  was taken**; scale first and you group them by **how they were done** — which is the truth. The decoy
  answer is literally *"the job that stole a similar amount"*, i.e. the mistake a real investigator would
  make — better motivated than `waterfalls`' weight-in-grains.
- **Ladder — mirrors `waterfalls` rung for rung** (the pre/post convention wants the same question style
  on a different dataset; see `rooms/flat_clustering/waterfalls/notes.md` → *Verified ladder*):
  1. **S1** run k-means on the job records, read off the **largest crew's size** (MCQ).
  2. **S2** **click the elbow** — how many crews are operating? (pick-the-point).
  3. **S3** summarise by cluster — characterise one crew (console-check).
  4. **BOSS** the scaling trap — *which job belongs to the same hand as the one at the vault?* Wrong
     unless scaled; **decoy = the unscaled haul-band mate**.
- **Escape — data-free meta-echo, INDEPENDENT of the dataset** (per canon; `waterfalls` sets the
  precedent that the escape's *k* need not match the data's). Candidate: recognise how many **distinct
  hands** are at work from props alone — e.g. tool-marks on the display cases — and read their sizes.
- **Setting/vibe bonus — claims genuinely unused ground.** No scenario is **urban** or **modern**, and
  **clinical / white / scrubbed** is the last register `vibe_inventory.md` lists as free; a gallery or a
  vault interior is exactly that. Claimed there 2026-08-27.
- **Watch:** keep it **measure-and-compare**, not **count-and-tally** — case files and ledgers drift toward
  `wrangling/egypt`'s manifest and `hierarchical_clustering/temple`'s ledger escape.
- No dataset / ladder verified yet. Next phase when it graduates: `escape_room_puzzles`.
- *Superseded modeling reading (2026-08-05, kept for the record):* "beat the thief to the vault" as
  fit-the-thief's-trajectory-then-extrapolate, laddering straight line → curve → multi-variable → RF boss.
  Still a coherent mapping — just a **less distinctive** one, since any dataset can be extrapolated,
  whereas *"how many offenders?"* is a question only clustering can ask.

### Canal boat + lock flight → **numerical modeling** (DISPLACES `sailing` as modeling scenario 1) — 2026-08-27
> **Decided 2026-08-27 (session "Canal boat", Lucas).** Carries its technique, like the henges entry did.
> `modeling/sailing` is **demoted to scenario 2** rather than retired — it was the cheapest thing in the
> corpus to change (intent-only, no dataset, no verified ladder). See `rooms/modeling/sailing/notes.md`.

- **Setting.** The player is the **captain of a canal boat**, working an inland waterway and its **flight
  of locks**. Vessel-as-moving-hub: the boat is the persistent home and the world scrolls past it.
- **Why modeling and not clustering (the path we walked, worth keeping).** A **lock** is a superb
  embodiment of **scaling** — you cannot join two waters at different levels until you equalise them,
  which is exactly `scale()` before a distance. That argued for flat clustering (as `waterfalls`' partner,
  whose boss IS the scaling trap). **Rejected**, because scaling is the *preprocessing step*, not the
  technique: there is no natural act on a canal where somebody discovers **unknown groups** in
  measurements. Locks are about **levels and passage**, not about **kinds**. The best construction
  available — a junction basin sending a mixed fleet down *k* arms — is just `waterfalls`' *k* pools
  reskinned, with the grouping bolted on rather than arising from the setting.
- **What a canal IS natively about:** discrete levels, connectivity, and above all the **water budget**.
  Every lock cycle spends a **lockful** from the pound above; the **summit pound** is the scarce resource;
  the defining engineering problem of a canal is whether feeders and reservoirs can keep the summit
  supplied. Historically real — canal companies built reservoirs and back-pumping engines for exactly
  this, and canals genuinely **closed when the summit ran dry**.
- **So: modeling (book ch.12).** Fit the **drawdown against the inflow**, extrapolate, and answer a single
  sharp number that decides whether you get through: **how many more boats can pass before the level
  fails?** Sharper than `sailing`'s diffuse "predict the safe passage" — which is the argument for the
  displacement.
- **Escape — must NOT be a rhythm-timing puzzle.** `sailing` keeps the **periodic** cycle (tide/swell
  superposition, time the window). The canal's is a **depleting supply**: extrapolate to exhaustion. State
  this separation deliberately; see the distinctness notes below.
- **Distinctness notes to write up front** (the corpus convention — cf. the two forests in
  `candidate_locations.md` and the T5 two-rail note in `travel_mechanic_inventory.md`; state the
  separation rather than leave it to be noticed later):
  - **vs `hierarchical_clustering/canyon`** — the *closest* rub, and it is about **water levels**, not
    harbours. Canyon is the corpus's heaviest user of gate-and-water vocabulary (drowned floodworks,
    sluice-cuts, an iron sluice-wheel, flood-gate heights) and its **rising flood is the clock chasing
    you**. A canal lock is **engineered stepped water on level ground**, raised and lowered deliberately
    by a person — the opposite relationship to the water.
  - **vs `wrangling/egypt` (Alexandria)** — milder than it looks. Egypt's boat is a **framing device**: you
    moor on page one and the scenario walks inland (deck → hold → quay → market → Canopic Way → Library →
    Pharos). It is a **city** scenario; the vessel never moves. The canal boat is the thing that moves.
    **But avoid its premise shape** — *"you captain a cargo boat and officialdom won't let you leave"* is
    Egypt's logline. Steer clear of cargo, manifests and paperwork; make it **passage and levels**.
    (Corollary: **do not** lean on historical **toll-house gauging** — measuring a boat's freeboard to
    infer cargo weight — however tempting the real history is. It is cargo bureaucracy, i.e. Egypt's.)
  - **vs `flat_clustering/waterfalls`** — waterfalls' escape is a **stream-diverter routing maze**. The
    canal must **not** be about diverting or routing water.
  - **vs `modeling/sailing`** — two boats in one chapter. Inland **stepped freshwater working boat** vs
    **open salt sea** is a wider gap than the two forests had, but write it down.
  - **vs `networks/subway`** — subway claims **true industrial interior**. So **not** the grimy Victorian
    brick canal; go **pastoral working-boat** (green, brown, misty), which is unclaimed.
- **Travel mechanic — genuinely new.** `travel_mechanic_inventory.md` **T9 (one-directional flow,
  proposed, no user)** is a current that carries you downstream only, with portage the costly way back.
  **A lock is the thing that defeats T9** — it is how you go uphill. Boat-as-persistent-moving-hub with
  **locks as level-gates** combines T6 (vessel between nodes) with T8 (elevation-transition beat) in a way
  nothing in the corpus does.
- **Prior art:** none. Swept 2026-08-27 — zero hits corpus-wide for towpath / narrowboat / barge /
  aqueduct / weir; "canal" appeared **twice**, both in `modeling/sailing/notes.md` as scenery. The idiom
  was **unclaimed and unrejected**.
- No dataset / ladder verified yet. Next phase when it graduates: `escape_room_puzzles`.

### England / henges → **PCA** — ⇒ GRADUATED to a build 2026-07-23
> **Now in build.** PUZZLE phase complete: `rooms/dimensionality_reduction/henges/` (verified ladder +
> engineered `druid_ingredients` dataset — see its `notes.md`). Kept here for the record. Next:
> `escape_room_story`.

Unlike the settings above, this one comes with its data technique baked in: **Principal Components
Analysis**. Setting: **England, a ring of standing-stone henges** (Stonehenge-like).

- **Layout.** A central hub; **each arch is a doorway into a different henge**. Henges are told
  apart by **stone colour** or by the **type of moss/lichen growing on them** — a per-henge visual
  identity so you always know which one you're standing in.
- **The altar.** In the middle of each henge is a **big altar** with **items arranged on it (stones,
  or similar)**. It's **always the same stones**, but their **arrangement changes from henge to
  henge**. That's the whole PCA conceit: each henge is a **different projection / rotation of the
  same set of points** — you walk through an arch and your **view onto the data rotates onto another
  principal component**.
- **The puzzle (PCA made walkable).** You need a way to **maximise the spread of the stones** — i.e.
  find the henge whose arrangement is spread out most, which is **looking along PC1**. Two candidate
  win-conditions to choose between at design time:
  1. **Find the max-spread henge** — walk the arches until you're looking along PC1 (max variance).
  2. **Order the henges by spread** — put the principal components in order, which is literally a
     **scree plot made walkable** (each henge = one PC; order them by variance). *(Lucas: "a scree
     plot could be involved — or find a particular principal component, something like that.")*
- **Open design questions (pin down before build):**
  - Is each altar's arrangement a genuine **2D scatter of the data projected onto that henge's PCs**,
    so a student could recognise the shape / the elbow?
  - Win = *find PC1* (single max-spread henge) **or** *order all the henges* (scree)? Different puzzles,
    both good.
  - Does **one henge = one PC**, and the escape asks for a particular component?
- **Pipeline note.** Because it already carries a technique (PCA), when this graduates it can skip
  straight into the `escape_room_puzzles` phase (technique + dataset + ladder) rather than needing a
  technique assigned first. Pairs naturally with a second PCA scenario on a different dataset (the
  pre/post-test convention).

### Light-shaft projection → **PCA** (the henges' pre/post partner) — parked 2026-07-25
> Carries a technique (**PCA**) *and* a mechanic. Reserved as the **second dimensionality-reduction
> scenario**, pairing with `henges` (PCA scenario 1). Setting deliberately **NOT a canyon** (the canyon is
> being built for hierarchical clustering; don't double up the landscape).

**The mechanic (saved from the "Canyon" session, 2026-07-25).** The same set of objects sits in one hall;
a **shaft of light enters through an aperture and its angle changes** (with the time of day / a rotatable
oculus). Each light-angle throws the objects into a **different projection / shadow-arrangement** — i.e.
each beam-angle is a *view along a different axis*. The puzzle: find the **angle of light at which the
objects spread out the most** (= looking along **PC1** / maximum variance), or **order the angles by spread**
(a walkable/lightable scree plot), or the angle at which one sub-group separates cleanly. It's the
**projection-gallery mechanic (#17, walk-the-PCs)** but the rotation control is **light**, not walking
through arches — a lovely, distinct spatial idiom for the *same* PCA lesson.

- **Why it's PCA not clustering.** A viewing angle = a projection axis; the "max-spread angle" = PC1. This
  is exactly the "look at the world as a whole along a principal component" reading Lucas flagged.
- **Setting (pick one, non-canyon, low overlap):** a **sun-temple with a rotating light-shaft / oculus**
  (an inner sanctum the beam crosses); an **observatory dome / camera-obscura tower**; a **prism/lighthouse
  lantern room**. Avoid Chaco-style butte/canyon framings (too close to the hclust canyon). The henges'
  standing-stone idiom is already claimed by scenario 1, so this partner wants a built interior with a
  controllable light source.
- **Data.** Reuse the PCA data thinking from `dimensionality_reduction/henges/notes.md` (a compositional /
  multi-axis set with a clear PC1 and a separable sub-group), on a *different* dataset for the post-test.
- **Pipeline.** Like henges, it already carries the technique — when it graduates it can go straight to
  `escape_room_puzzles` (ladder + dataset), then story/design. Mechanic logged in
  `travel_mechanic_inventory.md` context and `puzzle_inventory.md` #17.

## Notes
- Captured 2026-07-21 (Lucas, "ideas" session). Raw themes only — no technique, room ladder,
  or dataset assigned yet.
- Light-shaft → PCA parked 2026-07-25 (Lucas, "Canyon" session): the light-angle idea, saved off the canyon
  and reserved as the henges' PCA pre/post partner on a non-canyon interior.
- England/henges → PCA added 2026-07-23 (Lucas, "ideas" session). This one *does* carry a technique
  (PCA) and detailed mechanic notes — further along than a bare setting.
- Subway (dub techno, Iron Tangle mechanics) + jewel-thief heist (Bond music, "beat the thief to the
  vault") added 2026-08-05 (Lucas). Technique leanings penciled in the same session: **subway → embeddings**
  (the `japan` partner; or Data Vis III ch.5, then the one empty chapter) and **heist → numerical modeling** (the
  `sailing` partner). Leanings not commitments — settings still need a dataset + ladder before build.
  *Both leanings have since moved:* subway graduated to the **networks** chapter — **its own ch.7 as of
  2026-08-27**, not Data Vis III — with `beacons` as
  its partner, and the heist was **reassigned to flat clustering** on 2026-08-27 (see its entry).
- **Canal boat + lock flight → modeling, displacing `sailing` as scenario 1; heist → flat clustering**
  — decided 2026-08-27 (Lucas, session "Canal boat"). Reasoning in full in the two entries above. The
  short version: a lock embodies **scaling**, not **clustering**, so the canal went to modeling on its
  **water-budget** (summit-pound drawdown) reading; that displaced `sailing` to modeling scenario 2 and
  freed the heist, which turns out to be a much better *k*-means world because *"how many thieves?"* is
  a genuinely diegetic elbow. Companion edits made the same day: `rooms/modeling/sailing/notes.md`
  (demotion + canals trimmed), `candidate_locations.md` (both settings claimed),
  `vibe_inventory.md` (heist claims clinical/scrubbed), `travel_mechanic_inventory.md` (T9's first
  candidate consumer).
- **Chapter coverage after this decision (2026-08-27).** Paired: data_vis, data_vis2, wrangling,
  hierarchical_clustering, dimensionality_reduction, comparing_means, networks, modeling (canal +
  sailing), flat_clustering (waterfalls + heist). **`embeddings` is now the only chapter still short a
  partner** — `japan` stands alone. The later book chapters (homology, alignments, phylogenies) remain
  deferred on WebR blockers.
- **DATA VIS III DISSOLVED, 2026-08-27.** Following the extraction below, what was left of ch.5 (a
  grab-bag of six plot types with no progression — which is exactly why no scenario could ever track it)
  was distributed: distributions → comparing means, and 3D scatter / Venn / ternary / maps → an appendix.
  **There is no chapter 5.** One fewer chapter needing a scenario pair.
- **BOOK RENUMBERING, 2026-08-27.** Networks was extracted from `5_datavis_3.Rmd` into its own
  **chapter 7** (`7_networks.Rmd`), and every chapter from the old 7 upward moved up by one. Chapter
  numbers quoted anywhere in `escape_rooms/` were swept the same day. The mapping that matters here:
  hierarchical clustering 7→**8**, PCA 8→**9**, flat clustering 9→**10**, comparing means 10→**11**,
  modeling 11→**12**, language models 12→**13**, protein language models 13→**14**. Data vis I, II and
  III (3, 4, 5) and wrangling (6) are unchanged. Full record:
  `integrated_bioanalytics/notes/networks_chapter_notes.md`.

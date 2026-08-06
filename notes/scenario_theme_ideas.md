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
- **Suggested technique — embeddings (book ch.12/13; Lucas 2026-08-05, leaning not commitment).** A subway
  map is the canonical embedding metaphor: it discards *geography* and preserves *connectivity/topology* —
  exactly what an embedding does (near on the map = near in vector space, not near on the ground). Puzzle
  writes itself as **nearest-neighbour retrieval** with a "false friend" trap (a station geographically
  close but not actually connected / a different kind). Would be the **pre/post partner to
  `embeddings/japan` (Wind Shrine)** on a different dataset — the pairing convention that chapter wants.
  *Alternative home:* **Data Vis III (ch.5)** — a subway is literally a node-link **similarity network** /
  a map, and ch.5 currently has NO scenario at all (the biggest single gap). Pick at graduation.
- No dataset / ladder assigned yet.

### Jewel-thief heist → **numerical modeling** (suggested; the `sailing` partner)
- Setting: a **heist** — a jewel thief and a vault.
- **Music/vibe: James Bond-style** spy score.
- **Premise hook:** *beat the thief to the vault* — a race/clock framing (pairs with a timed or
  against-the-clock structure).
- **Suggested technique — numerical modeling / regression (book ch.11; Lucas 2026-08-05, leaning not
  commitment).** Modeling *is* fit-a-pattern-then-**extrapolate-to-predict**, and "beat the thief to the
  vault" is exactly that: take the thief's past jobs, fit their pattern/trajectory, extrapolate to predict
  the next target and get there first. The clock is the payoff a good prediction buys. Ladder can climb
  straight line → curve → multi-variable → boss (room for ch.11's random forest), same as `sailing`. Would
  be the **pre/post partner to `modeling/sailing`** (navigator predicts safe passage) on a different
  dataset — same technique, opposite skin.
- No dataset / ladder assigned yet.

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
  (the `japan` partner; or Data Vis III ch.5, the one empty chapter) and **heist → numerical modeling** (the
  `sailing` partner). Leanings not commitments — settings still need a dataset + ladder before build.

---
authority: intent
---

# Temple scenario (draft) — Hierarchical Clustering

Chapter `hierarchical_clustering`, scenario `temple`. **Idea captured 2026-07-18 (Lucas).** Draft only —
nothing designed/verified/built yet. Codec id: take `next_free_id` from `rooms/scenario_inventory.json`
when scaffolded (10 at capture time). Dataset TBD (an MSA / sequence-profile dataset that clusters cleanly;
align to the CHEM5725 Hierarchical Clustering chapter — `wood_smoke`/`chemical_blooms` are the existing
hclust datasets, but the "statues = a multiple sequence alignment" framing may want a bespoke MSA set).

## Theme

An **ancient Greek / Trojan temple** — the player is crawling through it to escape: tunnels, trapdoors,
nooks and crannies, shrines. Distinct from the field-science scenarios; statues, banners, stone.

## The big idea (two moves)

1. **The data IS the world — statues as a multiple sequence alignment.** Scattered through the temple
   are **shrine rooms**, each holding a **set of three statues**. The statues *are* the data (an
   MSA-like profile). Which statues stand in a shrine is that shrine's data row; shrines with similar
   statue-sets belong to the same cluster.
2. **The physical maze is a DECOY, not the dendrogram.** Lucas's key revision: the temple layout is
   **deliberately scrambled / random**, NOT laid out as the tree — because a tree-shaped building would
   *give the answer away*. The player must reconstruct the clustering **from the statue data**, not from
   which rooms happen to be near each other. (This is the pedagogically sharp bit — it directly guards
   against the naïve "things that are physically close must cluster" error.)

## Structure

- **Node / puzzle rooms** — rooms with **multiple doors out** and a **puzzle** (the graded Hierarchical
  Clustering analysis; hclust in the WebR console). The branching navigation holds.
- **Shrine / tip rooms** — hold the **three statues** (the data) + a **coloured banner** (red / yellow /
  green / … ) as the room's **identifier**. ~**9 tips**, which truly group (e.g. 2 + 3 + 4 = 9) — but
  the grouping is only knowable from the statues, not the map.
- The player **notes which statues are in which banner-room** as they explore (the field notebook is the
  natural place — auto-log shrine contents).

## The escape — a deduction ledger (catalogue #9)

At the exit, a **ledger**: the player must **cluster the banner-rooms by their statue identities** — e.g.
"red, yellow, green belong together" — and mark those groups. A group **locks in** when it's a correct
cluster (the Obra-Dinn confirmation rule from `ledger_and_inference_board_specs.md`). Once **all** clusters
are locked, a **sound cue** fires — the great temple exit door grinding open — and you escape. So the
escape *is* the hierarchical clustering, done by observation of the statue data.

## How it maps to our established vocabulary

- **Two-objective structure** (`two_phase_escape_design_notes.md`): the **node/puzzle rooms = graded
  analysis** (do hclust in R), the **shrine → ledger = the ungraded escape** — the unlabelled/observation
  echo of the same clustering skill. Consistent with the airship/hospital pattern.
- **Deduction ledger (#9)** is the escape mechanic — this scenario is its first intended home; rows =
  banner-rooms (colours), verdict = which cluster, groups derived from the statue data.
- **Data-as-world / "see the whole"** — the statues are the dataset made physical; the decoy maze forces
  clustering by data, not adjacency.
- **Aesthetic layer** — candidate `fx`/motif touches: torchlight flicker (warm, non-creepy), dust motes
  ambient, a low stone-temple drone; a "door grinds open" SFX on the ledger solve.

## Open design questions

- **Do the shrine statues also exist as a console dataset?** For the graded node-room puzzles the student
  must run hclust in R — so there's a CSV. Decide the relationship: are the statues a *diegetic rendering*
  of that same dataset (analyse in code, verify by observation), or is the escape purely observational
  (read statues, cluster by eye) while the node rooms carry the coded hclust? (Leaning: node rooms = coded
  hclust; escape ledger = observational echo — matches the alien-echo principle.)
- **Navigation + note-taking load.** A random maze of ~12–18 rooms (node + shrine) is a lot to track and a
  lot of **art to generate**. Guard against frustration: auto-log shrine statue-sets to the notebook; keep
  the maze small; maybe a collectible map. Scope this hard before building.
- **The MSA/statue data.** Design a statue-profile dataset where the 9 tips cleanly form 2+3+4 clusters,
  derivable from statues alone. Verify against the data (per the skill's step 3).
- **Pre/post pairing.** The chapter wants a **second** hierarchical-clustering scenario asking the same
  question style (per the pre/post principle) — temple is one of the pair.
- **Room count / engine.** The multi-door maze is authorable with `door.to`, but confirm the graph nav +
  back-nav behave for a non-linear layout (currently linear-leaning; may need the deferred graph work).

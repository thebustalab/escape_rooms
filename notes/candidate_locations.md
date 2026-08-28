---
authority: intent
---

# Candidate locations (cross-scenario pool)

Sibling of `puzzle_inventory.md` (mechanics), `scenario_theme_ideas.md` (themes / premises) and
`vibe_inventory.md` (light / palette / mood). This is the
**pool of landscape settings** a future scenario or room could sit in — evocative places worth visiting —
plus a roster of **settings already in use**, so new picks don't double up. Started **2026-07-24** (Lucas,
during the henges room-3 hunt). A location graduates OUT of here when a scenario claims it (note which +
date under `## Claimed`).

## Settings already in use (avoid doubling up)
- **alaska** (data_vis) — remote Arctic tundra field station; snow, cold, dusk.
- **Hawaii / Saltwater Intrusion** (data_vis) — tropical jungle lab + coastal wells + beach; volcanic island.
- **hospital / Vital Signs** (data_vis2) — hospital interior; bright summer, pharmacy, break room.
- **airship / The Alembic** (data_vis2) — brass-and-canvas airship adrift over floating islands, green evening sky.
- **trees / The Collector's Vault** (wrangling) — alien **FOREST** canopy; monorail between stations; cliff-top vault.
- **egypt** (wrangling) — Hellenistic Alexandria; port / market / Pharos lighthouse / Library.
- **temple / The Register of the Gods** (hierarchical_clustering) — a **ruined jungle temple** deep in
  rainforest at harsh noon; galleries, a service crawl, a cistern shaft, a roofless altar above the
  canopy. *Re-skinned 2026-08-26 from an ancient Greek temple, which turned out to share a civilisation
  with `egypt` (Hellenistic Alexandria) rather than merely a mood. Kept distinct from `hawaii`'s
  tropical jungle by LIGHT, not biome: hawaii is a warm lamplit interior at night with the forest beyond
  the glass; this is flat overhead noon, near-monochrome green-grey, the forest all around. Same move
  that keeps `squirrel`'s real wood distinct from `trees`' alien canopy.*
- **japan** (embeddings) — Japanese **wind shrine** (Shinto).
- **spa** (comparing_means) — a spa; **thermal baths** / wellness facets; interior.
- **squirrel/forest** (comparing_means, 2nd scenario) — a **real temperate mixed-deciduous wood** in late
  autumn→first snow; a **jay** flitting tree-to-tree (vertical hops); the Mother Oak roost. *Deliberately
  earthy/real to stay distinct from `trees`' alien glowing canopy + monorail* — the two forests don't
  double up (real deciduous + flight vs alien + rail).
- **subway / The Faintest Line** (networks) — a disused **Victorian underground railway**, dye-district
  goods lines repurposed as a lichen farm; brick, glazed tile, standing water. *The corpus's first true
  industrial interior; nearest neighbour is `temple`'s crawl-ways, which are ancient stone ruin (and,
  since the 2026-08-26 re-skin, root-choked jungle ruin), not a working plant.*
- **beacons / (networks, partner to subway)** — a **signal-beacon chain along a mountain range**; ridge
  posts, smoke by day, moving weather. *Homage to the Beacons of Gondor but its own range and names.*
  Kept **military-administrative** (rosters, fuel accounts, a survey ledger) to stay distinct from
  `temple`'s stone ruin and `henges`' druidic stones. **NB** beacons also holds the *high-altitude* and
  *high-key daylight* registers — which is why temple's re-skin went to jungle rather than a mountain
  monastery (Lucas, 2026-08-26).
- **henges** (dimensionality_reduction) — teleport-linked standing stones: night beach → black mountaintop →
  fireflies plain → **[room 3 TBD]** → great henge at dawn.

## Claimed
- **Ruined jungle temple** → `hierarchical_clustering/temple` (2026-08-26, Lucas). Claims three
  registers `vibe_inventory.md` listed as free — **harsh flat overhead noon**, **sun shafts (`rays`)**,
  and **near-monochrome with one colour reserved for meaning**. The last is functional: the nine banner
  colours are the ledger escape's row identifiers.
- **Mountain-ridge beacon chain** → `networks/beacons` (2026-08-12, Lucas). Partner scenario to
  `networks/subway`; grades the chapter's relational half. Chosen because **an edge means "I can see
  you"** — the most legible edge available — and weather *deletes* edges without moving a node.
  Claims three unused registers: high-key daylight, storm/cloud, and smoke rather than fire.
  Draft: `rooms/networks/beacons/notes.md`.
- **Salt flat / mirror playa** → `dimensionality_reduction/henges` **room 3** (2026-07-24). Chosen for its
  ethereal, otherworldly, druid-magic feel. Expansive/uniform → a **single teleport-in room**, not a
  room-chain (see the scale principle below).
- **Red-rock slot canyon** → `hierarchical_clustering/canyon` ("The Confluence", 2026-07-25). The dendritic
  drainage network = a dendrogram; descent + rising flood = agglomerative clustering + the cut. Whole
  continuous scenario. Draft in `rooms/hierarchical_clustering/canyon/notes.md`.
- **Inland canal + lock flight** → `modeling` **scenario 1** (2026-08-27, Lucas, session "Canal boat").
  Theme-stage designation — no folder, no build yet; carries its technique. Structured/linear, so
  **whole continuous scenario** per the scale principle below. Vessel-as-moving-hub: the boat is the
  persistent home and the world scrolls past it. **Displaces `modeling/sailing` to scenario 2.**
  *Distinctness, stated deliberately (cf. the two forests below):*
  - **vs `canyon`** — the closest rub, and it is about **water levels**, not harbours. Canyon owns the
    gate-and-water vocabulary (drowned floodworks, sluice-cuts, sluice-wheel, flood-gate heights) and its
    **rising flood is the clock chasing you**. A canal lock is **engineered stepped water on level
    ground**, raised and lowered deliberately by a person — the opposite relationship to the water.
  - **vs `egypt`** — Egypt's boat is a **framing device** (moor on page one, then walk inland: deck →
    quay → market → Library → Pharos); it is a **city** scenario and the vessel never moves. But avoid
    Egypt's **premise shape** — *"you captain a cargo boat and officialdom won't let you leave"* is its
    logline. Passage and levels, **not** cargo, manifests or toll-house gauging.
  - **vs `waterfalls`** — its escape is a **stream-diverter routing maze**; the canal must not divert or
    route water.
  - **vs `sailing`** — inland **stepped freshwater working boat** vs **open salt sea**.
  - **vs `subway`** — subway claims **true industrial interior**, so **not** the grimy Victorian brick
    canal. Go **pastoral working-boat**: green, brown, misty. Unclaimed ground.
  - **Prior art: none.** Swept 2026-08-27 — zero corpus hits for towpath / narrowboat / barge / aqueduct /
    weir; "canal" appeared twice, both as `sailing` scenery. Draft: `scenario_theme_ideas.md`.
- **Period city heist — gallery / vault / townhouse** → `flat_clustering` **scenario 2** (partner to
  `waterfalls`; 2026-08-27, Lucas, session "Canal boat"). Theme-stage designation — no folder, no build
  yet. **Claims two registers nothing else holds: URBAN and MODERN** (no scenario in the corpus is
  either), plus **clinical / white / scrubbed**, the last register `vibe_inventory.md` listed as free —
  a gallery or vault interior is exactly that. *Distinctness:* keep it **measure-and-compare**, not
  **count-and-tally** — case files and ledgers drift toward `egypt`'s manifest and `temple`'s ledger
  escape. Draft: `scenario_theme_ideas.md`.

## Candidate locations
Distinctness noted against the roster above. Light band skews **pre-dawn** (this list was seeded by the
henges arc); re-light freely for other chapters. **Best use** applies the scale principle in Notes.

| Location | Image / mood | Best use | Overlap flags |
|----------|--------------|----------|---------------|
| **Waterfall gorge** | henge on a ledge beside a great cascade, drifting spray, first rainbows, moss-wet stones | **Whole scenario** — structured, could carry a room-chain (ledges/pools/cave-behind) | **Clean** — water, but unlike Egypt's harbour or hawaii's coast. |
| **Red-rock slot canyon** ⇒ **CLAIMED** (`hierarchical_clustering/canyon`, 2026-07-25) | dawn light sliding down narrow sandstone walls, warm, vertical, close | **Whole scenario** — a network of canyons/chambers threads naturally | **Clean** — no dry warm canyon in use. |
| **Blooming heather moor** | endless purple heather, mist pooled in the hollows, stones rising from it | Room or scenario | **Clean** — very henge-authentic; no moor in use. |
| **Basalt giant's-causeway** | hexagonal columns stepping into a misty sea; arches formed of the columns | Room or scenario | Mild — basalt reads faintly *volcanic* (Hawaii); a cold misty causeway is otherwise distinct. |
| **Clifftop above a sea of cloud** | headland over a cloud-inversion, cloud-ocean lit pink-gold, distant peaks as islands | **Single teleport-in room** — expansive/uniform | Mild — cloud-sea + peaks-as-islands echoes **airship**'s floating islands / sky. |
| **Geothermal steam terraces** | tiered travertine pools, mineral-bright, veils of steam catching first light | Room or small scenario | Mild — thermal pools echo **spa**'s baths. |
| **Ancient misted forest** | henge among huge dark trees, fog between trunks, first birdsong, green-gold shafts | (scenario, but) | **Overlaps `trees`** (alien canopy forest) — avoid unless re-themed. |

## Notes
- **Scale — room vs scenario (Lucas, 2026-07-24).** Expansive, uniform settings (a salt flat, a sea of
  cloud) are hard to thread a *continuous* set of rooms through — best to **teleport in, experience one
  room, teleport out**. Enclosed or structured settings (a waterfall gorge, a canyon system, a forest) can
  host a **whole continuous scenario**. Note each candidate's fit in *Best use*.
- These lean to the henges' **pre-dawn** light band (that's what prompted the list); re-light as needed for
  other scenarios/chapters.
- When a scenario claims one, move it to `## Claimed` with the scenario name + date.

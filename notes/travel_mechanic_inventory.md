---
authority: intent
---

# Escape-room travel-mechanic inventory

A living catalogue of **travel mechanics** for the CHEM 5725 escape rooms — *how the player moves between
rooms and areas*, as distinct from the puzzles they solve once there. Sibling of `puzzle_inventory.md`
(what you solve), `candidate_locations.md` (where you are), and `scenario_theme_ideas.md` (the premise).
Started 2026-07-25 (Lucas, session "Canyon"), because travel had been reinvented per-scenario and never
collected in one place.

**Key framing.** Almost all between-area travel is the **same underlying door primitive reskinned by art +
narrative** — a monorail, a rope bridge, a teleport arch and a plain corridor are, to the engine, a door
that swaps you from one panorama to another. So this catalogue is mostly a **design/flavour** reference:
what movement *feels* like and what it can echo, not a list of separate engine features. The genuinely
engine-level distinctions are called out in the **Engine basis** column.

Companion notes: `doors_plan.md` (the shipped forward/back door model), `open_world_and_temporal_arc.md`
(decouple traversal from progression + the backtrack-safe global clock), and the elevation-beat mechanic
(#18 in `puzzle_inventory.md`).

## Two axes every travel choice sits on

1. **Topology** — the shape of the nav graph: linear corridor · hub-and-spoke · open maze · one-directional
   flow · single teleport-in node.
2. **Backtrack policy** — can you go back, and does going back stay consistent? See
   `open_world_and_temporal_arc.md`: the fix is to keep **place art constant** (spatial, position-based) and
   carry the one irreversible thing (the clock/season) in a **global overlay driven by state**, so revisiting
   a place shows *that place + the current clock*, never a backward jump.

**Scale principle (from `candidate_locations.md`, Lucas 2026-07-24).** Expansive, *uniform* settings (salt
flat, sea of cloud) resist a continuous room-chain — **teleport in, do one room, teleport out**. Enclosed or
*structured* settings (a gorge, a canyon system, a forest) can host a **whole continuous scenario**. Pick the
travel topology to match the setting's scale.

## Mechanic catalogue

| # | Travel mechanic | What it is | Used in | Backtrack | Engine basis |
|---|-----------------|-----------|---------|-----------|--------------|
| T1 | **Linear corridor, two-door back-nav** | Forward door CLOSED, gated on solve, shows the target's entry card; back door ALWAYS open, no gate, no entry. The default. | alaska, hospital, hawaii (the shipped model) | Yes (back door) | **Have** — `doors_plan.md`; forward/back `direction` + `to` per door |
| T2 | **Open maze (traversal ≠ progression)** | Every passage open from the start; the *ordering* is enforced on the puzzle hotspot (`availableWhen` + diegetic `lockedBody`), not the doors. Free Myst-style roaming. | squirrel (first intended consumer) | Yes, fully | **To build** — `availableWhen`/`lockedBody` on puzzle hotspots (`open_world_and_temporal_arc.md` item 1) |
| T3 | **Hub-and-spoke arches** | A central hub; each arch is a doorway into a different area; you always return to the hub. | henges (arch hub into each henge) | Yes (via hub) | **Have** — door graph shape (hub node with N doors) |
| T4 | **Teleport nodes** | Step through a portal / standing stone and you're elsewhere with no physical corridor between. Reads as magic; also the shape for a **single teleport-in room** in a big uniform setting. | henges (stone-to-stone); salt-flat / sea-of-cloud single rooms | Depends on graph | **Have** — cosmetically a door with no shared wall; single-room = a 1-node graph |
| T5 | **Rail / car between stations** | A vehicle carries you station to station along a fixed line; naturally couples to an **elevation** climb. | trees (monorail, climbing the canopy) | Yes if line is bidirectional | **Have** — door reskin + the elevation arc in the scene prompts |
| T6 | **Drift / vessel between islands** | A craft moves you across open space between discrete nodes (floating islands, rock islands). | airship (between floating islands); japan theme idea (rope bridges between rock islands) | Yes | **Have** — door reskin |
| T7 | **Flight / vertical hops** | You move as a flying creature, tree-to-tree / ledge-to-ledge; movement is felt as *vertical* and free. | squirrel (the jay flitting; feeds the height-recognition escape) | Yes | **Have** — door reskin; pairs with T8 |
| T8 | **Elevation-transition beat** | A short interstitial *before* each jump showing up / down / same-level, cumulatively teaching the relative heights of the places visited — the travel layer that *is* the escape's data source. | squirrel (heights → CLD grid escape) | Consistent by design (cumulative, not per-room) | **To build** — an `entry`-card variant with an up/down/level glyph (`puzzle_inventory.md` #18) |
| T9 | **One-directional flow** *(proposed)* | A current / conveyance carries you *downstream only*; going back means a deliberate portage. Creates real tension with backtracking — the flow embodies an irreversible process. | *none yet* — candidate for canyon (river float) | Asymmetric (forward free, back costly) | **To build if wanted** — door graph where back-doors are gated/absent, or a portage sub-move |
| T10 | **Surprise scripted launch** *(proposed)* | The puzzles *prepare* a vehicle (fuel / align / arm a rocket); solving the last one TRIGGERS an **unannounced** one-way launch — a scripted, animated transition (the atmosphere zooming past the window, then space) rather than a door the player chooses to walk through. The reveal *is* the payoff. | *none yet* — rocket-prep concept (session "ideas", 2026-08-05) | No (one-way launch) | **To build** — an animated launch interstitial, NOT a door reskin: a scene-over-scene zoom/parallax transition fired on the final solve |
| T11 | **Keyed vehicle unlock (inventory-gated route)** *(proposed)* | The player picks up a **key** early (a field-notebook item), then later finds a vehicle — a dirtbike or similar — whose route is sealed until that key is in inventory; turn the key, ride out somewhere new (a desert vista, a place off the map). Ties travel to the meta-inventory. | *none yet* — dirtbike/key concept (session "ideas", 2026-08-05) | Yes | **Mostly have** — a `clue` with `pickup`+`onPickup` sets a state flag; a door with `availableWhen` reads it (+ a `lockedBody` "locked — you need a key"). Reward scene is a door reskin |

## Backtrack-safe clock as a travel-shaped mechanic

The global, state-driven clock overlay from `open_world_and_temporal_arc.md` isn't travel per se, but it
**interacts with travel**: an irreversible environmental variable (dusk falling, winter closing, **water
rising**) advances with `rooms_solved` and renders identically over every scene, so free backtracking stays
consistent. When that variable also **opens or closes routes** (a flood cutting off low passages; a sun angle
lighting a slot), the clock *becomes* a travel mechanic — the world's traversability changes with progress.
This is the seam where "canyon rising water" and "sun-angle-gated passages" live (see below).

## Proposed / in design — canyon (session "Canyon", 2026-07-25)

Being actively riffed; not yet a build. The red-rock slot canyon is a **clean, whole-scenario** setting
(`candidate_locations.md`). Travel ideas under discussion, and the technique it might echo:

- **Bifurcating drainage network = a dendrogram (hierarchical clustering).** A dendritic canyon system — the
  geology term *dendritic* is literally "tree-like" — where tributaries merge downstream. Walking the
  confluences bottom-up **is** agglomerative clustering; the confluence elevation **is** the merge height.
- **Rising water = the dendrogram cut (and the clock).** The flash-flood clock does double duty: the water
  level is the horizontal cut across the dendrogram that defines *k* clusters. Set/read the level → get the
  cluster count. Unifies the loved "water-as-clock" and "bifurcating network" ideas into one technique echo.
- **Sun-angle-gated passages = viewing along an axis (PCA flavour, or hclust similarity reveal).** Light
  reaches different slots at different times; a sun-angle progression opens/closes routes. As pure PCA this is
  "look along a principal component" (kin to henges' walk-the-PCs, #17). As an hclust helper it reveals which
  distant fingers share a trait (colour/lichen) so you can judge similarity.
- **Open maze + backtracking** (T2) suits the forking slot geometry; **one-directional river flow** (T9)
  suits going *downstream toward the root* of the drainage tree.
- **Puzzle-node-serves-next-in-queue progression** (canyon, 2026-07-25): a lighter open-world variant of T2
  — travel is fully free; designated **puzzle nodes** each dispense **whichever puzzle is next in the
  sequence** on arrival (a queue), rather than pinning puzzle P to node N via `availableWhen`. Can't be locked
  out by visiting the "wrong" node; decouples elevation-reading from puzzle order. Small engine addition.

Fuller design lives with the scenario once a technique is chosen; note here which travel mechanics graduate.

## Waterfall diverter-maze (flat_clustering/waterfalls, 2026-07-26) — NEW, engine-modelled

A **self-reconfiguring descent maze**. The player climbs down a vast shaft of platforms joined by
bridges; **falling waterfalls cut the bridges** (a stream straight-down cuts the horizontal bridge in
its gap; diverted sideways it cuts the vertical ladders it crosses). The player throws **diverters**
(unlocked by solving each station's flat-clustering puzzle) to re-route the water, opening/closing
bridges — so the passable graph changes as you descend, and a deliberate backtracker (throw a lever,
descend, return and throw it again) is baked in. A **live top-down "viewing port" map** (the router
ported to JS) shows the whole shaft and updates as diverters flip.

- **Not a cosmetic door reskin — a real model.** `rooms/flat_clustering/waterfalls/cave_engine/`:
  `router.py` (flow → cut bridges for any diverter combination; reproduces the hand-authored states),
  `reach_art.py` (reachability + art budget), `player_map.html` (live map, router ported to JS),
  `puzzle_editor.html` (authoring tool). Puzzle authored in `puzzle.json`; full record in the
  scenario's `notes.md`.
- **Engine gap (Lucas to build in the harness):** movement gated on "bridge passable iff diverter
  state = X" (a `showWhen`-style edge condition reading `gameState`) — the natural extension of the
  open-world/counter gate. Diverters = `dial` hotspots; the viewing port = a `mapview`.
- **Ties to the technique:** the world is a *sorting engine* (channels flows into pools) — flat
  clustering as a machine; the escape is the k-means recognition on the flooded floor (count the pools).

## New ideas — session "ideas" (Lucas, 2026-08-05)

Two travel mechanics riffed, not yet attached to a technique or scenario. Both are catalogued above (T10, T11).

- **Surprise scripted launch (T10) — "you were building a rocket the whole time".** The whole scenario reads
  as ordinary prep work: each puzzle *readies* a space rocket (compute the fuel load, align the guidance,
  arm a stage). Then the final solve **launches it with no warning** — a scripted animation of the atmosphere
  rushing past the window, sky darkening to space. The trick is that the player never *chose* to travel; the
  travel is the reveal. Engine-wise this is the one genuinely non-door item on this list — it wants an
  **animated launch interstitial** (a scene-over-scene zoom/parallax, sky→space), fired on the terminal gate,
  not a panorama door-swap. Good candidate to pair with a technique whose escape *is* the launch (e.g. the
  final computed value is the one that gets you off the ground).

- **Keyed vehicle unlock (T11) — a key you carry, a ride you earn.** Somewhere mid-scenario the player picks
  up a **key** (a field-notebook pickup — `clue` `pickup` + `onPickup` sets a state flag). Later they reach a
  vehicle — a dirtbike is the given example — parked at the edge of the world; its onward route is **sealed
  until the key is in inventory**. Turn the key and you ride out to somewhere new and worth seeing (a desert
  vista, an off-map destination). This is the meta-inventory doing travel work: it's the same fragments-that-
  unlock pattern as the boss/escape meta-puzzles, but the payoff is *going somewhere* rather than *keying a
  code*. Mostly buildable today with `availableWhen` + `lockedBody` on the door reading the collected-key
  flag; the reward area is a plain scene reskin.

## Notes
- A travel mechanic graduates OUT of "proposed" when a scenario ships it — record the scenario + date in the
  **Used in** column.
- Most rows are **cosmetic reskins of the door primitive** — don't over-count engine work. Real engine items:
  T2 (`availableWhen`/`lockedBody`), T8 (elevation beat), and the state-driven clock/route overlay.

---
authority: intent
---

# PLACES brief — the shared Rothamsted world (step 3b, both ANOVA scenarios)

Session "ANOVA" (slot 4), 2026-11-01. Input to the world skeleton and the plate-swarm brief JSON
(`authoring_v2/plate_swarm/brief_anova.json`, not yet written). Research and plaque tiers: `research.md`.
Blueprints: `cellars/notes.md` §9, `glasshouses/notes.md` §8.

## Decided (Lucas, 2026-11-01)

- **Layout A:** one manor house with a **laboratory wing** at one end, **cellars under the whole house**, and a
  range of **glasshouses and pot-culture houses off the back garden wall**.
- **Boards (cellars):** the electrical **switchboard hangs in the kitchen** (main floor, player M); the **water
  board hangs in the wash-house** (cellars, player C). Both are where the supplies would enter, and neither room
  is on the passage, so a board's position cannot cue the answer.
- **Passage, stacked:** the **boiler room lies directly under the laboratory**, the **archive vault directly under
  the library**; the passage is a **narrow stair inside the thick wall between them**, carrying the heating main
  and cable. **M's door panel is behind the library bookcase; C's is at the archive vault end.** The players meet
  on the stair.
- **Glasshouses clocks:** the **regulator** stands in a **clock closet behind the Director's study panelling**
  (the secret door); the **main switch** that restores power after R2 is in the **cupboard under the hall stair**.
- **Plaques, one per scenario:** the **Sample Archive** (since 1843, CONFIRMED) in the cellars' **archive vault**;
  **Fisher & Mackenzie 1923** in the glasshouses' **study** (ANOVA claim still TENTATIVE: confirm from the paper
  before it is printed).
- **Landing text** for both approved by Lucas and snapshotted (`validate_story.py --accept`); `coverPrompt` and
  `worldPlatePrompt` authored in each `scenario.json`.
- **Glasshouses starts in a cellars room** (Lucas, the spa ↔ squirrel pattern): its first room is one of the
  cellars scenario's rooms, re-lit to the glasshouses' foggy Saturday morning (an image edit of the committed
  cellars art, never a fresh generation), gateless, with an open door into its own rooms. **The room is the FOOT OF
  THE CELLAR STAIR** (both players' start in cellars; changed from the drawing room at 4a, Lucas 2026-11-02, so a
  player of either scenario recognises it). Route: *Room graphs* below.

- **Weather and the outage (Lucas, 2026-11-01):** a **storm in the night**; a **supply line comes down near dawn**; the
  morning is the **still, foggy calm after it**. Aftermath detail in the art: wet glass, puddles, fallen branches.
  The fog look, the glasshouses' shadowless light and its lamplight-to-grey-dawn tension device all stand.
  Rejected: a foggy daytime thunderstorm (fog and thunder rarely coincide; lightning casts the shadows the clock
  puzzle must avoid); fog flashover on the insulators as the cause.
- **Clock rework (Lucas):** the line comes down **near dawn, 6:30 a.m.**, so the dials are only a couple of hours
  wrong: dark state 6:30, lit 7:00, regulator 9:15, mantel clock 11:40, door a **3-digit `lock`, answer 135**.
  Verified by `glasshouses/_scratch/escape/verify_clocks.py` (pass; VERIFY_BREAK fails). Rejected: 2:30 a.m. /
  answer 375 (daylight makes 3:00 plainly wrong, weakening the consensus trap); the door taking hours-and-minutes.
- **Plate weather (Lucas):** the world plate is drawn in **light, thinning fog** so the mood carries through
  (accepting less crisp geography); rejected a clear after-storm reference plate.

## Skeleton and plates (step 3b, done and LOCKED 2026-11-01)

- **World skeleton BUILT** (2026-11-01): `cellars/_scratch/world_skeleton/world.py` (shared by both scenarios; frame
  +Z north, +X WEST, recorded in its docstring). Checks exit non-zero (passage stacking, boards off the passage, clock
  closet in the study, glasshouses reached only through the garden gate); `WORLD_BREAK=1` fails as it should.
- **Master menu run** (`swarm_master_v1/`, brief `brief_master.json`): 4 of 4 fog variants survived the gate, each
  checked by eye against the block model (lab wing left, kitchen wing right, garden behind, path to the far gate,
  range beyond the wall with the potting shed right, limb across the fallen wires). **Lucas picked `fog_in_bands`**,
  frozen at `cellars/world_plates/master/master_sw.png`.
- **Derive runs** (`brief_derive*.json`, `swarm_derive_v1..v3/`): round 1 from_north had the house's front facing the
  garden, and east_high copied the master's camera; round 2 drew the master's south camera for both (cause: the shared
  `common` text was written in the master's framing, "front facing the camera", "drive from the left"; round 3 rewrote
  it in compass terms). **Rule for this world's briefs: describe places by compass, never by picture side, in
  `common`.** Round 3 from_north: house, garden and range all right (back door onto the path, kitchen wing left, lab
  wing right); the poles, limb and cedar beyond the house are mirrored. east_high not drawn in round 3 (budget
  spent on from_north). **Lucas accepted round 3 from_north as it is** (frozen at `cellars/world_plates/master/from_north.png`)
  and **skipped the east view** (interiors only; the block model fixes the end-to-end order).

## Room graphs (step 4a, Lucas 2026-11-02; sketches `cellars/_scratch/graph/draw_sketch.py`)

- **cellars:** both players start at the locked cellar door, M in the entrance hall, C at the foot of the cellar
  stair (voices only). Each goes east first (rungs 1-2: M drawing room, kitchen; C seed store, wash-house), then
  west (rungs 3-4: M library, laboratory boss; C archive vault, boiler room boss). M walks through the study
  (shared art with glasshouses). **Gates at rung 2, physical:** M's study key hangs on the kitchen key board;
  C's far cellars stay black until C's lights come on. **Power, no sync:** the line is back but every circuit
  tripped; at rung 2 M resets the house circuits at the kitchen switchboard (which also makes M's board live)
  and C resets the cellar circuit in the wash-house. Escape panels: behind the library bookcase (M) and at the
  archive vault end (C), each a travel clip into the passage stair, where they meet.
- **glasshouses:** starts at the **foot of the cellar stair** (re-lit cellars art, the stair door now open, so
  both scenarios share a room each player recognises); **the drawing room is dropped**. Route: hall → study
  (rung 1; gives the potting-shed key) → **back garden, ONE outdoor room** (Lucas's exception to interiors:
  fog, puddles, branches, the gate in the wall; the path turns east along the range front, because the glass
  houses have no outside doors and are entered only through the potting shed, the range's head house) → potting shed (locked until the key; rung 2, power back, throw
  the main switch under the hall stair) → pot-culture house (rung 3) → big glasshouse, possibly two rooms for
  scale (boss at the far end) → back to the study closet (regulator) → out again through the garden and the range
  to the **time-locked back gate onto the station lane**, just past the big glasshouse's far end: 135 (Lucas chose it
  over the front door and the master clock). The gate's keypad is boxed in the far-end room, seen through its end
  door; victory is a clip along the lane in fog. The front door is simply locked (the caretaker has the key).

## Sightlines (checkable)

- No room sees another room; every window shows only pale fog.
- No glasshouse sees the house, and the house sees no glasshouse (fog).
- Nothing in any room reveals the passage: no pipe or cable visibly running only through the library,
  laboratory, boiler room and archive vault; the library bookcase does not read as a door until it opens.
- The regulator is never visible until the study panelling opens (lit state only).
- The time-locked lane gate is visible through the end door of the big glasshouse's far end.

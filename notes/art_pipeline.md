---
authority: intent
---

# Automated art pipeline — the scene spec (design + phasing)

**Direction agreed 2026-08-03 (Lucas).** Turn scenario art-building from per-room hand-labour into an
automated cascade that stems from two things Lucas VERIFIES: the **network layout** (the room graph) and a
**description of vibes** (atmosphere). Everything else flows from there.

## The unifying abstraction — the SCENE SPEC
One structured object per room (`authoring_v2/scene_spec.py` documents the schema). It is an ordered
**left-to-right list of placed elements** + atmosphere, where each element is flagged for its role — it
either MOVES (a cinemagraph) or is a gameplay object (puzzle / door / clue). From that ONE spec, three
things derive **deterministically** (no second authoring pass):

1. `render_prompt(spec)` → the **gpt-image-2 prompt**, in the proven left-to-right spatial format
   ("On the far left, …; to the left, …; dead ahead, …"). gpt-image-2 follows this format well.
2. `cinemagraph_jobs(spec)` → **one batch job per animated element**, motion prompt + loop already written.
   The cinemagraphs fall OUT of the art step instead of being marked/prompted by hand afterwards — this is
   the core time-saver. Feeds the batch queue built 2026-08-03 (see hub_and_spoke_plan.md).
3. `to_hotspots(spec)` → the **hotspot stubs** the room needs (ambient for animated decor — no player marker;
   puzzle/door/clue for gameplay). So the spec seeds the whole room, not just the picture.

**The key design move** (Lucas's insight): declare the animatable objects **up front, as part of writing the
prompt** — place "a brass lantern swinging from a chain on the left", described in an animation-friendly way
(a lantern on a chain, not fixed to a post; steam deliberately venting) — rather than generating art and
reverse-detecting what to animate. So we already know WHAT moves, roughly WHERE, and HOW before the art exists.

**Boxes are deliberately NOT in the spec.** An element's pixel box is **localized after** the art is
generated (the spec says "the lantern on the far left"; a localizer finds the actual box, constrained by the
spatial hint — far more reliable than open-ended detection). `cinemagraph_jobs()` emits jobs without a box;
the localizer fills it before the batch runs.

## What already exists that this composes (not new)
Room graph / story-map · per-room `authoring.scenePrompt` · **world plate** (continuity anchor) · **per-room
reference crop** (incoming-door continuity, `_room_ref_crop`) · the **`ambient` hotspot type** (marker-less
cinemagraph decor) · the **batch queue** (`/api/batch-*` + `cinemagraph_batch.py`) · cinemagraph presets+loop.

## What is new to build
- The **scene-spec structure** (done: schema + pure renderer/extractors in `scene_spec.py`).
- An **LLM spec-author**: from (network + vibes + each room's role) draft the per-room specs; Lucas reviews.
- A **localizer**: post-gen, turn "the lantern on the far left" into an actual box (vision-assisted,
  constrained by the spatial phrase) → materialize ambient hotspots + fill the queued cinemagraph boxes.
- **Continuity scheduling** (phase 2): a landmark seen from room A must match when you enter it as room B.
  This forces a **generation ORDER** — establish/lock the landmark first (its art or a world plate), then
  rooms that depict it reference it. The `continuity` spec field is reserved for these links. Lean on the
  existing world-plate + reference-crop primitives first; full per-landmark continuity is a later refinement.

## Phasing (biggest win first; confirm each holds)
- **Phase 1 — scene spec → prompt + free cinemagraph annotations.** The heart; kills the manual authoring.
  **PROOF DONE 2026-08-03:** `authoring_v2/scene_spec.py` (pure, stdlib-only: `render_prompt` /
  `cinemagraph_jobs` / `to_hotspots`) + a faithful hand-written spec for the airship **boss** room
  (`authoring_v2/scene_specs/airship_boss.json`, built from the room's real prompt + ambient hotspots).
  Round-trip verified: `python3 scene_spec.py scene_specs/airship_boss.json` renders a prompt matching the
  real boss prompt's format AND yields 7 cinemagraph jobs + the puzzle + the door from the one spec.
  **WIRED INTO THE HARNESS 2026-08-03:** `harness_server.py` imports `scene_spec` and exposes
  `/api/render-scene-prompt {spec}` (stateless preview) + `/api/save-scene-spec {chapter,scenario,roomKey,spec}`
  (stores `authoring.sceneSpec` + renders into `authoring.scenePrompt` — which gen already reads — without
  clobbering other authoring fields; returns the derived cinemagraphs+hotspots). Both call the same
  `scene_spec` code a future "build world" orchestrator will use. Build-card UI (`harness_gpt.html`): a
  collapsible **scene spec** textarea per room + "Render & save → prompt" that fills the prompt field and
  reports how many cinemagraphs will fall out. **New routes → needs a harness restart to go live.**
  **Still gated on the localizer (Phase 2):** auto-*queuing* those cinemagraphs needs boxes, which the
  localizer fills post-gen — so today the spec writes the prompt + tells you what WILL animate; the actual
  batch-queue-from-spec lands with the localizer. **v3 decision:** NOT a rewrite — the automation is an
  additive layer over v2's manual controls; "build world" orchestrates the same gen/batch/spec primitives.
- **Phase 2 — localizer + LLM spec-author** (find boxes post-gen; draft specs from network+vibes).
  **LOCALIZER BUILT + WIRED 2026-08-03:** `authoring_v2/localizer.py` — asks a vision model (GPT-4o via the
  existing `OPENAI_API_KEY`, plain HTTP like generate_scene.py, image downscaled before upload) to find each
  spec element's box. Per Lucas's refinement it is fed THREE things + an explicit **relationship** blurb:
  the IMAGE, the generating PROMPT (names objects left-to-right → gives order/position), and the object LIST
  (id + desc + `at` phrase) — so it uses the prompt's ordering to disambiguate (e.g. which of two boilers).
  Returns `{id:{box,confidence}}`, clamped/ordered. Harness endpoint `/api/localize-room {chapter,scenario,
  roomKey[,model]}` runs it server-side (where the key lives) off the node's stored `sceneSpec` (or falls
  back to existing hotspots). Pure logic unit-tested (clamp/IoU/message assembly). **Vision ACCURACY not yet
  validated** — no key in the agent shell; run in the harness terminal (which has the key):
  `cd authoring_v2 && python3 localizer.py --scene ../rooms/data_vis2/airship/boss/scene.png --spec scene_specs/airship_boss.json --truth ../rooms/data_vis2/airship/scenario.json --room boss`
  — prints predicted vs the boss's real hotspot boxes + IoU/centre-dist (the boss has ground-truth boxes for
  boiler/steam/liquid2/etc). New endpoint → needs the harness restart to go live.
  **Phase 2b:** materialize `ambient` hotspots + queue cinemagraphs — DONE via approx-boxes + human nudge
  (see the DECIDED section above), localizer parked.
  **SPEC-AUTHOR — DONE 2026-08-03 (Claude is the author; no server LLM — Lucas's call).** Not a server-side
  model: Claude drafts the specs. Codified in `authoring_v2/SCENE_SPEC_GUIDE.md` (schema + rules: left-to-
  right `at` sweep, animation-friendly framing, boomerang/crossfade, seam awareness, doors, gameplay flags)
  + the skill **`escape_room_scene_spec`** (auto-triggers when Lucas asks to "write/draft the scene specs").
  Bulk plumbing: harness `/api/save-scene-specs {roomKey:spec}` (store + render all in one load-modify-save)
  and `/api/apply-spec-all` (materialize hotspots + queue cinemagraphs across the whole scenario). Tested.
  New routes → need the harness restart.
  **"BUILD WORLD" CONSOLE — DONE 2026-08-03.** `authoring_v2/ui/build_world.html` (served at
  `:8752/build_world.html`) — the thin v3 driver (NOT a rewrite; v2 grid + hub stay underneath). Scenario
  picker → 4 stages: (1) paste Claude's `{roomKey:spec}` → Load (`/api/save-scene-specs`); (2) generate+commit
  art per room (human — links to the art grid); (3) Apply all (`/api/apply-spec-all`); (4) review boxes + Run
  batch (`/api/batch-run`, polls). A per-room table shows pipeline status (spec ✓ / built ✓ / hotspots /
  cinemagraphs done vs candidates-to-pick) with an "open hub →" link per room. Status via new
  `/api/scenario-state`. Inline `node --check` clean. New routes (scenario-state, save-scene-specs,
  apply-spec-all) → need the harness restart. This is the one-button-ish surface; the automation below it all
  exists + is tested. Remaining polish (later): continuity-ordered gen (phase 3), a link to the console from
  the art grid, and optionally auto-driving the per-room art gen (currently human).
  **LOCALIZER ACCURACY FINDING (2026-08-03, validated on airship boss vs ground-truth boxes):** BOTH engines
  are poor on our art. GPT-4o (`localizer.py --engine gpt4o`): mean IoU ~0.15, places boxes by prompt order
  (uniform sizes, even x-spacing, 1.0 conf everywhere) — a coordinate grid overlay + anti-even-spacing prompt
  did NOT help. Grounding-DINO-tiny (`--engine gdino`, `grounding_dino_detect.py`, runs under ~/ComfyUI/.venv
  on the GV100, model cached): mean IoU ~0.07, collapses onto the big central apparatus for most queries;
  short noun-phrase queries didn't fix it. Only the console (big/central/distinct) localizes well (IoU ~0.53)
  in both. **Root cause:** stylised illustrations on a 3:1 equirect panorama are out-of-distribution for
  photo-trained detectors, the wide aspect gets squished on ingest, and repeated objects (2 boilers, all
  brass) defeat disambiguation. **Open decision (awaiting Lucas):** (a) tile the panorama into square-ish
  overlapping chunks + detect per tile + map back (standard panorama trick — attacks the squish, cheap-ish);
  or (b) DON'T chase pixel-perfect auto-boxes for ambience — place APPROXIMATE boxes from the spec's
  left-to-right layout (free) + a quick drag-to-fix in the existing flat editor. Given Lucas frames these
  cinemagraphs as low-stakes "just-for-fun" ambience, (b) is the ROI-honest lean; the big time-saver (spec
  auto-writes the prompt + every motion prompt + declares what animates) is ALREADY captured — only the box
  is unsolved. Engines kept behind `localize(engine=...)` so we can swap without touching the pipeline.
  **DECIDED (b) + BUILT 2026-08-03:** `scene_spec.approx_boxes(spec)` maps each element's `at` phrase → an
  approximate x-band (falling back to even left-to-right distribution), default mid-height box. Harness
  `_apply_spec` + `/api/apply-spec {chapter,scenario,roomKey}` materializes the room's stored `sceneSpec`:
  creates any MISSING hotspots (ambient/door/puzzle) with approx boxes (non-destructive — existing hotspots
  keep their tuned boxes/wiring) and queues a cinemagraph batch job (with box+prompt+loop) for each animated
  element lacking a clip; idempotent. Build-card button "Place hotspots + queue cinemagraphs". Flow: render
  spec → generate → commit → Place → open room, nudge the rough boxes in the flat editor, Run all. Localizer
  (`localizer.py` + `grounding_dino_detect.py`) kept for later/large-object use behind the engine flag. **New
  routes (apply-spec, localize-room, scene-spec) need the harness restart to go live.** The tiling-detector
  idea (option a) is parked, not pursued.
- **Phase 3 — continuity-ordered generation** across the graph.

## DECIDED — human stays in the loop at box-marking (2026-08-03)
Lucas's call after testing: **hotspot box placement is the one step where a human eye is worth it** — the
cinemagraphs live or die on subtle box adjustments (capture the whole moving thing without swallowing static
wall; where the composite edge falls; grab the intended object not a neighbour). This is judgement, cheap
for a human, expensive/unreliable for a model (confirmed: both a vision LLM and Grounding DINO failed).
**Consequences:** (1) stop chasing auto-localization — the localizer stays parked behind the engine flag,
no further effort. (2) The approx-boxes + human-nudge flow IS the design, not a stopgap. (3) **"build world"
= build to a box-review checkpoint:** the agent auto-writes prompts, generates art, places approximate boxes,
and writes every motion prompt, then hands the human a quick per-room box tidy before the cinemagraph batch
runs. (4) Invest where the human now works: **fast, precise box editing** in the flat editor — the current
gap is that existing boxes can't be dragged/resized (delete-and-redraw only), which is the wrong tool for
subtle nudges. Drag-to-move + corner-resize BUILT 2026-08-03 in the hub flat editor (`reproject_test.html`): drag a box
body to move it, drag a corner handle (shown on the selected box) to resize; a press without movement still
selects; changes persist on "Save hotspots" like a redrawn box; the 360 markers refresh on release. UI-only,
served live (hard-refresh, no restart). Replaces the old delete-and-redraw-to-move.

## Open decisions
- Vision model for the localizer / spec-author: **GPT-4o via the existing OpenAI key** (least new plumbing —
  already keyed for gen/doors/variants) vs Claude. Leaning GPT-4o.
- How much Lucas reviews: he verifies network + vibes; LLM drafts specs; a quick glance before spending GPU.
</content>

## Current state / in-flight (2026-08-03)
- **NETWORK VIEW added to build_world** — "Network & planned hotspots" panel: a card per spec'd room with its
  door connections + planned hotspots (from `to_hotspots`), no story/entry. `_scenario_state` extended to
  return per-room `doors` + `planned`. Lucas wants the network finalized (part of the spec) BEFORE art.
  **Server change → needs ONE more harness restart to feed the new data** (build_world HTML is served live).
- **FIRST REAL PIPELINE TEST IN FLIGHT — `wrangling/trees` ("The Collector's Vault"), 2 rooms: station1 +
  car_sq.** Fully-designed-but-unbuilt scenario (world/story/per-room designNotes + draft scenePrompts exist;
  zero art, zero hotspots). Decisions: 2 rooms first; place ALL hotspots as stubs (puzzle/clue/grid/door/
  ambient) so Lucas tunes every box in ONE pass; the scene-spec pipeline does ART + ambient + hotspot
  PLACEMENT only — puzzle GRADING is a separate wiring pass. **The 2 scene specs were DRAFTED and given to
  Lucas in chat (NOT yet loaded)** — station1 (mist/lanterns/spores animate + field_instrument puzzle +
  square_door→car_sq) and car_sq (window_mist/cabin_lantern/beetle_cabinet animate + collectors_note clue +
  square_door→station2). Next: Lucas restarts, pastes them into build_world stage 1 → Load → reviews network.
- **OPEN DESIGN (deferred, does NOT block art):** the monorail-car travel mechanic — two doors in/out vs a
  lever-gated "ride" (world-state) — the spec places the car's one visible door now; ride-gating is wiring.
- Trees design record lives in `rooms/wrangling/trees/notes.md` + `rooms/wrangling/trees/AGENTS.md`.

## Session 2026-08-04 — multi-view doors, the `switch` role, and the build_world console rebuild
Trees test still in flight (station1 + car_sq + now station2 spec'd). This session settled the monorail
travel mechanic and rebuilt the build_world network view. All logic-tested (py_compile + `node --check` +
pure-function node tests); **a harness restart carried the server changes** (Lucas restarted mid-session).

- **Monorail mechanic DECIDED — single-door, world-state switch, multi-view door** (supersedes the old
  two-door / shared-"down"-node back-nav in the trees notes). One door per car; a **lever (world-state
  switch)** in the car picks direction; the SAME door looks out on a different station per state. Chosen for
  panorama real-estate (later stations have two monorail lines → four doors would eat the view). **Runtime
  switching = deferred engine wiring** (the "world-state dial re-renders a room" pattern, partly built for
  `solvents`); **only the ART is done now** — every open-door reveal is generated in the art step.
- **Multi-view door in the pipeline (BUILT).** `scene_spec.dooropen_jobs(spec)`: a door element may carry
  `door.opensOnto:[{state,reveal[,when]}]`; each open-view becomes a **state-tagged `variant` job** on the ONE
  door hotspot (reuses the existing variant gen end-to-end — no new generation code; box = the door's own
  box). `_apply_spec` queues these alongside cinemagraphs. `_scenario_state` reports `doorViewCount` +
  per-door `views`. car_sq's door now declares 2 views (back→station1, forward→station2).
- **New `switch` hotspot category (BUILT).** `scene_spec.to_hotspots` recognises `switch:true` → type
  `"switch"` — a world-state control (lever/dial/valve), placed + boxed like a puzzle but **NOT graded**, so
  real WebR puzzles aren't confused with state levers. car_sq's `drive_lever` retagged puzzle→switch. Wiring
  reclassifies it to its real mechanic. (Guide: `SCENE_SPEC_GUIDE.md`.)
- **build_world console rebuilt** (`ui/build_world.html`, served live):
  - **Specs survive a restart.** New `/api/scene-specs {chapter,scenario}` → `{roomKey:spec}`; the console
    auto-fills the specs textarea from disk on scenario-select + a **↻ load from disk** button. So editing the
    scenario.json on disk + hitting refresh replaces paste-into-chat. Button renamed "Render network from spec".
  - **Network view merged into the specs card** and rebuilt as a **deterministic metro-map minimap**: each room
    is a top-down 360 circle (**top = ahead**, sides = left/right, bottom = seam/behind), hotspots are coloured
    dots on the ring at their real panorama angle (`_scenario_state` now returns each planned hotspot's `x`),
    hover/tap a dot for detail. Doors are ports; a line runs **door-to-door** to the target (leaves each port
    radially outward via a bezier so it never crosses a circle; lands on the target's return door, else a
    single-door room's only door, else the facing edge). Solid=forward, dashed=back, dotted=open; a **multi-view
    door gets an outer ring**. Layered by forward-door depth (no jitter). Force-directed was considered and
    **rejected** (jitter on a reference view; graphs are near-linear). Pure `buildNetSvg` is unit-tested.
  - **Fixes:** ring orientation was inverted (ahead-at-bottom → right-side doors landed on the left, lines cut
    across the circle) — corrected to ahead-at-top; and the door-to-door landing (single-door target).
- **Trees clue change DECIDED — drop the written car clues.** The cars' framed collector's notes are cut; the
  grouping (beetles=colour □, cones=size ○, shells=shape △) reads from the **tray art**, with the car's **shape
  motif on the display case** carrying the shape→trait mapping. Works because re-inspection is by riding back
  down (the two-view door / back-nav is the safety net) — the note was never load-bearing once backtracking
  exists. Station clues (field cards, science context for the WebR puzzles) stay. Trees design records
  (`rooms/wrangling/trees/notes.md`, `AGENTS.md`, per-room `designNote`s) updated to match.
- **station2 spec drafted + written to disk** (higher station: puzzle instrument + clue + forward circle door
  → car_ci + back square passage → car_sq). So the network now shows station1 → car_sq → station2.
- **Open (deferred, does NOT block art):** the switch's runtime wiring (state var + door-view selection + the
  freeze/hum sfx) and the car ride-gating — all the WIRING pass (`escape_room_wiring`).

## Session 2026-08-05 — level-1 art console, the world plate, conventions, and the deep gradient
Big session. The scene-spec pipeline now has a full in-console **level-1 art stage** (generate + wrap/seam +
commit per room), a **world plate** for cross-room continuity, and the trees scenario is **fully spec'd (all
8 rooms) + prompts rendered**, with Lucas actively generating room art. All logic-tested (py_compile +
`node --check` + the node suite, 49 green). **A LARGE batch of harness routes is pending ONE restart** (see
Gotchas at the foot). Built, in order:

- **Remaining 5 specs drafted** (`car_ci`, `station3`, `car_tr`, `boss`, `vault`) via `escape_room_scene_spec`,
  following the cars/stations pattern (car = single multi-view switch door + drive-lever + grouped-specimen
  cabinet with its shape motif, NO clue; stations = puzzle + field-card clue). **New `lock` role** added to
  `scene_spec.to_hotspots` for the vault's `grid-select` escape gate (the guide listed `lock:true` but the code
  never emitted it). Fixed **station1's missing field-card clue**. All 8 rooms' `scenePrompt`s rendered.
- **Skills updated** (Lucas's ask): `escape_room_wiring` (how to wire a `switch` hotspot's state + a multi-view
  door's view/target selection + the freeze/hum sfx — flagged as deferred engine work) and
  `escape_room_scene_validator` (a lever/switch maps to an ungraded `switch` hotspot; a multi-view door is one
  box with N pipeline-authored variants — count, don't re-author/flag). **Network graph extracted to a shared
  module** `authoring_v2/ui/net_graph.js` (browser + node), with a **regression test** `tests/net_graph.test.js`
  (7 tests, header = the arrow-fix failure narrative; added to the `npm test` list) — build_world.html loads
  the module now.
- **LEVEL-1 ART STAGE (build_world step 2).** Per-room: **Generate** (`/api/gen-room-pano` → ONE hi-res
  3072×1024 gpt-image-2 pano into `_scratch/l1_<room>.png`, keyed off explicit chapter/scenario, no
  active-scenario coupling), a preview thumb, **view prompt** (read-only — the spec is the source), **wrap &
  seam →** (opens the hub in `?level1=1` mode), and **Commit** (`/api/save-room-pano` → promotes the pano to
  `scene.png` + `built` + default full-360 wrap; renamed from Save; row tints green + button → "Committed ✓"
  when built). Regenerating REPLACES (one pano per room).
- **LEVEL-1 WRAP+SEAM HUB MODE** (`reproject_test.html?…&level1=1`): wrap + seam + commit ONLY — hides the
  Spots/Wrap spoke tabs (already in wrap), world-plate, door, candidate-seam, and the redundant "Save params"
  (Commit room saves the wrap). Seam-fix is **in place on the candidate BEFORE commit** via `/api/seamfix-scratch`
  (new; keeps a `*_preseam.png` backup). **Default vertical coverage → 90** (was 95).
- **WORLD PLATE.** A scenario-level `worldPlatePrompt` — a "world-bible" establishing panorama packing the key
  elements + palette, written **time-neutral** ("soft even daylight, neither dawn nor sunset") so per-room
  prompts drive the time-of-day arc. Lives in the **spec bundle** (a `worldPlate` entry, edited in stage 1 —
  single source of truth; read-only view in the panel). `/api/gen-world-plate` generates it FIRST in step 2 and
  auto-promotes to `_world/plate.png`; every room's `/api/gen-room-pano` references it. **KEY FINDING
  (web-searched, confirmed):** gpt-image-2 does **NOT** support `input_fidelity` (gpt-image-1 only — passing it
  400s) and processes references at **high fidelity always**, no loosen knob. So the "low-fidelity = world not
  lighting" lever doesn't exist; the ref is edit-oriented. Risk: it can flatten the dark→bright arc at the
  extremes. **BUT Lucas tested: the plate "didn't pull station1 too hard"** — so the single-neutral-plate
  approach is holding for now; the fallback (per-room "use plate" toggle, or phase plates) is designed but
  **not built** (offered, Lucas declined for now).
- **build_world console cleanup.** New **step 0 "Concept & spec"** (dream the real-world technique → escape;
  run the escape [NEW, Lucas to build] / puzzle / story skills → `design_notes.md`; then build the spec).
  Removed the subtitle, the network legend, stage-1 hint, load-from-disk toast; **"Render network from spec" →
  "Write spec to disk"** (it always wrote to disk; renamed for honesty — pairs with ↻ load from disk).
- **SEAM + VEHICLE-DOOR conventions (baked into `SCENE_SPEC_GUIDE.md`).** (1) The wrap seam (far-left =
  far-right = behind you) must be **continuous backdrop** — structural objects in the FRONT, matching backdrop
  at both far edges, **no linear features (cables/tracks) run off an edge** (gpt-image won't wrap a thin line;
  run cables UP or terminate). (2) A door that boards a vehicle **IS the vehicle's own door** — "a gondola
  docked, boarded through its own sliding door", NOT "a boarding door with a car beyond it" (the model renders
  two objects). Both learned on the trees stations; all 3 stations rebuilt to comply.
- **STRONG GRADIENT — station1 + car_sq deepened.** The bottom of the climb is now maximally **deep, dark,
  enclosed**: immense trunks all around vanishing into mist above AND below, only a few god-rays, lichen/spore
  glow the only warmth, negatives banning mountains/open-sky/sun. Maximises contrast with the sunlit summit.
  The car's two door-reveals now carry the gradient (dark station1 back ↔ brightening station2 forward).

### Level-1 step 2 now keeps up to 3 candidate panos per room (2026-08-05, later)
The level-1 pano stage went from **one pano per room** (`_scratch/l1_<room>.png`, overwritten each Generate)
to **up to 3 candidates** (`_scratch/l1_<room>_<n>.png`, n=1..`MAX_PANO_CANDIDATES`=3). Each candidate is a
tile in its room's row with three corner icons — **✓ commit** (top-left → `save-room-pano`, quick full-360
commit; flags the committed tile `live` via the node's `builtFrom`), **⤢ wrap/seam** (top-middle → opens the
level-1 hub `?img=<candidate>&level1=1`, whose Commit promotes the tuned wrap), **✕ delete** (top-right → new
`delete-room-pano`, also sweeps the `_preseam`/`_seamtmp` siblings). The old standalone **Commit** button and
**wrap & seam** link are gone (folded into the per-candidate icons). **A 4th Generate errors** — both the
client (`genPano` guard) and the server (`gen-room-pano` returns 409 when 3 exist); Generate picks the lowest
free index, so it **fills a gap** left by a delete. A pre-existing single `l1_<room>.png` (legacy, no index)
stays visible as a candidate so an in-flight build isn't orphaned. Backend: `_pano_candidates` /
`_next_pano_idx` / `_pano_re` helpers + `panoCandidates`+`builtFrom` in `_scenario_state`; regression tests in
`authoring_v2/test_harness_server.py` (`test_pano_candidates_and_gap_fill`, `…_keeps_legacy_single`,
`test_delete_room_pano_rejects_siblings_and_escape`). **Route signatures changed → needs a harness restart**
(adds to the pending-restart batch); `build_world.html` is served live (hard-refresh).

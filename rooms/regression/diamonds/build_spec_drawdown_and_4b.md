---
authority: intent
---

# diamonds — build spec: the drawdown board instrument, then step 4b scene specs

Written 2026-10-20 at a handoff (session "modeling", slot 2). Lucas approved both tasks in chat. Do A, then B.
Design record: `notes.md` (§3 escape, §5 board, §6 ladder, §7 engine delta, §10 ART CONSTRAINTS, §11 world
and network). Live state: `scenario.json` (19 rooms written by `_scratch/build_graph.py`).

## State at handoff

- Steps 1, 2, 3a, 3b DONE. Geography LOCKED: master `_scratch/world_skeleton/swarm_master_v2/menu_midday_clear.png`
  + `swarm_derive_v3/{arrival_sea,from_sea_s,east_high}.png` + `swarm_derive_v1/down_flight_n.png`. Known
  accepted flaw: one view shows the arch in the reservoir; fix per room only if a room inherits it.
- Landing, finish screens and cover prompt LOCKED (`validate_story.py --accept` done).
- Step 4a DONE apart from the drawdown hotspot: `build_graph.py` writes and proves the graph (`--check`).
  World model `_scratch/world_skeleton/world.py --checks`; groups `groups.py` → `groups.json` (seven
  clusters; previews in `out/groups/`). Graph drawing `_scratch/graph/diamonds_graph.png` (from scenario.json).
  Independent audit: `temp/audits/diamonds_graph_audit.md`; all its bugs fixed (lower-gate physics, dam
  retaining wall, one-way fill valves, living stones on lock 5's own bank, notes typo, one-sentence ladder).
- Lucas approved (2026-10-20): gates are the LOWER lock gates; build the drawdown board; go on to 4b.

## A. The drawdown board as an engine instrument — DONE 2026-10-20

Built as a generic `type: "instrument"` with `kind: "drawdown"` (engine: `shared/AGENTS.md` → *`instrument`*).
All acceptance checks met: office hotspot is the real type, rod settles at 79.60, tests green and each broken
once, `build_graph.py --check` passes, whitelists and docs updated. Steps kept below for the record.

Goal: the office's planned hotspot (`type: "instrument"`, a placeholder) becomes a real player hotspot
that opens the board in a modal, as settled in notes §5. Read the prototype README first.

1. Read `_scratch/drawdown_board/README.md`, `board.js`, `physics.js`, `test_physics.mjs`, `geometry.json`;
   `escape_rooms/shared/AGENTS.md` (engine conventions, how a new hotspot type was added; the `plaque`
   type built 2026-10-19 is the nearest precedent — search `openPlaque` in `shared/pano-player.js`).
2. Choose the type name (e.g. `drawdown`, or a generic `instrument` with `kind:"drawdown"`). Prefer a
   generic instrument contract if it costs nothing extra; say which in the report.
3. Port physics + rendering into `shared/` (a module like `shared/drawdown.js`, imported by
   `pano-player.js`), driven by hotspot data: still image path, geometry, season pegs (5 years),
   the readout. Never logged to the notebook; never gates anything; it is read by eye (escape input).
4. Update every type whitelist the `plaque` build touched (validate_scenes.py, validate_assets.py,
   scene_spec.py role, decoder/validate_keys.py, hotspots_edit.html, reproject_test.html), docs
   (`shared/AGENTS.md`, `authoring_v2/AGENTS.md`, hub `AGENTS.md` type lists) and the skills that name it.
5. Change `build_graph.py`'s office hotspot to the real type and re-run it (`--check` must pass).
6. Tests: port `test_physics.mjs` into the suite (settle = OLS; reads 79.60 on the escape set; rejects
   broken variants) plus a browser test that the modal opens and the rod settles. Run `npm test` and the
   touched Python tests; break the new tests once. `_scratch/drawdown_board/verify_escape.py` must stay green.
7. No vbump by hand (deploy.sh step 0 does it). Ledger: add "next deploy ships the drawdown instrument".

Acceptance: office hotspot opens the board, rod settles at 79.60 for the escape pegs, tests green and
broken once, `build_graph.py --check` passes, docs and whitelists updated.

## B. Step 4b scene specs (`escape_room_scenes` skill — load it and follow it)

1. One `sceneSpec` per room (19) written AGAINST the locked geography; each with its ROOM skeleton
   (`sceneSpec.scaffold = {"kind":"skeleton","layout":{"world":{...}}}`) cut from its group in
   `groups.json` (blocks + member `eye`/`heading`), via `authoring_v2/room_skeleton.py`'s `world` form.
   Check headings in `out/groups/*.png` first: lock rooms now stand at (bank*11, TOP, z0+10) facing up the flight.
2. Each room rides the most fitting accepted aerial(s) as `authoring.plateRefs` (avoid the view with the
   arch in the reservoir for sea rooms).
3. Honour notes §10 ART CONSTRAINTS: own feed pipe per lock; telltale costs crisp and code-engraved;
   lock-full state = barge risen (the one state variant per lock scene); sea lock board legible ONLY via
   the telescope (not from the wharf or boat); reservoir gauge 360 the only reservoir number; one journal
   page per level; no numbers anywhere else; fog an elevation gradient baked in; lower gates open behind the
   barge in the empty state, shut in the full state.
4. Plaques: depict each as a physical plaque beside its wonder, unlike clue props (rule in the skill).
5. Run the five-reviewer panel (sameness, physics, connectivity, schema, clue budget) as the skill says;
   then `authoring_v2/preflight.py regression/diamonds` must PASS and stamp.
6. Re-run `build_graph.py --check` and the graph drawing; tell Lucas to reload the harness (the console
   shows the rooms once specs exist).

Gotchas: `scenario.json` is written straight from scripts, never via the harness; `build_graph.py` rewrites
`rooms` wholesale, so put specs in through a separate regenerator that merges `authoring.sceneSpec` onto the
rooms (or extend `build_graph.py` to preserve `authoring`), never by hand edits a later regen would wipe.

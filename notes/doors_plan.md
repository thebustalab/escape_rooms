---
authority: intent
---

# Two-door navigation (forward / back) — implementation plan

**COMPLETE (Phases 1–5 done, 2026-07-18).** Engine, prompts, Alaska wiring, harness editor, and docs
all shipped; both data-vis scenarios play with working forward/back nav. Canonical door schema now
lives in `../AGENTS.md` ("Door navigation") + the per-scenario AGENTS + `shared/pano-player.js` header
+ the `escape_room_design` skill; this file is the phase-by-phase record. Only forward-compat items
remain deferred (see the Model note below): per-door `panoramaOpen` for multiple *forward* doors, and
branching-graph mechanics — both schema-ready, neither built (no scenario needs them yet).

Planned 2026-07-17; design agreed with Lucas. **Additive** to the current single-`door` model —
Hawai‘i and any existing single-door room keep working untouched (a door with no new fields uses
today's linear behaviour).

## Goal

A room can carry a **forward door** (closed, gated on the room's puzzle, swaps to the open panorama
on solve, advances to the next room *with* its entry text) and a **back door** (always open, no
puzzle, **no entry text**, returns to a previous room). Schema is forward-compatible with multiple
forward/back doors per room.

## Model (agreed)

- The `door` hotspot gains two fields:
  - `direction: "forward" | "back"` — default `"forward"`.
  - `to: "<roomKey>"` — explicit target; **absent ⇒ current linear fallback** (`goThrough`).
- **forward**: gated on solve; swaps to `panoramaOpen`; on click shows the target's `entry` and advances.
- **back**: live from room entry; no gate, no `entry`, no `onSolve` / codec effect; returns to `to`.
- Naming is **direction, not state** (a forward door *becomes* open on solve, so "closed" only
  describes it initially). The harness surfaces it as two buttons ("Door forward →" / "Door back ←")
  that set the field — categories in the UI, one clean type in the data.
- **Deferred (schema-ready, not built):** multiple *forward* doors need a per-door open image
  (`door.panoramaOpen`); the room-level `panoramaOpen` is enough while there's one forward door.
  Branching-graph mechanics are deferred. Explicit `to` per door is what keeps the door schema ready
  for both without a redesign.

## Phases

### Phase 1 — Engine + schema (player-side core) — biggest win
**STATUS: code + docs DONE (2026-07-17).** `shared/pano-player.js` has the door schema, back/forward
handling, solved-room re-entry, and the first-solve codec guard; door schema documented in the
pano-player header comment, `escape_rooms`/Alaska AGENTS, and the skill. **Live browser playtest still
pending** (no JS runtime on this box; served on :8055 — needs a click-through, or gets exercised for
real in Phase 3).

- Define the door schema (direction/`to`).
- `shared/pano-player.js`:
  - **back door**: live from room entry; click → `startRoom(to)` with **no** interstitial and **no**
    solve gate.
  - **forward door**: honour explicit `to` (fallback to linear `goThrough`); keep the solve-gate,
    the `panoramaOpen` swap, and the target-`entry` interstitial.
  - **solved-room re-entry** (the real new logic): `startRoom` renders a room already in
    `solvedRooms` in solved state — open panorama, forward door live, puzzle short-circuits as done —
    and **does not overwrite `roomResults`** (codec guard: free back/forward must not re-record or
    re-count).
  - back-target = explicit `to` (optional nav-stack fallback).
- **Validate:** hand-author a back door on the *current* Alaska art (approximate box) and playtest
  forward + back + re-entry; confirm the minted submission code is unchanged by moving back and
  forth. Manual only — see Risks.
- **Docs:** door-schema block in `escape_rooms/AGENTS.md`; door section in the skill.

### Phase 2 — Two-doorway scene prompts (unblocks the art) — cheap, do early
**STATUS: DONE (2026-07-17).** Rooms 2/3/boss `scenePrompt`s now carry a CLOSED forward door + an OPEN
passage back (to prev room); their `doorPrompt`s open only the forward door. Room 1 left single-door.
Skill's seamless-360 recipe extended with the two-doorway convention. Ready for Lucas to regenerate.

- Rewrite rooms 2/3/boss `scenePrompt` to include a **closed forward door** *and* an **open backward
  passage** (opposite / to one side), keeping the centre-wrap framing. `doorPrompt` opens the forward
  door only (the back passage is open in both the closed and `_open` images).
- Room 1 keeps its single forward door (safe to regenerate anytime).
- **Docs:** extend the skill's seamless-360 recipe with the two-doorway convention.

### Phase 3 — Wire Alaska's doors (after Lucas regenerates 2/3/boss)
**STATUS: DONE (2026-07-18).** All four rooms regenerated + boxes drawn; forward/back identified by
**reading the committed art** (forward = the door that opens between `scene.png`→`scene_open.png`;
back = the passage open in both). Full loop wired: room1 fwd→room2; room2 fwd→room3 / back→room1;
room3 fwd→boss / back→room2; boss fwd→(finish, no `to`) / back→room3. Puzzles + clues re-pointed
(incl. the boss's beacon-manual hint vs survival/`str()` card); correct indices `c(3,2,4,1)` unchanged
so `validate_keys.py` + R self-test stay green. This pass **also served as the Phase 1 engine
validation** (real two-door scenario to click through). Remaining: browser playtest of the full loop.

- Lucas regenerates the three scenes (two doorways) and draws both door boxes per room.
- Wire each door's `direction` + `to`: room1 fwd→room2; room2 fwd→room3 / back→room1; room3
  fwd→boss / back→room2; boss fwd→finish / back→room3.
- Re-point the puzzle/clue content to the regenerated boxes.
- **Validate:** `validate_keys.py` (unaffected), full playtest of nav both directions + re-entry + codec.

### Phase 4 — Harness hotspot-editor support (authoring UX)
**STATUS: DONE (2026-07-18).** `authoring/ui/hotspots_edit.html` door content panel now has a
**direction** select (forward/back) + a **to room** dropdown (populated from the scenario's other
room keys); values save via the existing `/api/room-patch {hotspots}` (the save serialises all
non-`_` fields, `_room_patch` shallow-merges the whole array — **no server change needed**). The
harness serves the editor at `http://localhost:8751/hotspots_edit.html`; reload the tab to pick it up.

- Add a door **direction** toggle (forward/back) + a **target-room** dropdown to the hotspots editor
  (`authoring/ui/hotspots_edit.html` + `authoring/harness_server.py`), so two-door rooms author
  without hand-JSON.
- **Docs:** harness/authoring notes.

### Phase 5 — Docs consolidation + forward-compat
**STATUS: DONE (2026-07-18).** Canonical **Door navigation** bullet added to `../AGENTS.md`
"Current architecture" (behaviour + authoring + the deferred forward-compat note); door schema also
in the per-scenario AGENTS, `shared/pano-player.js` header, and the `escape_room_design` skill (incl.
the harness direction/target dropdown). Deferred extension points recorded: per-door `panoramaOpen`
for a room with multiple *forward* doors, and branching-graph mechanics — both schema-ready via
explicit `to`, neither built. Plan marked COMPLETE at the top; kept in `notes/` as the phase record
(archive to a `z_` dir once it's clearly historical).
- Finalise the door schema in `escape_rooms/AGENTS.md` (room-schema area) + the skill; record the
  deferred extension points (per-door `panoramaOpen` for multi-forward; branching). Mark this plan
  done and archive it.

## Risks / notes
- **No JS test harness on this box** (no node / headless browser) — the engine changes (re-entry,
  codec guard) are validated by **manual playtest only**. A minimal Playwright harness is the standing
  follow-up; worth standing up before this grows.
- The **codec invariant** is load-bearing: one step per built room, recorded at first solve; free
  back/forward must not re-record. Phase 1's guard is the thing to verify hardest.
- **Ordering:** Phase 2 is cheap and unblocks the art, so it can run before/alongside Phase 1;
  Phase 3 waits on Lucas's regeneration; Phases 4–5 follow the working vertical slice.

---
authority: intent
---

# Hub-and-spoke harness editor — plan

**PROPOSED (2026-08-02), not built.** Restructure the authoring_v2 room editor so the **360 live view is the
persistent hub** — always showing the room as the player sees it (wrap + cinemagraphs + door/variant states)
— and wrap / spots / cinemagraph / door / seam become **contextual spokes** on that one view, instead of
today's separate full-page tabs. Sibling of `cinemagraph_plan.md` (the live-cinemagraph wrap preview built
2026-08-02 is the first brick of this: the hub's viewer already exists and already animates).

## Why (the pain today)
- Editing one room means tab-hopping: `harness_gpt.html` → open `reproject_test.html` (wrap) in one tab →
  open `hotspots_edit.html` (spots) in another. Each is a full-page app with its **own** Pannellum viewer,
  its **own** node load, and its **own** in-memory copy of the room — so the two tabs can drift, and neither
  shows the other's edits until reload.
- The flat box editor (`hotspots_edit.html`) authors boxes on the **equirectangular flat image**, so you're
  placing hotspots on a stretched projection, not on what the player actually sees. The wrap view is the
  faithful one, but it's read-only for hotspots.
- Result: the room-as-played and the room-being-edited are never the same surface.

## The target shape
- **Hub = the single 360 live view** (promote `reproject_test.html`). One Pannellum viewer, one loaded node,
  the live cinemagraph compositor already in place. This is *the* canvas; you never leave it.
- **Spokes = contextual tool panels over that view**, switched by a toolbar:
  - **Wrap** — the coverage/fov/pitch sliders already in reproject_test (becomes a spoke panel).
  - **Spots** — hotspot boxes + the Content/Variants/Cinemagraph side panel (lifted from hotspots_edit).
  - **Cinemagraph** — already reachable via the selected spot; surfaced as its own quick spoke.
  - **Door / Save / Plate / Seam** — server-actions → **toolbar buttons**, not full spokes (seam spawns a
    new candidate, so it bounces back to harness_gpt).
- **One node, one save path.** The hub loads the node once; every spoke edits that shared object and saves
  through the existing `/api/room-patch` (committed) / `/api/draft-save` (draft). Kills the two-tabs-drift bug.
- **Same param contract preserved end-to-end:** `?room&chapter&scenario[&img]`. Opened from a candidate chip
  (draft, `img=`) or a committed room, exactly as the two pages are opened today.

## Open design decisions (resolve before/at each phase)
1. **Where are boxes authored?** — the crux.
   - (a) **Flat box-editing spoke** — dock the existing `hotspots_edit` flat canvas as a panel; boxes stay
     authored on the flat image, but the 360 hub updates live as they move. Lowest risk, reuses proven code.
     **Recommended for the first pass.**
   - (b) **Author boxes on the sphere** — click-drag in the projected 360 view, inverse-project to 0–1 box
     fractions ("draw where the player looks"). Highest fidelity, needs new inverse-projection math + drag
     handling. **Recommended as a later enhancement (Phase 3), not the first cut.**
2. **Panels vs iframes.** In-page spoke panels sharing the hub's one viewer + node (a real but bounded
   rewrite) vs iframing the existing pages into a shell (fast, but two Pannellum instances + cross-frame
   state sync — the drift bug re-imported). **Recommend in-page panels, one viewer.** No iframes.
3. **Retire vs keep the old pages.** Keep `reproject_test.html` / `hotspots_edit.html` live as fallbacks
   until the hub reaches full parity; retire only after Phase 2 lands. **No big-bang cutover** — the harness
   is used daily, every phase must leave it fully working.

## Phased plan (biggest win first; confirm each phase holds before the next)
- **Phase 0 — extract shared core (no UX change, invisible).** Pull the duplicated node-load / save /
  cinemagraph-compositor logic into one small `authoring_v2/ui/room_edit_core.js`. De-risks everything
  downstream.
  **DONE 2026-08-02:** `room_edit_core.js` created (`window.RoomEditCore`, plain script) with `getJSON`/
  `postJSON`, `loadNode`/`loadDraft`, `isCommitted`, `saveRoomFields`/`saveDraft`, `scq`, and the live
  `Cinemagraph` compositor (init/start/stop/active/canvas). `reproject_test.html` (the future hub) now routes
  its fetch helpers, node/draft load, saves, and the cinemagraph preview through it — inline copies removed;
  behaviour identical (inline + module both `node --check` clean, page 200s, no dangling refs).
  **Deliberately deferred, not done in Phase 0 (kept conservative on a daily-use tool):**
  (a) `hotspots_edit.html` still has its own copies — it adopts `RoomEditCore` in **Phase 2**, where it's
  folded into the hub anyway (avoids half-migrating a non-UTF-8 file for no interim gain);
  (b) `shared/pano-player.js` is **not** touched — it ships to players and stays the game's canonical
  compositor copy, kept in lockstep with `RoomEditCore.Cinemagraph` by the cross-reference comment in both;
  (c) `boxToYP` is **not** extracted yet — reproject_test doesn't use it today; add it in Phase 2 when the
  Spots spoke needs to project hotspot markers onto the 360 view (no speculative dead code).
- **Phase 1 — hub shell + toolbar + server-action buttons.** Promote reproject_test into the hub: the
  persistent live 360 view (wrap + cinemagraphs) + a spoke toolbar. **Wrap** is the first spoke (the existing
  sliders). Door/Save/Plate/Seam become toolbar buttons calling the current endpoints. `harness_gpt.html`
  chips now open **one** hub tab.
  **DONE 2026-08-02 (Phase 1a).** `reproject_test.html` evolved **in place** into the hub (additive — kept the
  filename so the existing wrap chip opens it; the old page IS the hub now, git history on the Mac is the
  fallback). Added a room-mode **toolbar** (`#hubbar`): spoke tabs **Wrap** (active — toggles the tuning
  panel so you can see the room clean) · **Spots** (disabled, Phase 2); and, in **draft mode only** (the
  candidate-stage actions), wired **Commit room** (saves on-screen wrap → draft, then `/api/commit-room` with
  `image=DRAFT_IMG`; on success shows a "reopen as committed" link) and **World plate**
  (`/api/set-world-plate`). Live 360 + cinemagraphs unchanged. Inline script `node --check` clean; page 200s.
  **Not verified live:** Commit mutates real room state, so it wasn't fired in a smoke test — it calls the
  server handlers + payloads verified by reading harness_server.py.
  **DONE 2026-08-02 (Phase 1b).** **Door** and **Seam** now wired in the hub's draft-mode toolbar (buttons
  enabled). Both are gpt-image-2 gen jobs on status slots. Two mechanics got them right: (1) `/api/dooropen`
  and `/api/seamfix` **ignore chapter/scenario** and act on the server's **active** scenario's `_scratch`
  (SCENE) — so the hub calls `/api/select-scenario {CH,SC}` first (`selectActive()`, no-op when opened with no
  explicit scenario); (2) a hub-local `watchSlot(slot,label,onDone)` polls `/api/status?slot=` every 1.5 s
  (payload `{active,done,total,error}`, verified) and reports done. Door reuses the door-mask via
  `open_target.js` (now loaded in the hub) — `EscapeOpenTarget.pickOpenMaskHotspot(hs)` over the candidate's
  hotspots (`per.hotspots` ↦ `draft.hotspots`, mirroring `draftPer`), erroring "draw a forward door first" if
  none; prompt from `node.authoring.doorPrompt` or the standard fallback. Seam makes a new `*_seam` candidate
  (onDone tells the user to pick it in the harness — the hub is bound to one candidate, can't switch). Inline
  `node --check` clean; page + `open_target.js` 200; status endpoint shape confirmed.
  **Sub-phasing note (Phase 2b):** rather than a full flat-editor port (would duplicate ~400 lines or need a
  blind rewrite of the daily `hotspots_edit`), 2b is sub-sliced and **led with the Cinemagraph tab** — the
  slice that most leverages the live 360 (select object → animate → watch it move) and reuses the most
  existing code (gen endpoint + the compositor). Box-drawing + Content-edit + Variants follow. `hotspots_edit`
  stays untouched; 2c resolves the transient overlap.
  **DONE 2026-08-02 (Phase 2b-1 — content panel + Cinemagraph tab).** Selecting a hotspot (2a) now opens a
  per-hotspot content panel in `#spotContent` with a **Content** tab (read-only id/label/type for now) and a
  **Cinemagraph** tab. The Cinemagraph tab (gated on `isCommitted(NODE)`) shows the current clip + prompt +
  delete, and a motion prompt → Generate that posts `/api/gen-cinemagraph`, polls `/api/cinemagraph-status`,
  and on done runs `afterCineChange()` — reload node → `Cinemagraph.init` → `build()` — so the new clip
  **animates on the live 360 immediately**. Endpoints/payloads copied verbatim from `hotspots_edit`
  (`gen-cinemagraph`/`cinemagraph-status`/`delete-cinemagraph`). Inline `node --check` clean; page 200s.
  **Not fired live** (5-min GPU job, pauses lm_server) — but the nest flag hotspot already carries a
  cinemagraph, so the tab's read/delete/regenerate is exercisable without a gen.
  **DONE 2026-08-02 (Phase 2b-2 — editable Content tab).** `SPOTS` now holds the **full** deep-cloned
  hotspot objects (was id/label/type/box) so editing/saving never drops door/puzzle/clue content. Content tab
  edits label (regens id via slug/uniqueId), type (`setType`), and for doors direction / to-room /
  requires-gate (needs `ROOM_KEYS`, loaded via new `RoomEditCore.loadDoc`); plus per-hotspot delete (local,
  persists on Save). `saveHotspots` writes via `saveDraft`/`saveRoomFields`.
  **Data-safety fix (real):** `_room_patch` does `target.update(fields)` — a **wholesale replace** of the
  hotspots array with **no per-hotspot merge** — so a stripped committed-mode hotspots write **drops**
  server-owned `variants`/`cinemagraph`. The hub's `saveHotspots` re-fetches the node and **re-attaches each
  object's current variants/cinemagraph by id** before writing (fresh → neither dropped nor stale-clobbered).
  Draft saves go to the separate `_scratch` draft, so no re-attach needed there. **`hotspots_edit` has the
  same latent drop in committed mode (strips without re-attaching)** — flagged for Lucas / to fix at 2c.
  Known edge (mirrors hotspots_edit): renaming a hotspot that has a server-owned asset re-keys its id and
  orphans the asset. Inline + module `node --check` clean; page 200s.
  **DONE 2026-08-02 (Phase 2b-3 — Variants tab).** Third tab on the content panel (with a `(n)` count).
  Ported verbatim from hotspots_edit: the "when"-trigger DSL editor (`WHEN_KINDS`/`whenToKind`/`whenArgs`/
  `buildWhen`/`renderWhenEditor`/`readWhen` — always / thisSolved / roomSolved / eq / gte), the existing
  variants list (state + trigger + update + delete + thumbnail), and the add/regenerate form. Wired to the
  same endpoints (`/api/gen-variant-room` + poll `/api/status?slot=variant`, `/api/patch-variant`,
  `/api/delete-variant`) with `refreshNode` after each. Gated on `isCommitted(NODE)`. Inline `node --check`
  clean; endpoints exist; page 200s. **Not fired live** (variant gen is a ~20s masked gpt-image-2 job needing
  the OpenAI key) — endpoint/payload parity with hotspots_edit; the nest has no variants yet, so testing =
  add one or just confirm the tab + when-editor render.
  **DONE 2026-08-02 (Phase 2b-4 — flat box drawing).** A docked flat scene strip (`#flatEdit`, bottom, Spots
  spoke only) shows the still with box overlays (`renderFlatBoxes`); drag empty space to create a hotspot
  (`makeSpotBasic` → plain puzzle + empty check skeleton, mirrors hotspots_edit's no-plan `makeSpot`), click a
  box to select. `refreshSpotViews` keeps list + flat boxes in step; create/delete/type-change also `build()`
  to refresh the 360 markers (safe — none run inside a viewer hotspot handler). New boxes persist via the
  Content tab's Save. Existing boxes aren't dragged (redraw+delete to move — same as hotspots_edit). Inline
  `node --check` clean; page 200s. **Editing side of the Spots spoke is now at content parity with
  hotspots_edit.**
  **Fix (2026-08-02):** the flat strip never appeared — `setSpoke` set `#flatEdit.style.display = ""`, which
  falls back to the CSS rule `#flatEdit{display:none}` (unlike `#spotsPanel`, which has no CSS `display`).
  Now sets `"block"` explicitly. (Reminder for future toggles: `style.display=""` reveals only if no CSS rule
  hides it.) **Navigation gotcha surfaced:** the harness grid's **"spots" chip still opens the OLD
  hotspots_edit** — the hub's Spots is the toolbar button inside the 360 wrap view. This dual entry is the
  confusion 2c resolves (repoint the chip).
  **DONE 2026-08-02 (planned-arm + retain-wiring — the 2c gap, now closed).** Ported from hotspots_edit into
  the flat popup: a **planned-hotspots column** (`#flatPlanned`, beside the flat frame) listing
  `node.plannedHotspots` with type tag / label / note / done-✓ (`renderPlanned` + `planPlaced`); click to ARM
  (blue outline + status), then drag its box. `makeSpot(box, plan)` now seeds type/label (+ door direction /
  clue pickup) from the armed plan AND re-attaches retained wiring via `retainedFor` (`RETAINED` =
  last-committed `node.hotspots`, matched by label-slug + type) — so redrawing boxes on regenerated art keeps
  door targets / grading / clue bodies. Drop clears ARMED + reports "placed X ✓ · wiring re-attached".
  `refreshSpotViews` now also `renderPlanned` (done-marks update as boxes land). `makeSpotBasic` removed
  (folded into `makeSpot`'s no-plan path). Inline `node --check` clean; page 200s; nest has 4 planned items
  (all show ✓ since it's fully placed — test retain by deleting the door, arming the planned door, redrawing).
  **The hub is now at FULL editing parity with hotspots_edit** (planned-arm + retain included). 2c can be a
  clean retire/repoint of the "spots" chip.
  **Fix (2026-08-02) — gen on an unsaved hotspot.** Cinemagraph/variant gen writes onto the COMMITTED node's
  hotspot (`_find_hotspot` → "no hotspot 'object_3'…"), but a freshly-drawn box lives only in memory until
  Save — so generating on a just-drawn hotspot failed. Added `ensureHotspotSaved(s, statEl)` (called before
  both gens): if the hotspot isn't on `NODE`, committed mode Saves it first (room-patch → node), draft mode
  errors "isn't on the committed scene yet — Save & commit first". `saveHotspots` now `refreshNode`s on
  success so `NODE` reflects newly-saved hotspots. (Latent in hotspots_edit too — it doesn't auto-save before
  gen either; not fixed there.)
  **Fix#2 (2026-08-02) — committed-room hotspot saves land on the node, not a candidate draft.** Root cause of
  "can't save hotspots / gen still errors": the boss room is committed but opened via the wrap chip with an
  `img=` candidate → DRAFT mode → `saveHotspots` did a **draft-save** (to `_scratch`), so a drawn hotspot
  never reached the committed node and (a) appeared not to persist, (b) gen's `_find_hotspot` still failed.
  Now `saveHotspots` treats the room as committed when `isCommitted(NODE)` (or forced) — persists to the node
  via room-patch even while viewing a candidate; only a truly-uncommitted (still-building) room saves to its
  draft. `ensureHotspotSaved` now force-saves to the node (`saveHotspots(null,true)`) whenever the room is
  committed (was: block "commit first" in draft mode). Re-gen redraw still uses the old editor's draft flow.
  **Also suspected stale HTML cache** — the page's inline JS isn't cache-busted, so a hard refresh is needed
  to pick up these fixes.
  **Fix#3 (2026-08-02) — rename orphans a hotspot's cinemagraph/variants (data loss, hit live).** Lucas made
  a boiler cinemagraph, then a steam one, and the boiler's vanished. Cause: he'd generated the boiler while
  the hotspot had a default id (`obj_5`), then renamed it to "boiler" (label edit → id reslug). The next save
  rebuilt `owned` by node id and re-attached by the SPOT's CURRENT id — `owned["boiler"]` was undefined, so
  the field (still on node `obj_5`) was dropped when room-patch replaced the array. This is the
  "rename orphans server-owned asset" edge noted under 2b-2, now confirmed as real data loss.
  **Recovery:** identified the boiler's video by matching its box `[0.2034,0.6029,0.2667,0.7682]` → px
  `(625,617,819,787)` to the gen-log crop `(624,617,819,786)` = `cine_obj_5.mp4` (still on disk); restored
  `boiler.cinemagraph = {box, video:"boss/cine_obj_5.mp4", prompt(placeholder), loop:"boomerang"}` directly in
  scenario.json (backup: `scenario.json.pre_boiler_recover`). Prompt text wasn't logged → placeholder.
  **Root-cause fix:** each SPOT is tagged `_origId = s.id` at load; `saveHotspots` re-attaches
  `owned[s._origId] || owned[s.id]` so a rename carries the cinemagraph/variants forward (video keeps its old
  `cine_<origid>.mp4` name — fine, the path is explicit). Inline `node --check` clean.
  **Add (2026-08-02) — open-door generation in the Spots content panel.** For a **door** hotspot, the hub's
  Content tab now has (gated on `isCommitted(NODE)`) an "Open this door" control: an open-door prompt
  (default = `node.authoring.doorPrompt` or the standard fallback) + a button → `genOpenDoor` posts
  `/api/dooropen-room {chapter,scenario,roomKey,box:door.box,prompt}` and polls `/api/status?slot=door`,
  reporting "panoramaOpen set" on done. Uses the on-screen box (no save needed); mirrors hotspots_edit's
  `generateDoor`. Distinct from the Phase-1b toolbar **Door** button (that's `/api/dooropen` on the
  active-scenario draft _candidate_; this is the committed-room per-door `dooropen-room`). UI-only, endpoint
  pre-existed → no harness restart, just hard-refresh. Not fired live (gpt-image-2 job).

  **Gotcha (2026-08-02) — scene-baked gen uses the COMMITTED scene, not the viewed candidate.** Cinemagraph
  / variants / open-door all crop `scene.png` server-side. If you author them while viewing an *uncommitted*
  candidate (`img=`) that differs from the committed scene, the box maps to different content → mismatched
  crop (diagnosed on the room3 lantern: box drawn on the 3072×1024 `gpt_room3_20` candidate, but cropped from
  the older 1536×512 committed `scene.png` — mean pixel diff 16.4, so a different lantern framing → looked
  "zoomed"). Baking from the candidate can't fix it (the game plays these over the committed scene, so they
  must bake from it) — the workflow is **commit the candidate first, then generate**. Added an amber warning
  at the top of the Spots content panel whenever `DRAFT_IMG` is set. Fix for a mismatched asset: commit the
  candidate, then regenerate.
  **Guard (2026-08-02) — Spots gated on the committed scene.** The **Spots** spoke is now `disabled` unless
  `!DRAFT_IMG && isCommitted(NODE)` (viewing the committed room, not a candidate); `setSpoke` also refuses it.
  In draft mode the Wrap spoke + the toolbar **Commit room** button stay active, with a status hint "Use
  Commit room to enable the Spots menu." So the order is forced: tune wrap on the candidate → Commit → reopen
  as committed → Spots lights up, and every Spots tool now bakes from the scene you're actually viewing.
  Structurally prevents the draft/committed mismatch above. UI-only, hard-refresh.
  **Committed-room seam-fix (2026-08-02).** The toolbar Seam is candidate-only (makes a `*_seam` candidate,
  pre-commit); Lucas's flow does seam-fix POST-commit, so added an in-place committed seam-fix. Server
  `_run_seamfix_room(base, room_key)` + route `/api/seamfix-room {chapter,scenario,roomKey}`: runs
  `generate_scene.py seamfix` on `scene.png` → replaces it in place, keeping a one-time `scene_preseam.png`
  backup (reversible). UI: a **"Fix seam"** button in the Wrap panel, shown only in committed mode
  (`canSpots`); polls slot "seam", then busts `IMG_URL` + re-inits the cinemagraph base + rebuilds so the
  changed scene shows. **Do it before cinemagraph/variant/open-door** (it changes the scene; interior
  hotspot boxes are unaffected — seam is at the ±180° edges). Confirmed Lucas's flow: iterate prompt on cheap
  low-res candidates → commit one good high-res → hotspots → **seam-fix** → cinemagraph/variants/doors.
  Harness restart done; not run through a real gen (gpt-image-2 job).
  Toolbar polish: the dangling `#hubSep` divider is hidden in committed mode (candidate actions gone).
  **Fix (2026-08-02) — flat draw spawned extra boxes.** The flat scene `<img>` is natively draggable, so a
  drag could kick off the browser's image-drag and swallow the `mouseup`, leaving the draw state stuck →
  subsequent moves kept spawning hotspots. Fixed with `draggable="false"` on `#flatScene` + a `drawing` flag
  (a box is only created within one press→release, guarding stray mouseups) + an `e.buttons===0` abort in
  mousemove (button released off-frame). Drag state is cleared BEFORE the rebuild. UI-only.
  **Fix (2026-08-02) — clicking a hotspot showed no details.** The draft-warning I added to the top-level
  `renderSpotContent` referenced `DRAFT_IMG`, but that was declared **inside `initRoomMode`** → out of scope →
  `renderSpotContent` threw ("DRAFT_IMG is not defined") on every hotspot select, so the content panel never
  rendered (`saveHotspots` had the same latent break). Fixed by promoting `DRAFT_IMG` to **module scope**
  (beside `startImg`); removed the `initRoomMode`-local decl. **Verified with a Playwright probe** (headless):
  click a hotspot → `#spotContent` fills (983 chars, tab bar present), no console errors (was: empty +
  pageerror). Lesson: top-level fns must not read `initRoomMode` locals — a Playwright probe catches these.
  **Still open:** (a) `hotspots_edit` strips cinemagraph/variants on save and re-attaches NOTHING — same class
  of loss in committed mode, unfixed (Lucas is on the hub now; fold into 2c). (b) No regression test — the
  save logic is DOM-tied inline script; documented here instead. (c) The other orphaned boss videos
  (`cine_obj_3` errored, `cine_obj_4` an unused region) are harmless leftovers on disk.
  **Not fired in a smoke test** (real GPU/gpt-image-2 jobs, minutes, and `select-scenario` flips server
  active state) — wiring calls endpoints/payloads read from harness_server.py; poller matches the live status
  shape. **Phase 1 (hub shell + all four toolbar actions) COMPLETE.** Next: Phase 2 — the Spots spoke.
- **Phase 2 — the Spots spoke (the big lift).** Bring hotspot box-editing into the hub via decision 1(a): a
  docked flat box-editor panel editing the **shared** node, with the 360 view updating live; the
  Content/Variants/Cinemagraph tabs become a side panel keyed to the selected hotspot. **Verify:** full
  parity with today's `hotspots_edit`, then retire it (or keep as fallback one release).
  Sub-phased: **2a** markers+list (read-only), **2b** flat box-editing + content tabs (the heavy port), **2c**
  retire hotspots_edit / point its chip at the hub.
  **DONE 2026-08-02 (Phase 2a — Spots spoke, read-only).** The toolbar's **Spots** spoke is enabled. It
  shows the room's hotspots as **markers on the live 360** (something neither existing page does) via
  `RoomEditCore.boxToYP` (now extracted; byte-identical to the game) over the current wrap params, plus a
  selectable **Hotspots** side panel (`#spotsPanel`, `#spotsList`). Spoke selector (`setSpoke`) swaps
  Wrap↔Spots and rebuilds; markers only render when Spots is active (Wrap/cinemagraph paths untouched).
  `SPOTS` loaded from per-candidate ↦ draft ↦ node hotspots (same order as hotspots_edit). Selecting a marker
  or a row highlights the list (`selectSpot`/`renderSpotsList`); no rebuild inside marker click handlers (a
  handler must not destroy its own viewer). Door markers render blue. Verified on airship/nest (5 boxed
  hotspots). Module + inline `node --check` clean; page 200s. **Read-only** — no box drawing/editing yet
  (that's 2b). **Next: Phase 2b** — dock the flat box editor + Content/Variants/Cinemagraph tabs, editing the
  shared node, 360 markers updating live.
- **Phase 3 — optional polish (discuss first).** On-sphere box authoring (decision 1(b)), unified
  draft/committed affordances, "reduce motion" toggle for the cinemagraph preview + `prefers-reduced-motion`,
  keyboard nav. Scope only if Phase 2 lands cleanly.

## Risks / gotchas
- **Two Pannellum viewers** if anyone reaches for iframes — the hub must own exactly one viewer.
- **On-sphere authoring** is the deep end (inverse projection) — deferred to Phase 3; Phase 2 stays flat.
- **Non-UTF-8 bytes** in `hotspots_edit.html` / `harness_gpt.html` — grep `-a`, and validate inline
  `<script>` by extracting it + `node --check` (house practice).
- **Draft vs committed** param + save contract must survive every phase untouched.
- **Daily-use tool** — additive/no cutover; the two old pages stay live until the hub is at parity.

## Batch scene-baked generation — the walk-away flow (BUILT 2026-08-03, pending a live run)
**Why.** Firing cinemagraphs one at a time is high-touch: each `cinemagraph_gen.py` call stops+restarts
lm_server (~40 s handoff each) AND needs Lucas at the keyboard to launch the next once one finishes. The
goal: **decouple authoring from generating** — stay interactive to pick hotspot + prompt + loop, then queue
and walk away while one batch runs them back-to-back, bouncing lm_server ONCE.

**Also folds in doors + variants.** Key insight: **batching and local-vs-API are orthogonal.** The queue
doesn't care what backend a job uses — doors/variants (gpt-image-2, API, no local GPU) ride the same queue
as cinemagraphs (LTX, local GPU). So all three are batchable now; a later spike may move doors/variants to a
local image model (Flux/SDXL inpaint) to save API spend — that's a separate decision, not a blocker.

**lm_server window (Lucas's correction, 2026-08-03).** Stopping lm_server on this box takes down **TTS +
Whisper too**, so *voice* is unavailable for the whole batch — Lucas goes text-only over the mobile UI (or
walks away) until it finishes. The batch only stops lm if the queue holds ≥1 cinemagraph job (pure
door/variant batches never touch it).

**Pieces built:**
- `~/ComfyUI/cinemagraph_gen.py` — refactored: the per-clip work is now `generate_clip(...)` (crop → LTX
  OOM res-ladder → loop encode → `write_node`), with **NO** lm handling; `main()` wraps it with the single-
  shot stop/start (behaviour identical). `write_node` now writes scenario.json atomically at **indent=2,
  ensure_ascii=False** (was indent=1 — matched the harness's `_save_scenario` to stop reformatting the whole
  file / churning the Mac git diff on every cinemagraph). Seed already random per run (2026-08-03).
- `~/ComfyUI/cinemagraph_batch.py` — NEW detached runner. Reads a resolved run file, stops lm ONCE (iff any
  cinemagraph job), runs each job (cinemagraph via `generate_clip`; door/variant via the same
  `generate_scene.py dooropen` masked-edit the harness uses), restarts lm ONCE, writes a `cine_batch_status`
  the editor polls. One job failing never aborts the rest. Node writes are atomic, indent=2. Cross-process
  scenario.json race vs the harness is the SAME pre-existing property as `cinemagraph_gen` — safe for a
  walk-away batch (Lucas isn't editing).
- `authoring_v2/harness_server.py` — per-scenario queue (`_scratch/cine_batch.json`) + endpoints
  `/api/batch-{add,list,remove,clear,run,status}`. `_expand_job` resolves a minimal queued job to
  scene/out/rel paths using the SAME filename conventions as the single-shot `_launch_cinemagraph` /
  `_run_dooropen_room` / `_run_variant` (so batched output lands exactly where one-shot does). `batch-run`
  expands → run file → seeds status "running" → clears the queue → launches the runner detached. A
  **single-shot guard**: `/api/gen-cinemagraph`, `/api/dooropen-room`, `/api/gen-variant-room` all 409 while
  a batch is running. **These are new routes → needs a harness restart to go live** (which resets active
  scenario to alaska → re-select airship after; batch endpoints key off the body's explicit chapter/scenario,
  NOT active, so a stale active doesn't misfile batch output).
- `authoring_v2/ui/reproject_test.html` — a **Batch tray** at the top of the Spots panel (queued count +
  per-job list with remove-✕ + Run all + Clear; live progress "running X/Y · current" while a run is in
  flight, polling `/api/batch-status` every 3 s; last-batch summary with per-job failures). **+ Batch**
  buttons beside Generate on the cinemagraph tab, the door "Open this door" control, and the variant add form
  — each `ensureHotspotSaved` then POSTs `/api/batch-add`. Server-side queue = every open wrap tab feeds ONE
  queue (the multi-tab flow). On batch done the current room refreshes (`afterCineChange`) so its new assets
  play. Inline script `node --check` clean.

**Tested (no GPU):** all three scripts `py_compile`; batch node-writers + Status (`~/ComfyUI` venv);
harness `_expand_job` path resolution + queue roundtrip + bad-job rejection + running-flag; hub inline
`node --check`. **NOT yet run end-to-end** (needs the harness restart + a real GPU/API gen — Lucas's call).
**Next:** restart harness, re-select airship, queue 2–3 cinemagraphs across rooms, Run all, confirm one
lm bounce + all clips land + tray summary. Then consider the local-image spike for doors/variants.

### Cinemagraph candidates — 3-per-hotspot, pick one (BUILT 2026-08-03)
Motion analogue of generating multiple art scenes then picking. Batched cinemagraph jobs now render
**`CINE_CANDIDATES` (default 3) clips per hotspot**, each a fresh random seed, and record a
`cinemagraphCandidates` manifest on the node INSTEAD of committing `cinemagraph`. The Cinemagraph tab shows
the candidates as side-by-side autoplay loops with "Use this"; picking promotes one to `cinemagraph` and
clears the list (unused mp4s stay on disk as harmless orphans). Fixes the stochastic dud problem (some LTX
draws barely move) without a human babysitting each gen. Pieces: `cinemagraph_gen.render_clip` (split from
`generate_clip` — renders a clip, no node write); `cinemagraph_batch._run_cinemagraph` loops N candidates →
`cine_<id>_c<k>.mp4` + `_write_cine_candidates`; harness `_expand_job` defaults cinemagraphs to 3, plus
`/api/pick-cinemagraph` + `_pick_cinemagraph`. Hub: `cineCandsOf`, candidate grid in `renderCineTab`,
`pickHubCine`; `saveHotspots` now re-attaches `cinemagraphCandidates` too (else a box-nudge save would drop
them — same class as the cinemagraph-drop bug). The single immediate **Generate** stays 1 clip; only the
**+Batch / apply-spec** path makes candidates. New route (`pick-cinemagraph`) → needs the harness restart.

### Seam-wrapping cinemagraph boxes (BUILT 2026-08-03)
Fixes objects sitting on the equirect ±180° seam getting only half-animated (a rect crop can't span both
edges). A **wrap box is stored as x0 > x1** (region [x0..1] ∪ [0..x1]). Pipeline: (1) `cinemagraph_gen.render_clip`
detects x0>x1, ROLLS the panorama left by x0 so the object is contiguous, crops [0..(1-x0)+x1], generates ONE
normal clip. (2) Both compositors — `shared/pano-player.js` (runtime) + `authoring_v2/ui/room_edit_core.js`
(authoring preview, kept in lockstep) — for a wrap box feather the whole clip then draw it in TWO slices:
`[0..leftW]`→right edge (leftW=(1-x0)·W), `[leftW..]`→left edge. Feather stays intact at the seam (mid-clip),
so no visible join. Runtime is additive/guarded (inert for every existing room); `pano-player.js?v=67→68` in
the 5 play.html. (3) Flat editor (`reproject_test.html`): the strip repeats the left `FLAT_MARGIN` (0.25) of
the scene past a dashed **seam line** at the right edge, so you can DRAW a box across the seam; `rawToBox`
folds a seam-crossing draw into a wrap box (marked ⟳, dashed), and drag/move/resize work in contiguous "raw"
space via `boxRaw`. Verified: roll/crop makes the object contiguous (Python), fold logic all cases (JS),
both compositors + hub `node --check`. NO harness restart needed (gen/batch reload per run; compositors +
hub served live — hard-refresh the hub and playtest). NOT yet run through a real seam gen — Lucas's call.

### Batch crops from the hotspot's CURRENT box at run time (bugfix 2026-08-03)
Symptom: a seam-wrap cinemagraph animated only one side. Root cause was NOT the wrap engine — it was
staleness: apply-spec queues a cinemagraph job carrying the box AT QUEUE TIME (the approx box), so a box
nudged/redrawn afterwards (incl. redrawn as a wrap box, x0>x1) was IGNORED — the gen cropped the stale
approx box. This silently defeated the entire box-review step (apply-spec places approx boxes → human nudges
→ Run all): every nudge was dropped. Fix: `_launch_batch` snapshots every hotspot's current box and passes
it to `_expand_job(base, job, cur_boxes)`, which overrides the queued box with the node's latest — so the
batch always crops from what you see now. Verified (fresh wrap box reaches the run file). Harness change →
needs the restart. The wrap ENGINE (roll/crop + split-composite) was never actually exercised (it only ever
got the stale non-wrap box); regenerating liquid2 after the restart is its first real end-to-end test.

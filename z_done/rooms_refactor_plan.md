---
authority: intent
---

# Rooms umbrella + room-agnostic authoring — phased plan

Status: plan (2026-07-16). Turns the escape-room authoring harness into a
**room-agnostic, forward-compatible** pipeline for building any chapter's rooms,
and reorganises the tree around a `rooms/` umbrella. Pilot: the **Data
Visualization** chapter (Hawai‘i + Alaska scenarios). Supersedes the ad-hoc
Hawai‘i-only build; the current `AGENTS.md` "Goal" section still stands (convert
every `teaching/CHEM5725/exercises.csv` exercise into rooms, 1:1 with the book).

## The workflow this enables (the whole point)

For each book chapter, end to end:

1. **Design, together.** Read the chapter's `exercises.csv` rows + the book
   chapter. Decide what students must practise; map skills onto **practice rooms**
   (each scaffolds one move) plus a **boss room** = the actual assessed exercise
   (usually its figure-creation deliverable). Adapt — not invent — the storyline:
   `exercises.csv` already carries stories, but they have **people**; we convert
   them into empty, explorable spaces (Myst/Riven) where narrative is told through
   what's left behind (notes, instruments, aftermath). **No people, ever. No text
   in art.**
2. **Configure the harness.** Claude writes the scenario spec (`scenario.json`);
   the harness reads its column defaults (tags, scene prompts, door-open modifiers)
   from that spec instead of hardcoded values.
3. **Generate art (Lucas).** Run the harness: generate candidates, tune wraps,
   place hotspots, make open-door variants, "Send to room".
4. **Wire it up (Claude).** Build the playable scenario from the committed rooms +
   the spec: WebR puzzles with console-checks, the room graph, the submission codec.
5. **Test (Lucas).**
6. **Deploy.** Push to Pages; add an **"Exercises"** section to the matching book
   chapter with a clickable **cover image** linking to the scenario.

## Terminology (settle this first — it's load-bearing)

- **chapter** — a technique set aligned 1:1 with a book chapter (`data_vis`,
  `data_wrangling`, `pca`, …). A folder under `rooms/`. Groups scenarios.
- **scenario** — one themed playthrough of a chapter (`alaska`, `hawaii_aquifers`).
  The **unit that owns** `scenario.json`, `play.html`, `notes.md`, `AGENTS.md`, and
  its `roomN/` + `boss/` dirs. Reuses the established "scenario" concept (the flat
  engine's `window.SCENARIO`, ids 1–15).
- **room** — one pseudo-360 space with hotspots; a practice room or the boss.
- **spec** — `scenario.json`, **pure JSON** (single source of truth read by the
  harness, the player, and Claude). Runtime global renamed **`window.CHAPTER` →
  `window.SCENARIO`** for consistency (small change; `play.html` fetches the JSON
  instead of loading a JS file). One scenario = one `window.SCENARIO`.

## Target structure

```
escape_rooms/
  authoring/                 # chapter-agnostic tooling ONLY
    harness_server.py, generate_scene.py, PROMPTING.md, test_harness_server.py
    ui/                      # harness pages (moved out of alaska_pano/)
      harness_gpt.html, view360.html, reproject_test.html
  shared/                    # runtime player: pano-player.js/.css, webr-console.js, codec.js
  rooms/                     # umbrella
    data_vis/                # chapter (book-aligned technique set)
      alaska/                # scenario  (from the alaska_pano trial content)
        scenario.json, play.html, notes.md, AGENTS.md
        room1/ room2/ room3/ boss/    # committed rooms (scene + _open + wrap + hotspots)
        _scratch/            # harness candidate pool for this scenario (gpt_<tag>_NNN)
      hawaii_aquifers/       # scenario  (from data_vis/hawaii_aquifers/)
        scenario.json, play.html, notes.md, AGENTS.md
        room1/ … boss/
        _scratch/
    data_wrangling/, pca/, …   # future chapters
  decoder/
  z_done/                    # (already holds the archived flat engine)
```

## The spec schema — general graph, linear evaluator only (forward-compatible)

`scenario.json` is authored in the **full graph-plus-conditions** shape from day
one; the player initially implements only the **linear evaluator**. Non-linear
topologies (interconnected rooms, world-state gates like a draining fountain that
reveals the boss key) are then an **authoring + evaluator** change, never a
schema migration or a re-authoring of existing scenarios.

```jsonc
{
  "chapter": "data_vis",
  "scenario": "hawaii_aquifers",
  "id": 3,
  "title": "…",
  "story": "…environmental, unpeopled…",
  "packages": ["dplyr","ggplot2"],
  "datasets": [{ "name": "hawaii_aquifers", "url": "https://…csv" }],
  "setup": "…shared WebR setup R…",
  "state": { "rooms_solved": 0 },              // world-state vars (counters/flags)
  "rooms": [
    {
      "key": "room1",
      "title": "…", "technique": "…", "puzzleType": 1,
      "panorama": "room1/scene.png",
      "panoramaOpen": "room1/scene_open.png",
      "wrap": { "haov":360,"vaov":135,"hfov":70,"vOffset":0,"pitch":0 },
      "unlockedWhen": true,                     // condition (linear: first room)
      "onSolve": [{ "set": "room1_solved" }, { "inc": "rooms_solved" }],
      "hotspots": [
        { "id":"laptop", "type":"puzzle", "label":"laptop", "box":[…],
          "puzzle": {
            "starterCode": "…",
            "check": { "requires":["answer"], "expr":"…R logical…", "hint":"…" },
            "question": { "prompt":"…", "options":[…], "correct":0,   // MCQ fallback
                          "maxAttempts":3, "feedback":{…} } } }
      ]
    }
    // room2: "unlockedWhen": { "solved": "room1" }, room3: { "solved": "room2" } …
  ],
  "boss": {
    "key":"boss", "title":"…",
    "panorama":"boss/scene.png", "panoramaOpen":"boss/scene_open.png", "wrap":{…},
    "unlockedWhen": { "allSolved": ["room1","room2","room3"] },
    "deliverable": { "type":"figure", "exercise":"CHEM5725 DataVis Q3", "submitCodec": true }
  }
}
```

**Linear evaluator** understands only: `true`, `{ "solved": "<roomKey>" }`,
`{ "allSolved": [...] }`. **Forward-compat, not built now:** `{ "gte":
["rooms_solved", 3] }` and friends for world-state gates; `onSolve` effects
(`set`/`inc`) are already recorded so a counter-based gate works later with no
re-authoring. Doors go live when a target room's `unlockedWhen` passes.

## Phases (each verifiable before the next)

### Phase 1 — Reorg (no behaviour change) — ✅ DONE 2026-07-16
Outcome: `data_vis/` → `rooms/data_vis/`; harness pages → `authoring/ui/`; Alaska
playable content → `rooms/data_vis/alaska/` with scene scratch at `_scratch/`. Harness
rewired (`ROOT`=`authoring/ui/`, `SCENE`=`rooms/data_vis/alaska/_scratch`, new `/scene/`
route maps `scene/*` in) — restarted, all endpoints verified (scenes list, image serve,
wrap.json, traversal-guard 404, both viewer pages). `play.html` asset chain verified 200 at
new paths. Harness tests 8/8. **Residual:** `alaska_pano/` still holds `z_archive/` +
`z_done/` — the history-move guard blocks `mv` from a `z_*` source, so those two pre-existing
history dirs stayed put; the folder is otherwise empty. Lucas can relocate/remove them from a
terminal if desired. Deferred: the wider `AGENTS.md` path-reference rewrite rides Phase 2 (a
migration banner + the operational paths were fixed now).

Original scope:
- Create `rooms/`. Move `data_vis/` → `rooms/data_vis/` (keeps
  `hawaii_aquifers/` scenario intact).
- Promote the Alaska trial to a scenario: `alaska_pano/` content → its parts:
  harness pages → `authoring/ui/`; playable demo (`chapter_alaska.js`, `play.html`)
  → `rooms/data_vis/alaska/`; scene scratch (`gpt_gen_*`, `gpt_room*`, `wrap.json`,
  `hotspots.json`) → `rooms/data_vis/alaska/_scratch/`.
- Rewire harness paths (serve dir, scratch dir, "Send to room" target) — see Phase 3.
- Verify: harness boots under `harness_ui` tmux, serves the UI, `play.html` still runs.
- **Caveats:** (1) `alaska_pano/scene/z_archive/` is history-tier — the Bash-write
  hook blocks `mv` **from** a `z_*` source, so move the *parent* scene dir (source is
  not `z_*`) or leave `z_archive` in place and relocate around it; don't `mv` the
  `z_archive` dir directly. (2) Mac-only git repo, Syncthing-synced — no commits here.

### Phase 2 — Spec schema + convert existing content — ✅ DONE 2026-07-16
- `scenario.json` authored for **alaska** (faithful conversion of `chapter_alaska.js`,
  which is archived to `alaska/z_done/`) and **hawaii_aquifers** (room1 live off the
  committed room dir + real puzzle content; rooms 2–3 + boss are `built:false` design
  stubs in a `planned` block / `boss`; boss region key still OPEN).
- `pano-player.js` now **fetches `scenario.json`** (relative to `play.html`) instead of
  reading the `window.CHAPTER` global; concept renamed **chapter → scenario**
  (`window.SCENARIO` shape). Both `play.html` shells are bare (no data `<script>`).
- Graph fields (`unlockedWhen`/`onSolve`/`state`/`boss`) present as **data only** — linear
  play unchanged. Verified: both JSONs parse; both scenarios' full asset chains serve 200
  (play.html, scenario.json, shared modules, room images). WebR not headless-testable here.
- **Carry-over into later phases:** hawaii room1's door-hotspot box is provisional
  (`_boxProvisional`) — tune in the harness; alaska room1 still references `_scratch/…`
  (not yet committed via "Send to room"). Scenario `id`s (alaska 6, hawaii 1) are
  provisional until the codec is wired (Phase 5); reconcile with `decoder/decode_codes.R`.

Original scope:
- Write `scenario.json` for `hawaii_aquifers` (room1 is already committed) and for
  `alaska`, in the general shape above.
- Point `play.html` at `scenario.json` (fetch+parse); rename `window.CHAPTER` →
  `window.SCENARIO` in `pano-player.js` + the shells.

### Phase 3 — Harness becomes spec-aware — ✅ DONE 2026-07-16
- **Active-scenario model** in `harness_server.py`: `ACTIVE {chapter,scenario}` drives `SCENE`
  (`rooms/<ch>/<sc>/_scratch`, auto-created) and `COMMIT_BASE` (`rooms/<ch>/<sc>`). New endpoints
  `GET /api/scenarios` (scan `rooms/*/*/scenario.json`), `GET /api/scenario-config` (the active
  scenario's `authoring.series`), `POST /api/select-scenario`. `commit-room` accepts a bare
  **`roomKey`** → `rooms/<ch>/<sc>/<key>` (sanitised, traversal-confined); `roomDir` still works as
  an explicit override. All confined to `rooms/`/`escape_rooms/`.
- **Authoring prompts moved into the spec:** each `scenario.json` gained a top-level
  `authoring.series` `[{key,tag,scenePrompt,doorPrompt}]` (hawaii = the 4 prompts formerly
  hardcoded in the page; alaska = room1). The harness no longer hardcodes `ROOM_PROMPTS`/`DOOR_PROMPTS`.
- **UI (`authoring/ui/harness_gpt.html`):** a scenario dropdown (from `/api/scenarios`); selecting
  one calls `/api/select-scenario` and rebuilds **one column per series entry** seeded with its
  prompts; "Send to room" sends `roomKey` (the selected base's column) → the active scenario's dir.
- Verified: `harness_server.py` syntax OK; **tests 12/12** (added scenario-listing, path-escape
  reject, select-scenario SCENE/COMMIT_BASE derivation, roomKey sanitising); live endpoints exercised
  (scenarios list, config, switch alaska↔hawaii giving 1 vs 4 series, `_scratch` auto-create). UI JS
  is manual-verify only (no headless browser here).

Original scope:
- Load column defaults (tags, scene prompts, `DOOR_PROMPTS`) from the scenario's
  `scenario.json` rather than hardcoded Hawai‘i/Alaska values.
- `POST /api/commit-room`: target `rooms/<chapter>/<scenario>/roomN/`; scratch pool
  under `rooms/<chapter>/<scenario>/_scratch/`. Keep traversal confinement to
  `escape_rooms/`. Update `authoring/test_harness_server.py` for the new paths.

### Phase 4 — Engine: linear evaluator + console-check primitive — ✅ DONE 2026-07-16
- **Console-check primitive** in `pano-player.js`: a puzzle carries EITHER `question` (MCQ) OR
  `check:{prompt,requires,expr,hint,maxAttempts,feedback}`. `buildCheckCard` renders a "Check my
  answer" button; `checkAnswer` verifies every `requires` var via `exists()` (missing → hint, no
  attempt spent) then evals `expr` (a single R logical) with `webR.evalRBoolean` against the live
  session (`rconsole.webR`). Same feedback ladder as MCQ. Student assignments persist because
  WebR's `captureR` and `evalRBoolean` share the global env (same env the datasets load into).
- **Linear graph evaluator**: `condOK()` supports `true` / `{solved:key}` / `{allSolved:[keys]}`;
  `applyEffects()` records `set`/`inc` into a `gameState` bag; `solveRoom()` adds to `solvedRooms`
  + applies effects; `goThrough()` advances to the first unsolved room whose `unlockedWhen` passes
  (linear order for now). Unsupported gates (counters) read as locked + a console warning.
- **Pilot:** Hawai‘i room1 converted MCQ → console-check (assign the runaway analyte to `answer`;
  `expr: is.character(answer) && length(answer)==1 && answer=="dissolved_solids"`).
- Verified: hawaii JSON valid; **R expr semantics checked in Rscript** (correct→TRUE,
  wrong/multi/missing→FALSE); new player symbols all defined + referenced. **Needs a live
  browser play-test** to confirm the session-state grading end-to-end (no headless browser here).
- Deferred (as planned): codec `solved`-byte encoding (Phase 5); non-linear counter gates.

### Phase 5 — Codec (done) + boss deliverable (deferred) — 🟡 2026-07-16
- ✅ **Codec wired.** `pano-player.js` tracks per-room `{answer, attempts}` (MCQ → chosen index;
  console-check → `answer=1`), and at the finish mints a code via `shared/codec.js`
  (`window.EscapeCodec`, loaded by each `play.html` before the module) keyed on the scenario `id`
  + `SECRET`. The done screen shows the code with a copy button. `SECRET` moved into
  `pano-player.js` (from the archived `escape-engine.js`) and matches `decode_codes.R`.
- ✅ **Scenario ids reconciled** (the Phase 2 carry-over): **alaska=6, hawaii=7** (hawaii's old `id:1`
  collided with the decoder's `ALASKA_KEY`). Added `DATA_VIS_ALASKA_KEY` / `DATA_VIS_HAWAII_KEY` to
  `decode_codes.R` (grade with `grade_one`; grow `correct` as rooms are added) + a pano round-trip
  regression. **R self-test green.**
- ⏸ **Boss figure deliverable — DEFERRED (blocked on boss art).** The boss rooms are `built:false`
  (no scene), and `buildCaption()` still needs WebR verification, so the "download the WebR plot as a
  PNG watermarked with x500 + code" step can't be built or tested yet. Spec lives in
  `hawaii_aquifers/notes.md` → item 2. Do it when a boss room is generated.
- **Verify:** R self-test passes (incl. new pano round-trip → grade 10). No node here, so the
  **JS↔R end-to-end** needs a browser-produced code decoded in R (`decode_code(code, x500)`) — the
  one live check outstanding.

### Phase 6 — The authoring skill
- `.claude/skills/build_escape_room/` — drives the design conversation, writes
  `scenario.json`, adapts `exercises.csv` stories into **unpeopled** narrative,
  picks puzzle types, and wires the scenario. Composes the harness (Lucas-run) and
  the phases above. Graduates once the shape is proven on the pilot.

### Phase 7 — Deploy + book integration
- Push to Pages; scenario link `https://thebustalab.github.io/escape_rooms/rooms/<chapter>/<scenario>/`.
- Add an **"Exercises"** section to the matching `integrated_bioanalytics` book
  chapter: a clickable **cover image** → the scenario. (Book is a bookdown; that
  edit lands in `websites/thebustalab.github.io/integrated_bioanalytics/`.)

## Harness → Scenario IDE (Phases 6+, agreed 2026-07-16)

Turn the authoring harness into the **single surface for creating AND editing every room
in a scenario**, reading/writing `scenario.json` as the one source of truth. Decisions
locked: (1) `scenario.json` `rooms[]` is authoritative — each room node holds its image
refs + `wrap` + `hotspots` (+ content) + settings inline; the `_scratch/*.json` and
`roomN/*.json` sidecars **retire** as persistence. This closes today's hand-copy gap
(harness wrote sidecars; the player reads inline node data). (2) Per-room **wrap** and
**hotspots** editors are **buttons that open in a new tab** with a **"Save and close"** that
patches that room's node. (3) Editable-settings depth is **phased** — structural first
(image, wrap, hotspot boxes/types/targets, room title/technique), rich puzzle/check content later.

- **Phase 6 — server foundation — ✅ DONE 2026-07-16.** `GET /api/scenario` (full doc);
  `POST /api/room-patch {roomKey, fields}` (shallow-merge into `rooms[key]`, preserves siblings +
  untouched fields, rejects unknown key); `POST /api/scenario-patch {fields}` (top-level merge).
  `_save_scenario` writes atomically (`.tmp`+`os.replace`) with a rolling `scenario.json.bak`
  (gitignored). Tests 15/15 (merge-preserves-siblings, unknown-key reject, top-level merge). Live
  endpoints verified on alaska. NOTE: the save layer normalises formatting (arrays → multi-line);
  first patch of each scenario.json reformats it (same data). No UI/player/data-model change yet.
- **Phase 7 — data model + UI columns — ✅ DONE 2026-07-16.** Both `scenario.json` consolidated:
  `rooms[]` = ALL rooms self-contained, each with `built`, `authoring:{tag,scenePrompt,doorPrompt}`,
  and (for stubs) `designNote`; `authoring.series` / `planned` / top-level `boss` **retired** (boss is
  now a `rooms[]` node, `isBoss:true`). Player: `isBuilt(r)=!!r.panorama` gates the first-room pick,
  `goThrough`, and the codec steps — stub rooms are carried for authoring but skipped when playing
  (Hawaii codeword stays 1 step). Server: `_scenario_config` derives from `rooms[]`; commit calls
  `_commit_node` (points the node at `roomN/scene.png`(+`_open`), sets `built:true`, seeds `wrap`
  from the committed `roomN/wrap.json` if the node has none). Harness UI: columns built from
  `rooms[]` (editable title/technique/tag + authoring prompts + built/stub badge), **Save all rooms**
  (patches each node), commit refreshes the badge. Tests 16/16. Verified live (config from rooms,
  scenario switch, both scenarios serve). Wrap/hotspots authoring still uses the shared sections
  (transitional) → per-column new-tab editors are Phases 8–9.
- **Phase 8 — wrap editor tab — ✅ DONE 2026-07-16.** `reproject_test.html?room=<key>` (IDE mode)
  fetches `/api/scenario`, loads the room node's committed scene via the new **`/sfile/<path>`** server
  route (serves any file under the active scenario dir — handles both `roomN/scene.png` and
  `_scratch/…`, traversal-confined), prefills from `node.wrap`, and its **"Save and close"** does
  `room-patch {wrap}` then `window.close()`. Legacy `?img=` mode (shared tester → `_scratch/wrap.json`)
  kept. Harness columns gained a per-column **"Edit wrap →"** button (enabled once the room is built)
  that opens the tab. Verified: `/sfile/` serves committed + `_scratch` images (404 on traversal),
  wrap `room-patch` preserves hotspots/built. Tab JS is manual-verify (no headless browser).
- **Phase 9 — hotspots editor tab — ✅ DONE 2026-07-16.** New standalone `authoring/ui/hotspots_edit.html?room=<key>`:
  loads the committed scene (`/sfile/`) + `node.hotspots`, draw-to-add boxes over the flat image, per
  hotspot edit **label / type (puzzle·clue·door) / box**, delete. **"Save and close"** → `room-patch
  {hotspots}` + close. **Structural only** — each hotspot's puzzle/clue **content is preserved** (client
  merges via `_orig`: `{...contentOf(orig), id, type, label, box}`); rich content editing is Phase 10.
  (Type-change leaves stale content, but harmless — each player type reads only its own fields.) Per-column
  **"Edit hotspots →"** button (built rooms only). Verified: page serves; hotspots `room-patch` preserves
  the laptop's `check`+`starterCode` and the room's wrap/panorama/built. NOTE: door-open image generation
  for a room's `panoramaOpen` still happens via the shared candidate section before commit (transitional).
- **Phase 10 — rich content editing — ✅ DONE 2026-07-16.** The hotspots editor now carries FULL
  hotspot data and shows a per-hotspot **content panel** by type: **clue** → `body`; **puzzle** →
  `starterCode` + a grading toggle: **console-check** (`prompt`, `requires`, `expr`, `hint`, `maxAttempts`,
  feedback correct/wrong[]/reveal) or **multiple-choice** (`prompt`, `options`, `correct` index,
  `maxAttempts`, feedback); **door** → box only. Switching type/grading swaps in the right skeleton.
  Save strips `_`-prefixed marker keys and `room-patch {hotspots}` writes the whole array. Verified with
  a full content round-trip (edit `check.hint` + label, expr/wrong[] intact; revert restores exactly).
- **Phase 11 — create-new-room / new-scenario — ✅ DONE 2026-07-16.** Server `POST /api/add-room
  {roomKey,title,technique}` appends a stub node (built:false, authoring skeleton, linear `unlockedWhen`
  on the previous room, rejects dupes); `POST /api/new-scenario {chapter,scenario,title}` scaffolds
  `rooms/<ch>/<sc>/scenario.json` (one stub room + `_scratch/`) with a **fresh id** (`max(on-disk ids, 5)+1`
  to clear the archived 1–5 decoder keys), rejects existing. Harness header gains **"+ room"** and
  **"+ scenario"** buttons (prompt-driven). Tests 18/18; verified live on a throwaway scenario (id 8,
  linear add, dupe reject) then cleaned up. **Reminder:** a new scenario's `id` is provisional — add its
  key to `decoder/decode_codes.R` when its codec grading is set up. **The scenario IDE (Phases 6–11) is
  complete** — every authoring step (create → generate → commit → wrap → hotspots → content → settings)
  now runs through the harness on `scenario.json`.

## Post-audit fixes (2026-07-16) — all 5 external-audit findings resolved

- **F1 (latent wrap crash) — fixed.** `pano-player.js buildViewer` guards `room.wrap || {…}` (a built
  room with no wrap no longer throws). Belt-and-braces: `_commit_node` now ALWAYS leaves a wrap on a
  committed node (existing → `seed_wrap` → sane default), so a wrapless built room can't be produced.
- **F2 (ACTIVE cross-scenario clobber) — fixed.** Write paths take an EXPLICIT scenario: `_scenario_base`
  + `base` param on `_load/_save/_room_patch/_scenario_patch/_add_room`; `GET /api/scenario` + `/sfile`
  + `room-patch`/`scenario-patch`/`add-room` accept `?chapter&scenario` / `{chapter,scenario}`. The wrap
  + hotspots tabs and the board pass their own `chapter+scenario`, so a save targets the scenario the tab
  LOADED, never whatever is ACTIVE. New test `test_room_patch_explicit_base_no_cross_scenario_clobber`.
- **F3 (dead sidecars + inline trip-hazard) — fixed.** `_commit_room` no longer writes `roomN/wrap.json`
  / `hotspots.json` (returns `seed_wrap` for the node instead); the committed stale sidecars were deleted;
  the inline wrap + hotspots sections were REMOVED from `harness_gpt.html` (they wrote `_scratch` files the
  player never read). Door-open generation moved to the hotspots tab: new `POST /api/dooropen-room`
  masks the door box on the committed `scene.png` → `scene_open.png` + sets `panoramaOpen`. Single
  authoring path now: generate → Send to room → Edit wrap → Edit hotspots (+ content + door-open).
- **F4 (setType content loss) — fixed.** `hotspots_edit.html setType` no longer wipes content on a
  type toggle; it only ensures the new type's skeleton exists (leftover fields are ignored by the player).
- **F5 (default coverage) — fixed.** `reproject_test.html applyWrap` defaults aligned (vaov 90, hfov 110).
- **Verify:** harness tests 19/19; codec self-test green; Finding-2 fix confirmed live (explicit patch to
  Hawaii while Alaska active → Hawaii changes, Alaska untouched); `/sfile` + `dooropen-room` validations
  pass. **Now-unused server endpoints** `/api/save-hotspots` + the candidate-based `/api/dooropen` are dead
  (the inline editor that used them is gone) — harmless, left for a future tidy. The browser JS of the
  three tabs still needs a manual click-through (no headless browser here).

## Editor UX pass (2026-07-16) — draft-in-scratch + puzzle/hotspot split

- **Header** → "escape room editor"; **"Suggest (Claude)"** removed (button + client `suggest()` +
  server `suggest_prompts` + `/api/suggest`).
- **Draft-in-scratch (edit before commit).** Pick a candidate in a column → **Edit wrap / Edit
  hotspots / Edit puzzle** enable (draft mode) and open on that candidate (`?img=<file>`, loaded from
  `/sfile/_scratch/`). **Save and close** writes to `_scratch/draft.json` (`{ "<roomKey>":
  {image,wrap,hotspots} }`) — NOT the node. **Send to room** copies the drafted image → `room/scene.png`
  AND promotes `draft.wrap` + `draft.hotspots` onto the node (built:true), then clears the draft. Lets
  you draft several rooms before deciding; `scenario.json` stays clean until commit. A tab opened with
  no `?img=` (a committed room) edits the live node directly (as before). Precedence everywhere:
  draft ?? committed node. Server: `_load/_save_draft`, `_draft_room_merge`, `_draft_clear`,
  `GET /api/draft`, `POST /api/draft-save`; `_commit_node(...,draft=)` promotes; commit clears. Test
  `test_draft_merge_and_commit_promotes` (2-tab merge + promote + clear). 22/22.
- **Marking vs content split.** **Edit hotspots** = boxes / type / label (+ clue body + door-open,
  which is committed-only). Puzzle CONTENT moved to a new per-room **Edit puzzle →** tab
  (`puzzle_edit.html`): lists every `puzzle` hotspot, edits starterCode + console-check/MCQ + feedback,
  save-and-close (draft or node). Multi-puzzle per room supported. Both tabs write the same hotspots
  array, merged by id (load-then-save-full), so neither clobbers the other.
- **Not headless-testable:** all four tabs' browser JS. Server draft flow verified live (draft-save
  merge + read-back) + unit test.

## Open decisions / to confirm during build
- **Boss region answer key** (Hawai‘i) still unresolved — Lalamilo/Kamaile vs the
  CSV's "Kona". Resolve from the outlier wells before locking Room 3 + boss.
- MCQ kept as a per-node fallback, or console-check only once proven?
- Does the boss figure stay hand-graded, or get a lightweight structural `check`?
- Chapter-level `AGENTS.md` at `rooms/<chapter>/` too, or only per-scenario? (Lean:
  add one when a chapter accrues cross-scenario facts.)

## Standing follow-up — no automated test for browser JS
The player + all four authoring tabs (`harness_gpt.html`, `reproject_test.html`, `hotspots_edit.html`,
`puzzle_edit.html`) are **only manually verifiable** — this box has no node / headless browser, so the
audit's client-side fixes (F1 `buildViewer` wrap guard, F4 `setType`) and the whole draft/commit UI flow
have no regression test. To close it: stand up a Playwright smoke harness (load a scenario, drive
generate→pick→Edit tabs→Send to room, boot WebR, solve a puzzle, assert the door swap + code). Server
logic IS covered (`authoring/test_harness_server.py`, 22 tests). Also open: the two dead endpoints
`/api/save-hotspots` + candidate `/api/dooropen` (harmless, remove in a future tidy).

## Not doing now (but the design leaves room for)
- Non-linear / interconnected practice rooms; world-state gates (the draining-
  fountain-reveals-the-key antechamber). Schema is ready; evaluator + authoring come later.
- Variable room counts beyond 3+boss — the graph model already allows it; the
  4-column harness UI just batches when a scenario needs more than four.
- ggtree-for-wasm and the embeddings technique (both flagged in `AGENTS.md`).
```

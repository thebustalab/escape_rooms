---
authority: history
---

# escape_rooms/ — rooms-umbrella refactor + scenario-IDE: phase-by-phase history

Archived 2026-07-17 from the top-of-`AGENTS.md` migration blockquote once the refactor was
complete. This is the historical record of HOW the migration happened (Phases 1–11, the
post-audit hardening, and the 2026-07-17 harness+player polish). For CURRENT state, read
`escape_rooms/AGENTS.md` → "Current architecture (post-refactor)". Do not edit — history tier.

---

**STRUCTURE MIGRATION IN PROGRESS (Phase 1 done, 2026-07-16).** The tree is moving to a
`rooms/<chapter>/<scenario>/` layout with authoring tooling split out — see
`rooms_refactor_plan.md` (the phased plan). **Path mapping already in effect:**
`alaska_pano/{harness_gpt,view360,reproject_test}.html` → **`authoring/ui/`** (the harness
now serves `authoring/ui/` on :8751, and maps `scene/*` to the active scenario's `_scratch/`
via a `/scene/` route); `alaska_pano/{play.html,chapter_alaska.js,AGENTS.md}` → **`rooms/data_vis/alaska/`**;
`alaska_pano/scene/` → **`rooms/data_vis/alaska/_scratch/`**; `data_vis/hawaii_aquifers/` →
**`rooms/data_vis/hawaii_aquifers/`**. A residual `alaska_pano/` remains, holding only its
pre-existing history dirs (`z_archive/`, `z_done/`) that the history-move guard won't relocate.
**Phase 2 done (2026-07-16):** each scenario now carries a pure-JSON **`scenario.json`** (the
single source of truth, read by the player and — soon — the harness). `play.html` is a bare shell;
`shared/pano-player.js` **fetches `scenario.json`** (relative to the page) instead of reading a
`window.CHAPTER` global — the concept is renamed **chapter → scenario** (`window.SCENARIO` shape).
`chapter_alaska.js` was converted to `rooms/data_vis/alaska/scenario.json` and archived to that
scenario's `z_done/`; a `rooms/data_vis/hawaii_aquifers/scenario.json` was authored (room1 live,
rooms 2–3 + boss are design stubs, boss region key still OPEN). The room graph fields
(`unlockedWhen`/`onSolve`/`state`/`boss`) are present as **data only** — the player still runs a
linear chain until the evaluator + console-check land (Phase 4).

**Phase 3 done (2026-07-16) — the harness is scenario-aware.** It no longer hardcodes the Hawai‘i
`ROOM_PROMPTS`/`DOOR_PROMPTS`; each `scenario.json` carries a top-level **`authoring.series`**
`[{key,tag,scenePrompt,doorPrompt}]` and the server has an **active scenario** (`ACTIVE`) that drives
`SCENE` (`rooms/<ch>/<sc>/_scratch`) + the commit target (`rooms/<ch>/<sc>/`). New endpoints:
`GET /api/scenarios`, `GET /api/scenario-config`, `POST /api/select-scenario`; `commit-room` takes a
bare **`roomKey`**. The UI (`authoring/ui/harness_gpt.html`) has a scenario dropdown and builds one
column per series entry.

**Phase 4 done (2026-07-16) — console-check + linear graph evaluator live in `pano-player.js`.**
A puzzle now carries EITHER `question` (MCQ) OR `check:{prompt,requires,expr,hint,maxAttempts,feedback}`,
graded on the **live R session** (`webR.evalRBoolean(expr)`, `requires` guarded via `exists()`).
Room advancement runs through `condOK()` (`true` | `{solved:key}` | `{allSolved:[keys]}`); `onSolve`
`set`/`inc` effects record into a `gameState` bag (counter gates still deferred). Hawai‘i room1 is the
pilot (MCQ → console-check on `answer`).

**Phase 5 done (2026-07-16) — submission codec wired.** At the finish, `pano-player.js` mints a
per-student code via `shared/codec.js` (`window.EscapeCodec`, loaded by each `play.html` before the
module): one step per room ({answer, attempts}; console-check rooms encode `answer=1`), keyed by the
scenario's `id` + `SECRET` (now in `pano-player.js`, matches `decoder/decode_codes.R`). Scenario ids
renumbered to avoid decoder collisions — **alaska=6, hawaii=7**; decoder gained `DATA_VIS_ALASKA_KEY`
/ `DATA_VIS_HAWAII_KEY` (R self-test green). (The once-deferred **boss-figure download/watermark**
deliverable is now **BUILT** — see the 2026-07-17 note below.)

**Phase 6 done (2026-07-16) — scenario-IDE server foundation.** The harness is becoming the full
create/edit surface for a scenario's rooms, with `scenario.json` `rooms[]` as the **one source of
truth** (the `_scratch`/`roomN` `wrap.json`/`hotspots.json` sidecars retire — the player reads the
inline room node). New server endpoints: `GET /api/scenario` (full doc), `POST /api/room-patch
{roomKey,fields}` + `POST /api/scenario-patch {fields}` (shallow-merge, atomic write, rolling
`scenario.json.bak`, gitignored).

**Phase 7 done (2026-07-16) — consolidated data model + IDE columns.** `scenario.json` `rooms[]` is
now the whole room list, each node self-contained: `built`, `authoring:{tag,scenePrompt,doorPrompt}`,
`wrap`, `hotspots`, graph fields, (+ `designNote` on stubs, `isBoss` on the boss). **Retired:** the
top-level `authoring.series`, `planned`, and separate `boss`. Player skips panorama-less **stub**
rooms (`isBuilt=!!panorama`) for both play + codec. Harness UI builds one column per room node
(editable title/technique/tag + prompts + built/stub badge) with **Save all rooms** and a commit that
points the node at its images.

**Phase 8 done (2026-07-16) — per-column wrap editor tab.** Each built room's **"Edit wrap →"** button
opens `authoring/ui/reproject_test.html?room=<key>`, which loads the committed scene (new server route
**`/sfile/<path>`** serves any file under the active scenario dir, traversal-confined), prefills from
`node.wrap`, and **"Save and close"** → `room-patch {wrap}` + `window.close()`.

**Phase 9 done (2026-07-16) — per-column hotspots editor tab.** Each built room's **"Edit hotspots →"**
opens `authoring/ui/hotspots_edit.html?room=<key>`: draw boxes on the committed scene, edit each
hotspot's **label / type (puzzle·clue·door) / box**, **"Save and close"** → `room-patch {hotspots}`.
the hotspots editor also carries **rich content** (Phase 10): selecting a hotspot shows a content panel
by type — clue `body`; puzzle `starterCode` + a **console-check** (prompt/requires/expr/hint/maxAttempts/
feedback) or **multiple-choice** (prompt/options/correct/feedback) grader; door = box only. So the
per-column new-tab editors (generate → commit → wrap → hotspots incl. content) are the full authoring
path; the shared sections below the columns remain only for candidate-stage door-open generation.

**Phase 11 done (2026-07-16) — the scenario IDE is complete.** Harness header **"+ room"** (`POST
/api/add-room`, appends a linear stub node) and **"+ scenario"** (`POST /api/new-scenario`, scaffolds
`rooms/<ch>/<sc>/scenario.json` + `_scratch/` with a fresh id = `max(on-disk ids,5)+1`). So EVERY
authoring step — create → generate → Send to room → Edit wrap → Edit hotspots (+ content) → Save all —
now runs through the harness on `scenario.json`; nothing needs hand-JSON. A new scenario's `id` is
provisional until its key is added to `decoder/decode_codes.R`.

**Post-audit hardening (2026-07-16).** (a) Harness **writes take an explicit `chapter`+`scenario`**
(`_scenario_base` + `base` params; `/api/scenario` + `/sfile` + patch/add-room accept `?chapter&scenario`
/ body) so an editor tab always saves the scenario it LOADED, never global ACTIVE (fixed a silent
cross-scenario clobber). (b) The **inline wrap + hotspots sections were removed** from `harness_gpt.html`
and the dead `roomN/wrap.json`/`hotspots.json` sidecars retired — wrap, hotspots, content, AND door-open
(`POST /api/dooropen-room` → `scene_open.png` + `panoramaOpen`) now live in the per-room "Edit …" tabs;
the shared section below the columns is just **Send to room** (commit). (c) `_commit_node` always leaves
a wrap so a committed room can't crash the player. `/api/save-hotspots` + candidate `/api/dooropen` are
now dead endpoints (harmless). (d) **Commit is explicitly targeted too** (`/api/commit-room` takes
`chapter`+`scenario`, reads that scenario's `_scratch`), and a **SAVE_LOCK** serialises every
scenario.json load-modify-write (HTTP handler threads + the door-open background thread would
otherwise race and silently drop each other's fields). (e) **Cache-buster gotcha:** pages hitting
`?chapter&scenario` endpoints must append `t=` query-aware (`p.includes("?") ? "&" : "?"`) — a
second `?` reaches the server inside the scenario value and 404s it (broke the wrap tab once).
Some prose further down still says `authoring.series` / `window.CHAPTER` /
`alaska_pano/…`; when it conflicts with this note or the mapping above, this wins.

**Harness + player polish (2026-07-17).** Two big shape changes plus a batch of player UX.
**(1) The harness is now a 6-step walkthrough** (`authoring/ui/harness_gpt.html`), top to bottom:
**1 Choose scenario** (full-width picker + a **scenario cover** generator — gpt-image-2 poster for
the book's exercises page: prompt → `gpt_cover_*` candidates in `_scratch` at a square size → "set
cover" copies the pick to `<scenario>/cover.png` and sets `scenario.cover` via `POST /api/set-cover`;
`coverPrompt` persists on the scenario. The `+ room` / `+ scenario` / `Save all rooms` buttons
were REMOVED — scaffold new scenarios/rooms by talking to an agent; metadata now saves as part of
each room's Save); **2 Build rooms** — per-room cards with a **forced-order** button stack
(generate → Edit wrap → Edit hotspots → **Make open door** → **Save room**), each button
locked/ready(amber)/done(green) so the sequence is legible; everything is authored on the
`_scratch` **draft** and **Save room = the single commit-out-of-scratch** (`/api/commit-room`
promotes the draft's wrap+hotspots, copies `scene.png`+`scene_open.png`). "Make open door" runs
`/api/dooropen` on the picked candidate using the draft's door-hotspot box, then shows a **closed→open
preview** so you can inspect / regenerate (edit the modifier, click again) before saving; **3 Author
puzzles & clues**; **4 Entry screens** (landing scenario-level fields via `scenario-patch` + each
room's interstitial `entry` via `room-patch`); **5 Finish screen** (`scenario.done` title/body via
`scenario-patch`); **6 Save all** (`saveAll` — one `room-patch` per room for settings+`entry` plus
one `scenario-patch` for landing+finish; **text only — never commits scratch→room or generates art**).
No server changes were needed — all six steps ride existing endpoints.
**(2) Clue text moved into the puzzle editor** (`puzzle_edit.html`, now "Puzzles & clues"): it
renders a card per puzzle AND per clue (the clue's `body`); the hotspots editor now owns only
box/type/label + door-open. Field-width fix there too (`width:100%` — block textareas were
collapsing under `flex:1` with no flex parent).
**Player (`shared/pano-player.js` + `.css`):** enter each room **facing the closed door**
(`doorYaw`); on solve, **return to the yaw you were facing** when you opened the puzzle
(`resumeYaw`) — no snap to front; **no more white flash** on room swaps (dark bg on `#pano` +
Pannellum containers, and the new scene **fades up from black** via Pannellum's `load` event);
the **puzzle modal is near-full-screen and grows unbounded for tall plots** (overlay scrolls; the
plot pane is no longer an inner scrollbox), MC pane narrowed to give the WebR editor more room;
**ambient particles** on both entry screens — scenario-level **`ambient`** (`"fireflies"` default |
`"snow"` | `"none"`; Alaska uses snow), `spawnParticles`, reduced-motion aware; optional
per-room **`entry`** interstitial "loading" card (schema: string or `{title,text,button}`).
**Attempt counts persist across modal close/reopen within a session** (`attemptCounts` Map) but
**reset on a full page reload** — so they're **deliberately NOT a graded signal** (decision
2026-07-17): grade on the **submission key** (completion + answers, minted at the finish) + the
**watermarked figure**; the attempts byte stays in the codec, just unused for grading (stripping
it is an optional follow-up — see Known follow-ups). **Download-figure deliverable (BUILT — closes
the deferred boss-figure item):** the WebR console has a **⬇ Download figure** button that saves the
latest plot as a PNG with a **visible x500 corner stamp** + an **invisible LSB watermark** carrying
`x500|scenario|epoch` (red-channel LSB, `ESRW` magic + len + UTF-8, MSB-first, frame repeated;
invisible, survives a lossless PNG download, destroyed by JPEG/screenshot/heavy edit). Recover it
with **`decoder/decode_watermark.py`** (`--selftest` round-trips the JS↔Python scheme, like the
codec's R self-test; `--json` parses the fields). **Cache convention (load-bearing for authoring):**
each `play.html` links the shared assets as **`?v=N`** — **bump N on any `shared/` edit** (now
`v=12`) so a plain reload picks it up; and **`scenario.json` is fetched `{cache:"no-store"}`** so an
authored text edit shows on reload (the browser was serving a cached `scenario.json` — looked like
stale text; the private-tab-works symptom was the tell).

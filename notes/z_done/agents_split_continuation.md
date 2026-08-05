---
authority: intent
---

# escape_rooms AGENTS.md subdivision — continuation handoff (2026-08-05)

Handoff doc for finishing the by-audience subdivision of the oversized `escape_rooms/AGENTS.md`. Written
mid-reorg (the "clean up" session) so a fresh agent can finish the precision part with a clean context.
**When done, archive this doc to `notes/z_done/`.**

## Goal & principle

The hub `escape_rooms/AGENTS.md` was ~1454 lines — almost too big for agents to load. Subdivide it by
**audience along the existing folders**, exploiting AGENTS.md auto-load (a sub-component file loads only
when an agent works in that subtree):
- **Hub `escape_rooms/AGENTS.md`** keeps only what a **scenario author** needs (scenario-building happens
  under `rooms/…/`, which auto-loads the hub but NOT sibling folders): author-facing **schema**, the
  skills pipeline, Goal/book-tracking, paired-scenario rule, concurrent-editing, the open-world design
  canon, and a sub-file index.
- **`shared/AGENTS.md`** = runtime **player engine implementation** (loads when editing `shared/*.js`).
- **`authoring/AGENTS.md`** = harness + scene pipeline (loads when editing `authoring/`).
- **`decoder/AGENTS.md`** = codec byte-scheme + anti-cheat (loads when editing `decoder/`).

**Safety rule (mobile nuance):** a pointer to another AGENTS.md is a DEAD LINK mid-turn on mobile, so
anything an author needs **while writing a scenario** MUST stay in the hub. Author-facing schema → hub;
implementation → sub-file. Err toward keeping in the hub when unsure.

## Done so far (this session)

- **`z_history/canon_history_stale_layout_sections.md`** — the two fully-stale pre-refactor sections
  ("Room directories — stable naming", "Layout & the scenario-as-data pattern") captured verbatim; hub
  section replaced by a pointer.
- **`authoring/AGENTS.md`** (~374 lines) — created. Holds: `## Hosting`, `## 360-panorama scene
  pipeline` (moved VERBATIM — still contains stale pre-refactor content to clean, see Stage 8), and
  `## Authoring — the harness walkthrough` (the 124-line walkthrough bullet). Frontmatter `authority: canon`.
- **`decoder/AGENTS.md`** (~65 lines) — created. Holds the codec byte-scheme contract + the anti-cheat
  posture (former "The codec contract" + "Security & anti-cheat posture" sections).
- **Hub** trimmed 1454 → ~1065. Removed → pointer: Hosting, 360-pipeline, codec contract, security,
  the harness walkthrough (kept 2 author rules inline: content-on-`plannedHotspots`, explicit door `to`).
- **`shared/AGENTS.md` does NOT exist yet** — Stage 1 creates it.

**Conventions to match:** frontmatter `---\nauthority: canon\n---`; a `## X — moved to \`<file>\`` (or
`## X (moved …)`) pointer left in the hub keeping the author-facing gist + a → pointer; sub-file section
headers noted "(moved from the hub 2026-08-05)"; paths in sub-files are relative to the `escape_rooms/`
root. `**/AGENTS.md` and `z_history/` are already gitignored — new sub-files stay private automatically.
This tree is **git only on the Mac** (Syncthing-synced) — no commits on this box.

## Concurrency caution

Multiple agents + Lucas's live harness work this tree. **Re-verify the two big sections' line ranges
before editing** (another agent may have shifted them). Serialise edits to the hub. Every atomic
step leaves the hub valid (pointers resolve) — safe to stop between stages.

## Temp fragments on disk (verbatim content sources for Stage 4)

`_frag_notebook.md` `_frag_clueimg.md` `_frag_modaltitles.md` `_frag_datarender.md` — extracted from the
ORIGINAL line ranges (content verbatim; line numbers now stale). Delete when Stage 4 is done.

## Remaining stages

1. **Create `shared/AGENTS.md`** (frontmatter canon; scope = the runtime player engine `pano-player.js`
   /`.css`, `debrief.js`, `sfx-mixer.js`). Intro like the other sub-files.
2. **Split `## Current architecture`** — keep the HUB list below inline (compact schema); move the SHARED
   list to `shared/AGENTS.md`. Leave the hub section as a schema reference + a pointer to `shared/` for internals.
3. **Split `## Ambience`** — keep the 4 schema blocks in the hub; move engine internals to `shared/`;
   move sound-SOURCING + mixer writeback + auto-balance to `authoring/AGENTS.md`.
4. **Small sections** — `## Field notebook`, `## Modal titles suppressed`, `## Clue images`,
   `## Data-rendered assets`: keep author-facing schema in hub, move rendering/engine detail to `shared/`,
   clue-image *generation* flow to `authoring/`. (Data-rendered-assets rule is an author/build discipline —
   likely stays in hub.)
5. **Distribute `## Known follow-ups`** (~296 lines): harness follow-ups → `authoring/`; engine follow-ups
   → `shared/`; cross-cutting/parked design ideas → keep in hub or move to `notes/`/root `todo.md`. Trim done items.
6. **Drop duplicates** (keep ONE canonical copy): figure watermark (×3: Current-arch, Security→now decoder,
   REQUIRED item 1); debrief schema (×2: Current-arch + REQUIRED item 3); "attempts session-only/not graded"
   (×2); `sound_pull` sourcing (×2 in Ambience); cache-bump convention (central rule + scattered token values).
7. **Add a sub-file index** near the hub top (a short table: `shared/` engine, `authoring/` harness,
   `decoder/` codec, plus the existing `tests/AGENTS.md` and per-room `rooms/*/AGENTS.md`).
8. **Polish — clean the stale 360 content now in `authoring/AGENTS.md`** (the long-deferred "reviewed
   rewrite"). KEEP inline (live reference): gpt-image-2 custom sizes + `vaov≈360×H÷1536`; seamless-wrap
   prompt recipe; max 3:1 / min-512 rule; the `billing_hard_limit_reached` 400 diagnostic; wrap tuning
   (`reproject_test.html`, wrap schema + vOffset/hfov clamps); hotspot-geometry formula; the shell hazards
   (tmux restart, no self-match `pkill`, blocked foreground `sleep`); the `ControlMaster=no`/`cm-harness.sock`
   tunnel gotcha. RELOCATE/trim as archaeology (into `z_history/`): "Removed true-360 tooling" (already in
   `z_history/canon_history.md`), the DECISION narrative, the four-column harness UI, `view360.html`,
   `gpt_compare.html`, the dead `/api/save-hotspots`/`/api/dooropen` endpoint inventory, "Playable chapter
   BUILT / codec not yet wired" (contradicts current "Codec wired"), all `alaska_pano/` paths.

Target hub after all stages: ~600 lines. Verify at the end: `grep -n '^## ' AGENTS.md`, grep for dangling
"see \"…\"" refs, confirm every pointer path resolves, and re-run `decoder/validate_keys.py` if any codec text moved.

---

## The keeper classification (the map for Stages 2–3) — paragraph-by-paragraph

Produced by an adversarial keeper over the two sections (2026-08-05). Author-facing → HUB; implementation → SHARED.

### `## Current architecture` — HUB (keep inline)
Rooms/tree orientation intro; `scenario.json` single-source-of-truth; **`rooms[]` node shape** (`built`,
`authoring:{tag,scenePrompt,doorPrompt}`, `wrap`, `hotspots`, `unlockedWhen/onSolve/state`, `designNote`,
`isBoss`); **puzzle-grading schema** (`puzzle` = `starterCode` + `question`{MCQ prompt/options/correct/
maxAttempts/feedback} OR `check`{prompt,requires,expr,hint} OR `map`{image,points[{lake,box}],answer,…});
**door schema** (`box`+`direction:forward|back`+`to`; forward gates/swaps/entry, back always-live no-entry,
absent⇒legacy); **gateless-room rule** (reading rooms need `back`+explicit `to`; terminal escape holds the
gate; don't gate gateless `unlockedWhen` on another gateless); **open-maze schema** (`direction:"open"`;
`availableWhen` condOK grammar + `{gte:[k,n]}` + `lockedBody` on puzzle/lock/grid AND door; `requires`
in-room vs `availableWhen` cross-room; `clue.onPickup`; **`grid` hotspot** items×buckets/`answer:{item:bucket}`,
ungraded); **codec ids** (one step per built room; live ids alaska=6, hawaii=7); **debrief schema**
(`scenario.debrief{title,intro}` + `room.debrief` string|{heading,body}); scenario-level `ambient` +
per-room `entry`; **`lock` type** + per-gate solve model (`door.requires`, only primary graded gate → codec);
"image asset refs in scenario.json need `?v`"; **stone-portal author flags** (`stonePortals:true`; stone
keypad = `lock` `mode:"stones"`, raw `|`/`_` `answer`, `length`; `preAwakened:true`; `endsEscape:true`
door|lock gate with `availableWhen`/`requires`); **`pick` fields** `idColumn`(req)+`idNoun`; consistency-spec
habit; migration-history pointer + the ⚠️ stale-section box; project overview + two-formats orientation.
PLUS the 2 rules already extracted from the walkthrough: content-on-`plannedHotspots` (shape
`[{type,label,direction?,pickup?,note?}]`, carries full payload, attaches at commit by `(type,slug(label))`);
"author every door's `to` explicitly".

### `## Current architecture` — SHARED (move to shared/)
`webR.evalRBoolean`, `openMapPuzzle`/`buildMapCard`, `.mappt` CSS, `condOK()` internals, `onSolve set/inc`
→ `gameState`; `goThrough`, "codec not re-recorded on solved re-entry", `door.panoramaOpen` forward-compat;
**the whole "Analysis-finish trigger = completion not position" bugfix** (`analysisComplete`/`finishAnalysis`/
`analysisFinished` guard, the boss-door `to:"escape1"` war-story) — distil one HUB line ("finish fires when
every built graded analysis room is solved, independent of room order"), rest SHARED; `openGrid`/`buildGridCard`/
`.gridsel`/`portalUnlocked`/`doorIsOpen`/`handleDoor`; debrief engine (`debrief.js`, `window.EscapeDebrief`,
`#debriefBody`, `renderDebrief`, `switchSubTab`, the "second TAB not behind-modal" war-story); **Finish +
submission screen** DOM (`#skipChip`, `exportSubmissionPdf`, "code baked into PDF only", "music keeps playing");
**Player UX** internals (`doorYaw`/`resumeYaw`/fade-from-black/modal-✕ rationale/HUD); Figure-download +
watermark (`decode_watermark.py`); **cache-convention** core (bump `?v` on play.html + `test_play.html`,
separate counters, "suspect caching first", two dead endpoints) + the **`gateKey(roomKey,id)` room-namespacing
war-story**; stone-portal engine (`forwardDoor`/`portalUnlocked`/`portalAwakened`, `compositeAwakened`/
`drawStarfield`, `mintCode` skips ungraded, `validate_keys.py` skip rule, `hasPendingEscape`/`hasEscapePhase`,
hawaii bug narratives, `confirmX500`/`captureSubmissionWork`/`stampAllFigures`/`renderStudentPickSvg`/
`bootConsole`, **cache-token VALUES** `pano-player.js v=57`/`css v=54`/`sfx-mixer.js v=6`, jsPDF-CDN note).

### `## Ambience` — HUB (keep inline): 4 schema blocks
**music** (`music`, `musicVolume` 0–1 default 0.1, `musicCredit{text,url}`); **`room.sfx` layer schema**
(sound or array; layer `{src,volume?=0.7,duckMusicTo?,delay?=0,mode?:loop|interval,gapMin?/gapMax?,
crossfade?=4}`; sfx not silenced by music toggle; `duckMusicTo` dips music); **`solveSfx`** (path or
`{src,volume?}` default 0.9; resolution hotspot→room→SCENARIO); **`heel`/`sickness`** overlays
(`heel:true`|`{mode:progressive,by:analysis,toward,maxDeg}`; `sickness:{ramp:analysis,clearOn:cure,maxDim}`;
absent⇒no-op).

### `## Ambience` — SHARED (move to shared/)
music-toggle render; "music must not restart on modal" resilience war-story (`buildViewer` snapshot/restore,
pause-guard, `musicOn`); sfx engine internals (`_sfxCrossfade`/`_sfxInterval`/`startRoomSfx`/`stopRoomSfx`,
equal-power crossfade, `<1.2s` fallback, `sfxHandles`, legacy `crossfade`-folded parsing); sfx on/off chip
(`sfxOn`/`playOneShot`/`localStorage panoSfx`); solve-sting engine (`solveRoom`/`playOneShot`/`PanoMixer`);
`heel`/`sickness` engine (`updateEnvironment`, `--heel-base`/`heelRoll`, `#sickness` CSS, `heelBaseDeg`/
`sicknessDim`, cache tokens); the two **test-play affordances** (`window.TEST_PLAY`/`isTestPlay`, ⏭ Solve
button; locked-door walk-through bypass at `doorIsOpen` in `handleDoor`).

### `## Ambience` — AUTHORING (move to authoring/)
Room-ambience harness Step (freesound + `sound_pull` observer + `youtube_audio --section/--fade`,
`_scratch/audio/` naming, `GET /api/audio-candidates`, `POST /api/commit-sound`, `CREDITS.md`); solve-sting
SOURCING tail (`puzzle_edit.html` picker, `solve_<roomKey>_<gateId>_<n>.mp3`, `sound_pull`,
`notes/solve_sounds.md`); test player + live mixer (`test_play.html`, `sfx-mixer.js`, `window.PanoMixer`);
volume writeback (`/api/save-mix`, `_apply_mix`, `_cors`, `syncSoundVolumesFromDisk`, `test_apply_mix_*`);
auto-balance (`_apply_balance`, ffmpeg loudnorm, `auto_balance.py`, `/api/auto-balance`, `test_apply_balance_*`).
"Flat scenarios (archived)" → one-line pointer or drop.

### Duplication flags (Stage 6 — drop extras, keep one)
1. Exit-debrief schema: Current-arch + REQUIRED item 3. 2. Debrief-on-submission: Current-arch + stone-portal
block. 3. "Attempts session-only/not graded": Player-UX + Security. 4. Figure watermark: Current-arch +
Security + REQUIRED item 1 (×3). 5. `sound_pull` sourcing: solve-stings + room-ambience (both in Ambience).
6. Cache-bump convention: central rule + scattered per-area token values.

---
authority: intent
---

# Ambient cinemagraph loops — setup plan

**IN PROGRESS (spec + Phase 0 spike, 2026-07-31).** Animate elemental regions of a 360° panorama (sky,
water, torches, foliage) into seamless loops that play in-game — the biggest immersion track from the
art-options discussion. Research done (subagent), Phase 0 spike built; generation pipeline gated on one
decision (self-host vs API). Additive throughout: inert for every room without a `cinemagraph` field.

## The runtime crux — SOLVED without a viewer swap

Pannellum (the existing viewer) natively supports **`panorama: <canvas|video>` + `dynamic: true`**, which
re-uploads the texture every frame via `texImage2D` while projecting the SAME equirectangular sphere. So a
cinemagraph is **`compositeVariants` promoted to per-frame**: keep a base still on an offscreen canvas,
`drawImage` the animated region (a hidden looping `<video>`, or a procedural draw) into just its box each
`requestAnimationFrame`, and let Pannellum re-upload. Because it's still an equirectangular texture with the
same `haov/vaov/hfov/pitch`, **hotspot projection (`boxToYP`) and `room.wrap` tuning keep working
unchanged** — hotspots are DOM markers positioned by yaw/pitch, independent of a still vs live texture.
- Integration point: `shared/pano-player.js` `_renderViewer` (~line 1055, the `pannellum.viewer(...)` call)
  + a `startCinemagraph()/stopCinemagraph()` rAF module next to `compositeVariants` (~998); cancel the rAF
  in the `viewer.destroy()` path (~1035).
- Rejected: whole-frame Pannellum video plugin (Video.js dep, no region control); swapping to
  Photo Sphere Viewer / three.js VideoTexture (rewrites hotspot projection + wrap + the 5 play.html shells
  for a feature only some rooms need). Only fall back to PSV if `dynamic:true` proves unstable.

## Data model (mirrors `variants`)

A hotspot/room gains an optional `cinemagraph`:
`{ "box":[x0,y0,x1,y1], "video":"room1/sky_loop.webm", "prompt":"drifting aurora, seamless loop", "fps":24 }`
— `box` reuses the 0–1 fraction convention (`compositeVariants`/`boxToYP` already consume it); `video` is a
room-relative path like `panorama`. Inert for existing rooms.

## Generation pipeline

- **Primary (self-host):** `Lightricks/LTX-2.3-22b-LoRA-Cinemagraph` (HF) — image-to-video, locked camera,
  single-element motion, explicit loop prompting; takes our base PNG (or masked region) as first frame. The
  GV100 (32 GB VRAM) comfortably runs it (floor ~16–24 GB). Zero per-call cost; fits the "author on Lucas's
  machine, ship static assets" model. Needs `diffusers` + the LoRA weights (~tens of GB download).
- **Fallback (hosted, no infra):** Runway Gen-4.5 image-to-video with Motion Brush (constrain motion to the
  sky/water region + loop), or fal.ai-hosted LTX (~$0.04–0.12/s). No install; per-call cost.
- **Seam:** author the animated box in the panorama INTERIOR (away from the ±180° edge) → wrap stays trivial
  since the moving region never touches the seam. Escape hatch: apply the existing `seamfix` roll to the
  video frames. Wrap-safe motion (drift/shimmer/flicker/sway, never a lateral pan) is inherent to the
  cinemagraph LoRA's single-element static-camera scope.

## Web asset format

VP9/WebM (primary) + H.264/MP4 (Safari/iOS fallback), `muted loop autoplay playsinline`, 3–6 s, 24 fps.
Region-only band (e.g. a 3072×~400 sky strip) keeps files < 1 MB; a full 3072×1024 loop ~2–6 MB. Texture
dimension ≤ 4096 (WebGL/mobile cap). Ambience AUDIO stays on the existing sfx mixer, not the video track.

## Phased plan

- **Phase 0 — spike (built 2026-07-31, `authoring_v2/ui/cinemagraph_spike.html`):** self-contained page —
  procedural equirect scene on a per-frame canvas + `pannellum.viewer(..., {panorama:canvas, dynamic:true})`
  + two hotspots + a Rebuild button. Proves the animated texture tracks the pan, hotspots project, perf is
  fine, and a viewer rebuild doesn't hang (the #686/#836/#856 risk). No shared-player change. **Lucas: open
  it on the harness and confirm.**
- **Phase 1 — runtime, one room, additive:** `startCinemagraph/stopCinemagraph` + one branch in
  `_renderViewer` reading a `cinemagraph` field; cancel rAF on `destroy`. Ship one hand-authored loop into
  one room. Inert for all other rooms.
- **Phase 2 — generation tool:** `generate_scene.py cinemagraph` (reuse dooropen mask + seamfix roll +
  ffmpeg encode). **← the self-host-vs-API decision lands here.** `diffusers` install + LoRA download if
  self-host.
- **Phase 3 — authoring:** `/api/cinemagraph` + `_run_cinemagraph` + `_add_cinemagraph` in
  `harness_server.py`; a chip in `hotspots_edit.html` (author like a variant).
- **Phase 4 — generalize + accessibility:** water/torches/foliage across rooms; a "reduce motion" toggle
  (also honour `prefers-reduced-motion`); pause rAF when the tab/room isn't visible (mobile battery).

## Risks
1. **Mobile perf/battery** from per-frame `texImage2D` — mitigate: short, region-only loops; pause rAF when
   hidden.
2. **Pannellum `dynamic:true` rebuild stability** (#686/#836/#856) — Phase 0 must confirm before Phase 1.
3. **Autoplay policy** — muted + playsinline required.
4. **Seam** on an edge-spanning animation — author in the interior; seamfix-on-video is the fallback.

## Decision needed before Phase 2
Self-host LTX-2.3 on the GV100 (zero per-call cost, ~tens-of-GB model download + `diffusers` install) vs
start on a hosted API (Runway/fal, no install, per-call cost). Phase 0 + 1 don't depend on this.

---

## Status update (2026-08-01) — PROVEN end-to-end + runtime shipped

**Phase 0 spike + generation are DONE and validated.** Lucas: the tight high-res flame "looks excellent…
more than good enough." Key learnings:
- **Region-crop is the way.** Whole-panorama loops are soft (a 3:1 scene squished into ~768px). Cropping a
  SMALL region and generating it at high res puts all the detail on the moving thing; the rest of the
  full-res still stays crisp. A torch flame at 256×896 (tight core) looked great; a whole sky patch did not.
- **VRAM fit:** the 29.5 GB full checkpoint OOMs on the 32 GB card; use the **25 GB transformer-only**
  (`ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled`) via UNETLoader + separate VAE + Gemma-on-CPU.
  Small regions fit high res easily. An auto **resolution-fallback ladder** picks the highest that fits.
- **Auto-flame detection:** target the bright CORE (top-percentile luminance + warm), NOT the warm glow
  (which grabs most of the image).
- **Orchestration:** a **self-contained detached python script** (`~/ComfyUI/torch_cinemagraph.py`, run via
  `setsid`) owns the whole GPU handoff (stop lm_server → generate → **guaranteed restart in `finally`**) and
  survives session boundaries. This is the pattern the harness generation route should reuse.
- **lm_server** = `embed_server` on :8080 (LLM+embed+Whisper+TTS), ~8 GB steady. Restart recipe in
  [[project_lm_server_gpu_handoff]]. Restarting it mid-model-load can leave it down — send C-c, then relaunch.

**Runtime (Phase 1) is BUILT in `shared/pano-player.js` (2026-08-01, ?v=65):** `activeCinemagraphs` +
`startCinemagraph` + a per-frame canvas compositor (draw composited still → stamp each cinemagraph's box
region from a hidden looping `<video>`, feathered → `viewer.setUpdate(true)` with `dynamic:true`).
Composed after the awakened + variant stages; `_renderViewer` gained a `dynamic` flag + `_cineStop`
teardown (cancels the rAF + releases the videos on room change). Additive/inert for cinemagraph-free rooms;
41 node tests green. Data model: `hotspot.cinemagraph = {box, video}` (room-relative video path like
`panorama`). Prototype viewers: `authoring_v2/ui/torch_view.html` (flat) + `cinemagraph_region_view.html`
(360).

**Remaining — authoring integration (the "create it in the hotspot menu" ask):**
1. **Reusable generator** — generalize `torch_cinemagraph.py` into a parameterized `cinemagraph_gen.py`
   (input scene + box + prompt + out → crop → LTX ladder → loop), keeping the guaranteed-restart handoff.
2. **Harness route** — `/api/gen-cinemagraph` kicks off the detached generator (long, ~5 min, pauses
   lm_server); the UI polls a status file. On success, write `hotspot.cinemagraph = {box, video}` on the node.
3. **Hotspot editor UI** — an "Animate region" action in `hotspots_edit.html` (draw box → motion prompt →
   Generate → preview), beside the Variants tab. Save strips `cinemagraph` like it strips `variants` (server-owned).
4. **End-to-end demo** — wire one real room (a torch/brazier or the airship aurora) and play it.

---

## Authoring integration BUILT (2026-08-01) — create cinemagraphs from the hotspot menu

The full "make it in the hotspot editor" loop is wired and verified (38 py tests, editor JS parses, all
route guards 400 correctly, no accidental gen, lm_server healthy):

- **Reusable generator** `~/ComfyUI/cinemagraph_gen.py` — parameterized (`--scene --box --prompt --out
  --scenario --room --hotspot --video-rel --status`): crop the box → LTX resolution-fallback ladder →
  stage the mp4 → **write `hotspot.cinemagraph={box,video,prompt}` into scenario.json** → guaranteed
  lm_server restart. Writes a status JSON the editor polls. (Generalizes the proven `torch_cinemagraph.py`;
  no gpt-image-2 / no auto-flame — the box is author-given.)
- **Harness routes** (`authoring_v2/harness_server.py`): `/api/gen-cinemagraph` launches the generator
  DETACHED (`start_new_session`) and returns immediately; `/api/cinemagraph-status` polls the status file;
  `/api/delete-cinemagraph` drops the field. Helpers `_launch_cinemagraph` / `_cine_status_path` /
  `_remove_cinemagraph`. Output committed at `rooms/<ch>/<sc>/<room>/cine_<hotspot>.mp4`.
- **Editor** (`authoring_v2/ui/hotspots_edit.html`): a **Cinemagraph** tab beside Content/Variants — shows
  the current clip + delete, and an "Animate this region" form (motion prompt → Generate → polls status →
  preview). Uses the selected hotspot's box. Save strips `cinemagraph` (server-owned, like `variants`).
- **Flow:** commit a room → mark a hotspot box → Cinemagraph tab → motion prompt → Generate (~5 min, briefly
  pauses lm_server) → the node gets its `cinemagraph` → the runtime (pano-player.js ?v=65) animates just
  that box in-game.

**Untested (Lucas's live acceptance):** one real end-to-end generation *through the editor* (the guards +
plumbing are verified, but a full gen is a ~5-min GPU job I didn't trigger in smoke tests). **Cinemagraph
track is feature-complete pending that run.**

---

## Session addendum (2026-08-01, later) — authoring live, loop fix, 6s, wrap-hub idea

**Editor unified (less navigation).** Cinemagraph/Variants/door-open generation were blocked in draft
(`img=`) mode; they're generated from the committed `scene.png` so they now light up whenever the room is
**committed**, even while viewing a candidate. `hotspots_edit.html` gained `const isCommitted = () =>
!!(NODE && (NODE.panorama || NODE.built))`; the three draft guards became `DRAFT_IMG && !isCommitted()`
(door-open wiring: `!DRAFT_IMG || isCommitted()`). No more separate committed-editor URL.

**Crossfade loop option (2026-08-02).** Boomerang reverses motion at the turnaround — wrong for *directional*
motion (rising smoke, bubbles, embers visibly fall). Added a **crossfade** loop as an alternative in
`~/ComfyUI/cinemagraph_gen.py` (`crossfade()` + `--loop {boomerang,crossfade}`, default boomerang): ffprobe
the clip, blend the tail back into the head via `xfade` (`seam = xfade(tail,head,d)` then the middle; output
length `T−d`, and out's first==last source frame so the wrap is seamless) — **no reversal**, so directional
motion keeps going one way. Falls back to boomerang on any ffprobe/ffmpeg error. Verified on a synthetic 3 s
clip (out = 2.209 s = 3−0.8). Threaded through: harness `/api/gen-cinemagraph` `loop` param →
`_launch_cinemagraph(..., loop)` → `--loop` (server whitelists to boomerang/crossfade; **needs a harness
restart**, done); the choice is stored on the node's `cinemagraph.loop` and a **loop-style `<select>`** was
added to the Cinemagraph tab in BOTH `reproject_test.html` (hub) and `hotspots_edit.html` (preselects from
`cine.loop`). Not run through a real GPU gen (5-min job) — but the ffmpeg filtergraph is proven on a real clip.

**Loop fix — BOOMERANG (ping-pong).** LTX clips drift directionally, so a plain loop JUMPS at the seam
(a turbulent flame looked fine only because its last frame ≈ first). Fix = forward+reverse encode via
ffmpeg (`[0]split[a][b];[b]reverse,trim=start_frame=1,setpts=PTS-STARTPTS[r];[a][r]concat=n=2:v=1:a=0`),
which is seamless for ANY motion. Applied to the existing `rooms/data_vis2/airship/nest/cine_obj_1.mp4`
(a flag — `_orig.mp4` backup kept) and **baked into `~/ComfyUI/cinemagraph_gen.py` (`boomerang()`, used in
place of the raw copy)**. Caveat: it reverses motion at the turnaround — fine for oscillatory/ambient
(flag, water, drift, flame), wrong for rising smoke/embers (would fall) → crossfade is the alt if needed.

**Clip length bumped to ~6s.** `cinemagraph_gen.py --length` default 25 → **73** (~3s source @24fps →
~6s after boomerang); res-ladder low end widened to `(896,768,640,512,448,384,320)` so longer (more-VRAM)
clips still land. TRADE-OFF: 6s ≈ 3× VRAM of 1s → may generate at lower resolution. Unbuilt alt offered to
Lucas if too soft: generate ~49 frames but play at ~16fps (keeps res, gentler pace) — would need patching
the workflow's CreateVideo/fps + LTXVConditioning frame_rate.

**OPEN / NEXT (Lucas's idea, not built):** (1) make **wrap mode** (`reproject_test.html`, the 360 preview)
**play cinemagraphs live** (reuse the runtime compositor so the wrap preview = what players see). (2) Bigger:
restructure the harness editor as a **hub-and-spoke** with the 360 wrap view as the hub and spots/seam/
cinemagraph/door as contextual spokes off it (a real navigation refactor — scope separately). Lucas was
asked "build the wrap-preview-plays-clips piece next + sketch the hub plan?" — awaiting his go.

---

## Session update (2026-08-02) — wrap preview plays cinemagraphs live (#1 BUILT)

Lucas said go on #1 + sketch #2. **#1 done in `authoring_v2/ui/reproject_test.html`:** ported the game's
`startCinemagraph` compositor into the wrap tester. In **room mode**, `initCinemagraphs(node)` runs before
the first `build()`, collects the node's `cinemagraph:{box,video}` hotspots, preloads the still (`IMG_URL`)
into an offscreen canvas, and creates a looping muted `<video>` per clip (served `/sfile/<video>?t=…&SCQ`,
same path shape as the still). `build()` then feeds Pannellum the **canvas + `dynamic:true`** (instead of the
plain still URL) and runs a per-frame rAF that repaints the still and stamps each video's box, feathered by
the same radial-gradient mask as the runtime — so the wrap preview animates exactly what the player sees.
Additive/inert: `CINES` stays empty in picker mode and for rooms without cinemagraphs, so `build()` renders
the plain still as before. rAF is torn down + restarted on every slider/`Preview as player` rebuild
(`stopCineLoop`/`startCineLoop`); the `<video>`s persist (single-room page, no room-change teardown needed).
Inline script parses (`node --check`); page 200s and the nest `/sfile` video serves 200. **Verified as far as
headless allows — pending Lucas's visual confirm** on the airship/nest "wrap" chip (hard-refresh after open).
Not (yet) ported: door-open / variant states in the wrap preview (the still is the raw `scene.png`, not the
composited base) — offered as a follow-up, not built. **#2 hub-and-spoke:** now planned in its own intent
doc, `notes/hub_and_spoke_plan.md` (built through Phase 2b + planned-arm/retain; 2c pending).

## `ambient` hotspot type — cinemagraph-only, no player marker (2026-08-02)

New hotspot **type `ambient`**: decoration that carries a cinemagraph but shows **no player marker/ring and
isn't clickable** — pure ambient animation. The engine already treats types with positive filters (unknown
types are inert to gating/codec/doors), so the only runtime change is in `shared/pano-player.js` `_renderViewer`:
the marker list now `.filter(h => h.type !== "ambient")`. `activeCinemagraphs` scans `hotspot.cinemagraph`
**independent of markers**, so an ambient hotspot's clip still composites. Cache bumped `pano-player.js?v=65→66`
(all 5 `play.html`). Authoring: `ambient` added to `TYPES` in both `reproject_test.html` (hub) and
`hotspots_edit.html`; the hub Content tab shows a "decoration only — no player marker; animate on the
Cinemagraph tab" hint and draws ambient markers/boxes **ghosted (dashed)** in authoring (still selectable — you
edit them; only the *player* hides them). 41 node tests green after the pano-player change; e2e (Playwright)
not run (needs browser+servers) — worth an in-game check that an ambient hotspot animates with no ring.

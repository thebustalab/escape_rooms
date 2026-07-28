---
authority: history
---

# Escape Rooms — Design History (archived 2026-07-15)

**ARCHIVED — read for the *reasoning*, not for what's current.** This is the full
design-evolution log: hub-and-spoke → chain-of-case-rooms pivot → gpt-image-2 pseudo-360
pano → the playable pano chapter, plus the deleted DiT360 / SD-360 true-360 saga. Its
settled decisions have graduated into `../AGENTS.md` and the per-folder `AGENTS.md` /
`notes.md` files; the still-open items are in `../AGENTS.md` → "Known follow-ups". History
tier — do not edit. (Original heading: "Hub-and-Spoke + Explorable-Map Design Notes"; that
model was superseded early — see "SETTLED MODEL — chain of case-rooms".)

## Why we're changing it

The current rooms work — they run real R in the browser, gate answers behind
multiple-choice steps, record attempts, and mint a per-student submission code. The
pedagogical driver is sound: it speed-bumps AI-assisted cheating (a real problem
last semester) because the answers are the *product of running the analysis*, and it
warns on paste. But the interaction is a linear conveyor belt of questions, which
badly undersells the "escape room" concept. Lucas's actual vision has never been
written down anywhere until now:

- An **atmospheric, gamified space** — "mist and ribbon" — that students move around
  in and explore, rather than a stepped panel they click through.
- A **multifurcating path** of sub-problems that fans out and then **converges** on a
  final challenge.
- **Escalating complexity across the course**: each chapter's room gets richer as
  students accumulate techniques. The side-paths exercise techniques they already
  know; the "final boss" is the *new* technique for that chapter.

## Decisions taken

### Structure: hub-and-spoke (not true branching)

True branching — where a choice sends the student into genuinely different content —
authors combinatorially and gets exponentially worse as rooms grow. We're **not**
doing that. Instead: **hub-and-spoke**. Several independent sub-puzzles ("spokes")
sit open in the space, each exercising one technique, solvable in any order. Solving
enough of them unlocks the **boss** node. Every student ultimately touches the same
node set — they just walk their own route through it. This delivers the *feel* of
exploration and convergence without the authoring blow-up, and it's a natural home
for **spaced retrieval practice**: spokes review prior chapters' techniques, the boss
requires this chapter's new one.

- **Boss gate:** "solve N of the M spokes to unlock the boss" (N tunable per
  scenario), so there's genuine optionality and freedom to explore, not a forced
  sweep of every node.
- **Node states:** hidden-in-mist / available / solved. Solving a spoke clears more
  of the map and reveals adjacent nodes and hints toward the boss.
- **Escalation is pure authoring.** The engine is generic; growing a chapter's room
  from 2 spokes to 8 is just more nodes in that scenario's data file. The ambition is
  front-loaded into building the map system **once**; every subsequent chapter room is
  content only.

### The three layers (design independently)

1. **Interaction structure** — the puzzle graph (the load-bearing change).
2. **Content-escalation model** — the rule for populating a chapter's room (old
   techniques → spokes, new technique → boss).
3. **Atmosphere / art** — the mist, the ribbon, the explorable map (the skin).

### Codec implication — good news

The current submission code is fixed-length: one byte per step, same steps for
everyone. True branching would break that (you'd have to encode *which* path was
walked, forcing a rewrite of both `codec.js` and `decode_codes.R`). Hub-and-spoke
with a **known, fixed node set** still fits the existing scheme almost unchanged —
one byte per node (chosen answer + attempts), plus a solved/attempted bit. The
pedagogy we want and the codec we already have happen to agree. Keep the JS/R codec
contract in sync (see `AGENTS.md` → "The codec contract").

### Art is generated at *authoring* time, not runtime

Critical constraint: **no live image generation in the student's browser.** That
would drag an API key client-side — exactly what ruled out the embeddings exercises.
Instead we generate the atmospheric backgrounds and node illustrations **once, on
Lucas's machine, at authoring time**, and ship them as ordinary static image files.
The browser just displays them and animates the mist over the top. Consequences:
cost is trivial (a scenario's ~10–20 images ≈ a couple of dollars), no key exposure,
stays pure WebR. The mist/fog itself is plain canvas/SVG — a fog layer that clears in
a radius around each node as it unlocks or is solved; no service needed for that, only
for the art underneath.

## Image generation — research & recommendation (2026-07-14)

Need: API-driven, **style-consistent** batch generation of a scenario's illustration
set, easy to plug into an authoring script on the box. State of the field:

- **OpenAI GPT Image 2** (released Apr 2026) — **recommended primary.** Best-in-class
  prompt adherence on multi-part prompts, accurate in-image **text rendering** (useful
  if we bake labels/signage into art), and — decisively for us — it can generate **up
  to 8 style-consistent images in one call** and accepts **up to 16 reference images**
  to lock a house style. Dead-simple `images.generate` / `images.edit` API. ~\$0.05/
  image (medium), ~\$0.21 (high). Easiest integration + strongest consistency story.
- **Google Gemini native image models** ("Nano Banana Pro" `gemini-3-pro-image-preview`
  ~\$0.134/img; Nano Banana 2 ~\$0.045/img) — strong alternative, clean Gemini API.
  Note: **Imagen 4 is deprecated (shutdown 2026-08-17)** → if we go Google, use the
  Gemini native image models, not Imagen 4. Slight churn risk against "set and forget."
- **Leonardo AI / Ideogram** — nice reference-based character-consistency APIs
  (`@mention` a saved Element); worth knowing if consistency ever fights us.
- **FLUX.2 / open-weight (NVIDIA Cosmos, Stable Diffusion 3.5)** — self-host is heavy;
  not worth it for a low-volume authoring-time job.
- **Midjourney v7** — great images, but no clean official API / ToS friction; skip for
  a programmatic pipeline.

**Pick: GPT Image 2**, for easiest integration + native style-consistent set
generation + strong prompt adherence. Cost at authoring volume is negligible.

**Credential handling (standing repo policy):** an OpenAI API key is a *new*
credential. Store it on the box only (bash scope), authoring-time only, **never**
client-side. If it lands in a file, pair it with a `permissions.deny` entry in the
same change (per root `AGENTS.md` → credential-class standing policy).

## Canvas / WebR / the boss figure (2026-07-14 decision)

Preserve what worked in the *old* workflow — Lucas gives written feedback on a
**figure** each student produces — by making the **boss a figure task**, manually
graded, while the **spokes stay auto-graded multiple-choice**. Clean division of
labour:

- **Spokes** → machine-checkable MC, attempts recorded, folded into the submission
  code, auto-graded by the R decoder. The retrieval-practice / AI-speed-bump layer.
- **Boss** → the student applies the chapter's **new technique** to produce a
  **figure** in the WebR console, downloads it as a PNG, and uploads it to Canvas.
  Lucas grades it by hand with feedback — the pedagogically valuable part he wants to
  keep. The figure *is* the evidence the new technique was actually used.

**Integrity link:** watermark the downloaded figure with the student's **x500 + the
submission code**, so the manually-graded figure ties back to the auto-graded spoke
record. Lucas grades the figure and can glance at the embedded code to confirm the
spokes were genuinely worked — and that the figure belongs to this student.

**Canvas mechanics:** one assignment per room, taking **two artefacts** — the
submission **code** (text entry / comment) and the **figure** (file upload). Canvas
supports text-entry + file-upload together; confirm the exact submission-type setup
when we wire a real assignment.

**Enabling tech:** WebR already renders plots to a canvas (`webr-console.js`); a later
phase adds a **"Download your figure"** button that exports that canvas to PNG with
the watermark baked in. No server needed.

## Phase-1 data schema (locked)

`scenario.js` grows from a flat `steps` array to a node graph:

```js
window.SCENARIO = {
  id: 1,
  version: 1,
  // ... story / screen1 / datasets / packages / starterCode as today ...
  nodes: [
    { key: "s1", type: "spoke", technique: "datavis",
      title, prompt, options: [...], answer: idx, maxAttempts, feedback: [...] },
    { key: "s2", type: "spoke", technique: "wrangling", /* ... */ },
    // ... more spokes exercising PRIOR chapters' techniques ...
    { key: "boss", type: "boss", technique: "clustering",   // THIS chapter's new one
      title, brief,
      figureSpec: "what the figure must show",
      // no MC answer — produces a downloadable, watermarked figure, graded by hand
    },
  ],
  bossGate: { requires: 2 },   // solve N spokes to unlock the boss
};
```

**Codec impact is minimal** (nice surprise): spokes serialize in scenario-defined
order exactly like today's steps — one byte each (answer idx + attempts) — plus one
header bit for "boss figure downloaded". The boss figure's *grade* lives outside the
code (manual). The order a student *solves* nodes in doesn't affect the code, because
we always serialize in canonical node order. So `codec.js` / `decode_codes.R` barely
change; the real Phase-1 work is in `escape-engine.js` (graph render, node states,
the gate).

## Status

- **Phase 1 — BUILT & signed off (2026-07-14).** Graph engine mode, codec
  extension, decoder, and a trial room all in place and verified live.
  - `shared/escape-engine.js` now runs two modes: **linear** (`S.steps`, Alaska —
    untouched, still works) and **graph** (`S.nodes` hub-and-spoke). Spokes open
    from the start, tackled in any order; boss locked until `bossGate.requires`
    spokes are *resolved* (solved or attempts-exhausted — "resolved" not "solved"
    is used for the gate to avoid soft-locking a stuck student).
  - Codec change was minimal, as predicted: `attempts = 0` now means "skipped
    node"; a trailing **boss byte** records figure-produced. Mirrored in
    `codec.js` + `decode_codes.R`; R self-test green (linear + 10-step long-code +
    new graph round-trip with skipped spoke + boss byte → 17 pts).
  - Grading: `grade_graph()` + `DEMO_KEY` in `decode_codes.R`.
  - Trial room: `demo_hub/` ("The Noatak Dossier", scenario id 2) — 3 spokes
    reuse the Alaska questions (known key 18/3/1) + a boss figure task, gate 2-of-3.
    Placeholder node-button visuals (borrows `../alaska/style.css`); the real map
    is Phase 2.
  - **Live end-to-end proof:** browser-minted code `CMV5-1S46-D0` (x500 `bust0037`)
    decoded in R → solved leads 1 & 2, skipped lead 3, gate opened boss,
    boss_reached, 17 pts; wrong-x500 decode rejected. JS-encode == R-decode on a
    real browser run.
- **Phase 2 — BUILT & signed off (2026-07-14).** The button list is now the
  explorable mist map.
  - New `shared/map-view.js` (`MapView` class): spatial layout (boss centre,
    spokes in an auto ring; per-node `pos:{x,y}` % override), a **canvas
    fog-of-war** that clears around each node by animated clarity, **ribbons**
    (SVG) drawing from each resolved spoke toward the boss, and the boss
    **emerging from the mist + pulsing** when the gate opens. `pointer-events:
    none` on fog/ribbon layers so clicks reach the node markers.
    `ResizeObserver` keeps the canvas crisp.
  - Engine graph mode rewired to drive `MapView`; node detail opens as an
    **overlay** over the map; spoke cards are **cached per node** so leaving and
    returning to a lead preserves the attempt counter (no reopen-to-reset).
  - Verified live: browser code `CMV1-7HC6-XG` (bust0037) → 20 pts, boss reached.
    Alaska (linear) unaffected. Codec unchanged in Phase 2.
- **Phase 3 — NOT started, and its SCOPE CHANGED (see below).** Lucas's Phase 2
  feedback: the map reads as *a map*, not *a navigable, realistic space* — that
  spatial-place feel is what he actually wants from Phase 3, not just generated
  art laid under the current top-down node map.
- **Boss figure download + x500/code watermark — not built** (boss is a
  placeholder "record it & finish" button for now). Folds into Phase 3.

## Phase 3 — the navigation-ambition fork (open decision, 2026-07-14)

Original Phase 3 = "generate atmospheric art, lay it under the node map." Lucas
wants more: a *place you move through and encounter problems in*, not a decorated
diagram. That's a genuine fork on how far to push navigability. Options, cheapest
→ most ambitious (all keep the same puzzle guts underneath — spokes + gated boss
figure — only the *shell* changes):

1. **Art-backed map** (original plan). Generated background under today's node
   map; markers become illustrated objects. Cheapest; still reads as a map.
2. **Point-and-click illustrated scene** (Myst / adventure-game feel). One wide
   generated scene of the S&R station / Noatak; nodes become clickable *objects*
   (the wall map, the radio, the laptop). Fog → "unexplored/dim" regions.
   Feels like a place; still 2D; image-gen is exactly the right tool. **Likely
   sweet spot.**
3. **Multi-viewpoint / 360° panorama** (look around, click to move between
   pre-rendered viewpoints; Pannellum/Marzipano for panos). Genuinely spatial,
   no 3D engine. More authoring (several scenes + connectivity), medium effort.
4. **Real 3D first-person** (Three.js/WebGL, walkable). The fullest "realistic
   navigable space" — but image-gen does **not** produce navigable 3D geometry
   (you'd need modelled scenes / Gaussian splats / NeRF), plus controls,
   collision, big maintenance. Overkill for a low-stakes R assignment.

**Two hard selection criteria:** (a) **escalation must stay pure authoring** — a
new chapter's room should be data + a few generated images, not a bespoke build,
which rules 4 out and cautions on 3; (b) **navigation must not fight the
pedagogy** — the point is R analysis + a figure; keep movement light so it serves
engagement rather than becoming a game-dev project. Recommendation leaning to
**2, optionally borrowing 3's "look around" for key scenes.** Needs the OpenAI
key wired (authoring-time only) before any art work.

## SETTLED MODEL — chain of case-rooms (2026-07-14, supersedes hub/gate)

After reading the real problem bank (`teaching/CHEM5725/exercises.csv`) with Lucas,
the model settled and **pivoted away from the hub + N-of-M gate**:

- A chapter's escape room is a **chain of case-rooms → a boss figure at the end.**
  Rooms are worked **in order**; solving a room's multiple-choice (the product of
  the analysis) is the **key that opens the door to the next room**.
- **Each room = one narrative case** with its **own scene** (own generated image),
  dataset, and analysis. The cases in a chapter are unrelated worlds, so a
  **framing device** ("an analyst working a stack of field case-files, stepping
  into each") justifies the room-to-room jumps.
- **Rooms grow with the course:** later chapters have more rooms and lean on
  **earlier chapters' techniques**; the boss is the chapter's newest technique +
  the **figure deliverable** (manually graded). Intermediate rooms are MC-locked
  doors (auto-graded). Escalation stays pure authoring — just list more rooms.
- **Figure at the end only** (default) — matches "leading to the boss/figure at
  the end." Knob: could add a figure per room to mirror the current per-problem
  grading, at more grading cost.
- **Replay / practice branches** (parked): each room may offer optional low-stakes
  practice variants (same technique, different/randomised data) to drill on;
  don't affect progression.
- **Content pipeline:** `teaching/CHEM5725/exercises.csv` holds ~9 technique sets
  × 2 narrative cases (each already with MC answer, solution code, and Midjourney
  scene art). `teaching/CHEM5725/problem_sets.md` holds Lucas's **authoring
  templates** (simplify-language, brainstorm hard MC, backstory, image-prompt) —
  the recipe for generating new case-rooms at scale.
- **WebR reality-check:** embeddings (live PubMed/HF API keys) and hierarchical
  clustering (`ggtree`, no wasm) don't run client-side as written — deferred
  ("sort ggtree when we get there").

### Engine: JOURNEY mode — BUILT (2026-07-14, browser-unverified)

- `escape-engine.js` now has a **third mode**, `flow: "journey"` (alongside linear
  and hub/graph, both untouched): ordered `nodes`, each with its own `scene`,
  `intro`, and per-room `starterCode`; solving a room reveals a glowing **door**
  onward; the last room is the boss figure. Encodes as spokes-in-order + boss byte
  — codec unchanged. `makeBossCard(node, onRecord)` now takes a finish callback so
  journey and hub reuse it.
- **Art authoring:** `authoring/generate_scene.py` (reads `OPENAI_API_KEY` from env
  only — never in repo, never client-side; run via a login shell) + prompts under
  `authoring/prompts/`. `gpt-image-2`, ~4¢/scene at 1536×1024 medium.
- **Trial room:** `datavis1/` (scenario id 3) — the Data Visualization chapter as a
  2-room chain (Alaska lakes → Hawai‘i aquifers) → boss figure, each room its own
  generated scene. Decoder key `DATAVIS1_KEY`; journey round-trip in the R
  self-test (17 pts, boss reached). **Awaiting Lucas's live browser sign-off.**
- Note: Hawai‘i `correct` index is from the sheet (1-based 3 → 0-based 2); confirm
  against the real answer key.

### Engine: EXPLORE mode — pannable multi-room (2026-07-14, browser-unverified)

Lucas's next ask: a *case* should be **several rooms**, each a navigable space, not
one scene. Built as a fourth engine mode, `flow: "explore"`:

- Schema: `rooms[]`, each with `views[]` (images you pan between with ‹ › arrows,
  looping) and `artifacts[]` placed on views — `type:"clue"` (flavour/hint text)
  or `type:"question"` (the room's one real MC). Solving a room's question opens a
  **door onward**; the last room ends the case. Encodes one answer per room + a
  reserved trailing byte (no boss figure in this prototype).
- Per Lucas's spec: **3 rooms, each 3 view-images, 2 artifacts per room (1 clue +
  1 question)**. Artifact `pos` are %-coords on the view; currently centred
  defaults — nudge onto the objects once the art is in.
- Trial room: `alaska_station/` (scenario id 4). Art = 9 views generated as a batch
  via `authoring/generate_scene.py genset --manifest
  authoring/prompts/alaska_station_set.json` (3 facings per room, shared style
  preamble; not seamless panoramas — discrete "look around" facings, the
  achievable/right interpretation). Decoder key `ALASKA_STATION_KEY`.
- **Deliberately no R problems yet** — this is a navigation prototype (Lucas: get
  the room/pan/artifact structure right first, wire the real R problems after).
- Style consistency across a room's 3 views currently relies on prompt discipline;
  can improve later with reference-image conditioning (gpt-image-2 takes up to 16
  refs).
- **Full-screen + console-in-pop-up (2026-07-15, Lucas's refinement):** the scene
  fills the viewport; the R console is no longer a persistent left panel — it's a
  single live widget parked in a hidden `#console-holder` and **relocated into the
  question pop-up** (`mountConsole`/`unmountConsole` move the DOM node, preserving
  the booted WebR session + wiring). Clicking the amber (question) orb pops up a
  modal with the console beside the multiple-choice; clue orbs pop up just text.
  WebR still boots once at entry. Note: hotspot `pos` may need re-nudging for the
  full-screen crop (background `cover`).
- **Awaiting Lucas's live browser sign-off.**

### 360 generation harness (DiT360/FLUX, 2026-07-15)

- **Model:** FLUX.1-dev + DiT360 LoRA (equirectangular 360), run locally on the
  GV100. Benchmarked ~2 min 20 s per 2048×1024 image, ~25 GB VRAM (fp16 + CPU
  offload). Env: conda `dit360b` (clone of base + torch 2.5.1cu121 + diffusers-git
  + peft/accelerate; torchaudio removed). Weights gated — the HF account accepted
  the FLUX.1-dev licence.
- **Harness** in `~/dit360_bench/` (outside the repo): `harness.py` (config-driven
  generator, writes `scene/runs.json` manifest + `scene/progress.json`), `jobs.json`
  (editable batch spec: defaults + per-job lever overrides), `run.sh` (frees the
  GPU → generates → **always restores the servers via an EXIT trap**),
  `harness_server.py` (tiny localhost server on :8751 behind the interactive UI).
- **Interactive UI:** `alaska_pano/harness_ui.html` (served by harness_server on
  :8751) — sliders for #seeds / #prompt-variants / steps / guidance, seed-then-
  prompt picking, live progress bar. `gallery.html` reads `runs.json`; `view360.html`
  (Pannellum, ?img= param) is the reprojection viewer. **Prefer driving generation
  through the UI** (its run.sh runs under the persistent tmux `harness_ui` server,
  so it survives `--resume` session boundaries — a Bash-launched `run.sh` got
  reaped mid-run and orphaned `harness.py`, deadlocking against a restarted
  lm_server; the tmux path avoids that).
- **Per-step progress:** harness.py passes `callback_on_step_end` → writes
  `progress.json` per denoising step (`img`/`step`/`steps`); the UI bar advances
  smoothly (`Image X of N · step Y/28`).
- **LLM prompt-variant suggestions:** phase-2 "🪄 Suggest variants with Claude"
  → `POST /api/suggest` → Claude Haiku (via `AAPI`) writes N varied FLUX prompts
  from the phase-1 prompt, fills the editable boxes. Chosen over local Gemma: image
  gen stays fully local, only the trivial text task is cloud (~free, better
  prompts, no GPU juggling). The "unload FLUX → load Gemma → reload" dance is
  unnecessary — a pure-local variant would just call lm_server's Gemma in the
  window *before* FLUX loads (one-line swap).
- **Funnel (harness_ui):** seed sweep → prompt variants (Claude suggest) →
  **guidance sweep** → **final high-step render** → **open-door variant** (5 stages,
  each unlocks the next on pick). Default guidance = 2. Scout low-steps, render
  final high-steps. Server returns exact filenames (`enrich()`) so the client never
  reproduces the slug.
- **Inspiration image → prompt:** `POST /api/caption` → Claude *vision* (Haiku, via
  AAPI) writes a 360 FLUX prompt from an uploaded reference's vibe. Chosen over
  img2img because DiT360 is text-to-2:1-equirect only; a flat photo can't img2img
  into a 360.
- **Open-door variant = local FLUX inpainting** (`inpaint.py`, `FluxInpaintPipeline`
  on the cached FLUX.1-dev — no new model). UI: draw a box on the final image →
  `POST /api/inpaint` → inpaint only that box; **composite the original back outside
  a feathered mask so every non-door pixel is byte-identical** (needed so all
  non-door facings match between closed/open). Regenerating at the same seed with an
  "open door" prompt does NOT work (whole room drifts). `run.sh` generalised to
  `run.sh <script.py> <job.json>` (harness.py or inpaint.py); `run_active()` matches
  both. **The GPU inpaint run itself is browser-unverified — first live test pending.**
- **Levers (see `authoring/PROMPTING.md`):** mush is **seed-driven**, not
  prompt-complexity-driven. Steps sweet spot 28 (50 ≈ 28). Guidance 2.8–3.8 (DiT360
  default 2.8). FLUX wants natural-language, front-loaded prompts (CLIP truncates at
  77 tokens); drop quality-tag filler; prefix "This is a panorama." Workflow: sweep
  seeds → lock the best seed → refine prompt → upscale last.
- **`pgrep -f` footgun:** a pattern that also appears in the *current shell command*
  matches that shell — `pkill -f "harness.py …"` self-signals (exit 144). Kill by
  PID or use the `[h]arness` bracket trick; the server's `run_active()` matches the
  specific `harness\.py [^ ]*\.json` to avoid false positives.

### Live canvas panorama + tuner (2026-07-15)

- **Tuner:** `alaska_pano/tune.html` — loads the full panorama and does the
  slice/crop/zoom/blur live on a canvas with sliders (overlap, crop-height, zoom,
  blur, facings, ‹ › pan, door-open toggle) + a readout / "copy bake command".
  Use it to find values, then bake into the scenario config.
- **Engine now renders pano rooms live on a canvas** (not pre-sliced PNGs): a room
  with `panorama` + `panoramaOpen` + `facings` + `doorFacing` + `slice:{overlap,
  cropHeight}` + `blur` + `actions:{<facing>:{…}}` is drawn by `drawPanoFacing`
  (shared math with the tuner). Advantages: continuous blurred sides, live-correct
  at any window size, and "baking" tuned values = editing config numbers (no
  re-slice). The old sliced-PNG `views` path is still supported (alaska_station).
- **Continuous blur fix (Lucas):** the blurred sides are now the SAME panorama at
  the SAME scale, shifted to align with the sharp facing — so the sides are the
  real neighbouring room continuing outward, just blurred (a cover-blur base still
  fills the outer edge of the end facings, which have no neighbour). Replaces the
  old mismatched cover-zoom fill.
- `alaska_pano` room 1 now uses this (overlap 150, crop-height 920, blur 30,
  contain); room 2 stays a simple sliced-PNG room. The pre-sliced desk/bulletin/
  kitchen/door PNGs are now unused by room 1 (kept, harmless).

### Panorama room + door mechanic (2026-07-15, Lucas's design)

Lucas's refinement: build a room as ONE cohesive panorama, sliced into 4 facings,
with a door facing that opens on solve.

- **Art pipeline** (`authoring/generate_scene.py`, now with `slice` + `edit`):
  generate a wide 1536×1024 panorama (`gen`), `slice` it into 4 equal vertical
  facings (desk / bulletin / kitchen / door_closed, 384×1024 each), then `edit`
  the WHOLE panorama with an "open the door" prompt and slice the door quarter as
  `door_open` (editing the whole image keeps the door quarter dimensionally
  aligned with the closed one). `edit` uses `POST /v1/images/edits` (multipart via
  `requests`). The door-open edit came out cleanly consistent (same lantern/frame,
  door now open onto a room beyond).
- **Engine** (`flow: "explore"`, extended): a view may be `{door:true, openImage}`
  and/or carry a single `action:{type:"question"|"clue", label, …}` (a labelled
  button per facing — avoids per-object hotspot placement, which the full-screen
  crop made fiddly). On solve, the door facing's background swaps to `openImage`
  and a **"^ Go through"** button appears **on that facing** (student pans to it);
  door-less rooms fall back to a generic advance button. Tall slices are shown
  `contain` over a blurred `cover` `.pano-fill` so they letterbox nicely.
- **Trial:** `alaska_pano/` (scenario id 5) — a 4-facing cabin panorama (room 1,
  MC on the desk) → through the door → a second room (reused interior, MC on the
  radio) → finish. Decoder key `ALASKA_PANO_KEY`. Aspect caveat: 4-way slice of a
  1536-wide image = portrait facings; the blurred-fill letterbox is the mitigation.
- **Overlap + crop + cover refinement (2026-07-15):** `slice` now takes `--overlap`
  (facings share content — you glimpse the next area from each view, cohesion) and
  `--crop-height` (trim to a centred band so facings are less portrait). Re-sliced
  the cabin at `--overlap 300 --crop-height 640` → facings ~534–684×640, and switched
  `.pano-bg` to `background-size: cover` so they zoom to fill with minimal blurred
  edges (slight res loss, accepted). `.pano-fill` kept as a fallback.
- **Awaiting Lucas's live browser sign-off.**

## Scene 360: DECISION — gpt-image-2 wrapped as pseudo-360 (2026-07-15)

**Settled after testing every realistic route: keep the gpt-image-2 image and wrap
it as a pseudo-360 in Pannellum.** Lucas preferred the gpt look over every true-360
generator we could produce. True equirectangular is **abandoned** — not for lack of
trying, but because nothing beat the gpt-2 image quality. Forward work is **fine-tuning
the wrap + resolution of the gpt-2 image**, not chasing true 360.

**What "pseudo-360" means:** feed the single wide gpt-image-2 shot to Pannellum with a
partial-coverage `haov`/`vaov` (Lucas liked **360 h / 135 v / 70 fov**). Pannellum
treats it as if it covers that angular range and lets you drag/spin around it. It is
**not** geometrically true 360 (no real back wall, poles are approximated), but it
reads as immersive and preserves the gpt look. Tester: `reproject_test.html`.

**Everything tried, and why each was set aside** (so nobody re-litigates this):

| Route | What it is | Verdict |
|---|---|---|
| **gpt-image-2 wrapped (CHOSEN)** | wide gpt shot in Pannellum at haov/vaov 360/135/70 | best *look*; Lucas prefers it. Not true 360 but good enough. |
| DiT360 | FLUX.1-dev LoRA, native equirect 2048×1024, local (`~/dit360_bench`, `harness_ui.html`) | true 360, "only moderately happy" |
| Path 1: reproject + outpaint gpt shot to full 360 | outpaint the sides/back | REJECTED — outpainting "adds stuff: more doors, windows"; stories need control of exits |
| Path 2: SD-T2I-360PanoImage / Diffusion360 (`~/sd360/`) | image→equirect, prompt-steered outpaint | BUILT & ran (env + models work, `i2p_run.py`, true 1024×512 equirect) — **rejected on quality** (soft, low-res) |
| Blockade Labs **Skybox AI** (hosted API, true equirect) | text/image→360, only turnkey 360 API | Lucas tried it on their website — "okay at best," worse than gpt-2 wrap |
| OpenAI gpt-image-2 / Google Imagen / Midjourney *for true 360* | — | dead end: none output geometrically-true, seam-correct equirect |

**True-360 tooling is kept, not deleted** (`~/dit360_bench`, `~/sd360`, their envs +
models) in case we revisit, but it's off the critical path.

### Fine-tuning the gpt-2 wrap (the actual forward worklist)

gpt-image-2 maxes at **1536×1024**, so angular resolution is the main limit — zoom in
and it softens. Levers to tune:

1. **Coverage** — freeze `haov`/`vaov`/default `hfov` (start 360/135/70) as the viewer
   defaults so every scene wraps consistently. `vOffset`/`pitch` to frame the horizon.
2. **Resolution** — upscale the gpt shot **before** wrapping so it stays sharp when
   zoomed. Real-ESRGAN is already installed in the `sd360` env (`RealESRGAN_x2plus`);
   a 2× pass on a 1536×1024 gpt image → 3072×2048 before Pannellum. Test whether the
   upscaler's invented detail is acceptable (it was *not*, for SD-360's SR — judge
   separately here since the input is a clean gpt image, not a diffusion latent).
3. **Default hfov** — cap zoom-in so students don't push past where it blurs.
4. **Prompt** — the canonical cabin prompt lives in
   `authoring/prompts/gpt_compare_set.json`; five renders at `scene/gpt_test_1..5.png`.
   Regenerate variants via `authoring/generate_scene.py` (gpt-image-2, `OPENAI_API_KEY`
   env-only).

### gpt authoring harness — BUILT, true-360 tooling deleted (2026-07-15)

Lucas: "truly we can delete the old dit360 stuff … let's commit to GPT, it's really
much better." So the DiT360 tuning funnel was replaced with a lightweight **gpt-image-2
harness** and the true-360 tooling was **deleted** (no longer "kept on disk").

- **New server: `authoring/harness_server.py`** — moved *in-repo* (was `~/dit360_bench/`),
  still :8751, still under the `harness_ui` tmux session. gpt-image-2 is a cloud API and
  Real-ESRGAN is light, so it carries **none** of the old GPU-eviction / `run.sh` / conda
  machinery — it just shells out to the authoring scripts and reports progress via an
  in-process polled job. Endpoints: `/api/generate` (N candidates → `scene/gpt_gen_NNN.png`),
  `/api/suggest` (Claude Haiku variants), `/api/save-wrap` (→ `scene/wrap.json`),
  `/api/save-hotspots` (→ `scene/hotspots.json`), `/api/scenes`, `/api/status`.
- **New UI: `alaska_pano/harness_gpt.html`** — funnel: generate → pick base → wrap &
  freeze defaults → hotspots. Prefilled with the canonical cabin prompt.
- **Upscale: built, tested, DROPPED.** A Real-ESRGAN 2× stage was wired and proven
  end-to-end (`gpt_test_1.png` 1536×1024 → 3072×2048, MKL threading-layer clash fixed
  with `MKL_THREADING_LAYER=GNU`), but Lucas compared the 2× against the original and
  **preferred the originals** — so `upscale.py`, `/api/upscale`, and the UI stage were
  removed. The `sd360` env + `RealESRGAN_x2plus.pth` (~5.5 GB) are now **orphaned**,
  purgeable on Lucas's word.
- **Deleted (~53 GB total):** `~/dit360_bench/`, the SD-360 diffusion models, conda envs
  `dit360` + `dit360b`, and the gated FLUX.1-dev HF cache (~32 GB, purged on Lucas's OK).
- **Hotspot authoring — BUILT (2026-07-15).** Box-draw over the flat gpt image →
  label/action/target per box → `/api/save-hotspots` → `scene/hotspots.json`. First built
  as a standalone `hotspots.html`, then **folded inline into `harness_gpt.html` stage 4**
  (Lucas: one authoring surface, only the wrap tester pops out; the viewer link was
  dropped). `view360.html` rewritten to read `wrap.json` + `hotspots.json`,
  map each box centre → yaw/pitch, and drop pulsing clickable hotspots (modal for
  puzzle/note/clue, panorama swap for `swap`). Verified: save round-trips (2-hotspot demo
  on `gpt_test_1`), all pages 200, geometry sane (laptop → yaw 0°/pitch −12°).
- **Verified live:** server serves all pages; `/api/save-hotspots` + `/api/save-wrap`
  round-trip. `/api/generate` is wired but not yet run (base not picked). Still open: the
  wiring `puzzle` hotspots to real WebR MC (currently a placeholder modal). [The `swap`
  open-door target was BUILT later this session — see the door-open bullet below.]
- **Iteration after Lucas's testing (2026-07-15):**
  - **Wrap workflow moved into the tester.** `reproject_test.html` is now the tuner AND
    saver — drag to frame (pitch captured), sliders for haov/vaov/hfov/vOffset, "Save
    params for this image". `wrap.json` became a **per-image map** so each candidate keeps
    its own params; harness stage 3 dropped "Save as defaults" for "⟳ Load saved params".
  - **Bug fixes:** (1) blank viewer — a saved `vOffset:130` (valid range only ±~22° at
    vaov 135) blanked Pannellum; now clamped to ±(180−vaov)/2 and hfov to 40–120 in BOTH
    the tester's save and the viewer's read. (2) hotspot fields ate text mid-type — the
    card's click-select rebuilt the list and destroyed the focused input; fixed by
    guarding the select against input/select/button clicks and switching fields to live
    `oninput` that refreshes only the box overlay, never the list.
  - **Hotspot editor folded inline** into `harness_gpt.html` stage 4 (was a `hotspots.html`
    pop-out; deleted). Only the wrap tester pops out now.
  - **Wide-panorama — native size.** First tried cropping a 1536×1024 shot, but a probe
    showed **gpt-image-2 accepts custom sizes** (1536×576 renders directly, gpt composing a
    cohesive wide room — the "three fixed sizes / max 1536×1024" belief was gpt-image-1's,
    now corrected). So the crop was reverted: the harness "wide panorama" toggle (default on,
    height 576) generates **natively at 1536×H** — Lucas's "I want the generated image to be
    1536×576" so gpt fills the wide frame. Wide rooms wrap with much less vertical stretch;
    `vaov ≈ 360 × H ÷ 1536` (576→135, the default wrap). Generate-height default later set to
    **512**; wrap-tester defaults set to **vaov 95 / hfov 120 / vOffset −5 / step 40**
    (mirrored in the viewer + hotspot-editor fallbacks).
  - **Door-open swap target — BUILT.** gpt-image-2 accepts an image+mask **edit** (masked
    inpaint), so `generate_scene.py dooropen --input --box --prompt` masks just the door box,
    edits "door open," and composites the result back through a feathered box so **every
    non-door pixel is identical** between closed/open (the guarantee the abandoned FLUX
    inpaint gave). Wired end-to-end: a `swap` hotspot in the editor shows a "Generate
    open-door image" button + editable prompt, reusing its box → `/api/dooropen` →
    `scene/<img>_open.png` → auto-set as the hotspot target; the viewer's `swap` flips the
    panorama on solve. Verified live on `gpt_test_4` (door → dim room beyond, rest untouched).
  - **Playable chapter — room 1 BUILT & signed off (2026-07-15).** `alaska_pano/play.html` +
    `chapter_alaska.js`: the pseudo-360 rooms are now a playable, gated chain. Room 1 of the
    Alaska `filter()` chapter runs end-to-end on `gpt_gen_5`(+`_open`): click the laptop →
    WebR editor (`filter(park == "NOAT")` → 55) + MC gate → correct answer swaps to the
    open-door panorama and the door advances. Settled model: 3 `filter()` rooms (single →
    multi-condition → +a basic plot) then a **boss** (the helipad) = a figure +
    `buildCaption()` deliverable, downloaded and uploaded to Canvas. Separate flow from
    `escape-engine.js`; reuses `webr-console.js`; codec not yet wired. Three Pannellum
    gotchas cost a round each — see `alaska_pano/AGENTS.md` → "Playable chapter". Other
    agents are authoring rooms 2–4 in this directory (four-column harness).
  - **Room-directory convention + harness "Send to room" (2026-07-15).** Rooms are moving
    to per-room directories under a chapter (`data_vis/<case>/<roomN>/`), each **self-contained
    and stable-named**: `scene.png` (closed) + `scene_open.png` (open door — kept together,
    corresponding) + `wrap.json` + `hotspots.json` (both re-keyed to `scene.png`). The harness
    produces this via **`POST /api/commit-room {image, roomDir}`** (a "Send to room" control):
    it copies the chosen `scene/` candidate + its `_open` partner into `<escape_rooms>/<roomDir>/`
    under those stable names and carries that image's wrap + hotspots. This decouples the
    playable rooms from the churny `gpt_<tag>_NNN` candidate names, and keeps every closed/open
    door pair matched. `roomDir` is confined to the `escape_rooms/` tree (traversal rejected).
    Migration target: move the Alaska room into `data_vis/` too, and lift room-universal bits
    (e.g. the Pannellum gotchas) up to `escape_rooms/`-level docs.

### Clickable hotspots — authoring harness (agreed approach #1)

Pin **clickable hotspots to real objects** (laptop, door, map, stove, cork board)
that survive panning. **The wrap decision does NOT cost us this** — Pannellum maps
pixels to angles **linearly across whatever `haov`/`vaov` we set**, so a box drawn on
the flat gpt image still converts to viewer coords with no calibration. Just use the
chosen coverage (360/135) as the mapping range instead of a full 360/180:

```
yaw   = (x / width)  * HAOV - HAOV/2          # e.g. HAOV=360 -> -180..180
pitch = VAOV/2 - (y / height) * VAOV          # e.g. VAOV=135 ->  67.5..-67.5
```

(If HAOV/VAOV were the full 360/180 this reduces to the true-equirect formula.)
Interactables sit near the horizon, where the mapping is most accurate.

**Plan — a new hotspot-authoring harness** (its own page, sibling of the tuning
funnel; reuses the box-draw canvas built for the door work):

1. Load a scene's wrapped gpt image on the flat box-draw canvas.
2. Draw a labeled box per interactable; each box → a `hotspots.json` entry.
3. Optional **"suggest objects"** button: Claude-vision pass proposes objects + boxes
   as fractions to pre-seed, then nudge/label (approach #2 bolted onto #1).
4. Viewer (`view360.html`) reads `hotspots.json`, converts box centre → yaw/pitch
   (across the scene's `haov`/`vaov`), drops a Pannellum hotspot with a sized clickable
   area; its click handler pops a note/puzzle modal, reveals a clue, or **swaps the
   panorama** (closed door → an open-door variant image).

**Schema (draft) — `scene/hotspots.json`:** carries the wrap coverage so the viewer
can convert boxes → yaw/pitch (see formula above).
```json
{
  "image": "gpt_test_1.png",
  "haov": 360, "vaov": 135, "vOffset": 0,
  "hotspots": [
    { "id": "laptop", "label": "Laptop", "box": [0.44, 0.52, 0.56, 0.66],
      "action": "puzzle", "target": "terminal_1" },
    { "id": "door", "label": "Door", "box": [0.70, 0.40, 0.82, 0.80],
      "action": "swap", "target": "gpt_test_1_open.png" }
  ]
}
```
`box` = [x0,y0,x1,y1] fractions. Viewer computes the centre for the marker and can use
the box extent to size the clickable div. `action` ∈ {puzzle, note, clue, swap};
`target` resolves per action. (The door-open `swap` target is now a separately
authored/edited gpt image, since inpainting was part of the abandoned true-360 track —
revisit how we make the open-door variant when we build the door mechanic.)

## Phased build plan (biggest structural win first)

1. **Phase 1 — graph logic.** Convert the step model from a linear list to a
   hub-and-spoke graph: nodes with hidden/available/solved states, a boss gated behind
   "N of M spokes," submission code recording per-node results. Prove it round-trips
   through the R decoder self-test. Placeholder visuals — just make the machine work.
2. **Phase 2 — map interaction.** Lay nodes out spatially, make them clickable, add
   the fog-of-war that clears as students progress. Still placeholder art, but it now
   *feels* like exploring a space.
3. **Phase 3 — art.** Generate the atmospheric backgrounds + node illustrations (GPT
   Image 2), wire them in, add ambience. The mist/ribbon vision lands on screen.

Confirm each phase holds before the next (repo default for large designs).

## Open questions / still to decide

- **House art style** — one consistent visual language so every chapter's room feels
  like the same world. To be defined with Lucas before Phase 3.
- **Which scenarios first** — presumably grow the existing `alaska/` room into the new
  format as the reference implementation, then template from it.
- **Boss-gate N per scenario** — default ratio of spokes-required-to-unlock.
- **ggtree-for-wasm** and **embeddings** follow-ups (from `AGENTS.md`) still stand and
  intersect with which techniques can be spokes/bosses.

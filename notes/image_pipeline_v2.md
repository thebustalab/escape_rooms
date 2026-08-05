---
authority: intent
---

# Harness V2 — image pipeline upgrades

**IN PROGRESS (spec 2026-07-31).** Phased plan to upgrade the authoring harness's image
pipeline. Three upgrades, sequenced cheapest-first: **(B) native higher resolution**, **(A) world-plate
reference continuity**, **(C) generalized state variants**. Work happens on a copy of the harness at
`authoring_v2/` (runs on **:8752**, alongside the production **:8751** harness — same `rooms/` tree, run
one at a time per scenario). **Phase 1 (B) is DONE (live gen passed).** **Phase 2 (A) world-plate is
BUILT in `authoring_v2/`, pending Lucas's live spike** (which doubles as the Phase 0 de-risk). **Phase 3
(C) BUILT as Option 2 (runtime compositing) — per-hotspot variants, pending Lucas's live test.** See
per-phase status below. Model + endpoints are already current
(`gpt-image-2`, REST `/v1/images/{generations,edits}` — verified 2026-07-31), so this is about
*resolution*, *cross-room continuity*, and *reuse of the masked-edit primitive* — not a model bump. The
OpenAI **Responses API** for the iterative authoring loop is explicitly OUT of scope for V2 and parked in
`../AGENTS.md` → "Known follow-ups".

Additive throughout: every change keeps existing scenarios (Alaska, Hawai‘i, airship, …) working
untouched. A room that sets no new fields uses today's behaviour.

## Motivation — the weak seam

Base scenes in a room series are each generated **independently** from their own text prompt
(`cmd_gen` → `/v1/images/generations`, which takes NO input images). Cross-room continuity — same night
sky, same floating islands, same palette — is held together *only* by repeating a shared-world clause in
every prompt, policed by the `escape_room_scene_validator` and `consistency/rubrics/art_style.md`.
Nothing forces two exterior views to share actual horizon pixels. V2 closes that seam (A) and sharpens
the panoramas that stretch across a 360° pan (B), reusing the multipart `/images/edits` plumbing the
door-open flow already trusts.

## Pivotal architectural fact

`/v1/images/generations` (scene gen) cannot accept input images. `/v1/images/edits` (door-open,
`cmd_edit`/`cmd_dooropen`) already does multipart image upload and takes up to 16 images. So **B is a
config change; A requires routing scene gen through the edits path; C is a rename/generalize of the
door-open primitive.** All three land on the edits plumbing that already exists.

Key files (paths relative to `escape_rooms/`):
- `authoring/generate_scene.py` — owns all OpenAI HTTP. `API` base line 30. Subcommands `gen`
  (208–214, `cmd_gen` 73–89 → generations), `edit` (226–231, `cmd_edit` 146–163 → edits multipart),
  `dooropen` (232–238, `cmd_dooropen` 166–201 → edits + mask + feather-composite).
- `authoring/harness_server.py` — `:8751` server. `/api/generate` 1072 (size default `"1536x1024"`
  1079), `_run_generate` 730–751 (argv 740–742, no `--model`), `_run_dooropen`/`_run_dooropen_room`
  781/800 (patches `panoramaOpen` at 811), `/api/commit-room` 1189 → `_commit_room` 836–874 +
  `_commit_node` 514–542 (`panorama` 527, `builtFrom` 528, `panoramaOpen` 530–531).
- `authoring/ui/harness_gpt.html` — room-column template 398–419 (height `.wideH` 405, cap 1536;
  Generate `.gen` 408), `generate(key)` 1120–1135 (size `"1536x"+wideH` 1122; POST `n:2 quality:"high"`
  1129), door-open `.doorprompt` 412 + `makeOpenDoor` 1233–1256 (posts `/api/dooropen` w/ box 1247),
  cover gen 958.
- `authoring/ui/open_target.js` — `EscapeOpenTarget.pickOpenMaskHotspot` (which hotspot the mask reveals).
- `shared/pano-player.js` — runtime scene swap, line 771: `(openState && room.panoramaOpen) ?
  room.panoramaOpen : room.panorama`.
- `tests/` — `node --test` units + Playwright e2e (`e2e/smoke.spec.js`, `alaska_full.spec.js`).

---

## Phase 0 — De-risk the reference-image behaviour (spike, ~1 room, throwaway)

**Now runnable directly in the v2 harness (built 2026-07-31).** The `--ref` path shipped with Phase 2's
plumbing, so the spike no longer needs a hand-rolled CLI call: set a world plate from a candidate
("plate" chip), then generate another room with "world plate" ticked, trying fidelity low vs high. The
go/no-go questions below still stand — record the finding here.


Before any harness wiring, confirm empirically that "generate a 360° scene conditioned on a world-plate"
actually gives backdrop continuity *without* over-constraining composition.

- By hand (CLI, no harness changes), take one airship room's `scenePrompt` and one candidate scene as a
  provisional "world plate", and call `/v1/images/edits` with the plate as the single reference image +
  the room prompt. Try `input_fidelity` low/omitted vs high.
- **What we're testing:** (1) does the sky/horizon/palette carry over? (2) does the edit still honour a
  *different* room composition (interior vs exterior, different foreground object) or does it just echo
  the plate? (3) is prompt retuning needed vs the generations-endpoint phrasing?
- **Exit:** a go/no-go note appended here. If edits-from-plate collapses composition freedom, fall back
  to a lighter continuity mechanism (e.g. plate only for exterior rooms, or a shared sky-strip
  reference) before committing Phase A. No code shipped in Phase 0.

---

## Phase 1 — (B) Native higher resolution  ·  smallest, do first

**DONE — live acceptance gen passed 2026-07-31 (Lucas: higher-res "beautiful").** What shipped in the copy: a
per-room **scale** selector (1×=1536 wide / 2×=3072 wide) that multiplies *both* axes, a live output-size
readout that turns red when the picked size breaks limits, a `generate()` client guard, a server-side
`_valid_size()` guard on `/api/generate` (rejects bad sizes with a 400 *before* any OpenAI call), and a
regression test `test_valid_size` (suite now 35 green). Server compiles, boots on :8752, bad sizes
(5000×5000, off-aspect 3072×256) rejected end-to-end with no generation triggered. **Not yet verified:** a
real 3072×1024 gen against OpenAI (Lucas's live test) + that the door-open variant returns at 3072×1024.

Generate base scenes at up to **3072×1024** (still 3:1) instead of 1536×512. Replaces the deleted
Real-ESRGAN 2× stage with native 2×. Door-open variants auto-track because `cmd_dooropen` re-derives its
size from the input image (`generate_scene.py:186`) and resizes the result to match (192–193).

1. **UI** (`harness_gpt.html`): make width a variable, not the literal `"1536x"`.
   - Room-column template ~405: raise the `.wideH` `max` above 1536, or add a width control / a
     resolution preset (`1536×512` vs `3072×1024`). Update the hint text at 406.
   - `generate(key)` ~1122: replace `const size = "1536x" + wideH` with a width read from the new
     control (`${w}x${h}`).
   - Cover gen (958) can stay 1024×1024 or bump to 1536² — cover is square, unaffected by the 3:1 arc.
2. **Server** (`harness_server.py`): `/api/generate` already passes `size` straight through; only the
   default literal `"1536x1024"` at 1079 needs to become the new default (or stay — the UI sends size).
3. **CLI** (`generate_scene.py`): bump the `--size` default at 212 (and 217/230) if we want the
   command-line default to match; harness always sends an explicit size so this is cosmetic.
4. **Tests / checks:** confirm `size` validity (multiple of 16, ≤3840 edge, ≤3:1). Regenerate one room
   at 3072×1024, commit, walk it on `:8751`, then door-open it and confirm the variant comes back at
   3072×1024 automatically.

**Cost note:** tokens/latency scale with pixel count (~4× the pixels → materially slower + pricier per
gen). Keep 1536×512 as a "draft" preset for fast iteration and reserve 3072×1024 for the committed pass.

**Exit:** UI offers a resolution choice; a room generated at 3072×1024 renders crisply and its door-open
variant tracks; `_scratch` and commit paths handle the larger PNGs.

---

## Phase 2 — (A) World-plate reference continuity  ·  the real fix

**BUILT in `authoring_v2/` 2026-07-31 — pending live spike/acceptance gen.** End-to-end plumbing shipped:
`generate_scene.py gen --ref PATH [--input-fidelity low|high]` routes through `/images/edits` with the
plate as a repeated `image` form field (up to 16, no mask → full-frame gen guided by the plate); server
`_set_world_plate`/`_world_plate_abs` + `/api/set-world-plate` commit a chosen candidate to
`<scenario>/_world/plate.png` and record `scenario.worldPlate`; `/api/generate` takes `worldPlate:true` +
`inputFidelity` and 400s if no plate is set; UI adds a per-candidate "plate" chip, a per-room "world
plate" checkbox, a single global "plate fidelity" selector (low/high) in the top bar, and a plate-state
hint. Guards verified (bad candidate, no-plate gen,
bad fidelity all 400 with no OpenAI call); server test `test_set_world_plate_copies_and_patches` added
(suite 36 green). **Not yet verified (Lucas's live spike):** a real referenced gen — does the plate carry
the backdrop while the prompt keeps composition freedom, and low vs high `input_fidelity`?

One canonical **world plate** per scenario, passed as a reference into every room's generation, so all
rooms share pixel-anchored backdrop continuity instead of only shared prompt text. Gated on a Phase 0 go.

1. **New generation path in `generate_scene.py`.** Scene gen must move off `/images/generations`. Two
   options — prefer (a):
   - (a) Add `--ref PATH` (repeatable, up to 16) to the `gen` subcommand; when present, `cmd_gen` posts
     to `/v1/images/edits` with `files=[("image[]", plate), …]` + the room prompt, instead of
     `/images/generations`. When absent, behaviour is unchanged (back-compat). Model stays `gpt-image-2`.
   - (b) A separate `genref` subcommand — cleaner separation but duplicates the candidate/out plumbing.
   - Expose `input_fidelity` per the Phase 0 finding (likely low/omitted so the plate guides backdrop,
     not composition).
2. **Server** (`harness_server.py`): `/api/generate` (1072) parses an optional `world_plate`/`ref` field;
   `_run_generate` (730–742) threads it into the argv as `--ref <path>`. The plate is a scenario-level
   asset (e.g. `rooms/<ch>/<sc>/_world/plate.png`) resolved server-side, so the UI sends a flag/name, not
   the bytes.
3. **Plate authoring.** Add a small "world plate" affordance: generate one plate for the scenario (reuse
   `/api/generate` at the scenario's backdrop prompt), commit it to `_world/plate.png`, and let each room
   toggle "use world plate" on its Generate. Record the plate path in `scenario.json` (scenario-level,
   e.g. `worldPlate: "_world/plate.png"`) so builds are reproducible and `builtFrom` can note it.
4. **UI** (`harness_gpt.html`): a scenario-level "Generate/Set world plate" control, plus a per-room
   "use world plate" checkbox in the room column (398–419) that adds `ref` to the `generate()` POST
   (1120–1135).
5. **Consistency tooling.** Once a plate anchors the backdrop, the `escape_room_scene_validator`
   "shared-world backdrop continuity" check shifts from "did the prompt repeat the clause" toward "did
   the room use the plate" — note this in the validator skill when built.
6. **Tests:** regenerate two exterior airship rooms off one plate; confirm horizon/sky share pixels
   (not just intent); confirm an interior room still composes freely with the plate as reference.

**Tradeoff / risk:** editing-from-a-plate is conditioning, not free generation — the Phase 0 spike exists
precisely to prove composition freedom survives. If not, scope A down to exterior rooms only.

**Exit:** a scenario can carry one world plate; rooms generated against it share real backdrop pixels;
back-compat preserved for ref-less gens.

---

## Phase 3 — (C) Generalized state variants  ·  broadest, do last

**BUILT in `authoring_v2/` + `shared/` 2026-07-31 as OPTION 2 (runtime compositing) — pending Lucas's
live test.** Lucas chose full compositing over the single-panorama fallback (he has rooms needing two
objects changed at once). What shipped:
- **Data model** — variants live per hotspot: `variants:[{state, when, box, prompt, panorama}]`. `when`
  uses the engine condition DSL (`condOK`), extended with `{eq:[key,val]}` for dial/state equality.
- **Runtime** (`shared/pano-player.js`, the one shared player — additive + gated, inert for every
  variant-free room): new ES module `shared/variant_resolve.js` `pickActiveVariants()` (pure,
  node-tested — `tests/variant_resolve.test.mjs`) picks each object's last-satisfied variant; `buildViewer`
  now composites base + each active variant's box region on a canvas (mirrors the existing
  `compositeAwakened` starfield path) so independent object states render together. `play.html` ×5 bumped
  `pano-player.js?v=63→64`.
- **Server** (`authoring_v2/harness_server.py`) — `/api/gen-variant-room` reuses the door-open masked-edit
  primitive verbatim (only output name + written field differ) → `var_<id>_<state>.png` + records the
  variant on the hotspot; `/api/patch-variant` tunes the trigger without regenerating; `/api/delete-variant`.
  Helpers `_add/_update/_remove_variant` + `_find_hotspot` (tested: `test_variant_add_remove`).
- **Editor** (`authoring_v2/ui/hotspots_edit.html`) — the first in-page tab system: a **[Content][Variants]**
  tab bar over the selected hotspot. The Variants tab lists an object's variants (thumb + trigger editor +
  update/delete) and an add/regenerate form (state + trigger builder + prompt + Generate). Variants are
  **server-owned**; the editor's Save strips `variants` so a stale in-memory copy can't clobber them.
- **Verified**: 37 python + 41 node tests green; all variant routes 400 cleanly with no OpenAI call;
  editor + scenario.json load intact. **Not yet verified (Lucas's live test):** a real variant gen and the
  in-browser composite of two simultaneous object states.

Original single-panorama plan (Option 1) preserved below for context; superseded by Option 2.


The door-open primitive (masked box edit + feather composite, `cmd_dooropen` 166–201) is already
state-agnostic. Only the *naming* is hardcoded: `dooropen` end-to-end, a fixed `scene_open.png` output,
and the single `panoramaOpen` node field the runtime swaps. Generalize to arbitrary state deltas (lever
thrown, lights on/off, panel lit, water drained).

1. **Schema.** Replace the single open/closed pair with a **state-variant map** on a room, e.g.
   `variants: { "<stateKey>": { panorama: "scene_<key>.png", box: [..], prompt: "..." } }`. Keep
   `panorama`/`panoramaOpen` as the back-compat shorthand for the binary door case.
2. **CLI** (`generate_scene.py`): `cmd_dooropen` is already the general primitive — parametrize the
   output name and let the caller name the state; the mask/box/prompt are already inputs.
3. **Server** (`harness_server.py`): generalize `_run_dooropen_room` (800–820) so the node field it
   patches (currently hardcoded `panoramaOpen`, 811) is the variant's field; add a route (or extend
   `/api/dooropen-room`) that takes a `stateKey`.
4. **Runtime** (`shared/pano-player.js`): line 771 swap becomes a resolver over the current world-state →
   the matching variant panorama, falling back to `panorama`. This is the real reach — it touches game
   state, not just authoring.
5. **UI** (`harness_gpt.html`): the door-open modifier (`.doorprompt` 412, `makeOpenDoor` 1233) becomes
   an "add state variant" affordance keyed by state; the mask target picker (`open_target.js`) already
   generalizes.
6. **Tests:** a scenario with a non-door state variant (e.g. a lamp on/off) that the runtime swaps on the
   right state transition; confirm binary-door scenarios still work unchanged.

**Blast radius:** unlike B and A, this changes the scenario schema *and* the player runtime — sequence it
last, build only when a scenario actually needs a non-door state variant (the validator already asks for
it, but no built scenario needs it yet).

**Exit:** a room can declare N state variants, each authored as a masked delta of its base; runtime swaps
on world-state; binary-door back-compat intact.

---

## Out of scope for V2 (parked)

- **OpenAI Responses API for the iterative authoring loop** — multi-turn "same scene, move the keypad
  left" candidate iteration. Real refactor of the `generate_scene.py` call layer; Lucas judged it
  unnecessary for now (2026-07-31). Parked in `../AGENTS.md` → "Known follow-ups". Revisit only if the
  manual reject→regenerate loop becomes a bottleneck.
- **Reviving a standalone upscaler (Real-ESRGAN etc.)** — superseded by Phase 1 native higher-res.

## Suggested sequencing

Phase 0 spike → **Phase 1 (B)** ship (quick quality win, de-risks nothing but immediately useful) →
**Phase 2 (A)** ship if Phase 0 is a go (closes the weak seam) → **Phase 3 (C)** when a scenario needs a
non-door variant. B and A both ride the existing `/images/edits` multipart path, so they're low-risk
despite the payoff; C is the schema+runtime reach.

---

## V3 — art polish batch (2026-07-31)

A grab-bag of art improvements after the three phases. Quick, on-pipeline wins built + verified in
`authoring_v2/` and `shared/`; two bigger tracks staged.

**Built + verified (38 python / 41 node green):**
- **Expanded ambient FX** (`shared/pano-player.css`, +`?v=58` on the 5 play.html) — new `fx-*` overlays
  **godrays / rain / dust / haze** joining flicker/frost. The fx system is data-driven (`applyFx` makes a
  `.fx-<name>` div for any name in `scenario.fx`/`room.fx`), so these are CSS-only, gentle, and
  reduced-motion-aware. Authoring = add the name to a scenario's/room's `fx` array. No generation.
- **Seam-safe 360 wrapping** — `generate_scene.py seamfix` rolls the pano so its L/R seam is centred,
  masked-edits a centre strip continuous (reusing the door-open mask+feather primitive), rolls back →
  clean wrap. Harness `/api/seamfix` + `_run_seamfix` make a non-destructive `<name>_seam.png` candidate;
  UI adds a **"seam"** chip on candidate tiles. Pure `_roll_h` invertibility is unit-tested.
- **Provenance (C2PA) hygiene** — confirmed base scenes preserve gpt-image-2's embedded C2PA
  "AI-generated" metadata (they're written byte-verbatim, no PIL round-trip); commits byte-copy. Invariant
  now documented in `cmd_gen` so a future refactor won't silently strip it. Pixel-editing paths
  (dooropen/seamfix/variant) invalidate any signature by definition, so provenance lives on the base scene.
- **Relight / time-of-day — no build needed:** authored as a Phase 3 **state variant**. Add a variant on a
  sky/room-spanning hotspot box with a prompt like "same scene at dusk, warm low light" and a trigger
  (`{solved:…}` / dial `{eq:…}`); the compositor swaps it in. So "torch lit," "dawn→dusk," "power on" are
  just variants — the Phase 3 system already does relighting.

**Staged (not built):**
- **Batch single-call multi-candidate (#2)** — gpt-image-2 returns up to 8 coherent images in one call;
  today the harness loops N subprocess calls (`_run_generate` at n×`gen`). Switching to one call with `n>N`
  is fewer API calls + a mutually-coherent candidate set, but it's a `_run_generate` / job-bookkeeping
  refactor (collect N images from one subprocess) — do as its own careful pass.
- **Progressive preview (`partial_images` streaming)** — authoring-UX; candidates resolve visibly instead
  of popping in after ~20s. Moderate harness change.
- **Cinemagraph ambient loops (#7)** and **depth parallax (#8)** — the two big tracks from the art-options
  discussion; new video/depth model dependency and a viewer change respectively. Need explicit go before
  starting.

## Per-room CONTEXT reference (2026-08-02) — built (Phase A)

Problem: a room's generated interior ignores how it looks from outside — the airship **bridge** reads as a
tiny enclosure from the deck but generates as a big well-appointed room. The **world plate** is the wrong
lever (it's ONE scenario-wide backdrop for cross-room *style* continuity, not per-room scale). Fix: a
per-room reference = a **crop of where the room is seen from the room that enters it**, fed as the gen
`--ref` (same `/images/edits` path the plate uses) **instead of** the plate for that room.
- **Server** `_room_ref_crop(base, room_key)` (harness_server.py): source box = the room node's `refFrom`
  {room, box} override if set, **else the incoming DOOR's box** (a `door` hotspot in another room with
  `to == room_key`); crops it from that source room's committed `scene.png` → `_scratch/refcrop_<room>.png`;
  None on any miss (→ falls back). `/api/generate` uses it when `req.roomRef` is set (precedence over
  `worldPlate`). Tested on bridge → crops room2's door box (72×163).
- **UI** harness_gpt build card: a **"room reference"** checkbox (`.useRoomRef` → `body.roomRef`) beside
  "world plate"; opt-in per gen (not auto — auto would change every room's gen). Reuses the plate-fidelity
  select (low = composition freedom, recommended). **Needs a harness restart** to pick up the route (done).
- **Decisions (Lucas):** default source = the connecting door's box; a marked box can override (the
  `refFrom` override is read by the server but **its authoring UI is Phase B, not built** — for now the
  default door-box is what ships); used **instead of** the plate (prompt handles world/style fine).
- **Caveat:** the door box is often narrow → a small crop (bridge = 72×163); a marked custom box (Phase B)
  gives a larger, more detailed reference. **Not run through a real gen** — crop + plumbing verified; the
  gpt-image-2 edit itself is Lucas's to try (tick "room reference" when generating the bridge).

## Per-DOOR open art (2026-08-02) — built. Multiple doors can open independently, each with its own image.

Was: a room had ONE room-level `panoramaOpen` (a whole-scene swap), shown only when the FORWARD door opened.
So multiple closed doors couldn't each open with their own art. Now each door hotspot can carry its own
**`openImage`** (a base-sized scene with THAT door open), and it **composites — exactly like a variant —
when its own gate is solved** (`doorIsOpen` already handles per-door `requires` gating; a door can map to any
puzzle/lock in the room, or the room's primary gate). Several doors open at once → several composites.
- **Runtime** `shared/pano-player.js`: `activeVariants(r)` now appends, for each `door` with `openImage`
  where `doorIsOpen(h,r)`, a `{box:h.box, panorama:h.openImage}` pseudo-variant → reuses `compositeVariants`
  entirely. New `basePanorama(room, openState)` keeps the closed base for per-door rooms (guards against
  double-open if a room ever has both `panoramaOpen` and `openImage`). **Inert for existing rooms** (none
  have `openImage`; legacy `panoramaOpen` swap unchanged). Rides the existing solve-rerender (`buildViewer`).
  Cache bumped `pano-player.js?v=66→67`. 41 node tests green.
- **Generation** `harness_server.py::_run_dooropen_room(..., hotspot_id=None)`: with `hotspotId`, writes
  `door_<id>_open.png` + sets that hotspot's `openImage` (via `_find_hotspot`+`_save_scenario`); without,
  legacy `scene_open.png`+`panoramaOpen`. Route `/api/dooropen-room` reads `hotspotId`. **Needs harness
  restart** (done).
- **Hub UI** `reproject_test.html`: the door Content panel's "Open this door" now sends `hotspotId` → per-door;
  shows "set ✓" + "Regenerate open image" once done; refreshes the node so the door's `openImage` sticks.
- **Not run through a real gen** (gpt-image-2 job) — plumbing + tests verified; Lucas to try. **Canonise
  `door.openImage` in `escape_rooms/AGENTS.md` once confirmed live.**

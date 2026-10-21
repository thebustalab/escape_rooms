---
authority: intent
---

# BUILD — Seedfall lift ride (up_4a → up_5a) by compositing, then Cameraman

Lucas, 2026-10-21 (session "seed fall"): "document this and hand off to a new agent to try it."

## Goal and why

A transit clip for the lift door in `up_4a` ("The lift up to level 5" → `up_5a`): the player steps into the glass lift
car, rides UP the cliff, and steps out onto the level-5 pine terrace. If it works it becomes the pattern for Seedfall's
other lift rides (Lucas wants 3–4 lift rides among ~9 transits per player) and possibly the finale. It plays AS the
panorama via `door.transit {video, rollFrom, rollTo}` (hub `escape_rooms/AGENTS.md` → `transit`). Nothing is wired yet.

**The blocker, measured:** LTX `exp_travel.py` (first frame + last frame + prompt) will NOT slide the view downward past
the car windows. Five attempts, all on the bottom → middle car frames (`frames/w1_bottom.png` → `frames/w2_mid.png`):

| attempt | net vertical travel of the view through the left window (+ = down = car rising) | verdict |
|---|---|---|
| plain rise prompt (chain segment `sf_lift_s1`) | −328 px | goes DOWN; windows fill with blank rock mid-clip |
| strongly worded ascent prompt (`sf_lift_up_strong`) | −349 px | goes DOWN; wording ignored |
| render as a descent middle → bottom, play reversed (`sf_lift_up_reversed`) | +12 px | right way but a CROSSFADE, no slide |
| hand-made guide frames (view slid down 1/3, 2/3; `--guide …@24:0.6`, `@48:0.6`) (`sf_lift_up_guided`) | −217 px (−173 in the middle third) | goes DOWN between the guides |

Measurement (verified against a synthetic 10 px downward shift → +10.0): Farneback optical flow, median dy over the
left glass pane `x 180–430, y 100–380` on frames resized to 1536×512, summed over the clip. Clips are in
`Tools/temp/cine/_travel_exp/<tag>.mp4`. Lucas watched them and agreed ("still goes down", "still no go").

Ruled out already (don't retry): wording, reversing a descent, image-pin guides at 0.6. From the clouds work
(`rooms/dimensionality_reduction/clouds/notes/BUILD_storm_transit_camera_control.md`): the camera-controls LoRA
(hold-then-cut) and the seamless-equirect LoRA (no gain). Installed on ComfyUI `:8289`
(`GET /models/loras`): `LTX-2.3-22b-LoRA-Cinemagraph/…cinemagraph-0.9`, `camera_test/LTX2.3-22B_IC-LoRA-Cameraman_v2_14000`,
`camera_test/Seamless-Equirectangular-LTX2.3-LoRA`, `camera_test/ltx-2.3-lora-camera-controls`.

## Inputs that already exist (all in `_scratch/lift_ride_4a_5a/`)

- `frames/aerial.png` — oblique aerial of this one tower (geometry anchor). `make_prompts.py`, `gen_stills.sh`.
- `frames/w1_bottom.png`, `w2_mid.png`, `w3_high.png`, `w4_top.png` — 3072×1024 equirect car frames, the car identical
  in all four (Lucas liked them). Gate open at bottom/top, shut mid-climb; the view opens over sea and city near the top.
- `frames/w0_up4a.png`, `w5_up5a.png` — the two rooms' committed `scene.png` rolled (`make_ends.py`); rolls in
  `meta.json` (`rollFrom 124.336`, `rollTo -126.68`).
- `frames/car_mask.png` — 255 = car, 0 = view through the glass. Built in `make_guides.py` from the max pairwise
  difference across w1..w4 (< 22 after blur), opened 7, closed 15, dilated 5; car fraction 0.461. Good on the frame,
  rail, gate bars and lantern; check the right-hand pane, where the matching sky leaves small islands.
- `make_guides.py` — the inpaint-the-car-out + scroll machinery (window band rows 0.12H–0.95H). Reuse it.

## Step 1 — the composite ride (no AI motion; CPU only)

1. **A tall view to slide.** The four car frames' views are four separate draws and do not join. Generate the
   behind-the-glass view as continuous layers instead, with `authoring_v2/generate_scene.py gen` (`--ref
   frames/aerial.png --ref frames/w1_bottom.png --ref frames/w3_high.png`, `bash -lic` so `OPENAI_API_KEY` is in scope):
   - **near layer**: the sheer grey limestone face and the tower's iron cross-braces, seen straight on from a hand's
     breadth away, as a tall vertical strip (portrait 1024×1536; make two and stack, or generate 1024×1536 and repeat
     with a vertical seam fix) — it scrolls FAST;
   - **far layer**: the view out over the sea and the cliff city from low (yard level) up to high (above the
     terrace parapet) as one tall image — the yard with shed and plum-purple beeches at the bottom, the sea and
     the lit city spreading as it rises, the pine terrace parapet at the top. It scrolls SLOWLY.
   One spec-driven prompt each (Rule: new panoramas through `scene_spec.render_prompt`; these are flat layers, so a
   plain prompt is acceptable — say "flat straight-on photograph, no perspective panorama").
2. **Composite** 73–121 frames at 24 fps, 3072×1024: per frame, `out = car_mask·w1_bottom + (1−car_mask)·view`, where
   `view` = far layer offset by `t·Df` blended under near layer offset by `t·Dn` (near only where the side panes face
   the rock — the left pane(s); the front gate and right panes look out to sea → far layer only). Ease in/out (smoothstep).
   Content moves DOWN the frame as `t` grows. Optionally a slow car-light flicker; keep it subtle.
3. **Ends.** Start = `w1_bottom`'s own view (match the far layer's bottom to it, or crossfade the first ~8 frames from
   the real w1); end = crossfade the last ~8 frames into `w4_top` (the car arriving in the lift house). The walk-in
   (`w0_up4a → w1`) and walk-out (`w4 → w5_up5a`) segments are forward pushes; render those with `exp_travel.py` as
   henges did (forward pushes work), or composite a simple zoom.
4. **Check direction before showing anyone**: the flow measurement above must read clearly POSITIVE through the
   rock-facing pane and positive-but-smaller through the sea-facing panes (parallax). Then `clip_motion_map.py`
   and a 12-frame contact strip.
5. Deliver: `ffmpeg … -c:v libx264 -b:v 8M -pix_fmt yuv420p -movflags +faststart`; phone copy at 1536×512 to
   `Tools/temp/mobile_previews/seedfall_finale/lift_ride_composite.mp4`; 360 view by staging a copy as
   `_scratch/cine_cand/up_4a/transit__lift_composite.mp4` and linking
   `http://127.0.0.1:8752/cine360_clip.html?chapter=comparing_means&scenario=squirrel&room=up_4a&state=transit&cand=lift_composite`
   ("transit" is not a real state, so tab 3 ignores it).

## Step 2 — Cameraman IC-LoRA with the composite as reference

Exactly the clouds method (`clouds/notes/BUILD_storm_transit_camera_control.md`, `_scratch/storm_transit/run_g3.sh`):
`cinemagraph_tools/exp_travel.py --a frames/w1_bottom.png --b frames/w4_top.png (or w2/w3 for a shorter test)
--ic-lora camera_test/LTX2.3-22B_IC-LoRA-Cameraman_v2_14000.safetensors --ref-video <composite.mp4> --size 1536x512
--a-strength 0.6 --prompt "<rising glass lift; the car fixed; the view slides down>"`, then upscale (clouds:
`refine_x2.py` exists; Lucas saw no difference, so a plain lanczos upscale is fine). Rules that bit clouds: render at
1536×512 (3072×1024 with a reference gives grey mush); keep the vehicle FIXED in the reference (it is, by the mask).
Measure direction the same way; show Lucas the composite and the Cameraman render side by side.

## Acceptance

- The view through the glass moves DOWN (car rising) for the whole climb, measured, with no crossfade or reversal.
- The car does not change shape or move. No blank-rock blackout mid-climb.
- Lucas has watched it in the 360 viewer and said which version (composite or Cameraman) he wants.
- Only then: wire `door.transit` on up_4a's lift door (`rollFrom`/`rollTo` from `meta.json`), the reversed clip on
  up_5a's lift-down door with the rolls swapped, back up `scenario.json` to `z_archive/` first, lock writes with
  `authoring_v2/scenario_lock.py`.

## Constraints

GPU renders go to ComfyUI `:8289` and share it with other scenarios' `room_iterate` jobs (expect ~15–22 min per
segment). Run long jobs detached (`setsid nohup …`), never as a session background job. Never commit in the
escape_rooms repo from host2.

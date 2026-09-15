I checked the frames, the spec, and the code path rather than the worker's description.

**Verified on disk:**

- `authoring.sceneSpec` has exactly one element with `motion.moves` + `vigour` + `phrase` — `blade_spout`. `lenticulars` carries only the legacy `animate` block, so `_has_authored_mover` (long_agent.py:3554) sees one mover, and the RENDER branch (long_agent.py:4252) will not refuse.
- I ran `scene_spec.render_motion_prompt(spec)` myself: 38 words, *"…The spout of meltwater jetting from the crack in the blade and arcing down into the stone basin at its foot. Only that moves…"* — the spout and nothing else. `spec.get("rigid")` is absent and no element has `still_as`, so no rigid escalation is wrongly switched on.
- `authoring.scenePrompt == SS.render_prompt(sceneSpec)` → `True`. Not hand-written, equirect clause present.
- `scene.png` (3072×1024) is stamped 2026-09-14 23:48, and progress.md records it committed from `l1_shears_3.png` and seam-staged that minute (run 0.016 → 0.008, `needsWork` false). It postdates the spec edit.
- I looked at the native crop. The spout is there and it is **bounded**: a jet arcing clear of the blade into a worn basin with wet streaming rock below, occupying roughly the left sixth of the frame. Nothing like a frame-filling cloud sea.
- No clip exists against this art — `cine_base.mp4` is 2026-09-07.

**On the path objection that has previously blocked this room:** the last evaluation on record (for `spindle`) rejected this same reasoning on the grounds that the runner goes `cine_iterate.py → cine_stage → motion_spec.render_prompt(authoring.motionSpec)`, whose hero here is the stale `lens_cloud`. That objection does not apply to this loop. `plan.json` sets `room_iterate: true`, and the render logs in `outputs/` are `anvil_ri50_render.log`, `anvil_ri53_render.log` — the `ri<cycle>` tag written only by `_launch_cine_room`, which shells out to `cine_room.py`, which hardcodes `--arms motion` into `exp_art_prompt.py`. That arm resolves through `motion_prompt()`, where the sceneSpec wins and the `.txt` is the fallback. `authoring.motionSpec` feeds only the separate `spec` arm, which is not rendered here. I also checked the bake: `CS.bake_loop(..., mask=None)`, so the room's stale `cine_base.mask.json` (boxed to `lens_cloud`) is not applied on this path either.

None of the reject conditions hold: no settings change (end guide stays at the plan's 0.70), the mover is bounded, no zero-return argument, nothing accepted or written into committed art or hotspots, no hand-written prompt, and this is RENDER rather than a re-author of an unrendered mover. Room state is `{"art_generated": 1}` with no `needs_still`, so the runner will launch rather than park.

VERDICT: PASS
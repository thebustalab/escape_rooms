I checked the frames, the spec, and the actual code path rather than the worker's description — and specifically re-tested the claim that blocked the previous cycle.

**What holds up:**

- `scene.png` is 3072×1024, written today 21:09:10 with `scenario.json` at 21:09:20; `spindle_motion_ri4.mp4` — this loop's own render — is from 19:21, *before* the new still. So no clip has been rendered against this art. `state.json` has `spindle: {art_generated: 1, retries: 1}` with no `needs_still`, so the RENDER branch's first guard passes.
- The committed `sceneSpec` carries exactly one element with `motion.{moves,vigour,phrase}` — `day_cloth`. `name_crag`'s spindrift is a legacy `animate` block, invisible to `_has_authored_mover`. Second guard passes.
- I looked at the cloth at native resolution: a white sheet lashed at four corners to an iron frame, bellied under wind load, lower corners weighted on stone, hard-edged against plain sky and snow. ~13% of frame width, ~7% of frame area. Bounded and near-field — not a frame-filling mover.

**The previous gate's objection does not survive checking.** Cycle 24 rejected a near-identical decision on the grounds that the runner resolves through `cine_stage.py` → `motion_spec.render_prompt(authoring.motionSpec)`, which names `needle_spindrift` and bans flags. That is the wrong entry point. `long_agent._launch_cine_room` (long_agent.py:3756) invokes `cine_room.py`, which shells to `exp_art_prompt.py --arms motion --no-stage` (cine_room.py:4222), and `exp_art_prompt.arms_for` builds the motion arm from `motion_prompt(scenario, rm, room)` — spec-first since 2026-09-13, with `motionSpec` feeding only the unrequested `spec` arm. I resolved it live:

> locked-off static camera, zero camera movement. The broad white signal cloth on its frame snapping and rippling in the updraught, its weighted lower corners kicking. Only that moves; everything else stays perfectly still. Seamless natural loop.

The cloth, not the spindrift. The stale `art_prompt_motion/beacons/spindle.txt` is fallback-only and unreached. The `cine_base.mask.json` spindrift box is also not in play: `exp_art_prompt` bakes with `mask=None` and `--no-stage` into `temp/cine/_art_prompt_exp/`, touching neither committed art nor hotspots.

Against the rejection list: no settings change (0.70 is `cine_room.py`'s own documented default), a bounded mover not a frame-filling one, no zero-return-as-death argument, no acceptance and no write to committed art, prompt authored from the spec rather than by hand, and not an AUTHOR_MOVER on an unrendered mover. The job's own `review_note` prescribes exactly this beat — "Generate the still, commit, seam (auto), render ONCE, gate" — and the still is now the only new thing since ri4.

Word count is 36, not the worker's 34. Nothing turns on it.

VERDICT: PASS
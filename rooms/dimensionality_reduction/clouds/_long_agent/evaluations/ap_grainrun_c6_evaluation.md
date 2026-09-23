Verified independently against disk rather than the worker's summary:

**Render recipe** (`ap_grainrun_motion_ri4.params.json`): 3072x1024, end_guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242, looped — the settled recipe, and the worker proposes no change to any of it.

**Spec** (`scenario.json` → `ap_grainrun.authoring.sceneSpec`): exactly one of the seven elements carries `motion.moves: true` — `streamer`, vigour "brisk and snapping", phrase "the long membrane streamer snapping and rippling hard in the wind", boomerang loop. It is a ribbon tied to a strut close to the viewer: bounded, not frame-filling.

**Art staleness**: `authoring.scenePrompt` is md5-identical to `_scratch/.l1prompt_ap_grainrun.txt` (aa556edf…, 11396 bytes), and the ribbon clause is present in that committed prompt, so the still cannot be stale against the mover.

**The clip itself**: I extracted frames and computed a motion map. Frame-difference energy is concentrated in an 8×24 grid block at rows 4–5, cols 1–7 — the left-wing/strut region — at 5.5 against a global mean of 0.61, with the rest of the frame essentially static. Cropped frames confirm the pale membrane ribbon is depicted and visibly ripples across the sequence while the camera, dash, city and eyewall hold still. That matches the reported camera verdict, glitch breadth 0.0 and dead ratio 15.3 / peak 7.2; return is 0.24, not zero, so the ambiguous-zero trap is not in play.

None of the reject conditions fire: no settings change, no frame-filling mover, no zero-return-as-death, no acceptance and no write into `scenario.json`, no hand-written art prompt, and no AUTHOR_MOVER against an unrendered mover. The clip clears every reject-only gate and the remaining step genuinely is Lucas's eye.

VERDICT: PASS
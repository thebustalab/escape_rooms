I checked this myself rather than taking the worker's word.

**Verified against the artefacts:**

- **The stale phrase is real.** `scenario.json` `rooms[2].authoring.sceneSpec` → `cirque_tarn.motion.phrase` reads *"The signal lantern hanging from its short iron gibbet arm swings…"* while its `vigour` reads cat's-paws on the water. The committed 3072 `scene.png` shows no lantern, no gibbet arm and no mast anywhere. That is the two-sources-of-truth drift the pipeline exists to prevent.
- **It would poison the render.** `exp_art_prompt.motion_prompt` (cinemagraph_tools/exp_art_prompt.py:86-104) resolves beacons from the spec, not the `.txt` — and the `.txt` fallback carries the same lantern sentence anyway, so SOFTEN_PROMPT really is the wrong instrument.
- **The mover is bounded and depicted.** Tarn at roughly x 0.26–0.49, y 0.58–0.80 — about a quarter of the frame, ice-rimmed, clearly visible in the still. `cine_base.judge.json` scores `tarn_surface` **alive, p95 15.63**. Not frame-filling, and not a never-rendered mover.
- **The merge is free.** I dry-ran the fragment through `scene_spec.render_prompt`/`render_motion_prompt`: it matches `cirque_tarn` by `at`, deep-merges `motion`, keeps `desc` and `vigour`, and the **art prompt comes back byte-identical** — so `long_agent.py:4199` does not set `needs_still` and the panorama Lucas accepted on 2026-09-03 survives. The motion prompt changes from the lantern sentence to the tarn one.

None of the reject conditions fire: no settings change, no frame-filling mover, no zero-return reasoning, no clip accepted, nothing written to committed art or hotspots, no hand-written art prompt, and this is not AUTHOR_MOVER. It also answers cycle 7's failure correctly — the prior evaluator's objection was the cost of new art, which this decision eliminates, while still fixing the mismatch that evaluator itself conceded was real.

VERDICT: PASS
I verified each of the worker's claims directly rather than trusting the write-up.

**Confirmed against the artefacts:**

- **The spec-derived motion prompt is clean.** Running `scene_spec.render_motion_prompt` on the live `rooms[2].authoring.sceneSpec` returns exactly 38 words: *"locked-off static camera… Cat's-paws of wind travel in slow bands across the black surface of the tarn… Only that moves…"* — no lantern, no mast. Cycle 8's phrase fix landed.
- **No rigid bloat.** `exp_art_prompt.py:98` switches `rigid` on `spec.rigid` or any element `motion.still_as`. This sceneSpec has neither, so the 290-char `authoring.motionSpec.rigid` inventory is never read. The prompt stays short.
- **The mover is bounded and depicted.** `rams_head/cine_base.judge.json` scores `tarn_surface` at box `[0.26, 0.58, 0.49, 0.80]` — roughly a quarter of the frame — verdict **alive**, p95 15.63. `scene.png` has not changed since 2026-09-02, so that judge is against the currently committed art.
- **The still is human-accepted.** `seam.accepted: true`, `acceptedBy: "lucas 2026-09-03"`, `needsWork: false`, `seamBandRun 0.015`. A RENDER does not touch it.
- **No clip tests the current state.** `_long_agent/state.json` has rams_head with `retries: 1`, a single cycle-8 history entry, and no `attempts`, `last_gate` or `clip`. The `cine_base.mp4` on disk is dated 2026-09-09 — before the `scenario.json.bak_20260913_170250_animate_migration` and before cycle 8's fix, so it was baked from the lantern prompt.

**Against the reject conditions:** no settings change; mover is bounded, not frame-filling; gate report is `{}` so no zero-return reasoning is in play; nothing is accepted and nothing is written to committed art or hotspots; no hand-written art prompt; and this is RENDER, not AUTHOR_MOVER.

The one thing worth weighing is the run's review note — *"rams_head and crown were also dead at every setting and were re-authored"*. But that record is against the old configuration, the re-authored stills are explicitly uncommitted, this room's own judge file shows the tarn alive on the committed art, and the note's own instruction is "Render each ONCE and gate." rams_head has not yet had that one render. Cycle 7's AUTHOR_MOVER was correctly failed for proposing new art against a never-rendered mover; cycle 8 took the free fix; RENDER is the next step on the plan.

VERDICT: PASS
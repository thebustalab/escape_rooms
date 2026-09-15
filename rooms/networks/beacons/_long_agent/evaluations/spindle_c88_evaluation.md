I checked the worker's claims against disk rather than its summary.

**Verified independently:**

- **The spec-vs-txt question is the crux, and the worker is right.** The stale file art_prompt_motion/beacons/spindle.txt does still name the spindrift — but exp_art_prompt.py:86-108 resolves the sceneSpec **first** and falls back to the .txt only if the spec yields nothing. I ran scene_spec.render_motion_prompt against the live scenario.json spec myself: it returns *"…The broad white signal cloth on its frame snapping and rippling in the updraught, its weighted lower corners kicking. Only that moves…"* — the cloth, not the spindrift. The needle's spindrift sits in a legacy `animate` block that feeds nothing. Hand-editing that .txt is exactly what the one-spec-two-consumers design exists to prevent, and the worker correctly refused.
- **The mover is bounded and depicted.** I looked at the still at native size. The white cloth on its iron frame sits left of centre, bellied and strained, weighted corners lashed — roughly 12% of frame width. Not frame-filling.
- **Freshness holds.** scene.png is 2026-09-14 21:35; the newest spindle clip anywhere is spindle_motion_ri25.mp4 at 21:26, nine minutes earlier. (The worker only looked in the room dir and named the 09-07 cine_base — an imprecision that doesn't move the conclusion: every clip on disk predates the current still.)
- **No settings change.** plan.json carries `end_guide: "0.70"`; the worker proposes rendering at it, not moving it. Seed, steps, cfg, resolution, length all untouched.
- **The runner will actually act.** state.json has spindle as `{}` — no `needs_still`, no `held`, no `parked`, attempts 0 against a cap of 1 — so the room is picked, no art generation fires, `_has_authored_mover` is satisfied by day_cloth, and RENDER launches under a fresh tag. That matches the review_note verbatim: *"The art is CORRECT and CURRENT; do NOT regenerate it and needs_still must not fire. Render each ONCE against the art as it stands and gate."*

**Against the rejection list:** no settings lever, bounded mover not frame-filling, no zero-return-as-death reasoning (none invoked), no clip accepted and nothing written to committed art or hotspots, no hand-written art prompt, and AUTHOR_MOVER isn't proposed at all — so the never-rendered-mover trap doesn't apply.

This is step 3 of the pipeline with every precondition met. The runner should act on it.

VERDICT: PASS
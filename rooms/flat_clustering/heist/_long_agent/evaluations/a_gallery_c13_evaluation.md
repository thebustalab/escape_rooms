I checked the clip and the gate code directly rather than relying on the worker's summary.

**What I verified**

- **The render exists and is the one gated.** `a_gallery_motion_ri11.mp4` — 3072×1024, 73 frames at 24 fps, matching the `frames: 73` in the report. Written Sep 13 19:05, i.e. the cycle-11 render.
- **The gate is reject-only and breadth-only.** `cine_room.py:43` — "Gate on BREADTH only — `spike` was never validated as a threshold, so it is reported, never used." So `spike 6.46` is genuinely not a rejection. The worker is right on the substance but quotes the wrong number: the enforced constant is `GLITCH_BREADTH_REJECT = 0.70`, not 0.667, and the gate requires **both** the raw and the brightness-normalised reading to exceed it. Both are 0.042 here, so the clip clears either way — the slip changes nothing.
- **Return.** 0.23, and the report carries no `note` key, which the code only omits when `ret >= RETURN_ALIVE`. Non-zero, so the ambiguous-zero-return trap isn't in play at all.
- **The frames.** The dust sheet lifts and billows out between frame 0 and ~frame 36 and is settled again by frame 72 — a real, bounded, localised cloth mover confined to the plinth. The vitrine, plinths, trolley, roof glazing and both doorways are static across the loop. The glitch's `at_pct 37.5` (~frame 27) coincides with the sheet at full billow, which is the mover doing its job, not a structural transient — consistent with breadth 0.042.
- **The live spec.** `scenario.json` room `a_gallery` matches the spec quoted, with exactly one `motion` element (`sheet`). `authoring.seam` is `{needsWork: false, stage: "screened"}` with no `accepted` key — the worker's flag is accurate, and it correctly only *noted* it rather than proposing to stamp it, which would have been a human-only call.

**Against the reject list:** no settings change proposed (it explicitly calls end guide inert), no frame-filling mover, no zero-return-means-dead reasoning, no acceptance and no write into committed art or hotspots, no hand-written art prompt, no AUTHOR_MOVER. HOLD is the pipeline's correct terminal state here — the loop may reject but never approve, so a clip that survives all three gates goes to Lucas's eye.

VERDICT: PASS
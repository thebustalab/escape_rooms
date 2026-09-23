Verified independently rather than on the worker's word:

**Disk checks — all confirmed**
- `cockpit_motion_ri1.params.json` matches the canonical recipe exactly: `3072x1024, end_guide 0.70, cfg 2.0, steps 8, length 73, seed 4242`. One render, no settings drift.
- `cockpit_ri1_render.log` reproduces the gate block verbatim and ends with the runner's own line: *"survived gates — needs Lucas's eye"* plus *"NOTE: no clip here is accepted. Metrics reject; the eye decides."*
- Cycle 1 was RENDER; this is the first post-render cycle. The mover has genuinely been rendered.

**Frames — looked at them myself** (frames 0/30/60 of the looped clip)
- Camera is locked: composition, dash rim, wing edges and city silhouette register pixel-for-pixel across the loop. Consistent with `frame0_corr 0.974`, landmark drift 0 px.
- Motion energy is regional, not frame-filling. Column bands left→right read `1.06, 1.25, 8.14, 11.5, 6.33, 1.46, 1.07, 0.91` — everything lives in the centre-left, over the sampler globe and the cloud-gardens immediately above it. The city (left third) and the eyewall/lightning shelf (right third) are effectively static at ~1.0. No boil, no global churn, no structure tearing.

**Against the reject list**
- No settings change proposed. No mover proposed at all, so neither the frame-filling nor the never-rendered-AUTHOR_MOVER bar applies.
- Return is 0.28, not zero; the worker treats it as non-ambiguous and does not re-author off it — correct handling of that measure.
- HOLD accepts nothing and writes nothing into `scenario.json`.
- No hand-written art prompt; the motion prompt resolves from `sampler.motion.phrase` in the spec, and the brief's "NONE" is correctly read as the absent `.txt` fallback.

The one thing worth naming for Lucas when he looks: the moving region is somewhat wider than the globe alone — the white cloud-garden blooms drifting above the dash move with it. That is in-world (they're living mist in the spec) and bounded, but it's a judgement only the eye can settle, which is exactly what HOLD hands over. No metric here licenses pre-empting it.

VERDICT: PASS
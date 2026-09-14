I checked the files myself rather than the worker's summary.

**Verified independently:**
- Rendering `scene_spec.render_motion_prompt` off the *current* spec gives exactly the 62-word prompt the worker quotes: only the three candle flames move, plus the rigid pin naming the candles, the swag and the panelled walls. `rigid=True` does switch on automatically from `spec["rigid"]`.
- `render_prompt(spec)` is byte-identical to the stored `scenePrompt`, and the 14:20 backup confirms the edit touched only `motion.phrase` and the `rigid` string — the art prompt hash is unchanged before and after. No still is owed, which is what the review note demands.
- Timeline holds: newest clip `ri89` finished 13:50 (per its render log), the spec edit landed 14:20. The softened phrase and the candle pin have never reached the GPU.
- The `ri89` strip shows the failure Lucas described — frame 0 has three upright candles, mid-loop the sconce is a smeared bright blob. The diff panel puts the motion energy on the sconce, so the mover is bounded, not frame-filling.
- `state.json`'s `review_note` is explicit: softened phrase, candles pinned, "Render once and gate," do not re-author the art.

**Against the reject list:** no settings touched (params JSON identical across every prior clip and unchanged here), bounded mover not a frame-filler, the zero-return measure plays no part in the reasoning (return was 0.58 and unused), nothing accepted or written into committed art/hotspots, no hand-written prompt, and it is not AUTHOR_MOVER on an unrendered mover — it is the render of one.

The worker's one flagged-but-unacted item (the sconce `vigour` appearing twice in the ART prompt, via `desc` and `element_desc`) is correctly left alone: fixing it would change `render_prompt` and force the still regeneration the note forbids.

VERDICT: PASS
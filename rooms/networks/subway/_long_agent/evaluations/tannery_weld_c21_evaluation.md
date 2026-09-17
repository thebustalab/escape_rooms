I checked the artifacts rather than the worker's summary.

**Clip exists and matches the gate report's subject.** `tannery_weld_motion_ri19_looped.mp4` is there (3072x1024, source 73 frames — consistent with the report's `glitch.frames: 73`), and its `params.json` shows the house default render: end guide 0.70, seed 4242, steps 8, cfg 2.0. So cycle 19's RENDER did happen and is spent.

**Frames.** Sampling the loop at 0/15/30/45/59 and crop-sampling the source around the 76.4% glitch mark (frames 53–58, right-of-centre crop): the only thing changing is the row of hanging canvas sheets on the under-roof rail — hems lifting, folds running along the row, sheets leaning out of plumb. The tiled walls, the arch ribs, the yellow works unit, the rails and ballast, the spiral stair, the barrels and the floor register are all fixed frame-to-frame. Camera is genuinely still; there is no frame-filling drift and no non-mover moving. The 76.4% "glitch" spike is the sheets at their swing extreme, not an artifact — breadth 0.104 raw / 0.042 normalised is consistent with that, and nothing wrong is visible in the crops.

**Spec.** `hide_rail` is the single element carrying `animate`/`motion`, with authored `vigour` and `phrase`; it is a bounded mover (a row of cloth on a rail), not the whole frame. Nothing else in the spec claims motion. So there is nothing to re-author.

**Against the reject list:** no settings change proposed; the mover is bounded, not frame-filling; return is 0.08 and the worker does not treat it as death (nor should it — the dead gate is explicitly negative, ratio 12.06, peak 7.58); the decision does not accept the clip or touch `scenario.json`'s committed art or hotspots; no hand-written art prompt; no AUTHOR_MOVER on an unrendered mover. HOLD parks a survivor for a human eye, which is the correct terminal state — a metric can reject here but never approve.

The runner should act on the HOLD.

VERDICT: PASS
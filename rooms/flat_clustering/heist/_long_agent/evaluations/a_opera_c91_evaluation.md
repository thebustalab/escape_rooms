I checked the frames and the spec myself rather than taking the worker's write-up on trust.

**What I confirmed independently:**

- **The render is real and current.** `a_opera_motion_ri89.mp4` exists (13:49), and `scene.png` was regenerated at 13:36 — so the clip was rendered against the current still, which is what cycle 89 asked for. `ri89.params.json` is byte-for-byte identical to `ri82.params.json` (seed 4242, cfg 2.0, steps 8, end_guide 0.7, 73 frames, 3072×1024). **No settings lever was touched.**
- **The mover is the authored one.** Cropping `scene.png` at the dominant motion band (x 0.15–0.32) lands squarely on the gilt candelabra and its three lit candles — I looked at the crop. The hero band's temporal std is 23.0 band-mean against a frame median of ~1.3.
- **The rigid pin held.** Swag band 1.79, panelled wall 1.79 — indistinguishable from each other and at frame-background level. The "wall is weirdly breathing" complaint is genuinely answered here.
- **The mover is bounded, not frame-filling** — roughly 13% of frame width, and the secondary warm spots (x≈0.65, x≈0.91) measure 9.8 and 10.5 against the hero's 23, consistent with tier lights and alcove sconces rather than a competing mover.

**Where the worker overstated:** the hero motion is not confined to y 0.09–0.26 as claimed — it runs y 0.03–0.40 with a second lobe at y 0.36–0.59, covering the sconce body, scrollwork and mirror backplate. That is *within* what the spec authors ("their light shifting on the gilding around them"), so it isn't out of family, but the described blob is tighter than the real one. Their identification of the x≈0.65 strip is also loose — it's a vertical gilt frame edge adjacent to the tier lights, not purely "doorway alcove sconces." Neither error changes the conclusion, and their band-level magnitudes check out.

**On the reject criteria:** none fire. No settings change; bounded mover; return is 0.58, not zero, and isn't being misread; no clip accepted and nothing written to `scenario.json`; no hand-written art prompt; and HOLD is not AUTHOR_MOVER. HOLD routes a gate-clean clip to Lucas's eye, which is the sanctioned terminal state for this loop — the loop may auto-reject but never auto-approve, and the residual question here (do those thin gilt edges shimmer acceptably?) is exactly a human-eye call, not an art re-author.

VERDICT: PASS
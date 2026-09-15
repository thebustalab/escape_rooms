I read the four evidence files, then measured the ri50 clip rather than trusting the gate summary.

**What the clip actually does.** Camera is genuinely still — per-tile phase correlation frame 0→72 is ≤0.2 px everywhere with response ~1.0, so no drift and no zoom. The authored tarpaulin corner is alive and is the hottest thing in the frame (temporal std p90 18.8, max 88); visually it flogs convincingly. So the room is not dead and the mover is not too lively.

**The fault.** Nothing else is still. Against a sky noise floor of 0.96, the pixelwise temporal std is:

| region | mean |
|---|---|
| tarp (the authored mover) | 9.93 |
| bare rock pavement | 9.31 |
| spyglass tripod legs | 9.12 |
| survey sheet + stone | 8.35 |
| dispatch bundle + stone | 8.25 |
| stone slab body | 7.41 |
| report book + brass rule | 6.19 |

The mover is indistinguishable from the ground it stands on. Full-resolution crops confirm it is not air shimmer over stationary stone — the plate boundaries and cracks in the bare pavement reshape frame to frame, the filed report's pages and brass rule shift, the stone on the dispatch bundle grows, and the tripod legs change spread. Solid rock, the puzzle object and the clue object are all warping. That is also what drives the 0.625 breadth and the 0.0 return: a one-way whole-lower-frame morph that peaks at the last frame and never comes back.

This is the failure the ledger already records for this room ("two anvil clips at 26% live were called DEAD because the motion was in the FURNITURE"), and the pipeline's fix order puts the rigid scalpel before re-authoring. I dry-ran it: a two-item pin renders a 64-word motion prompt — under fenwatch's proven 66 and far from a_opera's 176-word camera-drift regression — and `render_prompt` is byte-identical, so the committed still stands and only the clip re-renders.

DECISION: PIN_NON_MOVERS
SPEC: ["the shattered rock pavement and the mountains behind it", "every object standing on the rock"]
WHY: The camera is still and the authored tarpaulin is alive, but the rock pavement, the far terrain, the slab with its filed report and the spyglass tripod are all warping at 6-9 temporal std against the mover's 9.9, so the mover is lost in a whole-frame boil that a two-item rigid clause pins at the cost of one re-render and no new art.
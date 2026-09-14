Read all four documents, then checked the room itself rather than reasoning from the spec text alone.

**What I found.** The spec's `nets` element is a bounded authored mover with a `motion` block carrying `moves`/`vigour`/`phrase` — so it is visible to `_has_authored_mover`, and the 2026-09-13 migration is why: it split the original desc, moving "floor-length net curtains billowing inward on the night air" out of `desc` and into `motion.vigour`. `element_desc` reassembles it, so the cached `scenePrompt` is byte-identical to the one that produced the committed still.

**The still delivers it.** I cropped the region at `just left of centre` (x≈0.36) and looked at it at native resolution: two floor-length net panels lifted clear of the open sashes and swept inward across the floor, unmistakably mid-motion, occupying about a quarter of the panorama — bounded, not frame-filling, and hanging cloth is the ledger's strongest confirmed mover category (p95 up to 76.8). The depicted vigour is mid-range — well off the mast, nowhere near dead-horizontal-in-a-gale — which is a sensible initial condition to render once from rather than pre-emptively adjust.

`render_motion_prompt` derives the house-form prompt from `motion.phrase` — oscillatory, mover-only, no travel. The "NONE" in the brief is the absent `.txt` file, not absent intent; the runner writes it.

Nothing here needs re-authoring, and there is no clip to fix.

DECISION: RENDER
WHY: The spec carries one bounded mover with authored vigour, the committed still visibly depicts the net curtains billowing inward off the open sashes at just-left-of-centre, and the motion prompt renders cleanly from `motion.phrase` — so the only thing missing is the single render at 3072x1024, end guide 0.70.

**One thing for the record, not acted on:** this room's cached `scenePrompt` is missing the EQUIRECT clause, the house style block and the edge-discipline block — it is a third stale prompt of the kind the brief warns about, cached before those were added. It is not a reason to re-author (the still works and re-authoring would burn the room's attempt budget), but if `a_townhouse`'s art is ever regenerated it must go back through `render_prompt` rather than reusing this string.
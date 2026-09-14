I checked the room myself rather than trusting the write-up.

**Verified:**
- No clip exists anywhere for this room — `find` over the tree turns up no mp4/webm. So the gate report being empty is real, and ADJUST_VIGOUR / SOFTEN_PROMPT genuinely have nothing to act on.
- The still is committed at 3072x1024, verdict `hold`, seam `screened` with `needsWork: false`.
- I looked at the panorama at native resolution. The beaded curtain is clearly depicted and is **doorway-bounded** in both places — a dense hanging bead fringe inside a door frame, roughly 7-8% of frame width each. Not frame-filling.
- I ran the prompt path rather than reading it: `exp_art_prompt.motion_prompt('heist','b_pawnshop', rec)` returns exactly the string the worker quoted, built from the spec's `motion.phrase` via `scene_spec.render_motion_prompt`. No hand-written prompt, no committed .txt overriding it.
- End guide 0.70 is the shipped default (cine_room.py:101), so "render at the default" is not a settings change.

None of the six reject conditions fire. It isn't a settings change, isn't frame-filling, doesn't touch scenario.json, doesn't invoke a zero return, and it explicitly declines AUTHOR_MOVER on the correct grounds — the mover has never been rendered.

**One correction to the worker's rationale, not to its decision:** the "hanging fringe p95 76.8" figure traces to `hanging_cloths p95 76.74` in egypt/market_price, and that judge note flags it as "very hot — over-driven and lively measure the same." The actual `canopy_fringe` reading there is 35.88. So the menu evidence is weaker than presented, and if anything hints the vigour could come back hot. That's a post-render question, and the render is what's needed to answer it.

Spoken version: the room checks out. There's a beaded curtain hanging in a doorway, clearly drawn, properly bounded — good cinemagraph material. Nothing's been rendered yet, so there's nothing to soften. I did catch that the worker oversold one supporting number, quoting a hanging-cloths reading that its own source flags as over-driven, but that doesn't change what to do next. Send the render.

VERDICT: PASS
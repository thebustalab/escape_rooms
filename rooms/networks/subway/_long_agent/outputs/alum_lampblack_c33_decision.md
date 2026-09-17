Read the four authority docs, then checked this room's actual state on disk.

**What I found**

- The spec carries exactly one mover: `soot_lamp`, with a full `motion` block (`moves`/`vigour`/`phrase`), so `_has_authored_mover` sees it and `render_motion_prompt` resolves cleanly from the spec — no `.txt` fallback needed. "Motion prompt: NONE" just means no committed file:
  > locked-off static camera, zero camera movement. The soot-lamp's tall yellow flame rolling and leaning in its open pan, its thick column of black smoke lifting steadily into the hood above it. Only that moves; everything else stays perfectly still. Seamless natural loop.
- The still (`alum_lampblack/scene.png`, committed today 13:44) **depicts that mover plainly** — open pan, tall yellow flame, a thick unbroken black smoke column rising into the hood, just right of centre, unobstructed and bounded, not frame-filling. I looked at it.
- No clip has ever been rendered: no `_scratch/cine_cand/alum_lampblack/`, no room entry in `state.json`, empty gate report.
- The committed art prompt differs from the current spec only by the two removed "Nothing else stands on this stretch of wall: no stair… no tunnel mouth" seam clauses — the round-3 cleanup Lucas mandated. That is a negative clause on the back wall, nothing to do with the mover, and the standing `review_note` says alum_lampblack's round-2 art is committed and good, needing a clip only, not new art. So it is not grounds to regenerate a panorama.

Nothing to author, nothing to soften, nothing wrongly moving.

DECISION: RENDER
WHY: The spec declares one bounded mover with authored vigour, the committed still plainly depicts that open-pan flame and its smoke column just right of centre, the motion prompt resolves from that same spec in the house form naming only it, and no clip exists yet — so the single default render at 3072x1024, end guide 0.70, is the next step.
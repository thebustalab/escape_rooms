I've read the pipeline, the report, the ledger's spindle entries, and `render_prompt`/`render_motion_prompt`, then checked the actual on-disk state.

**What's there:**

- The spec carries a bounded mover with authored vigour — `day_cloth`, the white signal cloth on its iron frame, `motion.{moves,vigour,phrase}` all present. Hanging cloth is the ledger's strongest-confirmed mover category (p95 up to 76.8); spindrift is explicitly on the *not confirmed* list, and the spec correctly leaves the needle's spindrift as a legacy `animate` block that feeds nothing.
- `scene_spec.render_motion_prompt` on the live spec returns the **cloth** phrase, not the spindrift one. The spindrift text in my brief is the stale `art_prompt_motion/beacons/spindle.txt` fallback; since 2026-09-13 the spec is the source of truth and the renderer will resolve the cloth. Nothing to fix — editing prompt text by hand is exactly what that design prevents.
- The still (`spindle/scene.png`, 2026-09-14 21:35) **depicts** the mover: the cloth is bellied out, straining, weighted corners hanging, occupying roughly a sixth of the frame width — bounded, not frame-filling.
- The only clip on disk (`cine_base.mp4`) is from 2026-09-07, against art that has since been regenerated and re-seamed. So no clip exists against the current still.
- `state.json`'s `review_note` is explicit about these three rooms: the art is correct and current, `needs_still` must not fire, render once against the art as it stands and gate.

Every precondition the pipeline asks for is met and the art step is done. There is nothing to author, nothing to soften, nothing to pin.

DECISION: RENDER
WHY: The spec already carries a bounded, well-depicted mover with authored vigour (the signal cloth), the spec-derived motion prompt names only it, the still is current, and no clip exists against that still — so this is step 3, one render at the default 0.70.
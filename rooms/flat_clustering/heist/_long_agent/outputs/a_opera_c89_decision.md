I've reconstructed the room's real state on disk rather than trusting the brief (its "current motion prompt" is again the stale `art_prompt_motion/heist/a_opera.txt`, which is only a fallback and is unreachable for heist — the renderer resolves from the spec).

**The mover has been changed, not tuned, and the art has already been regenerated.** The swag was retired as the mover after three measured wordings (ri75 swag band 5.23 vs frame median 1.17 — too aggressive; ri78 0.83 vs 0.86 — dead; ri82 at the intermediate wording, which survived gates but was superseded). The live spec now carries one bounded mover: the `sconce`, three candle flames, `motion.moves` + authored `vigour` + `phrase`. Flame is a confirmed mover category and is bounded by its own physics; the swag is now pinned in the two-item `rigid` clause with the panelled walls.

Verified against the files:
- `SS.render_prompt(spec)` is 3465 chars and **byte-identical to the stored `scenePrompt`** — no still is owed, `needs_still` will not fire.
- `scene.png` was committed at 13:36, **after** the 13:34 spec edit, and it depicts the sconce exactly as authored — three tall lit candles in a scrolled gilt candelabra with a mirrored backplate, small in frame, not frame-filling. The done-criterion "no clip animates a still that predates its own motion prompt" is satisfied.
- `render_motion_prompt(spec, rigid=True)` gives a 65-word prompt naming only the flames, carrying the two-item rigid pin — well short of the 176-word pin that drifted the camera on ri73.
- The newest clip on disk is `a_opera_motion_ri82` (13:11), which predates the new still by 25 minutes. **There is no clip for this art at all.** Budget: `generations` 1 of 2, one render due.

No fix rung applies — the mover exists, is bounded, and has an authored vigour; the art is current; there is nothing to soften or pin that isn't already pinned. What's missing is the render.

DECISION: RENDER
WHY: The room was re-authored onto a new bounded mover (three candle flames) and its still was regenerated at 13:36 from that spec, leaving the art prompt byte-identical to the stored one and the spec-derived motion prompt naming only the flames — but no clip has ever been rendered against this still, so a single render is the only thing that can answer whether the new mover works.
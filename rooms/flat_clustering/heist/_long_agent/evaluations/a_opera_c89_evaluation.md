I verified every load-bearing claim against the files rather than the write-up.

**Confirmed independently:**
- `SS.render_prompt(spec)` is 3465 chars and **byte-identical** to the stored `scenePrompt` — I ran it. No still is owed; nothing hand-written.
- The live spec has exactly **one** mover: `sconce`, `motion.moves` true, with an authored `vigour` and `phrase`. `render_motion_prompt(spec, rigid=True)` is **65 words**, names only the three flames, carries the deliberate two-item rigid pin — nowhere near the 176-word pin that drifted the camera on ri73.
- I looked at `scene.png` (13:36:05). The sconce is there as authored — a gilt candelabra with tall lit candles against the panelled/mirrored wall, small in frame. A **bounded** mover, not frame-filling.
- The 13:36:13 `scenario.json` write was still-commit bookkeeping only (`builtFrom` → `l1_a_opera_3.png`, seam stage reset). The `sceneSpec`/`scenePrompt` are identical in the backup, so the sconce authoring genuinely **predates** the image. The done-criterion holds.
- Newest clip on disk is `a_opera_motion_ri82` at **13:11**, 25 minutes before the still. **No clip exists for this art.**
- `_long_agent/state.json`: `generations` 1, `pending_render` null, and the standing `review_note` says in as many words that the mover was changed to the sconce and "the art must be regenerated first." That is done; the render is the next step it asks for.

**Against the reject list:** no settings touched; mover is bounded; the swag retirement rested on spatial band measurements (ri75 5.23 vs 1.17; ri78 0.83 vs 0.86), not on the ambiguous zero return, and in any case is already-committed history rather than the action proposed; nothing is accepted; no hand-written prompt; and it proposes RENDER, not AUTHOR_MOVER — which is precisely what the rule about an unrendered mover demands.

**One caveat to carry forward, not a blocker:** `approx_boxes` puts the sconce at x 0.28–0.44, but in the image the candelabra actually sits around x 0.21–0.28 — the box lands on the curtain and parapet instead. If the post-render per-subject liveness is measured against that box, it will sample static drapery and can call a working flame dead. Nudge the box onto the flames before trusting any DEAD verdict on this clip.

VERDICT: PASS
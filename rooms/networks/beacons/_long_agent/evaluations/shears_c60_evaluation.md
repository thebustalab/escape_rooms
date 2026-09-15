I verified the worker's claims independently rather than taking them on trust.

**The frames.** I extracted frames 0/15/30/45/60 from the raw `shears_motion_ri57.mp4` (3072×1024, 73 frames) and looked at the right half at native resolution. Frame 0 is clean: the brass spyglass on its tripod over the valley. By frame 30 a massive white water jet is erupting from the spyglass's objective end, arcing down-left across `valley_view` and the nine villages and landing on the platform; by frame 60 it has collapsed back to nothing. It is not in the committed still. The authored `blade_spout` on the left is meanwhile flowing correctly. The worker's account — and the prior cycle's evaluation note — are both accurate.

**The gates.** Camera still. Glitch breadth 0.167, well under the 0.70 both-readings bar. Return 0.01 / peak 10.08 is the cyclic-flow signature of falling water, matching `rams_head` (0.02 / 10.18), which was held. The worker reads the zero return as ambiguous, not as death — the correct direction.

**The plumbing.** I ran the runner's own apply logic against this payload:
- `long_agent.py:4178` — a JSON list sets `spec["rigid"]` cleanly, which is the failure mode that sank fenwatch c18 (a dict fell through to the element branch and corrupted `elements`). This payload is a list, so it lands.
- `long_agent.py:4213` and my simulation both confirm `render_prompt` does not read `rigid`: I rendered the art prompt before and after and they are byte-identical, so `needs_still` stays clear and the committed still is preserved.
- The resulting motion prompt is exactly 65 words, naming the spout as the sole mover plus one rigid clause for the spyglass — the same register as fenwatch's 66-word pinned prompt, nowhere near the a_opera failure.

**Against the reject list.** No settings lever (nothing touches seed, steps, cfg, end guide, resolution or length). No mover is proposed at all, bounded or frame-filling. The zero return is not treated as proof of death. Nothing is accepted and nothing is written into committed art or hotspots — PIN_NON_MOVERS writes only `sceneSpec.rigid` and the motion prompt file. No hand-written art prompt; the prompt is rendered from the spec. Not AUTHOR_MOVER. None fires.

The one genuine weakness is that "rigid and fixed — does not warp, drift, breathe, shimmer or change shape" is a shape-stability clause aimed at a *spawned water jet*, and the prompt already carried "Only that moves; everything else stays perfectly still," which the hallucination survived. But naming the offending object explicitly is the documented escalation for exactly this class (egypt's amphorae pot), the art is intact so re-authoring would be wrong, and the defect sits on a `clue: true` hotspot so the clip cannot be held for Lucas's eye as it stands. This is the correct next move and it costs one clip re-render, not a still.

VERDICT: PASS
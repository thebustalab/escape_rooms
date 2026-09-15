I checked the clip and the code myself rather than taking the worker's numbers on trust.

**The measurements hold.** My own temporal-std map over all 73 frames: sky sits at a 0.93 noise floor, the tarpaulin peaks around 13–14, and the entire rock pavement sits at 6–9. The mover is only about 1.4× the ground it stands on.

**The diagnosis holds, and it's visible.** Crops of frames 0 / 36 / 72 at full resolution show the writing slab growing toward the camera, the filed report's drawn map lines rewriting themselves, the brass rule changing angle, and the river stone on the dispatch bundle visibly swelling. That is the puzzle object and the clue furniture morphing, not air shimmer over stationary stone. It's one-way and peaks at the last frame, which is exactly what produces the 0.625 breadth and the 0.0 return. The tarpaulin corner, separately, flogs convincingly and stays bounded to its corner.

**Against the reject list, it's clean.** No settings lever is touched. No new mover. The zero return is explicitly *not* treated as proof of death — the worker argues the opposite and backs it. Nothing is accepted and nothing is written to committed art or hotspots. The art prompt is authored through the spec, not hand-written.

**I dry-ran the pin.** The two-item clause renders a 64-word motion prompt that reads cleanly, and `render_prompt` comes back byte-identical, so `needs_still` stays unset and the committed panorama survives — only the clip re-renders. The runner code path at Utilities/long_agent/long_agent.py:4218 confirms that's how it behaves.

One thing worth flagging to you separately: the worker's phrase "the mountains behind it" is accurate to the **art** — there's a snow massif and glacier across the whole back of the frame — but the **spec** demands a bare empty horizon with "no mountain, no ridge and no snow anywhere along it" and nothing standing higher than the viewer. The committed still contradicts its own spec. That's a stills-phase divergence, not this cycle's decision, and it doesn't affect the pin (naming real mountains as rigid carries no hallucination risk). But anvil's art and anvil's spec disagree, and someone should decide which one is wrong.

VERDICT: PASS
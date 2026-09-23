I checked the room myself rather than taking the worker's account on trust.

**Verified independently:**
- **Prompt freshness** — I re-ran `render_prompt` on the current sceneSpec and diffed it against the committed `scenePrompt`: identical, 10,635 chars both. And scene.png and scenario.json share an mtime of 22:57, matching the `art_generated: 1` record in _long_agent/state.json. The still is what this spec produced.
- **The mover is there and bounded** — I cropped x=0.36 and looked. One glass globe on the dash with a pale luminous bloom inside it, sealed in glass, roughly 4% of panorama width. Not frame-filling, and physically unable to travel.
- **No doubling** — I swept the whole dash band across all 3072px. Exactly one globe, with the oval reading-pane at centre and the crystal cells plus lever to its right. The `nose` element names the globe too, but the "drawn exactly once" guard held.
- **One mover** — `sampler` is the only element carrying `motion`. The derived motion prompt is exactly what the worker quoted, and names only drift, turn and pulse inside the globe — no streaming or parting.
- **No clip exists** — nothing for ap_pileup under the cine output dir or the staged candidate pool, and the gate report is empty. Nothing to diagnose.

Against the six reject conditions: no settings are being changed (it renders at the already-settled recipe), the mover is bounded, no zero-return reasoning is involved, nothing is accepted or written into committed art or hotspots, the prompt is spec-derived rather than hand-written, and it proposes RENDER rather than a re-author.

One thing worth watching when the clip comes back, though it isn't grounds to block the render: the central reading-pane also holds a glowing swirl that resembles the bloom, so the model may animate it too. That's a defect only a render can reveal, and the sibling `cockpit` room held first render on this same element at this same position.

VERDICT: PASS
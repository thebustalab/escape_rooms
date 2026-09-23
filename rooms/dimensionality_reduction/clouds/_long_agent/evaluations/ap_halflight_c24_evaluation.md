Checked the evidence directly rather than the worker's summary:

**Mechanical claims — all confirmed**
- `scene_spec.render_prompt(sceneSpec)` == committed `authoring.scenePrompt`, byte-identical at 10473 chars. Art cannot be stale.
- `movers(spec)` returns exactly one: `eyewall` ("slow and immense, a steady turning", the funnel twisting on itself). All six other elements `motion: null`.
- `render_motion_prompt` → 30 words, locked-off camera, one oscillatory mover, no net travel.
- `params.json`: 3072×1024, end_guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242 — the settled recipe, unaltered.

**Gates — read against `cine_room.py` itself**
`ok = camera != "CAMERA MOVES" and not glitched and not dead`. Glitch fires only when `min(raw, normalised) >= 0.70`; here min(0.479, 0.500) = 0.479, so no rejection — and the worker correctly did not try to "improve" a reject-only reading. Dead `false`. Return 0.36 is above `RETURN_ALIVE`, so not even the ambiguous-zero note fires.

**Frames — my own diff, 7 samples across the raw clip**
Column energy across 12 bands: `[1.5, 1.9, 1.8, 2.1, 4.6, 3.7, 5.9, 7.2, 8.4, 8.8, 5.1, 1.9]`. Energy is concentrated right-of-centre on the funnel and the ring-current band beneath it; the city (left third) and the bottom row (dash, nose) are quiet. Only 21% of pixels exceed a std of 5 — bounded, not frame-filling. The visual diff shows the funnel and current lit up, the two glowing dash objects shimmering faintly, and the city, wings and shell near-black. No camera drift.

One imprecision in the worker's reasoning: it excused the sampler-globe shimmer as "`cockpit`'s own accepted mover", but `cockpit` is a different room and here the globe lives in `nose`, which is `motion: null`. That's a faint glow-shimmer on a lit object, well below anything the loop may auto-reject on, and the proposed action is HOLD — so it changes nothing about what the runner does; Lucas's eye sees it either way.

No reject criterion applies: no settings change, no frame-filling mover, no zero-return-means-dead, no acceptance or write to `scenario.json`, no hand-written art prompt, no premature AUTHOR_MOVER. The render happened in cycle 22; parking the survivor for a human is the correct terminal step.

VERDICT: PASS
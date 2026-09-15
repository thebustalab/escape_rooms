I checked the worker's timeline and mechanics against the artifacts rather than its summary.

**The stale-gate claim is true, and I confirmed it three independent ways.** `fenwatch_ri16_render.log` contains that gate JSON verbatim — `peak 8.73`, `return 0.0`, `breadth 0.208`, `at_pct 77.8` — stamped `DONE 20:37`, and `fenwatch_motion_ri16_looped.mp4` is timestamped 20:37:44. `scenario.json` is 20:51:19, matching the c19 evaluation to the second. Nothing in the beacons cine dir postdates 20:37. So the report on the table is the pre-pin render.

**The pin landed correctly and is not inert.** `authoring.sceneSpec.rigid` is a bare string on disk — the form `long_agent.py:4170` reads — not the dict that failed silently a cycle earlier; the spec is clean at 9 elements with `gutter_pour` the single bounded mover. I ran the real renderer:

- with `rigid`: 66 words, naming the drystone yard wall, the stone office range and its slate roof — exactly the three regions c19's frame-by-frame found warping to a final-frame peak
- without: 39 words, which is what ri16 actually rendered

So a re-render is a genuine change, not a no-op. And `render_prompt` is byte-identical with and without `rigid`, and matches the stored `scenePrompt` exactly — the committed still (20:21, predating the render) is not discarded, and `needs_still` won't fire.

**The mover is demonstrably real.** The pour region measured peak 19.24 at f35 with return 0.13 — alive and cyclic. The whole-frame 8.73 is that averaged against warping masonry, which is precisely the defect the pin targets. The worker does not read the zero return as death; it reads it as the averaging artefact the prior region analysis already resolved.

Nothing on the reject list applies: seed stays 4242 with no settings touched, the mover is bounded, no clip is accepted, no committed art or hotspots are written, the prompt comes from the spec, and it is not AUTHOR_MOVER on an unrendered mover.

One wording slip, immaterial: the "two-item scalpel" phrase quoted from cycle 19 describes a clause that names three things. The clause itself is correct and tight.

Holding would put a clip Lucas's pipeline has already diagnosed and fixed in front of the one scarce resource here. Re-render first.

VERDICT: PASS
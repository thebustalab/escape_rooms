Verified independently on disk:

**Prompt resolution** — exp_art_prompt.py:87-107 does resolve motion_prompt from authoring.sceneSpec first, with the .txt as fallback only when the spec declares no mover. anvil's spec declares one, so the .txt is dead weight here. Confirmed the .txt (art_prompt_motion/beacons/anvil.txt, stamped Sep 14 23:31) still carries the pre-soften "flogging and cracking" phrase and is genuinely stale.

**Live prompt** — rendered it myself via scene_spec.render_motion_prompt: 62 words, rigid pin auto-on (spec["rigid"] is populated), and the only mover named is the tarp corner — "lifting and settling slowly, breathing rather than flogging". heat_shimmer and depot_smoke carry `animate`, not `motion`, and correctly do not enter the motion prompt. This is a bounded near-field mover, not a frame-filling one.

**Softening is phrase-only** — diffed the anvil room against scenario.json.bak_20260915_075430_soften_three: exactly one changed line, fuel_tarp.motion.phrase. vigour, desc and everything else untouched. render_prompt(spec) against the committed authoring.scenePrompt is 7056 == 7056 and byte-identical, so the committed panorama stands and no still work is implied. All 12 rooms and their hotspot counts are intact.

**Never rendered** — the only anvil clip on disk is anvil_motion_ri53_looped.mp4 at Sep 14 23:45, which predates the 07:54 soften. No render process in flight.

Against the rejection list: no settings change (seed explicitly held at 4242), bounded mover, no zero-return reasoning invoked at all (gate report is empty), no clip acceptance and no write to committed art or hotspots, no hand-written art prompt, and it proposes RENDER rather than AUTHOR_MOVER — which is exactly the criterion an unrendered mover demands.

One small slip in the worker's write-up: it says the stale .txt "is what the brief displayed", but the brief actually showed the softened spec. That doesn't touch the conclusion, which I confirmed by rendering the prompt directly.

VERDICT: PASS
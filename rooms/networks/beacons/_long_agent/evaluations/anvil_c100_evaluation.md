I checked the worker's claims against the files rather than its write-up.

**The diagnosis is right, and I confirmed it on the frames, not on Lucas's description.** I ran a temporal-std map over the raw ri96 render, 64 px blocks, and the motion is not where the prompt asked for it:

| region | ratio to median |
|---|---|
| tarpaulin, left | **0.84×** |
| book / writing-slab | **7.34×** (p95 92.8) |
| spyglass | 1.25× |
| sky | 0.14× |

The tarp sits *below* the noise floor — it never moved. Every one of the top fourteen motion blocks lands in x 1408–1856, y 576–768, which at native crop is the open book on the slab. The model animated the wrong object outright. That is a wrong-subject failure, not a pace failure, and the clip's own gate line ("survived gates — needs Lucas's eye", return 0.05) played no part in the worker's reasoning.

**The fix is already authored, and it is motion-only.** Diffing the pre-image backup scenario.json.bak_20260915_084707_anvil_disambiguate against live, exactly two keys changed in room 6 (anvil): the mover phrase, and the rigid clause — which now reads "the pale writing-slab and the filed papers weighted on it" in place of a vague pavement-and-mountains catch-all that named nothing the model could hold. `vigour`, `desc`, committed art and hotspots are all untouched.

**The safety property holds.** I re-derived it myself: `render_prompt(spec)` is 7056 chars and byte-identical to the committed `scenePrompt` — so no new panorama is implied and needs_still cannot fire. The live motion prompt resolves through the spec path to 69 words, one named mover ("the loose corner of the waxed canvas tarpaulin"), one rigid pin. heat_shimmer and depot_smoke carry `animate`, not `motion`, and correctly do not appear.

**Nothing blocks the render.** Timeline confirmed by mtimes: ri96 finished 08:23:57 EDT, the disambiguation landed 08:47:07 — the only clip on disk predates its own prompt by twenty-four minutes. retry_count 0, pending_render null, rooms.anvil {}, seed stays 4242 so the fix isn't confounded with a roll. Settings are untouched (cfg 2.0, steps 8, end_guide 0.70).

Against the reject list: no settings lever, the mover is one corner of a left-field object rather than frame-filling, no zero-return death claim, no acceptance and no write into committed art or hotspots, no hand-written art prompt, and the verb is RENDER — not AUTHOR_MOVER on an unrendered mover. The decision also matches the review note's own instruction to render once and gate.

One cosmetic slip in the write-up: the rigid pin is a single string naming two items, not two clauses. It changes nothing.

VERDICT: PASS
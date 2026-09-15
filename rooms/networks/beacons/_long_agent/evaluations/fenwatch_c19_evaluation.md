I checked the worker's claims against the artifacts rather than its summary.

**Re-measured the raw clip myself, region by region** — my numbers land on top of the worker's: pour + butt peaks 19.24 at frame 35 with return 0.13 (alive and cyclic), centre office 9.30, right seam wall 10.47, left seam wall 7.91 — all peaking on the *final* frame with zero return, and the smooth sky quiet at 1.25.

**I pushed one step further than the worker did**, because a monotone whole-scene drift can also be a slow camera push. Block-matching frame 0 against frame 72 over ±48 px finds the best alignment at exactly zero displacement for every stone block — no translation, no zoom. The 8–10 grey-level residual on masonry survives every rigid transform, and the sky doesn't drift, which rules out an exposure shift too. So it is genuinely a non-rigid warp accumulating on textured stone, which is the `rigid` escalation's exact signature.

**Verified the mechanics end to end.** I ran the real renderer against the live spec: the art prompt comes out byte-identical with the rigid clause added, so `needs_still` won't fire and the committed still isn't discarded; the motion prompt is 66 words with the two pinned items. The runner's apply branch takes a bare JSON list straight into `spec["rigid"]` (long_agent.py:4170), and `exp_art_prompt.motion_prompt` flips `rigid=True` off that key, so the escalation actually reaches the render. The worker's account of last cycle's dict payload failing silently is corroborated by the evaluator note in state.json, and the spec on disk is clean at 9 elements.

Nothing on the reject list applies: no settings change, no new mover, no frame-filling subject, no acceptance, no hand-written art prompt, and it explicitly does not treat the zero return as death — it re-measured and found the mover alive.

VERDICT: PASS
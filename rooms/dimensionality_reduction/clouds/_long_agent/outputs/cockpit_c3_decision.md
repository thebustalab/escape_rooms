Everything checks out against the authority docs. Verified on disk:

- **The clip exists and was rendered once** at the canonical recipe — `3072x1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242` (`cockpit_motion_ri1.params.json`), crossfade + seam repair applied.
- **The motion prompt is spec-derived, not NONE.** `scene_spec.render_motion_prompt` resolves it from `sampler.motion.phrase`: 31 words, one bounded mover, purely oscillatory (drifting/turning/pulsing inside a fixed globe) — no travel. The brief's "NONE" is the absent `.txt` fallback, which is the correct state now the spec is the source of truth.
- **All three gates clear**, not marginally: camera `still` (frame0_corr 0.974, landmark drift 0 px); glitch breadth 0.146 on *both* readings against the 0.70 two-reading threshold (`spike` 30.94 is reported, never enforced); dead gate `false` with ratio 24.16 against a <1.75 floor and peak 17.74 against <0.45.
- **Return 0.28 is non-zero**, so the ambiguity escalation doesn't fire — and it sits right where `market_price` ships at 0.23. The runner's own verdict line already reads *"survived gates — needs Lucas's eye."*

No lever applies. There is no evidence of over-liveliness (no metric measures it, and canon forbids rejecting a clip off sampled stills — that fails toward false rejection), the mover is bounded at ~1.5% of frame with vigour already authored soft, nothing is known to be moving that shouldn't be, and re-rolling is not mine to propose.

DECISION: HOLD
WHY: The single render cleared the camera, glitch and dead gates with wide margins and returned a healthy non-ambiguous 0.28, so the spec, the still and the spec-derived motion prompt have done their job and the only step left is the human eye, which no metric may pre-empt.
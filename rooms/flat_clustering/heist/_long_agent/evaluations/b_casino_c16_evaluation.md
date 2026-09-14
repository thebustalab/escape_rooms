I checked the clip, the params, and the ledger rather than the worker's summary.

**What I verified:**

- **The clip is real and is the known render.** The looped mp4 is byte-identical (md5 `60e6512d…`) to b_casino_motion_f70cal70_looped.mp4 — same seed 4242, end guide 0.70, 3072×1024. So this is the exact b_casino full-res render the ledger already logs.
- **Peak 8.06 is not a coincidence.** The ledger line reads "b_casino 8.06 and verdigris 8.08–9.35 against hood's 5.1–5.2 at full resolution." The worker's number matches the recorded live-cyclic figure exactly.
- **The correction names this room.** The 2026-09-11 entry quotes Lucas directly: b_casino and logwood_verdigris are "alive at both settings with good loops," their movement "a cyclic thing with one full cycle per loop." The gate tool's own docstring says the same — cyclic flow rises monotonically and loops fine, and a zero return cannot be read as death.
- **The frames back it up.** Across the sampled frames the smoke plume over the near baize visibly changes shape and position, gathering and thinning, while the chandelier, cage, doors and tables sit still. The mover is bounded to the near table under the lamp — not frame-filling.

**Against the reject list:** no settings change proposed, no frame-filling mover, it does not treat the zero return as death (it argues the opposite), it does not accept the clip or touch scenario.json, no hand-written prompt, and no AUTHOR_MOVER on an unrendered mover. HOLD here is a park for a human eye, which is precisely what a zero return justifies.

One small inaccuracy worth noting for the record: the worker describes the glitch gate as rejecting "only when both readings exceed 0.70," whereas the ledger documents it as breadth ≥ 0.667, reject-only, on a single reading. At 0.354 raw and 0.021 normalised the clip clears either version comfortably, so the conclusion stands — but the worker's stated threshold isn't the documented one.

VERDICT: PASS
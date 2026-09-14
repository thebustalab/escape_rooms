I checked the gate code and the pixels myself rather than the worker's summary.

**The gate readings hold up.** `cine_room.py:76` convicts only when `min(breadth_raw, breadth_normalised) >= GLITCH_BREADTH_REJECT` — both readings here are 0.0, and line 43 says outright that `spike` "was never validated as a threshold, so it is reported, never used." The 2.97 spike is not a gate. `cine_return_check.py` sets `RETURN_ALIVE = 0.05` and its calibration comment names lantern at exactly 0.13 as shipped work, so 0.13 clears and the ambiguous-zero escalation never arms. Camera is still. `cine_judge.py:17` defines HOLD as "it survived every gate and now needs Lucas's eye" — so this is the pipeline's own vocabulary for a handoff, not an acceptance, and nothing gets written.

**What I found looking at the frames myself,** which the worker did not mention: the change is not concentrated on the swag. At the peak frame, after a 17px low-pass to strip grain, the far-right wallpaper — flat seam material that should be rigid — moves *more* (3.25) than the swag curtain (2.50). It is structural, not a brightness wobble: whole-frame luminance swing is 0.83 with a 0.31 max single step, far under the `background_swing` region where hold was convicted at 6.07/2.75. I also checked the panorama wrap: seam discontinuity sits flat at ~1.7 across all 16 samples, the same residual the committed still already had, so it is not tearing.

**That finding does not overturn HOLD, and arguably is the argument for it.** Concentration was tested as a discriminator and explicitly rejected in this very codebase — a gate would have killed `a_vault` — so diffuse-change is precisely the kind of unvalidated measure the pipeline forbids from convicting. The amplitudes are 3-4 grey levels of 255. No render remains this cycle, and there is no validated basis for AUTHOR_MOVER against the one element that is in fact the frame's strongest coherent mover. A human eye is the only thing entitled to rule on whether that diffuse shimmer reads as wrong — which is where HOLD sends it.

None of the reject conditions fire: no settings change, no frame-filling mover, no zero-return-as-death (the return is non-zero and argued alive), no acceptance or scenario.json write, no hand-written art prompt, no AUTHOR_MOVER on an unrendered mover.

One slip in the worker's reasoning, which changes nothing: 0.23 is quay's return, not `market_price`'s (0.49). Both are in the shipped set, so the point stands.

Worth passing to Lucas alongside the clip: look at the crimson wallpaper at the frame edges, not just the swag — the residual there is real, sub-perceptual by every number I can take, and only his eye can settle it.

VERDICT: PASS
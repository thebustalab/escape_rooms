I checked the worker's claims against the artefacts rather than its description.

**Verified independently**

- **Provenance** — `scene.png` committed 07:01, clip rendered 07:14, `scenario.json` 07:01. The clip animates a still newer than its own spec edit. Params sidecar: 3072×1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4711, no LoRA, empty speed clause — the pinned recipe from `plan.json`, unchanged.
- **The glitch rule, from the source not the worker** — `cinemagraph_tools/cine_glitch_check.py:22` states it plainly: *"rejects only when BOTH `breadth` readings — raw, and with `luma_normalise=True` — exceed 0.70"*, because neither is safe alone (raw convicts a_vault's lamp at 0.896, normalised falsely convicted whistlegate at 0.771). Raw 0.50 / normalised 0.708 does **not** reject. The worker's threshold is the documented one. (Its one-line mechanism gloss has the two readings' failure modes swapped — raw is what a light inflates — but it named the whistlegate pattern and the gating conclusion is right.)
- **The spike is a lightning flash, not a distortion.** I pulled frames 62–66 and built amplified consecutive diffs: the event at 87.5% is confined to the eyewall on the right, with fork structure legible in the residual. The city side and the entire foreground are black across that transition. No "all the pixels go weird" signature.
- **The dash is stable.** Region-wise mean |f − f0| over all 73 frames: dash centre **1.53** (max 1.77), bottom band 1.79 — against storm right **12.95** and city left **3.59**. The energy sits in exactly the two approved movers; the foreground stays sharp.
- **Structure holds.** Frame 0 vs mid at native crop on the storm side: the funnel column, cloud bank and wing rim are in the same places; what changes is illumination. Camera gate's `frame0_corr` 0.982 / `landmark_drift_px` 0 / `loop_jump` 4.8 are real — they're in `cockpit_ri3_render.log:2`, and my own loop-jump measurement (4.43 on downscaled luma) agrees.
- **Return 0.48** is non-zero, so the ambiguous-zero trap is not in play, and the difference profile rises to ~12 mid-loop and returns — an out-and-back, not drift.

**Against the reject list:** no settings proposed, no mover authored (frame-filling or otherwise), no zero-return reasoning, no acceptance and nothing written to committed art or hotspots, no hand-written prompt, and not AUTHOR_MOVER. The pipeline's own log already recorded `"verdict": "survived gates — needs Lucas's eye"`, which is what HOLD hands on.

VERDICT: PASS
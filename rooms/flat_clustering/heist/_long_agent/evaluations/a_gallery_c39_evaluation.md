I pulled the ri35 frames and measured them myself rather than taking either the gate number or the worker's account on trust, and I checked the room's on-disk history against the prompt's `attempt_history` (which is stale — it lists only c35).

**Independent frame measurement.** 73 frames, mean-corrected absolute difference against frame 0, 8×24 block map:

- One region is hot and it is *bounded*: blocks at column 8/24 (x ≈ 0.33–0.38), rows 4–6 — peak activity **11.0 / 14.8 / 7.5** against a background of ~3 everywhere else. x 0.36 is `_POS["just left of centre"]`, which is exactly where the spec places the `sheet` element. The mover the spec authored is the mover the clip is animating, and it occupies about one twenty-fourth of the frame — bounded, not frame-filling.
- Its temporal profile is a clean arc: **0 → 5.27 peak at f41 → 2.43 at f72**, i.e. it falls back **54% off peak** before the clip ends. That is an out-and-back excursion.
- Everything outside that box rises to ~1.9 by f18 and then plateaus (peak 1.90 at f53, 1.88 at the end) — a diffuse whole-frame creep, not a mover.

So the gate's `return: 0.0` is a localised arc swamped by global drift. That is the documented false-dead, and the gate note itself flags it. My numbers differ in scale from the c38 evaluator's (different box and downscale) but agree in every structural respect.

**History check.** `_long_agent/state.json` confirms `cycles_completed: 38`, `attempts: 1` (1 of 2 renders), `retries: 2`; `progress.md` records c37 (ADJUST_VIGOUR → REVIEW) and c38 (ADJUST_VIGOUR → FAIL). The "too aggressive" note is Lucas's own, recorded in `notes/cinemagraph_pipeline.md:288`. The worker's account of state is accurate.

**Against the reject list.** No settings change proposed. No frame-filling mover. It does not treat the zero return as proof of death — it argues the opposite from frames and routes to a human eye, which is precisely what a zero return is allowed to justify. It accepts nothing and writes nothing into `scenario.json`. No hand-written art prompt. No AUTHOR_MOVER on an unrendered mover.

PARK is a legitimate terminal state under `done_criteria` ("PARKED with a specific stated reason a human can act on"), the WHY line parses as one line and carries an actionable reason, and the two questions survive in `outputs/a_gallery_c39_decision.md`. Parking preserves the last render for whatever Lucas actually says instead of spending it on an inference two evaluators have already rejected.

VERDICT: PASS
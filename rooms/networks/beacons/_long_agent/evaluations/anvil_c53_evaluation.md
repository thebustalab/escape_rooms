I verified every load-bearing claim independently rather than trusting the worker's table.

**The staleness claim is true, and the run's own log proves it.** From progress.md (UTC, local = −4):
- 03:12 UTC — anvil render launched
- 03:23 UTC — gated at return 0.0, peak 10.04, breadth 0.625 — *byte-for-byte the gate report on this table*
- 03:31 UTC — "PIN_NON_MOVERS applied. The art prompt is unchanged... only the clip needs re-rendering."

So the numbers I was handed were measured eight minutes *before* the fix existed. Holding on them would discard the fix and preserve the pre-fix render.

**The pin is real and it reaches the renderer.** This was the claim worth checking hardest, because anvil carries *two* rigid fields — a new two-item one in the scene spec (scenario.json:2449) and a long legacy one in a `motionSpec` block (:2476). I traced which one actually lands:

- long_agent.py:4209 calls `render_motion_prompt(spec, rigid=...)` on `spec["rigid"]` — the scene-spec one — and writes the result to cinemagraph_tools/art_prompt_motion/beacons/anvil.txt.
- `_launch_cine_room` passes no prompt; cine_room.py reads that persisted file.
- That file is stamped 23:31:42, is 64 words, and carries the two-item clause. ri50 rendered at 23:20:25 — **11 minutes earlier**, from the unpinned prompt.

The legacy `motionSpec.rigid` is not on this code path, so it doesn't contaminate the pin.

**The still is safe.** The runner only sets `needs_still` when `render_prompt(spec)` actually changes, and `rigid` appears nowhere in `render_prompt` — confirmed in state.json: `needs_still` unset, not parked. The committed panorama survives; only the clip re-renders.

**Against the reject list, clean.** No settings lever (end guide 0.70 is the plan default, unchanged). No new mover, frame-filling or otherwise. The zero return is not treated as death — the decision argues the opposite and backs it with the timeline. Nothing accepted, nothing written to committed art or hotspots. The prompt is spec-derived, not hand-written. Not AUTHOR_MOVER.

Guards clear: attempts 1 of max 2, no render in flight, status working.

Two things for the record, neither blocking. This render spends anvil's **last** attempt — a second failure parks the room rather than getting another try. And the prior cycle's flag still stands unresolved: the art shows a snow massif across the back of the frame while the spec demands a bare empty horizon with "no mountain, ridge or snow anywhere along it." The pin naming those mountains is harmless since they're genuinely in the image, but anvil's art and spec contradict each other and that's a stills-phase question someone should settle later.

VERDICT: PASS
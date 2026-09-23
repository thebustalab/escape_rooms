Verified independently, not from the worker's description:

**Gate code** (`cinemagraph_tools/cine_room.py:52-108`) and constants read directly:
- `GLITCH_BREADTH_REJECT = 0.70`, and rejection uses `min(raw, normalised)` — 0.146/0.146 is nowhere near firing.
- `DEAD_RATIO = 1.75`, `DEAD_PEAK = 0.45` — report gives 20.59 / 18.03, `dead: false`.
- `RETURN_ALIVE = 0.05` — return 0.08 is above it, so no ambiguity `note`, and the worker is not treating return as a death certificate.
- `camera: "still"` ≠ `"CAMERA MOVES"`. So `ok = True`, and no `auto_rejected` key.

**Render params** (`ap_pileup_motion_ri10.params.json`): cfg 2.0, steps 8, end_guide 0.7, seed 4242, 3072×1024, 73 frames — the settled recipe untouched. Nothing in the decision proposes a settings change.

**The clip itself** — I sampled the raw render and computed a per-pixel motion map: moving area is **9.2% of frame**, concentrated in x 0.25–0.62 with the hottest pixel at x=0.326, y=0.711, i.e. the sampler globe on the left of the dash. That is a bounded mover, not a frame-filling one. Frames at n=0/40 confirm the glass globe with the luminous bloom turning inside it, dash and reading-pane intact, no tearing or collapse.

**HOLD semantics** (`long_agent.py:4461`): sets `held`, stages the clip into the harness review pool, logs "NOT accepted." It writes nothing into `scenario.json`'s committed art or hotspots. No hand-written prompt, no AUTHOR_MOVER on an unrendered mover.

No reject criterion is met, and the gates are genuinely all clear. One thing worth Lucas's eye when he looks — the blooms above the dash read larger and looser by mid-clip than the globe-bounded bloom the spec describes — but that is a content judgement, and HOLD is precisely the route that puts it in front of him rather than spending more GPU on it.

VERDICT: PASS
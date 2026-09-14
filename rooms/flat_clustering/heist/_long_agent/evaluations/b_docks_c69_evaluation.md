I checked the render myself rather than taking the worker's word.

**Params** (`b_docks_motion_ri67.params.json`): end_guide 0.70, 3072×1024, 73 frames, steps 8, cfg 2.0, seed 4242 — the pinned defaults. Nothing was touched.

**My own localisation** (independent downsample, 73-frame raw clip):
- Per-column temporal std: background ~0.9–1.9 across the whole panorama, one blob at **x 0.125–0.22** rising to 7–8 on band means. Vertical extent y≈0.25–0.72, peaking 16–21 at y 0.31–0.44.
- Restricted to that band: **peak 9.1, argmax frame 27/72, return 0.30** — a mid-clip out-and-back arc, not a monotone one-way rise.
- Secondary bumps at x≈0.25–0.28 (3.25) and x≈0.81–0.86 (2.06) — small, and they sit on wet quay and lamp reflections seen through the hatch and the gangway door.

The worker's figures (11.4/12.1, peak 10.26, return 0.34, argmax 28) differ from mine only as you'd expect from a different downsample — same structure, same conclusion. Not fabricated.

**By eye**: frame 0 the tarp hangs lashed flat against the hatch edge; frame 27 a panel billows wind-filled into the opening; frame 72 it's back near hanging. Correct object, cloth behaviour, bounded to roughly a tenth of the frame. Crane, ship, barrels, board, terminal, crates all static. No people, no lettering.

Against the reject list: no settings change, no frame-filling mover, no zero-return-as-death argument (the opposite), no acceptance and no write to scenario.json, no hand-written prompt, no AUTHOR_MOVER. HOLD parks a live clip for your eye, which is exactly where a "is the billow too much?" question belongs.

VERDICT: PASS
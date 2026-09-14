I read the four evidence files, then checked the room itself on disk.

The spec already satisfies the one thing that governs animatability: a **bounded depicted mover** — the tarpaulin at the loading hatch, with vigour written into its `desc` ("flapping and snapping in the wind off the water"). I confirmed against the cached art prompt (`_scratch/.l1prompt_b_docks.txt`) that the committed `scene.png` was rendered from this exact spec, through `render_prompt` — equirect clause, seam anchor at head and tail, all present. And I looked at the still: the tarp is there, bounded, occupying about a quarter of the hatch, not frame-filling.

The ledger settles the rest. In the 2026-09-11 calibration factorial, b_docks is one of the four heist rooms **alive in all 16 cells**, with crisply nameable per-seed types (billowing / swishing / opening-and-closing) and no camera flags reported. That grid was run on this same committed still. The ledger line "b_docks barely moves" refers to its seed-divergence *metric* barely changing between resolutions, not to the room being quiet.

The motion prompt is already in house form, names the tarp and nothing else, ~34 words. Gate report is empty and nothing has been tried — so there is no clip to judge, and the pipeline's order is render once, then gate, then fix. Lowering or raising vigour now would be tuning ahead of evidence on a still a human has already triaged and committed.

DECISION: RENDER
WHY: The spec carries a bounded depicted mover with authored vigour, the committed still was rendered from that spec and is documented alive in all 16 calibration cells, the motion prompt names that mover and nothing else — so the only thing missing is the one render at 3072x1024, end guide 0.70.
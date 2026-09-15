Evidence read; state verified. Findings:

- **Spec on disk matches** what I was handed: `blade_spout` is the only element with a `motion` block (`moves`/`vigour`/`phrase`), so `_has_authored_mover` sees it and the motion prompt resolves from the spec — `render_motion_prompt(rigid=True)` reproduces the given prompt byte-for-byte, 65 words, rigid clause naming **one** thing (scalpel, not the 7-item inventory that drove a_opera's camera).
- **The still depicts the mover.** The current `scene.png` (3072x1024, regenerated 2026-09-15 01:20) shows a thick spout jetting from the blade face, arcing clear of the rock into a worn basin — bounded (~15% of frame width), with the authored vigour visibly rendered. This is the condition the whole loop rests on, and it is met.
- **The room's dead/too-fast history is all the old cloud subject at 1536** (ledger: "too fast at 0.75", seed-confounded sweeps). Irrelevant here — the mover is now the spout, not the lenticular, and `lenticulars` carries only a legacy `animate` block so it is absent from the motion prompt.
- **`state.json`'s `review_note` is explicit**: shears held a good clip overnight and was dropped only because a scenario-wide seam pass restamped its still after the render. *"The art is CORRECT and CURRENT; do NOT regenerate it and needs_still must not fire. Render each ONCE against the art as it stands and gate."* Sibling rooms spindle (c88) and rams_head (c90) already took that path; `rooms.shears` is `{}`.

Nothing to author, soften or pin. This is step 3.

DECISION: RENDER
WHY: The spec carries one bounded mover whose authored vigour is visibly depicted in a current 3072 still, the spec-derived motion prompt names only that spout with a single-item rigid clause, and no clip exists against this art — so one render at the pinned 0.70 is the whole remaining move.
I read the four authority docs, then checked the live spec, the clip on disk, and the render log against the gate report I was handed.

**The gate report is stale — it describes the clip from BEFORE last cycle's fix.**

- `fenwatch_ri16_render.log` shows the render ran 20:28–20:37 and emitted that exact JSON, byte for byte: `peak 8.73`, `return 0.0`, `glitch.breadth 0.208`, `at_pct 77.8`.
- The `rigid` pin from cycle 19 was written into `scenario.json` at **20:51** — fourteen minutes *after* that render finished.
- Nothing newer than `fenwatch_motion_ri16*` (20:37) exists in `temp/cine/_art_prompt_exp/beacons/`, and `attempts: 1` in `state.json` confirms exactly one render has ever happened on this art.

So the only clip in existence is the un-pinned one, whose defect cycle 19 already diagnosed region by region: the pour alive and cyclic at peak 19.24 / return 0.13, while the office and both seam walls warped to a final-frame peak with zero return. That is what the whole-frame 8.73 is averaging over.

**The fix is on disk and the prompts are correct.** The spec carries one bounded authored mover (`gutter_pour`, with its vigour), nine elements, no junk. `render_motion_prompt(rigid=True)` gives 66 words with the two-item scalpel — the a_opera register that held the camera, not the seven-item 176-word version that broke it. `render_prompt` still carries the equirect clause and the pour's vigour, so the still isn't discarded. And the committed `scene.png` genuinely depicts it: an unbroken rope of meltwater from the spout into a brim-full slate butt, slopping over onto the cobbles — bounded, hard-edged, and squarely in the ledger's confirmed-mover list.

Holding here would put a superseded clip in front of Lucas's eye, which is the one scarce resource in this pipeline. Re-pinning would be a no-op. Re-authoring would contradict the measurement that this art's mover is alive.

DECISION: RENDER
WHY: The rigid pin landed in the spec at 20:51 but the only clip on disk is ri16 from 20:37, so the gate report on the table is the pre-fix render — the spec, the 66-word pinned motion prompt and the committed still are all correct and no clip has yet been rendered from them.
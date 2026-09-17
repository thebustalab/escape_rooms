I read the pipeline, report, ledger, and `scene_spec`, then checked what actually drove this render.

**What I verified rather than assumed:**

- The brief's "current motion prompt" (ceiling water over the car) is the stale `art_prompt_motion/subway/logwood_verdigris.txt` fallback — the documented drift case. The spec is the source of truth and `render_motion_prompt` on the live spec returns the canvas-sheet phrase, which is what cycle 30 rendered.
- Where the motion actually is: per-tile wander on the RAW render (768×256, 24×8 tiles, brightness removed) puts every high tile in one narrow full-height column at x≈0.73, peaking 42.5 against a 1.56 median. Everything else sits at the noise floor — nothing that should be still is moving.
- What is at x≈0.73 in the still: the hanging pale canvas drip-tarp, bounded, hanging free of the wall. The mover the spec authored is the mover the clip animates.
- Amplitude (peak 7.72) sits inside the band of this scenario's other held clips (8.02–9.56); not too lively, not quiet.

The only flag is the 0.03 return, which is the settled dead-or-cyclic ambiguity — and the dead gate independently says alive (ratio 19.65, peak 10.67), with the localised signature above. That is an escalation, never a rejection.

DECISION: HOLD
WHY: The clip cleared every reject-only gate and its motion is measurably confined to one narrow full-height column at x≈0.73, exactly where the still depicts the authored drip-tarp, so there is nothing left for this loop to author or soften — only Lucas's eye to queue.

Worth flagging for a human, outside this cycle: the stale `.txt` fallback for this room still names ceiling water that the art does not contain. It did not affect this render, but it is the exact two-sources-of-truth drift the spec-first design exists to prevent, and deleting it would remove the trap.
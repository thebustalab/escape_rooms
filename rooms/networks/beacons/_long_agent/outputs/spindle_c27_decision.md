I read the four documents, then checked this room's actual state on disk rather than relying on the summary.

**What I found**

- The "current motion prompt" in my brief is the **stale `.txt` fallback** (the old spindrift sentence). It is not what rendered. `exp_art_prompt.motion_prompt` resolves `authoring.sceneSpec` first, and for spindle it emits the 36-word cloth prompt: *"…The broad white signal cloth on its frame snapping and rippling in the updraught, its weighted lower corners kicking. Only that moves…"*
- `spindle_motion_ri25.params.json` confirms the house recipe: 3072x1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242, and `bake_loop` was called with `mask=None`, so nothing was masked to the old `needle_spindrift` box.
- I measured where the motion actually is, per-tile temporal std on the raw render. It is concentrated at **x 0.08–0.25, y 0.25–0.62** — the `day_cloth` position (`at: "to the left"` → 0.20), peaking at 41.95. Every other band in the frame sits at the 1.4 noise floor, including the needle at x 0.36. So exactly one bounded mover animates, it is the authored one, and the spindrift the re-author brief demoted is genuinely still.

**The gates**: camera still; return 0.14 (real out-and-back, in the range of the shipped Egypt clips at 0.13–0.51); glitch breadth 0.104 raw and 0.042 normalised, both an order of magnitude under the 0.70-on-both threshold. Nothing rejects.

DECISION: HOLD
WHY: The clip cleared all three reject-only gates and the motion is measurably confined to the authored signal cloth with the rest of the frame at the noise floor, so there is nothing left for the loop to fix and the only remaining step is Lucas's eye.

Two things worth flagging for the record, neither of which is a decision I can take here:

- `cinemagraph_tools/art_prompt_motion/beacons/spindle.txt` still names the spindrift plume. It is inert (the spec wins), but it is precisely the two-sources-of-truth drift the one-spec design exists to prevent, and it is what made my brief's "current motion prompt" wrong. It should be deleted or rewritten when someone is next in that directory.
- The cycle-25 evaluator note in `state.json` argues the runner resolves through `cine_iterate.py` → `motion_spec.render_prompt(authoring.motionSpec)`, which would have rendered the old spindrift hero. That is not the path this render took — the clip is in `_art_prompt_exp/` and carries the cloth prompt. The objection may still be live for the `cine_iterate` path, but it did not affect this render.
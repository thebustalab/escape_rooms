I read the four authority documents, then checked the room's actual on-disk state.

**What I found:**

- The spec carries exactly one bounded mover — `drip_tarp`, with `motion.moves`, an authored `vigour` and its own `phrase` — at `just right of centre`, a closed-vocabulary position.
- `scene_spec.render_motion_prompt` resolves cleanly from that spec to: *"locked-off static camera, zero camera movement. The loose canvas sheet billowing gently and slowly in the draught from the tunnel, swelling and falling back. Only that moves..."* — one mover, named, ~35 words, house form.
- The "current motion prompt" quoted in my brief is the **stale `.txt` fallback** (the ceiling water — this room's own historical drift case). It is dead text: `test_motion_prompt_source.py` pins subway in `SPEC_SCENARIOS`, so the spec wins and the `.txt` is never read. No action needed, and nothing to fix in the spec on account of it.
- `scene.png` was regenerated at 15:55 today from the current spec, and I looked at it: the tarp is plainly depicted — a pale oiled canvas sheet hung from a roof pipe just right of centre, hanging free with a loose hem, bounded to roughly a sixth of the frame width. Not frame-filling, and it reads at the slack/gentle register the vigour asks for.
- `state.json` has `art_generated: 1` and no history, no attempts, no clip. The gate report is empty because nothing has been rendered.

Spec right, prompt right, still right, no clip. That is the RENDER case.

```
DECISION: RENDER
WHY: The spec declares one bounded mover — the drip_tarp — whose authored vigour the freshly regenerated still plainly depicts just right of centre, the motion prompt resolves from that same spec naming only that sheet at the gentle register, and no clip exists yet, so the single default render at 3072x1024, end guide 0.70, is the next step.
```
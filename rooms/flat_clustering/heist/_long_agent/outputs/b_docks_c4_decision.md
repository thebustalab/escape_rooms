Verified against the live spec: the migration renders both prompts byte-identically.

**DECISION: AUTHOR_MOVER**
SPEC: {"id": "tarp", "at": "to the left", "desc": "a heavy canvas tarpaulin lashed at the open loading hatch", "motion": {"moves": true, "vigour": "flapping and snapping in the wind off the water", "phrase": "the heavy canvas tarpaulin lashed at the open loading hatch billows and slackens in the wind off the water"}}
WHY: The bounded mover is already depicted and proven — b_docks is alive in all 16 cells of its calibration grid — but its vigour lives in a legacy `animate` block that `_has_authored_mover` (long_agent.py:3549, needs `motion.moves` + `vigour` + `phrase`) cannot see, so RENDER is refused unconditionally as it was in cycle 3; this fragment moves the same authored text into `motion.{moves,vigour,phrase}`, which I ran through `scene_spec` and confirmed leaves `render_prompt` byte-identical to the committed art prompt and `render_motion_prompt` byte-identical to `art_prompt_motion/heist/b_docks.txt`.

**For your eye, Lucas:** the runner will set `needs_still` and park the room, telling you to regenerate the art on :8752. Don't — the art prompt is unchanged, so the existing `scene.png` is exactly what a regeneration would produce. The cheap lever is:

`touch rooms/flat_clustering/heist/b_docks/scene.png`

That clears the staleness block and lets the render fire next cycle without discarding a human-triaged, seam-clean still. This is the same spurious park a_vault hit; b_docks was the identical shape, and these two were the only heist rooms carrying the legacy field.
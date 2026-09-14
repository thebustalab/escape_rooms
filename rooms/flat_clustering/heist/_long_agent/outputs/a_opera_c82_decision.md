I've reconstructed the room's state on disk rather than trusting the brief's summary. Here's what's actually true:

**The cycle-81 edit landed and nothing has been rendered since.**
- The live spec (`rooms/flat_clustering/heist/scenario.json`, room `a_opera`) carries the c81 phrase verbatim: *"…stirring slowly in a draught, its folds shifting a little and settling"*.
- `SS.render_prompt(spec)` on that spec is 3129 chars and **byte-identical to the stored `scenePrompt`** — so `long_agent.py:4089` did not set `needs_still`, and `state.json` confirms the room carries no `needs_still` and no `parked`. Lucas's reviewed still, including the lighter sizing, is untouched and still correct for this spec.
- `cinemagraph_tools/art_prompt_motion/heist/a_opera.txt` was rewritten at 12:57 (the c81 cycle) and now holds exactly the 39-word spec-derived prompt the brief quotes — the brief is no longer stale on this room.
- The newest clip on disk is `a_opera_motion_ri78` (rendered 12:36–12:45, **before** the 12:57 edit). `last_gate` and `clip` in state both point at ri78. There is no ri81 anything.

So the gate report in the brief is the *old* wording's clip, already resolved as dead by direct measurement at cycle 80/81 (swag band temporal std 0.83 against a frame median of 0.86 — no localised variance, which rules out the cyclic-flow reading the zero return leaves open). The new wording is unrendered.

**Budget:** `max_attempts_per_room: 2`, `attempts: 1`. One render remains — exactly the size of this job.

No rung of the fix ladder applies: the mover exists and is bounded and authored (`motion.moves` + `vigour`), the art prompt is unchanged so no still is owed, softening is the wrong direction (ri78 is dead, not lively), and re-authoring off a clip whose prompt has since changed would spend the art lever on a question the pending render answers for free.

DECISION: RENDER
WHY: The cycle-81 phrase edit is live in the spec, leaves the art prompt byte-identical so no still is owed and `needs_still` is unset, and has never been rendered — the newest clip (ri78) predates the edit by twenty minutes, so the one render left in budget buys Lucas a third measured point between his too-aggressive ri75 and dead ri78 instead of a blind question.
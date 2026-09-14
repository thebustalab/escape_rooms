Checked independently rather than on the worker's word:

- **No clip exists.** `a_opera/` holds only `scene.png` + `scene.judge.json` (Sep 5); no mp4/webm anywhere under the scenario, and the room record carries only `panorama`/`builtFrom`. Gate report and attempt history are genuinely empty, so `RENDER` is the pipeline's first step, not a retry.
- **The mover is authored and bounded.** `swag` carries `moves`/`vigour`/`phrase`, so `_has_authored_mover` returns true. In the committed 3072×1024 still the swag is a gathered crimson velvet curtain with tieback and bullion fringe occupying roughly 15% of the frame at the left — hanging cloth, bounded, not frame-filling.
- **Motion prompt verified by running it.** `SS.movers(spec)` returns exactly `['swag']`, and `render_motion_prompt` emits: *"locked-off static camera, zero camera movement. The heavy velvet swag curtain breathing slowly in the draught. Only that moves; everything else stays perfectly still. Seamless natural loop."* House form, one mover, oscillatory — matches the worker's quote verbatim.
- **The caution about not regenerating is correct, and I confirmed the reason.** `SS.render_prompt(spec)` is no longer byte-identical to the committed `authoring.scenePrompt`, so a re-render would replace a human-triaged still (`verdict: hold`, five recorded concerns) with different art. Not warranted before a clip exists.

Against the reject list: no settings lever proposed, mover is bounded, no zero-return reasoning invoked, no clip accepted, no hand-written art prompt, and it is not AUTHOR_MOVER on an unrendered mover.

VERDICT: PASS
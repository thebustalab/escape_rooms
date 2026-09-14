I verified each load-bearing claim against disk rather than the writeup.

**Confirmed:**
- `_has_authored_mover` will pass. The lamp carries `motion.{moves, vigour, phrase}` in `scenario.json` (all three required at `long_agent.py:3549`). The 17:02 migration landed it.
- `render_motion_prompt(spec)` is **byte-identical** to `cinemagraph_tools/art_prompt_motion/heist/a_vault.txt` — I ran it, didn't take it on trust. `render_prompt(spec)` is also exactly equal to the stored `scenePrompt`. Nothing hand-written.
- **The mover is bounded.** I looked at `scene.png` at size: a small caged bulb on a flex, hanging left of the bench in an otherwise very dark frame. The box-fronts are matte-dark, not mirror-bright, so the "in and out of relief" clause is a local light sweep, not a global strobe. All five checklist objects are depicted; both extreme edges are the same riveted steel.
- **No settings lever.** The RENDER branch (`long_agent.py:3855`) passes only `--end-guide` from `plan["end_guide"]` (0.70). The worker proposes no seed, steps, cfg, resolution or length change.
- **The still cannot block.** `state.json`'s `rooms` is `{}`, so `rs.get("needs_still")` is falsy and the guard at `:3835` does not fire. More to the point, Lucas's own `review_note` in that state file says a_vault "demonstrably animates. Proceed normally" — he has already adjudicated this exact question.
- Nothing accepts a clip or writes committed art/hotspots; no zero-return reasoning; not AUTHOR_MOVER.

**Three loose claims in the writeup, none of which change the decision:**
1. "`scenePrompt` is empty on this room" — false, it's 3076 chars. The overwrite hazard genuinely doesn't bite, but for a better reason: `render_prompt` already equals it exactly, so a rewrite is a no-op.
2. "`temp/cine` is empty" — false. There are 96 a_vault artifacts in `temp/cine/_art_prompt_exp/heist` from the 16-cell grid. But no *pipeline* clip at the pinned default, no verdict JSON, `pending_render` is null, and the render writes to a fresh `ri5` tag, so nothing is clobbered.
3. The cycle-2 edit was not a pure round trip — `scenePrompt` went 1737 → 3076 chars. I diffed it: every added sentence is panorama-discipline boilerplate (EQUIRECT, EDGE DISCIPLINE, ground-is-one-surface, camera line). **No element line changed** — the lamp and its vigour clause are identical in the prompt that produced the still. So the hazard the `needs_still` guard exists to catch ("a motion prompt naming a mover the still does not contain") does not exist here; the lamp is visibly in the frame.

The worker was also right to flag the 0.896 raw glitch breadth and *not* act on it — that is `cine_room.py`'s own reject-and-re-roll path, not grounds to touch the art.

The decision survives independent verification: a bounded depicted mover, machine-readable, prompts derived from the one spec, a still that contains it, no clip yet.

VERDICT: PASS
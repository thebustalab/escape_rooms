Read the four evidence files, then checked `a_opera` on disk rather than trusting the empty gate report.

**What the disk says.** The room *does* have a clip — `a_opera_motion_ri20_looped.mp4`, baked 2026-09-13 20:04, camera still, return 0.13, glitch breadth 0.0, "survived gates". But `scene.png` was committed at **22:24 that night**, two hours and twenty minutes *after* that bake. The committed `scenePrompt` (3129 chars) is byte-identical to what `render_prompt` produces from the current spec, and it differs from the 1834-char prompt in place when ri20 rendered. So ri20 animates the superseded panorama — the one with Lucas's "massive" lighter and the breathing wall. There is no clip for the current art.

**The spec is render-ready.** One bounded mover (`swag`, at `to the left`), `motion.moves`/`vigour`/`phrase` all present so `_has_authored_mover` sees it; the vigour rides into the art prompt as verified above. The `rigid` string auto-trips the escalation clause in `exp_art_prompt.py:98` — the motion prompt it will build names the panelled walls and mouldings as "rigid and fixed — they do not warp, drift, breathe", which is exactly the fix for Lucas's wrong-thing-moving note. "Motion prompt: NONE" just means no `.txt` fallback exists; the spec is the source of truth and resolves cleanly.

Nothing to author and nothing to adjust — the depicted vigour is already at the gentle end, and softening it further without a clip of this still would be tuning blind.

DECISION: RENDER
WHY: The current still is 2h20m newer than the only existing clip and was generated from a materially different prompt, so this art has never been rendered — it needs the one sanctioned 3072x1024 pass at end guide 0.70 before any further judgement is possible.
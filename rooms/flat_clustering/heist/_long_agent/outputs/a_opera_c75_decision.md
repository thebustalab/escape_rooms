I've read all four authorities and verified the room's live state on disk.

**What the evidence says:**

- **The last render, ri73 (10:24–10:33 today), was REJECTED for `CAMERA MOVES`** — glitch breadth was clean (0.104 / 0.083), return 0.68, so the fault was drive/prompt, not a glitch. Per the pipeline a camera rejection is never re-rolled, so it needed an authored change.
- **That change has been made, by a human, after the rejection.** `state.json`'s `review_note` diagnoses the drift as caused by the pin itself: the `rigid` clause had grown to seven named things, pushing the motion prompt to 176 words, and a long prompt that re-describes the scene is a documented cause of drift (ledger §"Enumerating what stays frozen", evidence against twice). The clause is now just *"the panelled walls and the gilded box parapet"*. `scenario.json` was written 11:35, an hour after ri73 rendered.
- **I checked which prompt the render will actually use, because the previous cycle's evaluation got this backwards.** It claimed `cine_room` reads the persisted `art_prompt_motion/heist/a_opera.txt`. It does not: `cine_room` shells out to `exp_art_prompt.py --arms motion` with no `--motion-file`, and `motion_prompt()` returns the spec-rendered prompt whenever the spec declares movers — the `.txt` is fallback only. I rendered it: **61 words**, matching the review_note exactly. The stale 104-word `.txt` (07:39) cannot fire.
- `movers(spec)` returns exactly one bounded mover, `swag`, carrying `motion.{moves,vigour,phrase}`, so `_has_authored_mover` passes and RENDER won't be refused.
- **No art change is pending.** `render_prompt(spec)` is byte-identical to the stored `scenePrompt` (3129 chars both), and `rigid` is not an input to `render_prompt` — so the committed `scene.png` (2026-09-13 22:24) is still the right still. No `needs_still`, no `parked`, attempts reset, budget 3.

The only thing that has never been rendered is the shortened pin. Both of Lucas's earlier notes on this room are already folded into the spec — the lighter is now sized at natural scale, and the breathing wall is what the pin addresses.

DECISION: RENDER
WHY: The spec carries one bounded mover with authored vigour, the committed still matches its own unchanged art prompt, and the human's shortened 61-word rigid clause — the authored fix for ri73's camera rejection — postdates every existing clip, so the correct next act is one sanctioned 3072x1024 pass at end guide 0.70 and a gate.
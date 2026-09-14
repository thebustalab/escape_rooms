I reconstructed the room's state on disk rather than trusting the brief's fields — its "Current motion prompt" is once again the stale `cinemagraph_tools/art_prompt_motion/heist/a_opera.txt` (the swag curtain), which is a FALLBACK and is unreachable for heist: `exp_art_prompt.motion_prompt` resolves from `authoring.sceneSpec` whenever the spec declares movers, and this one does.

**The state is exactly what Lucas's review note asked for, and it has never been rendered.**

- `review_note`: *"the candles are all drooping and weird — need a much gentler prompt, just gentle flickering"*, with the explicit instruction that the still is correct, `needs_still` must NOT fire, and the fix is the softened phrase plus the candle bodies pinned rigid. *"Render once and gate."*
- The spec now carries one bounded mover — `sconce`, three candle flames, with `moves` + authored `vigour` + the softened `phrase`. Flame is a confirmed mover category and is bounded by its own physics.
- The prompt the renderer will actually build (62 words) names only the flames and carries the three-item pin: *"The candles themselves, the crimson velvet swag curtain and the panelled walls are rigid and fixed…"*. `rigid=True` switches on automatically off `spec["rigid"]`, so the pin is already live without a PIN_NON_MOVERS beat.
- `SS.render_prompt(spec)` is byte-identical to the stored `scenePrompt`, and `scene.png` (14:20 spec edit vs. 13:36 commit) is the art Lucas confirmed correct. No still is owed.
- **The newest clip, `a_opera_motion_ri89` (13:50), predates the 14:20 spec edit.** It is the clip Lucas rejected for drooping candles; the softened phrase and the candle pin have never reached the GPU. Gate report `{}` agrees.

No fix rung applies: the mover is bounded with an authored vigour, the phrase is already the smallest verb available, the rigid list is at the three items the note caps it at, and the art is current and must not be re-authored. The only thing missing is the render.

(One cosmetic note for the record, deliberately not acted on: the sconce's `vigour` is also present verbatim at the end of its `desc`, so `element_desc` emits it twice in the ART prompt. Fixing it would change `render_prompt` and force a still regeneration the review note forbids.)

DECISION: RENDER
WHY: The spec's softened candle-flame phrase and its three-item rigid pin — the exact remedy Lucas's note prescribed for the drooping candles — were authored at 14:20, thirty minutes after the newest clip was baked, so no clip has ever been rendered against the current motion prompt and a single render is the only thing that can answer whether it holds.
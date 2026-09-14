I checked the four claims against disk rather than the worker's summary, and looked at the clip myself.

**Verified:**
- state.json for a_opera carries no `needs_still`, `spec_edited_at` or `parked`. The human's review_note says explicitly: "The committed seam-staged scene.png is the right art. Spend the render on the pinned motion prompt and gate it."
- The malformed `{"rigid": ...}` element is gone — a_opera's elements are exactly swag, parapet, console, lighter, back, on. The pin now lives at spec level.
- Only `swag` has `motion.{moves,vigour,phrase}`, so one bounded mover; `_has_authored_mover` will pass and RENDER won't be refused.
- attempts 1 against `max_attempts_per_room: 2` in plan.json — one render left, as claimed.
- Settings are not a lever here and aren't being touched: the runner takes `end_guide` from `plan.get("end_guide")` ("0.70"), not from the decision, and ri61's params show the sanctioned 3072x1024 / seed 4242 / 8 steps pass.

**The load-bearing check the worker asserted but didn't demonstrate** — that the render actually picks up the pin. It does, and not for the reason you'd guess. RENDER never re-renders the prompt; `_launch_cine_room` shells out to cine_room.py, which reads the persisted file at cinemagraph_tools/art_prompt_motion/heist/a_opera.txt. That file was written 07:39 by cycle 65's PIN_NON_MOVERS, and it carries the drape clause. The clip in hand, ri61, was baked 07:22 — seventeen minutes earlier, from the unpinned prompt. So the pinned prompt genuinely has never been rendered.

**The frames back the diagnosis independently.** In frame 0 both right-hand doorways are open and lit — the corridor and the grand stair. Mid-loop, both are swallowed: the velvet drapes have swept across and the openings are dark. By the last frame they're open again. The difference map lights up hard on exactly those two doors, which is the gate's motion at 83.3%; the authored swag on the left barely registers. Two clickable exits erased by an unpinned non-mover.

One correction to the worker's rationale that doesn't change the call: it argued for leaving the duplicated, "avy"-mangled half of the rigid clause alone because that half "carries the stronger language." That half isn't in the prompt about to be rendered at all — the persisted file predates the human's fold-in and holds only the clean first half. Which makes RENDER the better choice than it realised: a PIN_NON_MOVERS to tidy would re-render the prompt from the current spec and inject the mangled duplicate into the render.

No rejection criterion fires — no settings search, bounded mover, return is 0.43 rather than zero, nothing accepted or written to committed art or hotspots, no hand-written art prompt, and not AUTHOR_MOVER.

VERDICT: PASS
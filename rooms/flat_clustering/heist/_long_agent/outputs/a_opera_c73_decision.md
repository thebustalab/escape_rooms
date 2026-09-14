I've read the four authorities and verified the room's live state on disk.

**What I found:**
- `state.json` no longer carries `needs_still`, `spec_edited_at` or `parked` for `a_opera` — the human unparked it, and the `review_note` says explicitly: *"The committed seam-staged scene.png is the right art. Spend the render on the pinned motion prompt and gate it."*
- The malformed `{"rigid": ...}` element is gone from `elements` — `to_hotspots` now returns cleanly (`console, lighter, back, on`), no `KeyError`.
- `movers(spec)` returns exactly one bounded mover, `swag`, with `motion.{moves,vigour,phrase}` — so `_has_authored_mover` passes and RENDER won't be refused.
- The runner has been patched: `PIN_NON_MOVERS` now sets `needs_still` only when `render_prompt` actually changes, so the pin no longer parks the room.
- The only existing clip, `a_opera_motion_ri61_looped.mp4` (today 07:22), predates both pins — its gate report is the one in hand, and the evaluator's own frame-by-frame read of it found the grand-stair drape swallowing a live door hotspot. **The pinned prompt has never been rendered.**
- `attempts: 1` against `max_attempts_per_room: 2` — exactly one render left.

The spec-rendered rigid clause carries a redundant second copy of the pin (with one mangled token, "avy"), an artefact of the hand-fold. I considered spending this cycle on a `PIN_NON_MOVERS` to tidy it, but it is semantically correct and grammatically intact, the duplicate half carries the *stronger* language ("tied back at their tassels, both openings left wide"), and the ledger's only finding on prompt length is that a 288-word prompt did not *outperform* a short one — not that it fails. Tidying would burn the beat the human just cleared for a render.

DECISION: RENDER
WHY: The pin is correctly applied and the committed 2026-09-13 22:24 seam-staged still is the right art with an unchanged art prompt, so the one remaining sanctioned 3072x1024 pass at end guide 0.70 should go to the pinned motion prompt — the only clip that exists was rendered before the drapes were pinned and showed one of them erasing a clickable exit.
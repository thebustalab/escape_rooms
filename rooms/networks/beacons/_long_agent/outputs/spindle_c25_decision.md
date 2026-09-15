I read the four documents, then checked the room's actual state.

**What I found:**
- `scene.png` was regenerated today at 21:09:10 with `scenario.json` written 21:09:20 — the still is current with the spec, and every clip in the room dates to Sep 7 (stale art). Gate report `{}`, nothing tried.
- The spec carries exactly one bounded mover with a real `motion` block: `day_cloth` (`moves/vigour/phrase`). `name_crag`'s spindrift is a legacy `animate` block, invisible to `_has_authored_mover` and not in the prompt — one mover, not two.
- `scene_spec.render_motion_prompt(spec)` resolves from the spec and yields the cloth sentence, not the spindrift `.txt` quoted in the brief (that `.txt` is now only the fallback, and it is not reached since the spec declares a mover).
- I looked at the still at native resolution. The cloth is depicted clean and bellied under tension on its iron frame, stone-weighted corner, occupying ~13% of frame width at the near left — bounded, the same class of mover as heist's tarpaulin and dust sheet, which animated in all 16 cells.

The art depicts a bounded mover, the prompt names it and nothing else, and no clip exists for this still. That is step 3: one render.

DECISION: RENDER
WHY: The freshly regenerated still depicts one clean bounded mover (the weighted signal cloth), the spec's `motion.phrase` renders a 34-word prompt naming only that cloth, and no clip yet exists for this art — so the next step is one render at the 0.70 default, not another authoring pass.
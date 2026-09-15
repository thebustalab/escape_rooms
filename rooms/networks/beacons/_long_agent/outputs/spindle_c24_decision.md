I've read the four evidence files and checked the room's actual state.

**What I found:**

- `scene.png` and `scenario.json` were both written today at 21:09 — the still is current with the spec, not stale.
- The spec carries exactly one bounded mover with authored vigour: `day_cloth` — `motion.{moves, vigour, phrase}` all present. `name_crag`'s spindrift is a **legacy `animate` block only**, invisible to `movers()`.
- The still genuinely depicts it: a broad white signal cloth on its iron frame occupying the near left, hard-edged and bounded, clearly the strongest animatable object in the frame. The needle's spindrift is a faint wisp at best.
- The "current motion prompt" in the brief is the **stale `.txt` fallback** (`art_prompt_motion/beacons/spindle.txt`, the spindrift plume). I ran `render_motion_prompt` on the live spec: because the spec declares a mover, the spec wins and the effective prompt is the cloth one —

  > locked-off static camera, zero camera movement. The broad white signal cloth on its frame snapping and rippling in the updraught, its weighted lower corners kicking. Only that moves; everything else stays perfectly still. Seamless natural loop.

- Gate report `{}`, tried `[]`, and the only clips on disk are `cine_base.mp4` from Sep 7 — a week older than this art. Nothing has been rendered against the current still.

The spec and prompt are right and no clip exists. That is step 3, one render.

DECISION: RENDER
WHY: The spec carries one bounded authored mover (`day_cloth`, vigour written into its desc), the current still visibly depicts that cloth on its frame at the near left, the spec-derived motion prompt names that cloth and nothing else, and no clip has ever been rendered against this art.

One thing for the record, not a decision: `art_prompt_motion/beacons/spindle.txt` still holds the old spindrift sentence. It is unreachable while the spec declares a mover, so it cannot affect this render — but it is exactly the two-sources-of-truth drift the one-spec design exists to prevent, and it should be retired when someone is next editing that directory.
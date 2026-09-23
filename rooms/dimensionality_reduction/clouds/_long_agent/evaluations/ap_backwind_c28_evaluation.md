I checked the frames, the room's records, and the code path rather than the worker's description.

## What holds up

**The defect is real.** I pulled frames 0 and 36 myself. Frame 0 is the clean committed scene. Frame 36 carries a huge ochre torn-sailcloth structure running the full 3072 px, burying the eyewall, the derelict glider and both wings. It is not in the still. The worker's account of why the gates missed it is correct: `return 0.69` is high *because* the intruder arrives and leaves, and the glitch detector's 0.125 breadth caught only the onset edge of a slow growth.

**The history check is accurate.** `ap_backwind_c27_evaluation.md` exists and ends `VERDICT: FAIL` — cycle 27's HOLD really was rejected by an evaluator that pulled frames. The "Tried already" list I was handed omits it.

**The remedy is the right rung.** `exp_art_prompt.motion_prompt` resolves this room's prompt from `authoring.sceneSpec` (there is no `art_prompt_motion/clouds/ap_backwind.txt`), and the `rigid` switch is documented in-code as "the ESCALATION for a room where something that should be still is moving (pipeline step 6.2)". That is this failure. No reject criterion trips: no settings change, the proposed mover stays the bounded derelict wing, deadness is never invoked, and I confirmed the art-side `scene_spec.render_prompt` is byte-identical with `rigid` added — the panorama is genuinely untouched.

## Why it still can't be acted on

The SPEC payload is a **list**. `scene_spec.py:482` does `spec["rigid"].strip()`:

```
=== AS PROPOSED (rigid = LIST) ===
EXCEPTION: AttributeError 'list' object has no attribute 'strip'
fallback file exists: False
```

In `motion_prompt` that exception is swallowed by a bare `except Exception: pass`, falls through to a `.txt` fallback that doesn't exist for this room, and returns `None` — so the `motion` arm is never built. The cycle would silently render nothing and log PIN_NON_MOVERS as tried-and-ineffective, falsifying a lever that actually works. Every one of the eight rooms in the corpus that authors `rigid` (beacons, subway, heist, waterfalls) types it as `str`, and nothing normalises a list anywhere.

Joined into the string the code expects, the clause renders correctly at **63** words — not the 64 the worker reported, which is immaterial, but it means the word count was estimated rather than run:

> ... The viewer's own glider's two wide translucent membrane wings spread across the foreground, its dark shell nose and dash are rigid and fixed — they do not warp, drift, breathe, shimmer or change shape. Only that moves ...

The judgement is sound and the fix is one token — `"rigid"` as a comma-joined string instead of a two-element array. That's a correction to the payload, not a re-decision, so the decision shouldn't be discarded; it just must not go to the renderer as written.

VERDICT: REVIEW
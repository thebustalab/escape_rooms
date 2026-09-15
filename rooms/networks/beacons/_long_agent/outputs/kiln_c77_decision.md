Read the four evidence files, then checked the clip itself rather than trusting the ambiguous return-zero note.

**What the gate report hides.** `return 0.0` is the dead-or-cyclic ambiguity, and smoke is exactly the cyclic case that has fooled it three times. So I measured the raw render (`kiln_motion_ri75.mp4`, 73 frames, seed 4242, eg 0.70) directly:

- Temporal-std map, 64 px blocks: median 5.82, **max 1.9x median**, and the hot blocks are the y≈0.94 nadir row — compression noise, not a subject. The juniper plume region sits at **1.04x median**, i.e. dead on the noise floor. (Compare `shears`, where the authored mover read 16–27x.)
- `|frame_t − frame_0|` climbs monotonically 0 → 9.66 with no turn, and the rise survives brightness normalisation — a uniform whole-frame creep, not a localised mover.
- By eye, frame 0 against frame 72: the plume has the same forks and the same kink at the same heights. Three seconds of smoke would have reorganised completely. It is static.

Dead, not cyclic. Per step 6.3 the fix is the art.

**Why it died, and what I changed.** The still does depict the mover, so the authoring rule held — but it rendered it as thin, translucent, high-frequency filigree seen *against the busy textured red rock*, which the desc explicitly asked for ("rolls over against the warm red rock of the dome behind it"). Low-contrast fine detail against high-frequency background is what the clip model holds still at 3072. kiln is also the only beacons room whose vigour word was "slow"; the eleven live siblings all read "pouring hard", "cracking taut", "jetting thick", "hard rolling boil".

So the re-author keeps the substance (smoke is the one thing this room can have — the fire baskets must stay cold, and every other beacons mover is water or cloth), keeps it near-field and bounded, and changes the two things that killed it: a dense opaque body with a hard edge instead of a pale wisp, standing against open cobalt sky instead of rock, and bent hard downwind instead of climbing slowly. Verified both prompts build from the edited spec — motion prompt 38 words naming only the smoke, art prompt assembles through `render_prompt` with the element in its correct left-hand sweep position.

One thing worth flagging: the "current motion prompt" quoted in my brief is the stale `art_prompt_motion/beacons/kiln.txt` (banner cloud + heat shimmer). That is **not** what rendered — `exp_art_prompt.py:86` correctly preferred the spec, and the render used the juniper phrase. The harness is reading the fallback file for display.

```
DECISION: AUTHOR_MOVER
SPEC: {"id": "juniper_smudge", "at": "to the left", "desc": "a wide iron smudge dish on a low tripod standing on the flags close beside the viewer, packed and choked with smouldering green juniper and showing no flame at all, throwing up one dense opaque column of grey-white smoke with a solid woolly body and a hard edge to it \u2014 the column leaves the dish thick and unbroken, then leans right over off the vertical and out past the lip of the platform so that its whole upper length stands clear of the rock against open deep-cobalt sky, where it reads dark and sharp against the clean blue and tears away downwind in big slow-rolling billows", "motion": {"moves": true, "vigour": "smoking hard and driven well over from the vertical, the column bent downwind and shedding fat rolling billows off its top", "phrase": "the dense column of juniper smoke pouring up off the iron dish, bending downwind and rolling away in billows against the open sky"}}
WHY: The clip is dead, not cyclic — the plume region measures 1.04x the median block std and is visually identical at frames 0 and 72 — because the still depicts the mover as a thin translucent wisp against busy red rock, so it is re-authored as a dense hard-edged column standing against open sky and driven hard downwind.
```
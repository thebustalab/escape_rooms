I read the four authorities, then verified ri75 on disk rather than trusting the gate summary — the last two cycles' evaluations both turned on something the metrics could not see.

**What I confirmed:**

- **The brief's "current motion prompt" is not the one that fired.** That 104-word text is the stale fallback `cinemagraph_tools/art_prompt_motion/heist/a_opera.txt` (07:39). `exp_art_prompt.py:98` sets `rigid=True` from the spec's `rigid` key, so ri75 rendered the spec-derived prompt with the human's shortened clause — walls and parapet only, drapes deliberately unpinned.
- **All three gates cleared with margin.** Camera still (landmark drift 0 px, frame0 corr 0.962), glitch breadth 0.042 / 0.042 normalised against a 0.70 threshold on both readings, return 0.2 — non-zero, so not the ambiguous dead-or-cyclic case.
- **The motion is where the art put it.** A per-column temporal-std profile over the raw render puts every bit of movement in x 0.19–0.31 (std 6.25 / 7.11) against a 0.7–2.3 baseline everywhere else. `swag` is authored at `to the left` = 0.20. One bounded mover, in its own place.
- **The ri61 defect is gone.** That render had the grand-stair drape sweeping shut and swallowing a live door hotspot. In ri75 the doorway band (x 0.75–0.94) is the *quietest* in the frame at 0.80–1.15, and frames 0/18/36/54/72 show both openings unchanged — drapes tied back at the tassels, marble jamb, stair and carpet stable throughout. It held without being named.
- **Both of Lucas's standing art notes are answered in this render.** The far-left crimson wall he called "weirdly breathing" is the lowest-variance region on the panorama (0.73–0.95). The lighter reads at matchbox scale on the box rail with its crest legible, not the object that "occupies a huge portion of the view".

The swag itself visibly lifts and settles across the loop — a lower fold billowing out over the box rail and back. It is nearer "stirring" than "billowing", consistent with its authored vigour, and it occludes nothing: the console at 0.50 and the lighter at 0.64 sit well clear of the disturbed band.

I considered SOFTEN_PROMPT on the grounds that the fold travels a little further than "shifting a little" implies. I am not taking it. Return 0.2 sits beside `market_price`'s 0.23, which ships, and the pipeline is explicit that subtle motion is enough and that no metric — and no reading of mine — may approve or reject on liveliness where the eye is the judge. Softening a clip this close to the authored intent would spend a render to answer a question that belongs to Lucas.

DECISION: HOLD
WHY: ri75 cleared camera, glitch and return, its motion is confined to the single authored bounded mover at its authored position, the door-swallowing drape that spoiled ri61 is absent, and both outstanding human notes on this room are visibly resolved — so the clip is clean-pending-eye and there is nothing left for the loop to author.
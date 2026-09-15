I checked the worker's claims against the files rather than its description.

**Verified independently:**

- **The prompt really does derive from the spec.** I ran the live resolution for this room: `E.motion_prompt('beacons','broken_tooth', rec)` returns the spec-rendered string verbatim — *"locked-off static camera… The pour of snowmelt falling from the snow lip on the near tooth onto the flags below it. Only that moves…"* — not the stale avalanche text in art_prompt_motion/beacons/broken_tooth.txt. test_motion_prompt_source.py documents and pins that precedence for beacons since 2026-09-13. `movers()` returns exactly one element, `tooth_pour`, and ignores `avalanche`'s legacy `animate` block, as claimed.

- **The still depicts it, and it's bounded.** Looked at scene.png at native crop. The pour is there — heavy meltwater off a snow lip, falling about a man's height onto wet flags, dark wet channel cut across the stone. It occupies roughly 5% of the 3072px width, well inboard of both margins. Depicted vigour matches the authored vigour. Not frame-filling.

- **The mover has genuinely never been rendered.** scene.png and scenario.json are both 2026-09-15 01:21; cine_base.mp4 is 2026-09-07 14:12. More telling than the mtimes: cine_base.judge.json lists subjects `snow_banner`, `gorge_haze`, `survey_sheet` — an element set that doesn't exist in the current spec at all. That clip belongs to a superseded authoring. So RENDER, not AUTHOR_MOVER, is the correct move here.

- **Not a settings proposal.** 3072x1024 and end guide 0.70 are the pipeline's hard defaults (cine_render.py:42, cine_room.py:101). The worker is restating them, not reaching for a falsified lever.

None of the rejection criteria fire: no settings change, bounded mover, no zero-return reasoning invoked, no clip acceptance, no writes to committed art or hotspots, no hand-written prompt.

One imprecision worth noting: the worker says "no clip exists for this art" when a cine_base.mp4 file does exist — it's stale, not absent. The substance is right and I confirmed it by other means, so it doesn't change the call.

VERDICT: PASS
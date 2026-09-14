I checked the clip myself rather than relying on the worker's numbers.

**Per-column temporal std over the 73 raw frames** (my own measurement, 768-wide downscale):
- x≈0.15–0.28 (the authored swag at the box mouth): **0.90** — flat, static-background level.
- x=0.667–0.708: **13.10**; x=0.833–0.875: **19.61**; peak column x=0.839 at **29.32**.

The worker's shape is right: the motion budget landed entirely in the right-hand third, not on the swag.

**The frames confirm what those bands are.** Frame 1: both curtained doorways stand open — lit corridor on one, grand stair with chandelier, marble and balustrade on the other. Frame 37: heavy velvet has swept fully across both; the grand-stair exit is gone, the corridor door nearly so. Frame 73: both open again. That out-and-back is the 0.43 return, and it belongs to the wrong objects — the two movers are the `back` (→ briefing) and `on` (→ a_townhouse) door hotspots, both named in `rigid`. The left crop shows the swag correctly drawn, tied back with its tassel, bounded and well-placed, so this is not a dead-art case.

**The diagnosis of why the pin failed also holds.** The old clause pins "both curtained doorways" — the openings, not their drapes — while the sanctioned mover is "the heavy crimson velvet swag curtain". Every crimson velvet curtain in the room is eligible under that name and the model picked the two nearest the frame edge. Naming the drapes and separating them from the swag by side of the view is the right lever.

Against the reject list: no settings touched (the patch is the `rigid` field only), no new mover proposed let alone a frame-filling one, the return is 0.43 and is correctly read as the drapes' cycle rather than as proof of death, nothing is accepted and nothing is written to scenario.json, no hand-written art prompt, and it is not AUTHOR_MOVER. The replacement clause also retains every item the old one listed — parapet, panelled walls and mouldings, tiers and boxes, writing-slope and terminal, lighter — so nothing is lost in the swap, and its descriptive additions ("tied back at their tassels, both openings wide and lit") match frame 0 exactly rather than redirecting the art.

VERDICT: PASS
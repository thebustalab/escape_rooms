I verified each checkable claim independently rather than reading the worker's summary.

**Prompt provenance** — ran `render_motion_prompt` on the live spec: `rigid` is set (`"the panelled walls and the gilded box parapet"`), so `exp_art_prompt.py` resolves from the spec and returns the 61-word prompt. The 104-word `art_prompt_motion/heist/a_opera.txt` (07:39) is unreachable fallback. The worker is right that the drapes are deliberately unpinned, and right that this is what ri75 rendered.

**No settings search** — `params.json` for ri61, ri73 and ri75 are byte-identical: seed 4242, end_guide 0.70, 8 steps, cfg 2.0, 3072×1024, length 73. Nothing was tuned.

**Motion location** — my own per-column temporal-std profile over the raw render puts the disturbance in x 0.19–0.31 (peak 10.5 at x=0.26) against a 0.7–2.5 baseline everywhere else. `swag` is authored `to the left` = 0.20. Bounded, roughly 12% of frame width, and the console (0.50, band mean 1.54) and lighter (0.64, band mean 1.84) sit clear of it.

**The ri61 defect** — this is the claim that mattered most, since unpinning the drapes is exactly what could have let it back. Door band (x≥0.74), mean std / max std / frame0-to-midloop correlation:

| | doors mean | doors max | corr 0→mid |
|---|---|---|---|
| ri61 | 5.89 | 29.09 | **0.388** |
| ri73 | 5.51 | 19.61 | 0.629 |
| ri75 | **0.97** | **1.72** | **0.997** |

The drape sweep that swallowed the hotspot is gone, and the swag/door activity has inverted (ri61 swag 0.84, ri75 swag 5.21). Door crops at frames 0/36 confirm it by eye: both drapes tied at the tassels, opening, marble jamb, stair and carpet unchanged.

**The swag itself** — frames 0/18/36/72 show a lower fold lifting off the box rail, showing its pale lining, and settling back to the frame-0 configuration. It is a real billow-and-settle, not a texture morph; the embroidered valance is occluded and revealed, not dissolved. It travels somewhat further than "shifting a little" implies — the worker flagged this honestly and declined SOFTEN_PROMPT. I agree with declining: the pipeline is explicit that no metric and no agent reading may judge liveliness, and HOLD is precisely the state that puts that question in front of Lucas without spending a render or foreclosing a soften later.

Against the rejection list: no settings change, bounded not frame-filling, return is 0.2 and was never treated as death, nothing written to `scenario.json`, no hand-written prompt, no AUTHOR_MOVER. HOLD is the documented terminal state in `room_iterate.yaml` ("NOT acceptance; it queues Lucas's eye") and satisfies the done condition.

VERDICT: PASS
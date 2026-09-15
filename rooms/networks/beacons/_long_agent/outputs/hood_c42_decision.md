I read the four evidence files, then checked the render itself rather than the briefing's summary.

**What I found.** The briefing's "current motion prompt" is stale — it's the old cloud-sea text. There is no `art_prompt_motion/networks/hood.txt` fallback, and `render_motion_prompt` on the live spec emits:

> locked-off static camera, zero camera movement. The curtain of meltwater drips falling from the lip of the cowl just outside the rail, its threads breaking and reforming. Only that moves…

The raw render confirms that is what was driven. Column motion profile of `hood_motion_ri40.mp4` (frame median std 1.68):

| x band | × median |
|---|---|
| 0.09 – 0.28 (the drip curtain, authored `at: "to the left"` = 0.20) | **6.4 – 9.0x** |
| 0.31 – 0.78 (the cloud sea, `inversion`, centre) | 0.83 – 0.96x |
| both seam edges | 1.06x / 1.19x |

One contiguous band at 9x the median exactly where the mover is authored, and everything else — including the frame-filling cloud sea that is hood's known weakness at 3072 — flat at the noise floor. That is a bounded mover working, not drift, and no non-mover is moving, so the rigid escalation isn't indicated.

**Gates.** Camera still. Glitch breadth 0.125 raw / 0.083 normalised, both far under the 0.70-on-both threshold. Return 0.02 is the documented dead-or-cyclic ambiguity — and for falling water it's the cyclic-flow signature: `rams_head`, same run, same subject, returned 0.02 at peak 10.18 and was held. hood's peak of 9.5 sits with its four held siblings (9.04 / 10.18 / 10.36 / 10.78) and far above hood's historic dead readings of 5.1–5.2.

Nothing is left for the loop to fix.

```
DECISION: HOLD
WHY: The clip cleared all three reject-only gates and its motion is confined to a single contiguous band at 9x the frame median exactly where the authored drip curtain sits, with the cloud sea and both seams at the noise floor, so the 0.02 return is the cyclic-flow signature of falling water — the same reading rams_head was held on in this run.
```

One thing worth your eye beyond the clip: hood is the first room in this run whose peak is below 10, and its mover shares a subject (falling meltwater) with `rams_head`, against the review note's instruction that every room's mover be different.
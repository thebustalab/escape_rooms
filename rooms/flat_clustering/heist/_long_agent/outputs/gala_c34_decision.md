Read all four. Here's the state I found.

**The clip exists and no gate rejected it.** `gala_motion_ri32_looped.mp4` rendered at the canonical settings exactly — 3072x1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242. Camera: still. Glitch: breadth 0.042 raw / 0.021 normalised, an order of magnitude under the 0.70 both-readings threshold.

**The only open signal is the 0.00 return, and the pipeline forbids rejecting on it.** `cine_return_check` escalates, never rejects: a zero covers dead *and* cyclic flow, and the ledger records three separate wrong calls from this exact metric — b_casino's smoke, logwood_verdigris' water, crown's streaming pennant (return 0.03–0.05, alive). Long silk drapes and bunting in a breeze is the travelling-ripple case, and hanging cloth is the ledger's strongest confirmed mover category.

**The peak gives no deadness evidence either.** The historic 5.1-vs-8.06 peak tell is on a different scale from this run's numbers; within this run, gala's 3.78 sits mid-pack against the five rooms already held — briefing 2.51 (also return 0.00), b_stateroom 3.50, a_opera 3.60, b_pawnshop 4.28, a_townhouse 4.62. Three held clips score *below* gala.

Re-authoring here would be the documented error, not the fix.

```
DECISION: HOLD
WHY: The one sanctioned render cleared the camera gate and sits far under the glitch threshold on both readings, and its sole remaining signal — a 0.00 return — is the documented dead-or-cyclic ambiguity that must escalate rather than reject, with a peak mid-pack among this run's five held clips giving no independent evidence of deadness.
```

Three notes for when you look at it:

The judge to make is whether the drapes are actually moving. If they read as cyclic ripple travelling along the cloth, the 0.00 is correct and meaningless. If they're genuinely still, the remedy is ADJUST_VIGOUR — "lifting and falling steadily in the dawn breeze" is a mild depiction, and the hood precedent says pushing the depicted vigour up is the lever that wakes a quiet mover.

The still itself is still only *held*, not accepted — `authoring.seam.accepted` is false in `rooms/flat_clustering/heist/gala/scene.judge.json`, though the seam measures clean (ratio 0.0, delta 0.0, needsWork false).

Carried forward from cycle 32's evaluation and unaddressed: gala's cached `scenePrompt` predates the EQUIRECT clause. That's untouched deliberately — regenerating the panorama is the expensive lever and it's reserved for a clip confirmed dead.
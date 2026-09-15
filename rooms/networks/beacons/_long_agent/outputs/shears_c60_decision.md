I read the four authority documents, then checked the clip itself rather than the gate summary.

**What the gates say, and why they are not the issue.** Camera still. Glitch breadth 0.167, far under the 0.70 both-readings threshold. Return 0.01 with peak 10.08 — the documented cyclic-flow signature of falling water, the same register as `rams_head` (0.02, peak 10.18), which was held. On the numbers alone this room reads like a HOLD, which is what the previous cycle proposed.

**What the frames say.** I extracted frames 0/30/60 of the raw render and looked at the right half at native resolution. At frame 0 the brass spyglass sits on its tripod over the valley. By frame 30 an enormous white water jet is erupting **from the spyglass muzzle**, arcing down across the nine villages of `valley_view` and onto the platform; by frame 60 it has collapsed to a thin plume on the horizon. It is not in the committed still. The evaluator's account is correct and I verified it independently.

This is the invented-content failure class the pipeline names by example (verdigris' ceiling water, alum_madder's drops): the model applied the authored "jetting… arcing down" phrase a second time, to a different object, with no pins active. It lands on a `clue: true` hotspot, so it cannot be left standing as a candidate for the eye.

The fix is step 6.2, the rigid scalpel — not re-authoring the art, which is intact and correct, and not a settings change. I checked what the pin costs: `render_prompt` does not read `rigid`, so the art prompt comes back byte-identical and the committed still stands; only the clip re-renders. The pinned motion prompt is 65 words, the same register as `fenwatch`'s 66-word pinned prompt that rendered with the camera still, and well clear of the 176-word a_opera failure. One item, named once.

```
DECISION: PIN_NON_MOVERS
SPEC: ["the brass spyglass, its tripod and the folded survey sheet beside it"]
WHY: The clip is not dead — the authored blade_spout flows correctly — but a second, hallucinated water jet erupts from the spyglass muzzle across the villages from frame 15, so the remedy is the one-item rigid scalpel on the spyglass, which leaves the art prompt byte-identical and re-renders only the clip.
```
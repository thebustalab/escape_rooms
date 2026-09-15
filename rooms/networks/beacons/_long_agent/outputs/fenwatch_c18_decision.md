I read the four authority documents, then measured the actual clip rather than trusting the summary gate.

**The mover works.** The still genuinely depicts it — I looked at the panorama: a heavy rope of white water from a lead spout into a brim-full slate butt, overflowing onto the cobbles, bounded at roughly a sixth of the frame width, and falling water is on the ledger's confirmed-mover list. Traced on the RAW render, the pour+butt region rises to 18 within six frames and then fluctuates around 18–20, returning **0.17** with its peak at frame 29. That is a live cyclic mover, and it is exactly why the whole-frame return reads 0.00 — as cycle 16 predicted.

**But something that should be still is moving.** Every static region of the scene creeps monotonically, peaks on the *final* frame, and never comes back:

| region | peak | return | peak at |
|---|---|---|---|
| office slate roof | 14.60 | 0.00 | frame 72 |
| cobbled yard | 12.26 | 0.00 | frame 72 |
| far-right seam wall | 10.52 | 0.00 | frame 72 |
| drystone yard wall | 8.31 | 0.00 | frame 72 |
| sky (featureless) | 4.37 | 0.00 | — |
| **pour + butt** | **20.65** | **0.17** | **frame 29** |

Normalising each frame's global brightness away changes nothing (8.59 vs 8.58), so this is not an exposure shift — it is real content drift. The camera gate is right that there is no translation (`landmark_drift_px: 0`); this is a slow non-rigid warp, which is why only the smooth sky escapes it while every textured stone surface shows it. That is Lucas's *"the wall is like weirdly breathing"* on a_opera, and it is what is dragging the full-frame trace monotone and burying a mover that is otherwise doing its job.

Fix #2 in the pipeline's ordered list, not #1 and not #3 — the art is right, so it stays. The rigid clause is kept to **two items** and the prompt lands at 68 words, the register that worked on a_opera, not the 176 that made its camera drift.

DECISION: PIN_NON_MOVERS
SPEC: {"rigid": "the drystone yard walls and cobbles, and the slate roof of the office range"}
WHY: The pour is genuinely alive (region return 0.17, peaking mid-clip) but every stone surface in the scene warps monotonically to its final frame, so the non-movers are pinned and the clip re-rendered from the same art.
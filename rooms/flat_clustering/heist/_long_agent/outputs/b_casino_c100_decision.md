I have what I need. Here is the evidence, then the decision.

**The gate report is a clean pass, but the clip is dead.** I measured the raw `ri98` render spatially (per-pixel temporal std, 1536×512), the same way cycles 86 and 97 did, against the previous clip `ri84` as a live control:

| | ri84 (held at c86) | **ri98 (this clip)** |
|---|---|---|
| peak column-std | 5.81 **at x=0.082** | 1.78 **at x=0.500** |
| contrast over frame median | 4.11× | **1.74×** |
| band above half-max | x 0.061–0.155, **width 0.094** | x 0.091–0.996, **width 0.905** |
| max pixel-std | 68.8 | 25.2 |
| \|f_t − f_0\| | rises to 2.77 at frame 61 | 1.36 by frame 10, **flatlines at 1.66** |

ri84 is a textbook bounded mover: a sharp spike exactly where the ashtray is depicted, decaying away on both sides. ri98 has no peak at all — a broad low plateau across 90% of the frame whose maximum sits at **x=0.50, the cashier's cage, where the spec declares nothing moves**. The flatline-by-frame-10 signature is the same one the a_opera `ri78` evaluation used to call that clip dead. The 0.00 return here is not the documented cyclic-flow false alarm; there is nothing localised to be flowing.

**Why it died, and it is not the mover's authoring.** I diffed the spec against `scenario.json.bak_20260914_140023_casino_seam`: the *only* change since the still that animated is the **seam clause**. The `smoke` element — desc, vigour, phrase — is byte-identical across both. The 14:26 redraw moved the ashtray inboard from x≈0.06 to x≈0.23 and, more importantly, turned "a slow bank of cigarette smoke hanging over the near baize" into a room-wide haze lying across the far tables and mid-ground. That is the frame-filling failure the core finding names: diffuse is fine, frame-filling reads as drift or as nothing.

I verified the replacement element through both consumers: the motion prompt resolves to the 40-word house form, and the art prompt keeps the equirect clause with the seam anchor at head and tail (`seam head+tail: 2`).

```
DECISION: AUTHOR_MOVER
SPEC: {"id": "smoke", "at": "to the left", "desc": "a single compact plume of cigar smoke rising from the ashtray on the near baize, a clearly defined ribbon that climbs and curls over on itself in two or three distinct legible coils before thinning out, confined to that one narrow column of air directly above the ashtray, the rest of the room's air clear with no haze over the far tables, no smoke layer across the room and no general fog anywhere else", "animate": {"motion": "cigar smoke curling and rolling upward above the near ashtray", "loop": "crossfade"}, "motion": {"moves": true, "vigour": "curling and turning over visibly as it rises, the coils clearly on the move rather than hanging still", "phrase": "the compact plume of cigar smoke rising from the ashtray on the near baize, its coils curling and rolling over as they climb"}}
WHY: The seam-fix redraw kept the mover's authoring word-for-word but depicted it as a room-wide haze instead of a bounded plume, and the resulting render carries no localised motion anywhere — a flat 1.74x plateau peaking on the still cashier's cage — so the art must be re-authored to confine the smoke to one narrow column above the ashtray and to depict it visibly curling rather than "barely moving".
```

One thing for the record that this rung cannot reach: the room's `atmosphere` field still reads "dense smoke", which pulls against the new desc's exclusions and is a plausible co-cause of the room-filling draw. The element's negative clauses are the only lever a single-element decision has; if the next draw still hazes the mid-ground, that field is where to look.
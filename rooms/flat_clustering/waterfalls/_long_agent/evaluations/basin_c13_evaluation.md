I'm passing this. I checked the still myself rather than relying on the worker's account.

- **The still is current.** `basin/scene.png` (3072×1024) was regenerated at 08:27. The only basin clip, ri40 from 01:31, was made from an older still, so the flood has never been rendered against this one. A render is the right next step; authoring a new mover is not.
- **The mover is bounded.** The flood fills only the lower third of the frame. The basins, both threads, the ladder, the reckoning frame and the vault door all stand above the waterline. The threads stay rigid, as `AGENTS.md` requires.
- **No banned lever.** Rendering at 3072 is the pipeline's standard size, not a new setting. The worker doesn't treat a zero return as a dead clip; it says to check a still region of the frame first. Nothing gets accepted or written into the committed art or hotspots, and no art prompt is hand-written.
- **The still mostly matches the spec.** There are exactly three basins in a left-to-right line and exactly two threads. Both threads fall inside the right-hand (near) basin by the vault pillar, and the other two basins are unfed.

Two things for later, neither blocking:
- **Basin spacing:** the outer basin isn't clearly further from the middle one than the middle is from the near one, though the spec asks for that. A human should look at that when the still is reviewed.
- **The 2× retime:** the worker's fallback if the water looks slow changes clip timing. If it comes back as its own proposal, it needs judging then.

VERDICT: PASS
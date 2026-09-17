I checked the clip and frames myself rather than relying on the worker's summary.

**What the frames show.** The looped clip is 61 frames at 3072×1024. Sampling frames 0/15/30/45/60 and differencing them: mean absolute change ~2.7–2.9 grey levels between the start frame and the mid-clip frames, with about 4% of pixels moving more than 8 levels. That is not a dead clip. Frame 60 sits close to frame 0 (mean 1.3), which is the crossfade tail doing its job.

**Where the motion lives.** I gridded the difference map 4×8. The hot cells are the upper-centre-right block — 0.146 and 0.110/0.125 — which is precisely the curved wet retaining wall above and behind the train, the one authored mover. Everything else sits at 0.01–0.05, i.e. grain and lamp shimmer. So the mover is present, bounded, and in the place the spec puts it. Nothing frame-filling.

**The still itself** matches the spec: plain tiled wall left and right, spiral stair standing in from the left edge, the blue unit square on its rails dead ahead with a tunnel bore at each end, the sump pump and its channel at the right. No seam problem visible.

**Against the reject list.** The worker proposes no settings change — and notably does not, despite the params file showing end guide 0.70 and seed 4242 sitting right there as tempting knobs. It does not propose a frame-filling mover, does not treat the zero return as proof of death (it argues the opposite, correctly), does not accept the clip or touch scenario.json, does not hand-write an art prompt, and does not propose AUTHOR_MOVER. The mover has now been rendered once, so re-authoring would be premature in any case.

The zero return here is the cyclic-flow ambiguity the ledger already records: water sliding steadily downward never returns to its starting pixel configuration, so the out-and-back measure reads 0.00 on a perfectly live clip. Parking it for a human eye is the prescribed handling, and my own frame check independently corroborates that motion is real.

VERDICT: PASS
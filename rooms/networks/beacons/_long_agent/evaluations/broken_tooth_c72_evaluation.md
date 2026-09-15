I checked the artefacts myself rather than trusting the write-up.

**The prompt provenance checks out.** The .txt file in art_prompt_motion/beacons/broken_tooth.txt does still name the avalanche plume, but resolving the prompt through the real code path returns the pour phrase — the spec wins, as the precedence test documents. One mover, tooth_pour. The avalanche's `animate` block is not counted as a mover, so nothing else was asked to move.

**The motion is real and bounded.** My own per-tile temporal std on the raw render, on a different grid from the worker's, reproduces the same shape: every one of the top 14 tiles sits in one narrow vertical column at x≈0.14–0.23, y≈0.47–0.85, peaking at 24.1 against a max of 3.8 anywhere outside that column. That column is the near tooth, to the left. A crop sheet across the loop confirms it by eye — the falling stream re-fans and the splash at the base changes shape every sample, while the rock, the snow load, the wet flags and the far valley wall are static.

**So the zero return is cyclic flow, not death.** Falling water never comes back to its starting configuration; that is precisely the failure mode the gate warns has already called three good clips dead. Camera is still, glitch is 0.29 raw and 0.17 normalised, both far under threshold.

The decision parks the clip for your eye rather than accepting it, proposes no settings change, no re-author, and writes nothing into scenario.json. None of the reject conditions fire.

VERDICT: PASS
Read all four evidence docs, then checked the actual artefacts rather than re-deriving anything.

**The return 0.00 is the cyclic-flow reading, not a dead clip.** Per-tile temporal std on the RAW render puts every one of the top 14 tiles in a single narrow vertical column at x≈0.15–0.21, y≈0.44–0.88 — peak tile 33.19 against an outside-the-column max of 3.55 and a global mean of 2.13, a ~9x separation. That column is `tooth_pour` ("to the left", x=0.20). A six-frame crop sheet confirms it by eye: the falling stream shifts and re-fans, the splash at the base changes shape every sample, while the rock, the snow load, the flags and the far valley wall are pixel-identical across the loop. Falling water never returns to its starting configuration, which is exactly the `logwood_verdigris` / `b_casino` case the ledger records as scoring 0.00 while looping perfectly.

Everything else clears: camera `still`, glitch 0.292 raw and 0.167 normalised, both far under the 0.70-on-both threshold. One bounded mover, authored vigour matching what the still depicts, nothing else moving — no fix in step 6 applies.

Worth noting but not actionable here: `art_prompt_motion/beacons/broken_tooth.txt` still names the avalanche plume. It is a dead fallback — the spec declares a mover, so `render_motion_prompt` resolved the pour phrase and that is what rendered.

DECISION: HOLD
WHY: The clip survived every gate and the zero return is cyclic flow, not death — the pour is visibly alive in a bounded column at 9x the frame's background variance with everything else frozen — so it goes to Lucas's eye, which is the only thing that may accept it.
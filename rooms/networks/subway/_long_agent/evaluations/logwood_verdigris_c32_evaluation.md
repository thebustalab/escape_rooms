I checked the clip and the still myself rather than taking the worker's numbers on trust.

**What I found independently:**

- **Where the motion is.** My own per-tile temporal-std sweep on the raw 3072×1024 render (24×8 grid, frames 0/18/36/54/72) puts every elevated tile in columns 17–18 of 24 — x ≈ 0.73 — peaking 31.2 against a 2.73 median. Every other tile sits between 1.1 and 5.5, i.e. the noise floor. Column 16 shows a mild 6.4/6.6 bleed immediately adjacent. That independently reproduces the worker's localisation.
- **What is at x ≈ 0.73.** Frame 0 shows the pale oiled-canvas drip-tarp hanging from its pipe there, right of centre, clear of the wall — the `drip_tarp` element. A six-frame crop of that region shows it hanging narrow, swelling out into a full sheet, and falling back. That is the authored phrase ("swelling and falling back") animating the authored mover. The train, rails, platform, spiral stair and both tunnel mouths are static.
- **Bounded, not frame-filling.** The mover occupies roughly two of twenty-four columns.
- **The 0.03 return is a false dead-call here.** Within the tarp band, frame 72 is the *closest* frame to frame 0 (mean |Δ| 6.04) while mid-clip pairs sit at 10.4–13.5. The motion comes back toward its start; it is not one-way drift. The dead gate independently agrees (ratio 19.65, peak 10.67). The worker treats this as escalation, never as grounds to re-author — which is the correct handling of that measure.
- **Amplitude.** Peak 7.72 is at or below the band of this scenario's other held clips, so there is no basis to soften the vigour language, and the ledger records intensity language as working downward only.

Against the reject list: no settings change, no frame-filling mover, no zero-return-means-dead inference, no acceptance and nothing written to `scenario.json`, no hand-written art prompt, and no AUTHOR_MOVER on an unrendered mover. The stale-`.txt` note is flagged to a human rather than acted on, which is correct — it did not drive this render.

There is nothing left for the loop to author here; the clip needs Lucas's eye, which is what HOLD queues.

VERDICT: PASS
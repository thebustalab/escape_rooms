All four gates on this clip are clear, and the evidence files say that's the end of the machine's remit.

**Gate reading for `ap_stillstand` (clip `ap_stillstand_motion_ri16_looped.mp4`, rendered at the settled recipe — 3072x1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242):**

- **Camera** — `still`. No drift, no rejection.
- **Glitch** — breadth 0.125 raw *and* 0.125 normalised, against a threshold of 0.70 that requires **both** readings to fire. Clears by a factor of five. `spike` 22.75 is reported, never enforced (never validated; siblings `ap_pileup` 26.72 and `cockpit` 30.94 were both held).
- **Dead** — ratio 16.19 against a floor of 1.75, peak 17.49 against 0.45. `dead: false`, with wide margins.
- **Return** — 0.09. Above the 0.05 floor, and the real dead signal is *exactly* 0.00 (ledger, 2026-09-11: every clip Lucas called dead measured precisely 0.00; shipped Egypt clips run as low as 0.13, `lantern`). Not ambiguous, so no escalation.

The one number that looks low is `peak` 5.94, the lowest of the four clouds rooms (cockpit 10.17, ap_grainrun 8.02, ap_pileup 13.56) and near hood's dead 5.1–5.2. That is a settled dead end, not a signal: the ledger records peak excursion spanning 3.8–38.4 across clips Lucas called alive, "with no useful threshold", and the surviving half of his own concentration hypothesis is that amplitude is resolution-specific while the return is not. The dead gate — the calibrated, pinned instrument for this exact question — reads clear by an order of magnitude on both of its axes.

Nothing here is too lively, nothing that should be still is measurably moving, the spec's one bounded tethered kite was confirmed depicted in cycle 16 with a byte-identical art prompt, and the clip exists and is baked. There is no defect to act on, and no metric may approve.

DECISION: HOLD
WHY: The single render cleared every reject-only gate with wide margins — camera still, glitch breadth 0.125 on both readings against a both-must-fire 0.70, dead gate clear at ratio 16.19 / peak 17.49, and return 0.09 above the 0.05 floor and far from the 0.00 dead signature — so the art, the vigour and the spec-derived motion prompt have done their job and the only step left is Lucas's eye.
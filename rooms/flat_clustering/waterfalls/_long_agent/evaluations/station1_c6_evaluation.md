The runner should act on the worker's HOLD. I checked the clip myself instead of relying on the worker's summary.

- **What moves:** A frame-difference image shows motion only in the two water curtains, the one over the down-ladder and the one through the bridge. The walls, font, sample drawers, lever and cressets stay still, so both movers are bounded to their own areas and neither fills the frame.
- **Frames:** Frames sampled across the 2.5-second, 61-frame clip show the scene stable, with no warping or objects appearing and disappearing. That fits the glitch breadth of 0.0.
- **Return of 0.04:** The worker read this near-zero value as cyclic flow, which it is here: water pouring steadily down. The worker did not treat it as proof the clip is dead, and the dead check passed on its own (ratio 14.86).
- **Rules:** HOLD accepts nothing and writes nothing to `scenario.json`. It changes no settings, re-authors no mover and hand-writes no art prompt. It leaves the clip for Lucas to watch, which is the right outcome when the metrics can't judge a clip on their own.

VERDICT: PASS
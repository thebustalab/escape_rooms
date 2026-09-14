I read the four evidence documents, then checked the room on disk rather than trusting the gate note.

**What the numbers say.** `ri94` (14:33) is the first clip rendered against the softened candle phrase and the three-item rigid pin. It clears the camera gate (`frame0_corr` 0.968, `loop_jump` 1.56 — the low end of the population) and the glitch gate by a wide margin (breadth 0.021 against a 0.70 threshold). Only the return is 0.0, which the pipeline itself marks ambiguous.

**What my own measurement says.** The superficially similar dead clip `ri78` (return 0.0, peak 3.7) has a global pixel-std max of 9.17 with its top-moving pixels scattered across the whole frame — the noise-floor signature. `ri94` has a pixel-std max of **73**, and its top-400 moving pixels sit in a tight box at x 0.15–0.37, y 0.09–0.25 — the sconce. Column energy is 2.5–2.8 in blocks x 0.15–0.30 against a 1.0 floor everywhere else. Localised mover, everything else at the noise floor.

**What my eye says.** A ten-frame contact sheet of the sconce at full resolution: the flames visibly change height, lean and tip shape from frame to frame, while the wax bodies stay dead straight and fixed in every frame, and the panelled wall behind them does not move. That is precisely the pair of defects Lucas named — drooping candles and the "weirdly breathing" wall — both gone, with the flicker still legible. The zero return is the cyclic-flow false alarm the ledger documents: a flame never returns to its starting configuration pixel-wise.

No fix rung applies. Softening would extinguish the motion, strengthening does not work and is what bent the wax at `ri89`, the rigid clause is already at its two-to-three item cap, and the art is the still Lucas confirmed correct.

```
DECISION: HOLD
WHY: ri94 clears camera and glitch, and against the dead ri78 control it shows a 73-peak motion field confined to the candle flames with the wax and the wall provably still — the drooping and the breathing wall are both fixed, so the zero return is the cyclic-flow false alarm and this clip is a question for Lucas's eye, not a defect.
```
I checked every load-bearing claim myself rather than taking the worker's numbers on trust. Here's what held and what didn't.

**Confirmed independently:**
- ri94 was baked at 14:32, after the 14:20 spec edit — it genuinely is the first clip rendered against the softened flame phrase and the three-item rigid pin.
- Settings are byte-identical across ri78, ri89 and ri94 (cfg 2.0, end_guide 0.7, steps 8, seed 4242, length 73). No settings lever is in play, so nothing here is the falsified-knob trap.
- The dead control ri78 reproduces exactly as described: pixel-std max 9.2 with its top movers smeared over 95% of the frame — the noise-floor signature. ri94 peaks at ~71 with movers concentrated at the sconce.
- The wax is geometrically stable: sub-pixel edge drift on the candle bodies. The drooping is fixed.
- Zero return is **cyclic flow**, decisively. The sconce trajectory reverses direction 20 times — a one-way drift would reverse 0–2 times. Measuring return on the actual mover instead of globally gives 0.62, not 0.0. That's the documented false alarm, confirmed by measurement rather than by appeal to the ledger.

**Where the worker was loose:** it claimed the movers sit in a tight box at y 0.09–0.25. The real extent runs to y 0.76. That turns out to be a 6-pixel tail — 384 of 400 movers sit in the top 40%, peaked at y 0.1–0.2 — so the bounded-mover conclusion survives, but the box was overstated.

**The one thing I had to chase down:** my first edge metric flagged the lower panelled wall as the largest-drifting region in the frame, 14.5 px, which is precisely where Lucas's "breathing wall" complaint lives. That would have been a real defect hiding outside the crop the worker examined. It isn't one. That region is near-black — mean luminance 16, edge energy 27× lower than the wax — so the centroid was dividing by noise. Phase correlation returns exactly zero displacement in every region tested, full frame included. The wall is still.

The decision proposes no settings change, no frame-filling mover, no hand-written prompt, and no AUTHOR_MOVER on an unrendered mover. Critically, HOLD does not accept the clip or write to scenario.json — it parks it for a human eye, which is the only thing a zero return licenses, and matches the pipeline's rule that metrics may auto-reject but never auto-approve.

The runner should act on this: park ri94 for Lucas's eye.

VERDICT: PASS
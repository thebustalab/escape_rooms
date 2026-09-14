Checked the evidence myself rather than the worker's summary.

**What holds up:**

- The motion prompt at websites/thebustalab.github.io/escape_rooms/cinemagraph_tools/art_prompt_motion/heist/b_docks.txt is the house template wrapped around the tarp's own `motion.phrase` verbatim, naming only the tarp. Bounded mover, not frame-filling.
- The difference map in the strip confirms it: motion is a bright, tightly localised blob on the tarpaulin at the left hatch, everything else near-black. Frame 0 and last frame align — camera genuinely still.
- The glitch gate really is breadth-only. cine_room.py:27 states outright that `spike` "was never validated as a threshold, so it is reported and never enforced," with `GLITCH_BREADTH_REJECT = 0.667`. Breadth 0.0 is nowhere near it, so spike 2.89 is not a rejection.
- Return 0.31 is non-zero, and the gate emitted no ambiguous-zero note.
- The pipeline's own record at temp/cine/_art_prompt_exp/cine_room_20260913_173831.json already reads "survived gates — needs Lucas's eye". HOLD is that same disposition, and it accepts nothing and writes nothing into scenario.json.

**One thing the worker overstated:** the ri8 clip is byte-identical to the 14:39 firstrun — same md5 on the looped file, same seed and params. Cycle 8's render was a deterministic reproduction, not new output. That strengthens the case rather than weakening it: another render at the pinned default would return the same bytes again, so there is nothing mechanical left to try.

None of the reject conditions fire — no settings lever, no frame-filling mover, no zero-return misreading, no acceptance, no hand-written prompt, no AUTHOR_MOVER on an unrendered mover.

VERDICT: PASS
**Checked the clip myself, not the write-up.**

Frames 1 / 31 / 61 at the centre crop and full frames through the reported glitch point (68%) show:

- **One bounded tethered mover, and it moves.** The drogue kite changes attitude visibly across the loop — it swings, the membrane re-angles, the ribbon tail whips through a full ripple cycle — while staying on its line above the nose. It occupies a small fraction of the 3072-wide frame. Not frame-filling, no travel.
- **Everything else is genuinely still.** City, cloud-gardens, the eye-knot clot, the shell dash and its glowing nodules are pinned across all sampled frames. No drift, no crawling architecture.
- **The "spike 22.75" is the kite, not a defect.** Full frames at the glitch point are structurally clean — no tearing, no collapse, no popping geometry. Breadth 0.125 is consistent with a localised, authored mover, which is exactly what the spec asked for.
- **Loop returns.** Frame 61 sits close to frame 1 with the kite back near its start attitude; return 0.09 is real, not the 0.00 dead signature.

The `peak` 5.94 worry is correctly set aside — the kite is small, so a low frame-wide amplitude is what a correctly bounded mover *should* produce here, and the dead gate reads clear on both axes.

Against the reject list: no settings change proposed, no frame-filling mover, return is non-zero so the ambiguity clause doesn't bite, it does not accept the clip or touch `scenario.json`, no hand-written prompt, and no AUTHOR_MOVER on an unrendered mover. Cycle 13 authored the kite, cycle 16 rendered it, this cycle reads the result and stops. That's the correct end of the machine's remit — hold it for Lucas's eye.

(Minor, doesn't change anything: the looped file is 61 frames after loop trim, not the 73 rendered.)

VERDICT: PASS
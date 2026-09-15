I read the four evidence documents, then checked the actual clip rather than the gate summary.

**What the clip does.** A 9-frame contact sheet of the pennant region shows it flapping richly — the silk twists, the free end curls and uncurls, the profile is different in every frame. It is plainly alive.

**The escalation is the known false alarm.** `return 0.01` on a streaming pennant is exactly the cyclic-flow signature the ledger records three times, including on crown itself (return 0.03–0.05, and Lucas's verdict was "moving a lot"). Peak 9.85 sits right in crown's own measured band (7.67 / 9.21 / 8.56 across the vigour ladder; 8.18 / 8.39 / 8.01 across end guide).

**Two independent checks I ran because the contact sheet looked like it might be drifting:**
- Phase correlation of a static far-right region, frame 0 against every 9th frame: **(0, 0) shift at every step**. No camera translation. The gate's `camera: "still"` holds.
- Temporal-std column profile: motion concentrated at x ≈ 0.19–0.31, roughly 2x the frame baseline, with no secondary hotspot. That is the pennant, authored at x 0.20 and streaming rightward. Bounded, and nothing else is moving.

Glitch breadth 0.104 / 0.062 is far under the 0.70 threshold on both readings.

DECISION: HOLD
WHY: Camera is independently confirmed still with zero pixel shift, the glitch readings clear the threshold by a wide margin, and the only thing moving is the authored dispatch pennant — the zero return is the documented cyclic-flow ambiguity, not death, so this goes to Lucas's eye rather than back to the art.

One housekeeping note, no action taken: `cinemagraph_tools/art_prompt_motion/beacons/crown.txt` still says "guyed mast", which contradicts the spec's own negatives (no rigging or guy-lines). It is unreachable now that the spec declares a mover — the render used the 33-word spec-derived prompt — but it is a stale file that would bite if the `motion` block were ever removed.
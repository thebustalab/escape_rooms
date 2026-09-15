I verified independently rather than trusting the worker's numbers.

**Confirmed:**
- **The clip is alive.** A contact sheet of the mast region shows the pennant streaming with a genuinely different silhouette in every frame — the free end curls, uncurls and whips. Not dead.
- **Camera is still.** I ran phase correlation on *three* separate static regions (far-right snowfield, lower-left foreground rock, centre valley), frame 0 against every 9th frame: **(0,0) shift at every step in all three**. Stronger than the worker's single-region check.
- **The mover is bounded and is the authored one.** Elevated temporal std sits in one contiguous band with no secondary hotspot; everything else is 0.8–1.2× baseline. Visually that band is the pennant and nothing else.
- **The stale-file note is real.** `crown.txt` does say "guyed mast", contradicting the spec's "no guy-lines" negative. The rendered mast is plainly bare of rigging, which corroborates that the spec-derived prompt was used and the file was unreachable. Correctly flagged, correctly not acted on.

**Two corrections to the worker's numbers** (neither changes the outcome): the motion band is x ≈ 0.12–0.44 peaking at 0.31–0.38 at **3.3×** baseline, not "x 0.19–0.31, roughly 2×". The worker understated both the extent and the magnitude. It is still bounded — ~30% of frame width, ~10% of height — not frame-filling, and visual inspection confirms it is the pennant throughout.

**Against the reject criteria:** no settings change proposed; no frame-filling mover; the zero return is treated as ambiguous and routed to a human eye rather than used to justify a re-author — which is exactly what the gate permits; no clip accepted and nothing written to `scenario.json`; no hand-written art prompt; no AUTHOR_MOVER on an unrendered mover.

The escalation is the documented cyclic-flow false alarm, and PARK-for-human-eye is the sanctioned response.

VERDICT: PASS
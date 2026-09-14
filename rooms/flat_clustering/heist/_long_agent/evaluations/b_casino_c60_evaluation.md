Checked the clip myself rather than the worker's account of it.

**What the frames show.** Extracted all 73 raw frames and mapped where the pixels actually change. Motion is confined to x ≈ 12–25% of the width, vertically centred — the near baize corner where the ashtray and smoke live. Everything else in the frame (chandelier, cage, right-hand doors) is static: right-half temporal std 1.09, which is grain. A crop montage across the clip shows a cigar in a cut-glass ashtray with a ribbon of smoke that visibly changes shape from frame to frame. It's alive, and it's bounded — not frame-filling.

**The gates.** Diff-from-frame-0 rises to ~2.0 and plateaus, never coming back — that's the zero return, and it's exactly the one-way-drift signature the measure can't tell from death. The frames settle it: the smoke is moving. The "glitch spike" at 31.9% is one of a regular every-fourth-frame bump in consecutive diff (0.37, 0.49, 0.59, 0.41 recurring) — rhythmic, breadth 0.021, not a tear. Loop seam is 3.07× mean interior diff on low-contrast smoke; noticeable at worst, nowhere near an auto-reject.

**The decision itself** trips none of the reject conditions: no settings change, no frame-filling mover, it does not read the zero return as death, it does not accept the clip or touch scenario.json, no hand-written prompt, no AUTHOR_MOVER on an unrendered mover. The one soft number — peak 4.3, down from 8.06 — is the direct and intended consequence of the soften Lucas asked for ("way too quickly"), and re-rendering on that number would reverse his own note on a metric this room is named as a wrong call for.

Parking it for his eye is the right move; another render would burn a cycle to produce the same clip.

VERDICT: PASS
I pulled the frames myself rather than trusting the description.

**What the clip actually shows** (73 raw frames, 3072×1024, 24fps, still camera):

- **Camera is genuinely still.** The hut, the woodpile, the fire-basket, the spyglass tripod and the ladder head sit pixel-stable across frames 0→30→60. Outer column bands carry ~0.35–0.5 residual — noise, not drift.
- **The mover is alive and bounded.** Per-column motion energy concentrates hard in bands 4–6 of 16 (3.99 / 4.69 / 2.46) — exactly the left-of-centre headwall where the cascade is authored. Everything else sits at 0.34–0.5. Moving-pixel fraction is **8.5%**: one bounded mover, not a frame-filling one.
- **No dead stretch and no real glitch.** Consecutive-frame diff runs steady at 1.0–1.7 for all 72 transitions. At the reported glitch point (77.8% ≈ frame 57) the diff is 1.17 — unremarkable. Breadth 0.021 on both readings confirms it.

So the near-zero return is exactly what a falling-water mover produces — a flowing mover never returns to its start configuration pixel-wise — and the frames confirm it's flow, not death. The worker read the gate correctly.

Against the reject list: no settings change proposed (the params are untouched: seed 4242, eg 0.7, 8 steps, cfg 2.0), the mover is bounded not frame-filling, zero return is used to park rather than to declare death, nothing is accepted and nothing is written into `scenario.json`, no hand-written art prompt, and no AUTHOR_MOVER on an unrendered mover. HOLD is the only move available — metrics may reject but never approve, so this belongs to your eye.

One thing for you to look at when you do view it, outside this gate's scope: the ladder reads as a low gate/stile at the parapet rather than the tall vertical pinned ladder the spec describes, and the cascade renders as several braided strands rather than "a single long fall". Both are stills-phase fidelity questions, not motion faults.

VERDICT: PASS
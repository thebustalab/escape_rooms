I extracted all 61 frames and checked independently rather than trusting the write-up.

**What I verified:**
- Box `[0.34,0.21,0.52,0.37]` → 1044,215–1597,378 (553×163 px), unchanged from spec.
- Cloud fills **21.9%** of the box (luma>130); the rest is flat sky — the dilution claim is real.
- Restricted to cloud pixels: temporal range p95 **29.9**, |f31−f01| p95 **11.1**, peak **52.0** luma levels. On sky pixels: p95 3.1. Whole-box p95 collapses to 5.85 purely from averaging in dead sky, which is how the judge got 4.50.
- Centroid over the loop: x 263.4→270.6 (**7.2 px** on a 3072-px frame), y within 0.8 px, returning to frame-0 position — stationary as the spec demands.
- Visually, the f01 vs f31 crops differ in interior mottling and the underside light band, and the ×12 diff draws a clean, coherent lens outline (rim + underside) against black sky — not noise. The bright speckle on the summit snow is isotropic grain with no edge displacement, consistent with `landmark_drift_px = 0`.

The one number I couldn't reproduce is "area breathes 5.6%" — I measure ~0.5% at my threshold — but that's threshold-dependent and doesn't bear on the conclusion. The diagnosis is grounded in the frames, the PASS on a "dead" subject is backed by native-resolution evidence as required, and the rerender alternative is genuinely unavailable: raising a whole-box p95 for a subject that must hold station would require making the cloud drift, which the spec's negatives forbid outright.

VERDICT: PASS
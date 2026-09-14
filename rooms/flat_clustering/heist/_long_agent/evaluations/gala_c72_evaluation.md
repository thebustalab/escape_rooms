I checked the room rather than the write-up.

**Provenance holds.** `scene.png` was written 2026-09-13 22:24; `gala_motion_ri70.mp4` at 2026-09-14 08:18 — the clip is of the re-authored pennant art, not the dead drapes version (ri32, 21:22 the previous evening).

**Frames confirm the motion read.** Frame 0 shows the pennant art as specced: one varnished staff left of centre with a single navy house pennant, narrow slice of frame, everything else laid and still. Differencing f0↔f36 gives one bright bounded blob at the pennant plus faint wake texture on the open water right — tables, crystal, seating plan, salver and drapes show nothing, not even edge warping. That is a bounded mover, not a frame-filling one.

**The 11.17 spike is the authored gesture, not a defect.** At 90.3% (frame ~66) the f65↔f66 difference is confined to the pennant's free end curling and snapping over — a few hundred pixels, no tiling, no structure elsewhere. Frame 66 itself is clean. Breadth 0.062 raw / 0.042 normalised is consistent with what the pixels show.

**Loop seam is sound.** f72 against f0 differs only in the pennant region; the rest is identical, so the return of 0.21 is cyclic flag motion, not drift.

The decision proposes no settings change, no re-author, no accept, and writes nothing into `scenario.json` — it leaves a clean clip standing for a human eye, which is the only thing this loop is allowed to do with a surviving clip. The duplicated vigour wording it flags is carried forward, not acted on, which is correct.

VERDICT: PASS
I verified the worker's central claim independently rather than taking it on trust.

**Death of the clip — confirmed, and not via the zero return.** I computed a per-pixel temporal std map on the raw render `kiln_motion_ri75.mp4` (73 frames, 3072×1024) and tiled it at 64 px, then ran the identical measurement across every sibling clip in the same `ri` series:

| room | median tile | hottest tile | ratio |
|---|---|---|---|
| **kiln** | 5.82 | **10.96** | **1.88** |
| spindle | 5.44 | 61.79 | 11.37 |
| hood | 4.37 | 46.04 | 10.53 |
| shears | 5.12 | 48.71 | 9.52 |
| anvil | 6.50 | 48.65 | 7.49 |
| broken_tooth | 5.50 | 39.64 | 7.20 |
| whistlegate | 3.79 | 24.03 | 6.35 |

Every live sibling puts a localised peak of 24–62 somewhere in frame. kiln's entire map is flat noise — rows 2–7 all sit between 4 and 8 — and its hottest tiles are all on the bottom-edge flagstones at y=960, i.e. on stone, not on the plume. Cyclic flow would still register high local temporal activity; it registers none. This is a frozen frame, established by direct measurement, so the "zero return is ambiguous" reject does not apply. Frame 0 does derive from the committed `scene.png` (correlation 0.89, same composition).

**Against the reject list:** no settings change; a flag on a staff is bounded, not frame-filling; death is not inferred from the return measure; nothing is accepted and nothing written to committed art or hotspots; the spec is authored rather than the prompt hand-written; and the existing juniper mover *was* rendered (cycle 75, clip on disk). `AUTHOR_MOVER` is the menu's own sanctioned response to a dead clip.

Two things the runner should carry forward, neither of them disqualifying. First, the worker's rationale leans on "diffuse is the failure mode," but canon says the opposite — "Diffuse is fine (smoke works); frame-filling is not," and hood's 3072 failure is attributed to frame-filling, not diffuseness. The decision survives on its other leg (the plume is low-contrast over high-frequency rock, and cloth is the demonstrated substrate), and choosing `AUTHOR_MOVER` over `ADJUST_VIGOUR` is worker judgement, not a gate violation. Second, the spec will now carry three declared movers — the juniper, `dome_banner.animate`, and the new flag — so the motion prompt must name the flag and nothing else.

VERDICT: PASS
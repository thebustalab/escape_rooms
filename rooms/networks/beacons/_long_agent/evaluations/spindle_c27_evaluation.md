I checked the room's state myself rather than taking the worker's word for it.

**Frames.** The `ri25` strip's own difference panel (`|mid − frame 0| ×8`) shows one bright region: the white signal cloth at the near left. The needle, the valley, the spyglass, the fire-basket and both path corridors are black.

**Independent measurement.** Per-tile temporal std on 73 extracted frames (4×16 grid):

- Peak **34.8** at x ≈ 0.06–0.25, y ≈ 0.25–0.75 — the `day_cloth` position, plus **11.7** at the bottom-left tile, consistent with the authored "weighted lower corners kicking".
- Every other tile sits at **1.7–2.4**, the noise floor. The needle band carries no spindrift signal, so the element the re-author brief demoted is genuinely still.
- Background tiles at the noise floor also independently confirm the camera is locked off.
- Distance from frame 0 rises to ~6.1 mid-clip and falls back to ~3.8 at the end — a real out-and-back, not one-way drift. The gate's 0.14 return is non-zero and the worker does not lean on it.

**Worker's claims.** `exp_art_prompt.motion_prompt` (cinemagraph_tools/exp_art_prompt.py:88-107) does resolve `authoring.sceneSpec` first and falls back to the `.txt` only when the spec yields nothing — so the stale spindrift file at websites/thebustalab.github.io/escape_rooms/cinemagraph_tools/art_prompt_motion/beacons/spindle.txt is inert, exactly as claimed, and the frames confirm the cloth prompt is what rendered. The params.json matches the house recipe, though it records no mask field, so the `mask=None` claim rests on the code path, not that file — immaterial, since the measured motion map shows an unmasked render behaving correctly anyway.

**Against the reject list.** No settings change is proposed. The mover is bounded, not frame-filling. The return is non-zero and not treated as proof of death. No clip is accepted and nothing is written to `scenario.json`. No prompt is hand-written. No AUTHOR_MOVER on an unrendered mover. HOLD is the designed terminal state here — the loop auto-rejects but never auto-approves, so a clip that clears all three gates with one correctly-bounded mover is precisely what gets parked for Lucas's eye.

VERDICT: PASS
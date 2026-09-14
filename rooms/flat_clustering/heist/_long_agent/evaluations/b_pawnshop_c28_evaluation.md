I checked the frames and the on-disk state rather than the worker's summary.

**Verified independently:**
- **Mover is bounded.** Frame-difference profile across 16 vertical bands on the raw clip: motion concentrates in bands 2–3 (left beaded curtain) and 12–13 (right beaded doorway) at mean 4–10, against a 1.2–2.2 background floor everywhere else. The diff map shows the shelves, ledger, terminal, window and stair all still. Two doorway-width strips, not a frame-filling mover.
- **Camera gate.** Re-ran `cine_camera_check.py`: "one object moving (camera still)". Render log confirms `frame0_corr 0.946`, `landmark_drift_px 0` — those numbers are real, not invented (`outputs/b_pawnshop_ri26_render.log:2`).
- **Glitch gate.** Re-ran `cine_glitch_check.py`: breadth 0.0%. `cine_room.py:44` sets `GLITCH_BREADTH_REJECT = 0.70` and line 76–77 takes `min()` of raw and brightness-normalised — both are 0.0. Clear pass.
- **Return.** 0.14 is the RAW-clip measure, as `cine_room.py:59` requires ("the crossfade forges a return"). My run on the looped file gives 0.52, which is the forged figure — the worker used the right one. Non-zero either way, so the ambiguous-zero trap isn't in play.
- **Motion prompt provenance.** `art_prompt_motion/heist/` holds exactly a_gallery, a_vault, b_casino, b_docks — no b_pawnshop, as claimed. The spec's `beads` element carries `motion.{moves, vigour, phrase}`, so the prompt came from the spec, not a hand-written string.

**Two things to note, neither a rejection ground:**
- Both beaded curtains animate — the `beads` element on the left and the `on` doorway on the right. The spec describes `on` as "the beaded doorway through to the street", so this is depicted-consistent, and both remain bounded.
- The observer log records a `room_iterate` crash at 20:41:52 (`ffmpeg: moov atom not found`) — that was a read of the looped mp4 while it was still being written at 20:42:25. The file probes clean now (61 frames, 3072×1024) and the gate report was written at 20:43:09, after. Stale race, not a broken artefact.

The decision proposes no settings change, no re-author, no acceptance, and no scenario.json write. It parks a gate-surviving clip for the human eye, which is the only move left.

VERDICT: PASS
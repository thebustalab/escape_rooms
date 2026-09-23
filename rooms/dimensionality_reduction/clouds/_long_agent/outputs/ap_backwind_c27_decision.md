I've read the pipeline, the ledger's return-fraction calibration, the handoff's metric-trust table, and the room's own records. Summary of what I found:

**The render happened and it's clean.** `ap_backwind_motion_ri25.params.json` is the settled recipe exactly — 3072x1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242 — and both the raw and looped mp4s are on disk.

**Every reject-only gate cleared, with margin:**
- camera: `one object moving (camera still)` — the intended outcome, same label ap_grainrun and ap_halflight were held on
- glitch: breadth 0.125 on both readings against a 0.70 threshold on both (spike 16.85 is reported, never enforced)
- dead: ratio 8.5, peak 12.17 — well clear of the <1.75 / <0.45 reject lines

**The return/peak pair lands on top of a labelled ALIVE clip.** The ledger's calibration table has `station1 .60` at peak 18.1 / return 0.69, labelled ALIVE; ap_backwind is peak 17.84 / return 0.69. a_vault, the most unmistakably alive clip in the set, sits higher still at 38.4 / 0.90. So the high peak relative to its siblings in this scenario (8–13) is amplitude, not a fault — and there is no gate on amplitude, by design: the peak/mean ratio was tested as a glitch discriminator and rejected because real motion has high frame differences too.

**The one open question from cycle 25's evaluation is answered by the numbers.** The evaluator flagged the risk that the video model would translate the whole derelict glider rather than just flap its wing. Net travel is monotone and drives return toward 0.00; this clip returns 0.69, a strong out-and-back arc, and the camera gate reads still. Nothing to pin, and pre-emptive rigid clauses are the documented cause of camera drift.

Nothing to soften, nothing to re-author, nothing to pin. No metric may approve, so this goes to the eye.

DECISION: HOLD
WHY: The single render at the settled recipe cleared camera, glitch and dead with wide margins and returned 0.69 at peak 17.84 — the ledger's labelled-ALIVE `station1` point almost exactly — so there is no defect to act on and the only step left is Lucas's eye.
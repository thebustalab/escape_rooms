I've read the four evidence documents and inspected the actual artefacts rather than relying on the summary. Findings:

**The spec and the still are consistent.** The committed `scenePrompt` is byte-identical to `scene_spec.render_prompt(spec)`, and `scene.png` (12:29) predates the ri84 render (13:24). The spec-derived motion prompt resolves to the short smoke phrase; the stale `.txt` fallback is not the source of truth.

**The gate report is a clean pass.** Camera still. Glitch breadth 0.167 raw and 0.167 normalised — both far below the 0.70 two-reading threshold. Return 0.07, above the 0.05 drift floor, and this mover is cyclic flow anyway, where the ledger records three wrong calls from trusting amplitude.

**The low `peak` of 4.82 is the known metric failure, not a dead clip.** I measured the raw render spatially, the way the a_opera evaluation did. Temporal std maps to a bounded cluster at x 0.06–0.31, mid-height — the ashtray, cigar and smoke over the near baize — peaking at 9.97 against a still background of 0.7–0.8 across the entire right half of the frame. A ~12x contrast, tightly localised, with everything else stationary. That is the signature the pipeline is built to produce, and it is nothing like a_opera's dead ri78 (band 0.83 against a frame median of 0.86, no contrast at all). `peak` under-reads a bounded mover because it is a whole-frame mean.

**The dial-back landed, modestly.** Against ri14, the clip Lucas called "way too quickly": band frame-to-frame change fell 0.591 → 0.493 and the speed ratio 0.182 → 0.163, while the rest of the room quietened substantially (frame median 2.573 → 1.418). Whether that is far enough is his call, not a metric's — and it is a different still now, so his ri14 comment does not transfer cleanly. Softening blind here would repeat exactly what cost a_opera its budget at cycle 81, where an unseen over-softening rendered dead.

Lucas's `review_note` for this room said: new art, render once and gate, no re-authoring. That is done, and nothing rejected.

DECISION: HOLD
WHY: The clip cleared every gate — camera still, glitch breadth 0.167 on both readings, return 0.07 — and an independent spatial measurement confirms a bounded, well-localised left-side mover at ~12x contrast against a stationary remainder, so the low whole-frame `peak` is the documented cyclic-flow metric failure rather than a dead room, and the only question left (is the smoke still too quick on this new still?) is one no metric may answer.
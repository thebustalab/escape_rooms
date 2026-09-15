I've read the four evidence documents and checked the room's actual state on disk rather than the brief's summary. Findings:

**The brief's quoted motion prompt is the stale `.txt` fallback, not what will be used.** `scene_spec.render_motion_prompt` resolves from the spec and returns the 38-word house form: *"…The ribbon of smoke rising slowly and steadily from the smouldering cigar in the ashtray and spreading very gently across the near baize. Only that moves…"* The spec is the source of truth (pipeline step 2), and it carries exactly one bounded mover — `smoke` at "to the left", with `motion.{moves,vigour,phrase}` all authored and the vigour already softened to "drifting very slowly, barely moving in the still air".

**The still is current and was generated from this exact spec.** `authoring.scenePrompt` is byte-identical to `scene_spec.render_prompt(spec)`. `scene.png` was committed 2026-09-14 14:26:10, seam staged `blurred`, `needsWork: false`. I looked at the left third at native resolution: the cut-glass ashtray is there with the cigar tip live and orange, one thin ribbon climbing from it, and a low bank of smoke over the near baize — bounded to roughly x 0.06–0.31, not frame-filling, and depicted at the quiet vigour the spec asks for.

**No clip exists for this art.** The newest render, `b_casino_motion_ri84`, is 13:26 today — an hour *older* than the still. It animates the superseded 12:29 panorama, which is why `state.json` reset this room to `{"art_generated": 1}` and the gate report is empty. The plan's own done criterion forbids counting a clip whose still postdates it.

Nothing here justifies touching the vigour or the phrase: the "way too quickly" note Lucas made was against ri14 on a different still, the dial-back is already authored into this spec, and softening blind is what cost a_opera its budget at cycle 81.

```
DECISION: RENDER
WHY: The spec declares one bounded, vigour-authored mover that the committed 14:26 still visibly depicts, the art prompt and the spec-derived motion prompt both resolve clean from that same spec, and the only existing clip predates the still by an hour — so a single render at the pinned 0.70 and a gate is the one thing owed.
```
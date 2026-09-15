I've read the four evidence documents and verified the room's live state against the artefacts.

**What cycle 8 left behind.** It rewrote `cirque_tarn.motion.phrase` only, fixing the migration artefact that had the motion prompt asking for a signal lantern the panorama does not contain. I confirmed the fix landed: the live `scenario.json` spec now carries `phrase` = the cat's-paws sentence, and `scene_spec.render_motion_prompt` on that spec returns exactly the 38-word house-form prompt, with the mover named and nothing else.

**What I checked before deciding to spend GPU:**

- **The mover is real, bounded and depicted.** `cirque_tarn` carries `motion.moves/vigour/phrase`, so `_has_authored_mover` sees it. Prior evaluation placed it at roughly x 0.26–0.49, y 0.58–0.80 — a quarter of the frame, not frame-filling — and this room's own `cine_base.judge.json` already scored `tarn_surface` alive at p95 15.63 on this same art.
- **The art is committed and human-accepted**, seam `accepted: true`, `acceptedBy: "lucas 2026-09-03"`, `needsWork: false`, `seamBandRun 0.015` — well inside the accepted range. Re-authoring would discard a panorama Lucas signed off.
- **No rigid-clause bloat risk.** `exp_art_prompt` switches `rigid=True` on `sceneSpec.rigid` or any element `motion.still_as`; this sceneSpec has neither. The long inventory sits in `authoring.motionSpec.rigid`, which that path does not read — so the prompt stays at 38 words rather than ballooning into the a_opera camera-drift failure.
- **No clip exists for this state.** `state.json` shows rams_head with `retries: 1`, no `attempts`, no `last_gate`, no `clip` — and the gate report is empty. The mp4s on disk date to 2026-09-09, rendered against the stale lantern prompt, so nothing on disk tests the current spec.

The spec and the prompt are both right and untested. That is the RENDER case exactly — one render at the default, not a re-author and not a prompt edit.

DECISION: RENDER
WHY: The spec carries one bounded mover the committed, human-accepted still visibly depicts, cycle 8's phrase fix means the spec-derived motion prompt now names that mover and nothing else, and no clip has ever been rendered against this corrected state — so the pipeline's single render at the default is the next step.
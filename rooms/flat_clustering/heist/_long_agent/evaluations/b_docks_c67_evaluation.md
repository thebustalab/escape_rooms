Checked every claim against the tree rather than the worker's summary:

- **Spec** — `b_docks` carries exactly one mover, `tarp`, with `motion.moves`, a vigour and a phrase. `_has_authored_mover` will pass, so the RENDER branch won't refuse.
- **Art** — I looked at `scene.png` (3072x1024) at native scale. The tarpaulin is a lashed-back panel roped to the left jamb with its lower corner hanging free into the hatch opening, about 8% of frame width. That's a bounded mover, and it matches the re-authored desc, not the old "lashed at the open loading hatch" one.
- **Timing** — `scene.png` is 2026-09-13 22:23:56; the newest b_docks clip, `ri8`, is 17:36 the same day. The still is five hours newer, so this art genuinely has no clip.
- **Prompts** — `scenePrompt` on disk is byte-identical to `render_prompt(sceneSpec)` (3242 chars both), seam screened 22:24 with `needsWork: false`. And the worker's "for the record" note is right: `exp_art_prompt.motion_prompt` takes the spec over the `.txt` fallback, and `render_motion_prompt` returns exactly the softened sentence it quoted.
- **Runner state** — `b_docks` has no entry in `state.json` yet: no `needs_still`, zero attempts against a cap of 2, no pending render. The RENDER will actually launch at the plan's pinned end guide 0.70 rather than being parked.

No settings lever, no frame-filling mover, no zero-return reasoning, no clip acceptance, no hand-written prompt, and it isn't AUTHOR_MOVER.

VERDICT: PASS
I checked the frames and the spec directly rather than taking the worker's word.

**Verified against disk:**

- **Live spec is `scenario.json` → `rooms[b_casino].authoring.sceneSpec`**, and it matches the brief exactly — `smoke` carries `motion.{moves, vigour, phrase}` with the vigour already softened to "drifting very slowly, barely moving in the still air." (Note: `scene_specs_heist.json` on disk still holds a stale b_casino spec with no `motion` block at all — a seed file, not the source of truth, but worth cleaning up later.)
- **Art prompt is spec-derived, not hand-written.** `scene_spec.render_prompt(spec) == authoring.scenePrompt` returns `True`.
- **Motion prompt resolves clean from the same spec** — I ran it: *"locked-off static camera, zero camera movement. The ribbon of smoke rising slowly and steadily from the smouldering cigar in the ashtray and spreading very gently across the near baize. Only that moves; everything else stays perfectly still. Seamless natural loop."* One mover, explicitly pinned. (40 words, not the worker's 38 — immaterial.)
- **The mover is bounded and actually depicted.** I cropped the left third of the committed `scene.png` at native resolution: the cut-glass ashtray is there with the cigar tip live and orange and a single ribbon climbing from it, sitting around x≈0.17–0.27. A ribbon from a cigar is not a frame-filling mover.
- **No clip exists for this art.** Newest render `b_casino_motion_ri84` is 13:24/13:26 today; `scene.png` is 14:26:09 — the still postdates the clip by an hour. `state.json` shows `b_casino: {"art_generated": 1}`, no clip, no gate.
- **0.70 is not a settings change.** Every `params.json` on disk — ri14, ri58, ri84, and a_opera's held ri94 — is end_guide 0.7, cfg 2.0, steps 8, seed 4242, length 73. "Render at the pinned 0.70" means touching nothing.

**Against the reject list:** no settings change; mover is bounded; no zero return is invoked (the gate report is empty); nothing is accepted and nothing is written to committed art or hotspots; the prompt is authored through the spec; and it's RENDER, not AUTHOR_MOVER off an unrendered mover. None of the six conditions fires.

One item the worker didn't mention, not a blocker: the seam record carries `humanNote: "STAGE RESET: recorded 'blurred' predates this image file…"` with `accepted: false`. That's a stills-phase loose end for Lucas's eye, and it has no bearing on whether this render should go.

VERDICT: PASS